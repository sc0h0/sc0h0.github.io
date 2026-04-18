import csv
import json
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Iterable, List, Optional, Set, Tuple

import requests

# ============================================================
# CONFIG
# ============================================================

GITHUB_TOKEN = ""
OUTPUT_USERS_FILE = "melbourne_users.csv"
RESULTS_FILE = "melbourne_candidates.csv"
RUN_STATE_FILE = "simple_01_state.json"

SIX_MONTHS_AGO = datetime.now(timezone.utc) - timedelta(days=180)
SEARCH_SLEEP_SECONDS = 1.0
PROFILE_SLEEP_SECONDS = 0.25
MAX_SEARCH_PAGES_PER_QUERY = 10

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

SEARCH_QUERIES = [
    'location:"Melbourne" created:>2023-01-01',
    'location:"Melbourne Australia" created:>2023-01-01',
    'location:"Melbourne VIC" created:>2023-01-01',
    'location:"Melbourne Victoria" created:>2023-01-01',
    'location:"Geelong" created:>2023-01-01',
    'location:"Ballarat" created:>2023-01-01',
    'location:"Bendigo" created:>2023-01-01',
    'location:"Warrnambool" created:>2023-01-01',
    'location:"Shepparton" created:>2023-01-01',
]

MELBOURNE_BIO_HINTS = [
    "melbourne",
    "melbourne-based",
    "melbs",
    "melburnian",
    "melbournian",
]

VICTORIAN_UNI_TERMS = [
    "university of melbourne",
    "unimelb",
    "monash university",
    "monash",
    "rmit university",
    "rmit",
    "deakin university",
    "deakin",
    "la trobe university",
    "la trobe",
    "latrobe",
    "swinburne university",
    "swinburne",
    "victoria university",
    "vu melbourne",
    "federation university",
    "feduni",
    "melbourne business school",
]

GRAD_BIO_SIGNALS = [
    "student", "undergraduate", "postgraduate", "graduate", "grad student",
    "bachelor", "master", "phd", "studying", "final year", "first year",
    "second year", "third year", "fourth year", "recent grad", "new grad",
    "class of 2021", "class of 2022", "class of 2023", "class of 2024", "class of 2025", "class of 2026",
    "2021 grad", "2022 grad", "2023 grad", "2024 grad", "2025 grad", "2026 grad",
    "junior developer", "junior dev", "junior analyst", "entry level",
]

DATA_SKILL_SIGNALS = [
    "python", "sql", "tableau", "power bi", "powerbi", "excel",
    "pandas", "numpy", "matplotlib", "jupyter", "data analysis",
    "data analytics", "data science", "machine learning", "statistics",
    "business intelligence", "etl", "dbt", "spark", "bigquery",
]

NON_AUSTRALIA_SIGNALS = [
    "florida", " fl,", " fl ", ",fl", ", fl", " fl", "fl ",
    "united states", "usa", " us,", " us ", ", us",
    "canada", "united kingdom", " uk,", " uk ", "england", "scotland",
    "new zealand", "india", "germany", "france", "brazil", "singapore",
    "malaysia", "philippines", "nigeria", "ghana", "kenya", "pakistan",
    "bangladesh", "indonesia", "vietnam", "china", "japan", "korea",
    "california", "new york", "texas", "ontario", "british columbia",
    "london", "toronto", "vancouver", "auckland", "bangalore", "mumbai",
]

AUSTRALIA_SIGNALS = [
    "australia", "vic", "victoria", "nsw", "qld", "sa", "wa", "act", "nt",
    "melb", "aus,", "au,", ".au",
]

FIELDNAMES = [
    "username",
    "github_url",
    "status",
    "name",
    "location",
    "bio",
    "company",
    "created_at",
    "public_repos",
    "followers",
    "personal_repo_count",
    "recent_active_repo_count",
    "recent_active_repo_names",
    "active_languages",
    "uni_signals",
    "grad_signals",
    "data_skill_signals",
    "candidate_path",
    "summary_reason",
    "scanned_at",
]


