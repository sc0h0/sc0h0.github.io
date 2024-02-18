---
layout: post
---

One of my favourite websites <a href="https://pricehipster.com/">Price Hipster</a> tracks and displays the price changes of products online, allowing you to set up alerts based on your specified price threshold.

About two years ago, Dan Murphy's products stopped being displayed and tracked on Price Hipster due to unknown reasons. To this day, the products remain absent from the site.

As I had become dependent on this feature to find wine at discounted prices, I set out to build my own price tracker. This way, I could continue to complement my wife's expensive taste in <a href="https://toscanos.com.au/">Toscano's</a> cheese with equally fine wines, acquired at more affordable prices.

### Unexpected Results
I pieced together a script to collect Dan Murphy's wine price data <a href="https://en.wikipedia.org/wiki/Web_scraping">"en masse"</a>. These scripts ran several times over a few weeks to compile price snapshots, allowing me to spot price drops.

Eventually I noticed price drops on some interesting wines so I added them to my cart for checkout. Strangely, the prices at checkout did not match those captured by the data collection script. 

After some digging around, I found that the VPN used during the data collection process (to avoid the risk of Dan's perma-banning my own IP address) was having a different Click&Collect store automatically assigned than my local one.

The two different Dan Murphy's stores had their own price for identical bottles of wine, and the cheaper price was not marked as a clearance or "Member Offer" offer.

For example, the two identical wines shown below have different prices as of 17/01/2024: the bottle at Kew is priced at $40.60, whereas at Alphington, it's $57.99. That's a $17 discount for a drive of less than ten minutes! There is also no indication of a sale or "Member Offer" offer when viewing the bottle with the Kew store selected.

<figure>
  <img src="/assets/2024-02-03-img01.png" alt="" loading="lazy">
  <figcaption>
    As of 17/01/2024 two identical wines with a 30% price variation, dependent on Dan Murphy's stores that are approx. 10 minutes drive from one another.
  </figcaption>
</figure>

Even more baffling than the first example, the bottle below (Fawkner store) marked as a "Member Offer" offer is priced higher than an identical bottle with no sale mentioned (Collingwood store).

<figure>
  <img src="/assets/2024-02-03-img02.png" alt="" loading="lazy">
  <figcaption>
    A bottle marked "Member Offer" offer is priced higher than an identical bottle with no sale mentioned
  </figcaption>
</figure>

### Exploring Store-based Pricing
Now aware that price drops are influenced by both time and location, I decided to look into how location affects price. Using a price snapshot from 17th January for Dan Murphy’s <span style="color: #ff0000;">red wines</span>  across Victoria, I analysed whether there was any store-specific price variation for each wine. 

Out of roughly 4,900 unique red wine stock codes (which might not all be in stock), about 3,800 (around 80%) showed no difference in price between stores. If a wine had store-specific pricing and matched the lowest observed price, it was flagged and counted as a discounted wine.

<figure>
  <img src="/assets/2024-02-03-img03.png" alt="" loading="lazy">
  <figcaption>
    Top five Dan Murphy's stores by number of discounted red wines: Endeavour Hills, Epping, Hoppers Crossing, Fawkner and Hawthorn East.
  </figcaption>
</figure>

Among the top five stores is Fawkner, which has become my regular click and collect Dan Murphy's store.

<figure>
  <img src="/assets/2024-02-03-img04.png" alt="" loading="lazy">
</figure>

And the five stores with the lowest volume of discounted red wines:
<figure>
  <img src="/assets/2024-02-03-img05.png" alt="" loading="lazy">
</figure>

### Realistic Stealth Specials
Among the results were some extreme discounts, such as this <a href="https://www.danmurphys.com.au/product/DM_908516">"Bimbadgen Hunter Valley Shiraz"</a> that while in stock was selling for $16.99 at Glen Waverly, and everywhere else in Victoria had it for $26.99. If we limit the analysis to wines in stock, we get a more realistic picture of what we can expect in terms of Dan's Stealth Specials.

Assessing the range of red wines that are in stock and are available for collection in at least one store, we can see that a majority fall within a range of 25-30% discount against the average price of the particular bottle of wine. 
