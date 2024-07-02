---
layout: post
title: "Opening up Victoria’s open data platform"
---



The State Government of Victoria's "open data platform" <a href="https://www.data.vic.gov.au/about-datavic">DataVic</a> is promoted as "the place to discover and access Victorian Government open data."

However, every time I've used it, I've struggled to determine what data is available. The search function caters more to users who know exactly what they're looking for rather than those exploring available data.

### Defining the problem
The DataVic platform:
- Fails to effectively showcase available datasets
- Provides insufficient discovery tools for exploring data
- Inconsistently provides detailed data profiling

### The idea
Having recently watched a <a href="https://www.youtube.com/watch?v=PwFrN3dFiwY">demonstration</a> of making good use of Google Gemini Pro's large context window, I thought that with some web scraping and data preperation, a large text file profiling all available data files on DataVic might just allow me to use Gemini to query the available data.

### The approach
I wrote a script that downloaded every available CSV from the DataVic platform and based on each CSV created a json file that profiled each CSV. For example,
<figure>
  <img src="/assets/vicopendata/sample_json.png" alt="" loading="lazy">
  <figcaption>
    A sample json file profiling 
  </figcaption>
</figure>
In total there were around


### End
Feel free to fork and modify either repository (linked in the examples above) to set up your own Facebook Marketplace alerts!
