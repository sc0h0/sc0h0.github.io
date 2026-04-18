import base64
import csv
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

import requests
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================

GITHUB_TOKEN = ""

CANDIDATES_FILE = "melbourne_candidates.csv"
REVIEW_FILE = "candidate_code_reviews.csv"
STATE_FILE = "simple_02_state.json"

MODEL = "gpt-5.4"



MAX_REPOS_PER_CANDIDATE = 4

# New per-language limits
MAX_RECENT_SQL_FILES_PER_REPO = 10
MAX_RECENT_PY_FILES_PER_REPO = 10

MAX_FILE_BYTES = 80_000
MAX_TOTAL_CHARS_PER_CANDIDATE = 120_000
MAX_CHARS_PER_FILE = 4000
HTTP_SLEEP_SECONDS = 0.6
COMMITS_TO_SCAN_PER_REPO = 40

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="key",  # ignored by ChatMock
)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

INCLUDE_EXTENSIONS = {".sql", ".py"}

SKIP_DIR_HINTS = (
    "node_modules/", ".venv/", "venv/", "__pycache__/", ".git/", "dist/", "build/",
    ".mypy_cache/", ".pytest_cache/", "site-packages/", "vendor/",
)

SKIP_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".zip", ".parquet", ".csv", ".xls", ".xlsx", ".pdf"
)

FIELDNAMES = [
    "username",
    "github_url",
    "review_status",
    "reviewed_repo_names",
    "reviewed_file_count",
    "sql_skill_score",
    "sql_skill_confidence",
    "python_skill_score",
    "python_skill_confidence",
    "commenting_quality_score",
    "sql_structuring_score",
    "sql_python_interop_score",
    "segmentation_score",
    "collections_domain_score",
    "collections_domain_confidence",
    "technical_overall_score",
    "fit_for_junior_data_analyst",
    "fit_for_collections_analytics",
    "evidence_summary",
    "key_strengths",
    "key_gaps",
    "red_flags",
    "scanned_at",
]


def load_json(path: str, default: Dict) -> Dict:
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def gh_get(url: str, params: Optional[Dict] = None) -> requests.Response:
    while True:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=60)

        if resp.status_code == 403:
            reset_time = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset_time - int(time.time()), 5) + 5
            print(f"  github rate limit hit, waiting {wait}s")
            time.sleep(wait)
            continue

        return resp