def save_json(path: str, data: Dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def load_json(path: str, default: Dict) -> Dict:
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def gh_get(url: str, params: Optional[Dict] = None) -> requests.Response:
    while True:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=60)
        if resp.status_code == 403:
            reset_time = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset_time - int(time.time()), 5) + 5
            print(f"  rate limit hit, waiting {wait}s")
            time.sleep(wait)
            continue
        return resp


def safe_lower(x: Optional[str]) -> str:
    return (x or "").lower().strip()


def ensure_users_file() -> None:
    if not os.path.exists(OUTPUT_USERS_FILE) or os.path.getsize(OUTPUT_USERS_FILE) == 0:
        with open(OUTPUT_USERS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["username", "github_url", "status", "source_query"])
            writer.writeheader()


def ensure_results_file() -> None:
    if not os.path.exists(RESULTS_FILE) or os.path.getsize(RESULTS_FILE) == 0:
        with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def read_existing_users() -> Dict[str, Dict[str, str]]:
    ensure_users_file()
    users: Dict[str, Dict[str, str]] = {}
    with open(OUTPUT_USERS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get("username", "").strip()
            if username:
                users[username] = row
    return users


def append_users(new_rows: List[Dict[str, str]]) -> None:
    if not new_rows:
        return
    ensure_users_file()
    with open(OUTPUT_USERS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "github_url", "status", "source_query"])
        for row in new_rows:
            writer.writerow(row)


def update_user_status(username: str, new_status: str) -> None:
    ensure_users_file()
    rows: List[Dict[str, str]] = []
    with open(OUTPUT_USERS_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(OUTPUT_USERS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["username", "github_url", "status", "source_query"])
        writer.writeheader()
        for row in rows:
            if row.get("username") == username:
                row["status"] = new_status
            writer.writerow(row)


def read_results_usernames() -> Set[str]:
    ensure_results_file()
    out: Set[str] = set()
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = row.get("username", "").strip()
            if username:
                out.add(username)
    return out


def append_result(row: Dict[str, str]) -> None:
    ensure_results_file()
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)


def search_users_by_queries() -> None:
    state = load_json(RUN_STATE_FILE, {"phase": "search", "query_index": 0, "page": 1})
    existing = read_existing_users()

    if state.get("phase") != "search":
        print("Search phase already completed earlier.")
        return

    for q_index in range(state["query_index"], len(SEARCH_QUERIES)):
        query = SEARCH_QUERIES[q_index]
        page_start = state["page"] if q_index == state["query_index"] else 1
        print(f"[search] query {q_index + 1}/{len(SEARCH_QUERIES)}: {query}")

        for page in range(page_start, MAX_SEARCH_PAGES_PER_QUERY + 1):
            resp = gh_get(
                "https://api.github.com/search/users",
                params={"q": query, "per_page": 100, "page": page},
            )
            if resp.status_code != 200:
                print(f"  search error {resp.status_code} on page {page}")
                save_json(RUN_STATE_FILE, {"phase": "search", "query_index": q_index, "page": page})
                return

            items = resp.json().get("items", [])
            if not items:
                break

            rows_to_add: List[Dict[str, str]] = []
            for item in items:
                username = item.get("login", "").strip()
                if not username or username in existing:
                    continue
                row = {
                    "username": username,
                    "github_url": f"https://github.com/{username}",
                    "status": "pending",
                    "source_query": query,
                }
                existing[username] = row
                rows_to_add.append(row)

            append_users(rows_to_add)
            print(f"  page {page}: {len(items)} raw users, {len(rows_to_add)} new appended to {OUTPUT_USERS_FILE}")

            save_json(RUN_STATE_FILE, {"phase": "search", "query_index": q_index, "page": page + 1})
            time.sleep(SEARCH_SLEEP_SECONDS)

        save_json(RUN_STATE_FILE, {"phase": "search", "query_index": q_index + 1, "page": 1})

    save_json(RUN_STATE_FILE, {"phase": "scan", "last_username": ""})
    print(f"Search phase finished. Review {OUTPUT_USERS_FILE} if you want before scanning.")


