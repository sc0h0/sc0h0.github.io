---
layout: post
---

For the last 18 months the Walmer Street Bridge has been closed <a href="https://bicyclenetwork.com.au/newsroom/2023/12/20/walmer-street-bridge-ready-to-re-open/">(until recently)</a>. While it was closed, the detour added about 10 minutes to my commute. This closure and subsequent detour led me to reflect on the various `distinct` routes I've taken to work over the years, and what sets each one apart.

For instance, consider a morning when I take a slightly different path from my usual route, a variation I refer to as the 'Deviation'. Does this minor deviation qualify as an entirely new way of commuting to work? What if I briefly rode on the wrong side of the road for just 10 meters. While technically this is a different route, practically it's not significantly distinct from my usual route.

<figure>
  <img src="/assets/2023-12-26-img01.png" alt="Example Deviation" loading="lazy">
  <figcaption>
    A deviation (red) from typical route to work (blue). The deviation is a shortcut along a sandy section along the Yarra River.
  </figcaption>
</figure>

Before we can determine whether a route deviation constitutes an entirely different route, we need the ability to objectively differentiate between routes, preferably in a programmable way.

The following examples show how this can be achieved.

### Example 1: My lunchtime walk to ~~Safeway~~ Woolworths

Typically, my route involves initially heading west on Collins Street and then turning north onto Merchant Street.

<figure>
  <img src="/assets/2023-12-26-img02.png" alt="Typical walk to Woolworths" loading="lazy">
  <figcaption>
    My typical lunchtime walking route from my office to Woolworths.
  </figcaption>
</figure>

Sometimes, though very rarely, I would walk west on Collins St, turn right onto Import Lane, and then take a left along a pedestrian alley.

<figure>
  <img src="/assets/2023-12-26-img03.png" alt="Rare route to Woolworths" loading="lazy">
  <figcaption>
    My less-travelled walking route from the office to Woolworths, overlaid in red as the 'Alternative Route', with the regular route shown in blue.
  </figcaption>
</figure>

These two routes can be represented as sequences of four pairs of latitude and longitude coordinates.

<figure>
  <img src="/assets/2023-12-26-img04.png" alt="Both routes shown as four pairs of latitude and longitude coordinates." loading="lazy">
  <figcaption>
    Original and Alternative routes being represented as a sequence of four latitude-longitude pairs.
  </figcaption>
</figure>

To determine whether two routes are identical, or to quantify their differences if they are not, we can use the Lock-step Euclidean Distance (LSED). To visualise the calculation of this distance, we first compute the 'as-the-bird-flies' distance between corresponding points on each route. These distances are then squared, summed, and finally, the square root is taken.

In the example below, the LSED is calculated to be 112 meters. As expected, the LSED is non-zero, primarily because sequence point 3 is located at different positions in each route, while all other sequence points are identical.

<figure>
  <img src="/assets/2023-12-26-img05.png" alt="Lock-step Euclidean Distance (LSED)" loading="lazy">
  <figcaption>
    The calculation of the Lock-step Euclidean Distance (LSED). 
  </figcaption>
</figure>
