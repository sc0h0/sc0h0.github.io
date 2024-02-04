---
layout: post
---

One of my favourite websites <a href="https://pricehipster.com/">Price Hipster</a> tracks and displays the price changes of products online, allowing you to set up alerts based on your specified price threshold.

About two years ago, Dan Murphy's products stopped being displayed and tracked on Price Hipster due to unknown reasons. To this day, the products remain absent from the site.

As I had become dependent on this feature to find wine at discounted prices, I set out to build my own price tracker. This way, I could continue to complement my wife's expensive taste in <a href="https://toscanos.com.au/">Toscano's</a> cheese with equally fine wines, acquired at more affordable prices.

### Unexpected Results
I pieced together a script to collect Dan Murphy's wine price data <a href="https://en.wikipedia.org/wiki/Web_scraping\">"en masse"</a>. These scripts ran several times over a few weeks to compile price snapshots, allowing me to spot price drops.

Eventually I noticed price drops on some interesting wines and so I added them to my cart for checkout. Strangely, the prices at checkout did not match those captured by the data collection script. 

After some digging around, I found that the VPN used during the data collection process (to avoid the risk of Dan's perma-banning my own IP) was being assigned to a different store than my local one in Collingwood.

The two different Dan Murphy's stores had their own price for identical bottles of wine, and the cheaper price was not marked as a clearance or "Member's Only" offer.