def get_user_profile(username: str) -> Optional[Dict]:
    resp = gh_get(f"https://api.github.com/users/{username}")
    if resp.status_code == 200:
        return resp.json()
    return None


def get_repos(username: str) -> List[Dict]:
    resp = gh_get(
        f"https://api.github.com/users/{username}/repos",
        params={"per_page": 100, "sort": "updated"},
    )
    if resp.status_code == 200:
        return resp.json()
    return []


def detect_signals(text: str, terms: Iterable[str]) -> List[str]:
    lower_text = safe_lower(text)
    return [term for term in terms if term in lower_text]


def is_likely_melbourne_or_victoria(location: str, bio: str, company: str) -> Tuple[bool, str]:
    loc = safe_lower(location)
    combined = f"{safe_lower(bio)} {safe_lower(company)}"

    for signal in NON_AUSTRALIA_SIGNALS:
        if signal in loc:
            return False, f"non-AU signal in location: {signal}"

    if "melbourne" in loc or "melbs" in loc or "victoria" in loc or " vic" in loc or loc == "vic":
        return True, "Melbourne/Victoria signal in location"

    for signal in AUSTRALIA_SIGNALS:
        if signal in loc:
            return True, f"Australia signal in location: {signal}"

    if any(hint in combined for hint in MELBOURNE_BIO_HINTS):
        return True, "Melbourne hint in bio/company"

    uni_hits = detect_signals(combined, VICTORIAN_UNI_TERMS)
    if uni_hits:
        return True, "Victorian uni signal in bio/company"

    return False, "no convincing Melbourne/Victoria signal"


def check_recent_personal_activity(repos: List[Dict]) -> Tuple[bool, List[Dict]]:
    active_repos: List[Dict] = []
    for repo in repos:
        if repo.get("fork"):
            continue
        pushed_at = repo.get("pushed_at")
        if not pushed_at:
            continue
        pushed_dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        if pushed_dt >= SIX_MONTHS_AGO:
            active_repos.append({
                "name": repo.get("name", ""),
                "description": repo.get("description", "") or "",
                "pushed_at": pushed_at,
                "language": repo.get("language", "") or "",
                "stars": repo.get("stargazers_count", 0),
            })
    return len(active_repos) > 0, active_repos


def classify_candidate_path(profile: Dict, repos: List[Dict], active_repos: List[Dict]) -> Tuple[bool, str]:
    bio = profile.get("bio") or ""
    company = profile.get("company") or ""
    location = profile.get("location") or ""
    repo_text = " ".join(
        f"{r.get('name', '')} {r.get('description', '') or ''} {r.get('language', '') or ''}"
        for r in repos if not r.get("fork")
    )

    location_ok, reason = is_likely_melbourne_or_victoria(location, bio, company)
    uni_hits = detect_signals(f"{bio} {company}", VICTORIAN_UNI_TERMS)
    grad_hits = detect_signals(f"{bio} {company}", GRAD_BIO_SIGNALS)
    data_hits = detect_signals(f"{bio} {company} {repo_text}", DATA_SKILL_SIGNALS)

    if location_ok and (grad_hits or uni_hits):
        return True, f"local + uni/grad signals ({reason})"
    if location_ok and data_hits and active_repos:
        return True, f"local + data/project signals ({reason})"
    if uni_hits and active_repos:
        return True, "Victorian uni signal + recent personal activity"
    if grad_hits and active_repos and data_hits:
        return True, "grad signal + recent personal activity + data skills"
    if location_ok and active_repos:
        return True, f"local + recent personal activity ({reason})"

    return False, "did not meet simple stage-1 inclusion logic"