def ensure_review_file() -> None:
    if not os.path.exists(REVIEW_FILE) or os.path.getsize(REVIEW_FILE) == 0:
        with open(REVIEW_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def read_reviewed_usernames() -> Set[str]:
    ensure_review_file()
    out: Set[str] = set()
    with open(REVIEW_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get("username", "").strip()
            if username:
                out.add(username)
    return out


def append_review(row: Dict[str, str]) -> None:
    ensure_review_file()
    with open(REVIEW_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)


def read_candidates() -> List[Dict[str, str]]:
    if not os.path.exists(CANDIDATES_FILE):
        raise RuntimeError(f"Missing {CANDIDATES_FILE}. Run simple_01.py first.")
    with open(CANDIDATES_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_repos(username: str) -> List[Dict]:
    resp = gh_get(
        f"https://api.github.com/users/{username}/repos",
        params={"per_page": 100, "sort": "updated"},
    )
    if resp.status_code == 200:
        return resp.json()
    return []


def choose_relevant_repos(repos: List[Dict]) -> List[Dict]:
    personal_repos = [r for r in repos if not r.get("fork")]
    scored: List[Tuple[int, Dict]] = []

    for repo in personal_repos:
        score = 0
        text = f"{repo.get('name', '')} {repo.get('description', '') or ''}".lower()
        language = (repo.get("language") or "").lower()

        if language in {"python"}:
            score += 4
        if any(word in text for word in [
            "sql", "analysis", "analytics", "dashboard", "segmentation",
            "collections", "debt", "etl", "dbt", "notebook", "python"
        ]):
            score += 4
        if repo.get("stargazers_count", 0) > 0:
            score += 1
        if repo.get("pushed_at"):
            score += 2

        scored.append((score, repo))

    scored.sort(key=lambda x: (x[0], x[1].get("pushed_at") or ""), reverse=True)
    return [repo for _, repo in scored[:MAX_REPOS_PER_CANDIDATE]]


def get_repo_default_branch(owner: str, repo: str) -> Optional[str]:
    resp = gh_get(f"https://api.github.com/repos/{owner}/{repo}")
    if resp.status_code == 200:
        return resp.json().get("default_branch")
    return None


def is_relevant_code_path(path: str) -> bool:
    lowered = path.lower()

    if any(hint in lowered for hint in SKIP_DIR_HINTS):
        return False
    if lowered.endswith(SKIP_SUFFIXES):
        return False

    return any(lowered.endswith(ext) for ext in INCLUDE_EXTENSIONS)


def clean_text_for_llm(text: str) -> str:
    cleaned = []
    for ch in text:
        o = ord(ch)
        if ch in "\n\r\t" or 32 <= o <= 126 or o >= 160:
            cleaned.append(ch)
    return "".join(cleaned)


def get_recent_sql_and_py_files_from_commits(owner: str, repo: str, branch: str) -> List[str]:
    resp = gh_get(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        params={"sha": branch, "per_page": COMMITS_TO_SCAN_PER_REPO},
    )
    if resp.status_code != 200:
        return []

    commits = resp.json()

    sql_paths: List[str] = []
    py_paths: List[str] = []
    sql_seen: Set[str] = set()
    py_seen: Set[str] = set()

    for commit in commits:
        sha = commit.get("sha")
        if not sha:
            continue

        detail = gh_get(f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}")
        if detail.status_code != 200:
            time.sleep(HTTP_SLEEP_SECONDS)
            continue

        files = detail.json().get("files", [])

        for f in files:
            path = f.get("filename", "")
            lowered = path.lower()
            status = (f.get("status") or "").lower()

            if status not in {"added", "modified"}:
                continue
            if not is_relevant_code_path(path):
                continue

            if lowered.endswith(".sql"):
                if path not in sql_seen and len(sql_paths) < MAX_RECENT_SQL_FILES_PER_REPO:
                    sql_paths.append(path)
                    sql_seen.add(path)

            elif lowered.endswith(".py"):
                if path not in py_seen and len(py_paths) < MAX_RECENT_PY_FILES_PER_REPO:
                    py_paths.append(path)
                    py_seen.add(path)

            if (
                len(sql_paths) >= MAX_RECENT_SQL_FILES_PER_REPO
                and len(py_paths) >= MAX_RECENT_PY_FILES_PER_REPO
            ):
                return sql_paths + py_paths

        time.sleep(HTTP_SLEEP_SECONDS)

    return sql_paths + py_paths


def get_contents(owner: str, repo: str, path: str) -> Optional[str]:
    resp = gh_get(f"https://api.github.com/repos/{owner}/{repo}/contents/{path}")
    if resp.status_code != 200:
        return None

    payload = resp.json()
    if payload.get("encoding") == "base64":
        raw = base64.b64decode(payload.get("content", ""))
        if len(raw) > MAX_FILE_BYTES:
            return None
        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return None

    return None


def build_candidate_packet(username: str) -> Tuple[Dict, str]:
    repos = get_repos(username)
    chosen_repos = choose_relevant_repos(repos)

    packet = {
        "username": username,
        "repos": [],
    }
    total_chars = 0
    reviewed_file_count = 0

    for repo in chosen_repos:
        owner = repo.get("owner", {}).get("login", username)
        repo_name = repo.get("name", "")
        branch = get_repo_default_branch(owner, repo_name)
        if not branch:
            continue

        recent_paths = get_recent_sql_and_py_files_from_commits(owner, repo_name, branch)

        repo_entry = {
            "repo_name": repo_name,
            "description": repo.get("description", "") or "",
            "language": repo.get("language", "") or "",
            "pushed_at": repo.get("pushed_at", "") or "",
            "files": [],
        }

        sql_count = 0
        py_count = 0

        for path in recent_paths:
            content = get_contents(owner, repo_name, path)
            if not content:
                continue

            content = clean_text_for_llm(content)

            if not content.strip():
                continue

            content = content[:MAX_CHARS_PER_FILE]
            projected = total_chars + len(content)
            if projected > MAX_TOTAL_CHARS_PER_CANDIDATE:
                break

            repo_entry["files"].append({
                "path": path,
                "content": content,
            })
            reviewed_file_count += 1
            total_chars += len(content)

            lowered = path.lower()
            if lowered.endswith(".sql"):
                sql_count += 1
            elif lowered.endswith(".py"):
                py_count += 1

            time.sleep(HTTP_SLEEP_SECONDS)

        if repo_entry["files"]:
            print(f" repo={repo_name} sql_files={sql_count} py_files={py_count}", end=" ", flush=True)
            packet["repos"].append(repo_entry)

        if total_chars >= MAX_TOTAL_CHARS_PER_CANDIDATE:
            break

    packet_text = json.dumps(packet, ensure_ascii=False)

    return {
        "reviewed_repo_names": " | ".join([r["repo_name"] for r in packet["repos"]]),
        "reviewed_file_count": reviewed_file_count,
    }, packet_text


def extract_first_json_object(text: str) -> Dict:
    text = (text or "").strip()
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object start found in model output.")

    depth = 0
    in_str = False
    esc = False
    end = None

    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

    if end is None:
        raise ValueError("No complete JSON object found in model output.")

    return json.loads(text[start:end])


def score_candidate_with_chatgpt(username: str, packet_text: str) -> Optional[Dict]:
    prompt = f"""You are reviewing public GitHub code for evidence of junior-to-early-career analytics skill.

Candidate username: {username}

Assess the candidate on:
1. SQL skill
2. Python skill
3. Commenting/documentation quality
4. SQL decomposition and readability
5. SQL-Python interoperability
6. Segmentation / analytical thinking
7. Collections / debt-recovery domain evidence

Important rules:
- Use only the supplied repo/file evidence.
- Do not infer collections expertise unless there is explicit evidence.
- Prefer conservative scoring when evidence is weak.
- Mention concrete repo/file/path-based evidence when possible.
- Return STRICT JSON ONLY.

Return JSON with EXACT keys:
{{
  "review_status": "reviewed",
  "sql_skill_score": 0,
  "sql_skill_confidence": "low",
  "python_skill_score": 0,
  "python_skill_confidence": "low",
  "commenting_quality_score": 0,
  "sql_structuring_score": 0,
  "sql_python_interop_score": 0,
  "segmentation_score": 0,
  "collections_domain_score": 0,
  "collections_domain_confidence": "low",
  "technical_overall_score": 0,
  "fit_for_junior_data_analyst": "no",
  "fit_for_collections_analytics": "no",
  "evidence_summary": "",
  "key_strengths": [],
  "key_gaps": [],
  "red_flags": []
}}

Scoring guidance:
- Use 0 only when there is effectively no evidence.
- Use conservative scoring for sparse or mixed evidence.
- Keep evidence_summary concise but specific.
- key_strengths, key_gaps, red_flags should each be short lists of strings.

Repository packet:
{packet_text}
""".strip()

    for attempt in range(5):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
            )
            raw = (resp.choices[0].message.content or "").strip()
            return extract_first_json_object(raw)

        except Exception as e:
            msg = str(e)

            if "429" in msg:
                wait = 2 ** attempt
                print(f"  chatgpt rate limited for {username}, retrying in {wait}s")
                time.sleep(wait)
                continue

            debug_path = f"debug_error_{username}.txt"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(f"ERROR:\n{msg}\n\n")
                f.write(f"PROMPT_CHARS={len(prompt)}\n")
                f.write(f"PACKET_CHARS={len(packet_text)}\n")
            print(f"  chatgpt error for {username}: {e}")
            print(f"  debug saved to {debug_path}")
            return None

    return None


def main() -> None:
    if not GITHUB_TOKEN or GITHUB_TOKEN == "PUT_GITHUB_TOKEN_HERE":
        raise RuntimeError("Put a valid GitHub token into GITHUB_TOKEN before running.")

    ensure_review_file()
    reviewed = read_reviewed_usernames()
    state = load_json(STATE_FILE, {"last_username": ""})

    candidates = read_candidates()
    print(f"Loaded {len(candidates)} stage-1 candidates from {CANDIDATES_FILE}")

    processed = 0
    for idx, row in enumerate(candidates, start=1):
        username = row.get("username", "").strip()
        if not username or username in reviewed:
            continue

        print(f"[{idx}/{len(candidates)}] reviewing {username}...", end=" ", flush=True)

        try:
            repo_meta, packet_text = build_candidate_packet(username)
            print(
                f"packet_chars={len(packet_text)} "
                f"files={repo_meta['reviewed_file_count']}",
                end=" ",
                flush=True,
            )

            if repo_meta["reviewed_file_count"] == 0:
                review_row = {
                    "username": username,
                    "github_url": row.get("github_url", ""),
                    "review_status": "no_relevant_code_found",
                    "reviewed_repo_names": "",
                    "reviewed_file_count": 0,
                    "sql_skill_score": "",
                    "sql_skill_confidence": "",
                    "python_skill_score": "",
                    "python_skill_confidence": "",
                    "commenting_quality_score": "",
                    "sql_structuring_score": "",
                    "sql_python_interop_score": "",
                    "segmentation_score": "",
                    "collections_domain_score": "",
                    "collections_domain_confidence": "",
                    "technical_overall_score": "",
                    "fit_for_junior_data_analyst": "",
                    "fit_for_collections_analytics": "",
                    "evidence_summary": "No relevant recent .sql/.py files found within configured limits.",
                    "key_strengths": "",
                    "key_gaps": "",
                    "red_flags": "",
                    "scanned_at": datetime.now().isoformat(),
                }
                append_review(review_row)
                reviewed.add(username)
                save_json(STATE_FILE, {"last_username": username})
                print("no relevant code")
                continue

            review = score_candidate_with_chatgpt(username, packet_text)
            if not review:
                print("error from ChatGPT workaround, will retry next run")
                continue

            review_row = {
                "username": username,
                "github_url": row.get("github_url", ""),
                "review_status": review.get("review_status", "reviewed"),
                "reviewed_repo_names": repo_meta["reviewed_repo_names"],
                "reviewed_file_count": repo_meta["reviewed_file_count"],
                "sql_skill_score": review.get("sql_skill_score", ""),
                "sql_skill_confidence": review.get("sql_skill_confidence", ""),
                "python_skill_score": review.get("python_skill_score", ""),
                "python_skill_confidence": review.get("python_skill_confidence", ""),
                "commenting_quality_score": review.get("commenting_quality_score", ""),
                "sql_structuring_score": review.get("sql_structuring_score", ""),
                "sql_python_interop_score": review.get("sql_python_interop_score", ""),
                "segmentation_score": review.get("segmentation_score", ""),
                "collections_domain_score": review.get("collections_domain_score", ""),
                "collections_domain_confidence": review.get("collections_domain_confidence", ""),
                "technical_overall_score": review.get("technical_overall_score", ""),
                "fit_for_junior_data_analyst": review.get("fit_for_junior_data_analyst", ""),
                "fit_for_collections_analytics": review.get("fit_for_collections_analytics", ""),
                "evidence_summary": review.get("evidence_summary", ""),
                "key_strengths": " | ".join(review.get("key_strengths", [])),
                "key_gaps": " | ".join(review.get("key_gaps", [])),
                "red_flags": " | ".join(review.get("red_flags", [])),
                "scanned_at": datetime.now().isoformat(),
            }

            append_review(review_row)
            reviewed.add(username)
            processed += 1
            save_json(STATE_FILE, {"last_username": username})
            print(f"reviewed: overall={review.get('technical_overall_score', '')}")

        except Exception as e:
            print(f"error: {e} (will retry next run)")

        time.sleep(HTTP_SLEEP_SECONDS)

    print(f"Done. Reviewed {processed} candidates. Output: {REVIEW_FILE}")


if __name__ == "__main__":
    main()