def scan_pending_users() -> None:
    state = load_json(RUN_STATE_FILE, {"phase": "search", "query_index": 0, "page": 1})
    if state.get("phase") == "search":
        print("Search phase has not been completed yet.")
        return

    ensure_users_file()
    ensure_results_file()

    result_usernames = read_results_usernames()

    with open(OUTPUT_USERS_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    pending_rows = [row for row in rows if row.get("status") == "pending"]
    print(f"Scanning {len(pending_rows)} pending users...")

    for idx, row in enumerate(pending_rows, start=1):
        username = row["username"]
        if username in result_usernames:
            update_user_status(username, "done")
            continue

        print(f"[{idx}/{len(pending_rows)}] {username}...", end=" ", flush=True)

        try:
            profile = get_user_profile(username)
            if not profile:
                print("no profile")
                update_user_status(username, "done")
                save_json(RUN_STATE_FILE, {"phase": "scan", "last_username": username})
                continue

            repos = get_repos(username)
            personal_repos = [r for r in repos if not r.get("fork")]
            is_active, active_repos = check_recent_personal_activity(repos)

            include, summary_reason = classify_candidate_path(profile, repos, active_repos)
            if not include:
                print(f"skip: {summary_reason}")
                update_user_status(username, "done")
                save_json(RUN_STATE_FILE, {"phase": "scan", "last_username": username})
                time.sleep(PROFILE_SLEEP_SECONDS)
                continue

            bio = profile.get("bio") or ""
            company = profile.get("company") or ""
            location = profile.get("location") or ""
            repo_text = " ".join(
                f"{r.get('name', '')} {r.get('description', '') or ''} {r.get('language', '') or ''}"
                for r in personal_repos
            )

            uni_hits = detect_signals(f"{bio} {company}", VICTORIAN_UNI_TERMS)
            grad_hits = detect_signals(f"{bio} {company}", GRAD_BIO_SIGNALS)
            data_hits = detect_signals(f"{bio} {company} {repo_text}", DATA_SKILL_SIGNALS)

            row_out = {
                "username": username,
                "github_url": f"https://github.com/{username}",
                "status": "candidate",
                "name": profile.get("name", "") or "",
                "location": location,
                "bio": bio,
                "company": company,
                "created_at": profile.get("created_at", "") or "",
                "public_repos": profile.get("public_repos", "") or "",
                "followers": profile.get("followers", "") or "",
                "personal_repo_count": len(personal_repos),
                "recent_active_repo_count": len(active_repos) if is_active else 0,
                "recent_active_repo_names": " | ".join(r["name"] for r in active_repos),
                "active_languages": " | ".join(sorted({r["language"] for r in active_repos if r["language"]})),
                "uni_signals": " | ".join(uni_hits),
                "grad_signals": " | ".join(grad_hits),
                "data_skill_signals": " | ".join(data_hits),
                "candidate_path": row.get("source_query", ""),
                "summary_reason": summary_reason,
                "scanned_at": datetime.now().isoformat(),
            }
            append_result(row_out)
            update_user_status(username, "done")
            result_usernames.add(username)
            print(f"saved: {summary_reason}")

        except Exception as e:
            print(f"error: {e} (will retry next run)")
            # Leave as pending so rerun resumes.

        save_json(RUN_STATE_FILE, {"phase": "scan", "last_username": username})
        time.sleep(PROFILE_SLEEP_SECONDS)

    print(f"Stage 1 complete. Candidates are in {RESULTS_FILE}")


def main() -> None:
    if not GITHUB_TOKEN or GITHUB_TOKEN == "PUT_GITHUB_TOKEN_HERE":
        raise RuntimeError("Put a valid GitHub token into GITHUB_TOKEN before running.")

    ensure_users_file()
    ensure_results_file()

    search_users_by_queries()
    scan_pending_users()


if __name__ == "__main__":
    main()
