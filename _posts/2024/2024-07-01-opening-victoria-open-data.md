---
layout: post
title: "Opening up Victoria’s open data platform"
---



The State Government of Victoria's _"open data platform"_ <a href="https://www.data.vic.gov.au/about-datavic">DataVic</a> is promoted as _"the place to discover and access Victorian Government open data."_

However, every time I've used it, I've struggled to determine what data is available. The search function caters more to users who know exactly what they're looking for rather than those exploring available data.

### Defining the problem
The DataVic platform:
- Provides insufficient discovery tools for exploring data
- Inconsistently provides detailed data profiling

### The idea
Having recently watched a <a href="https://www.youtube.com/watch?v=PwFrN3dFiwY">demonstration</a> on using Google Gemini Pro's large context window, I realised that with some web scraping and data preparation, a large text file profiling all available datasets on DataVic might allow me to use Gemini to quickly perform discovery analyses of the available data.

### The approach
I wrote a script that downloaded every available CSV from the DataVic platform and created a JSON file profiling each CSV. The profiling for each CSV included:
- Filename
- Dataset page and description
- Filesize and rows
- Columns and two rows of sample data

For example:

<figure>
  <img src="/assets/vicopendata/sample_json_2.png" alt="" loading="lazy">
  <figcaption>
    A sample json file profiling data available on DataVic
  </figcaption>
</figure>

I initially had some issues automating the opening of Excel files and so decided to limit the analysis to simple CSVs. In total there were around 670 CSV files however only 300 had more than 500 rows (I decided less than 500 rows is more a table rather than data). There should have been more CSVs however it appears some of the APIs referenced by DataVic were broken.

I wrote a script that downloaded every available CSV from the DataVic platform and based on each CSV created a json file that profiled each CSV. For example,
<figure>
  <img src="/assets/vicopendata/nodata.png" alt="" loading="lazy">
  <figcaption>
    Broken links on VicGov.
  </figcaption>
</figure>

Noting that as of July 2024 the platform boasts around 5,700 datasets, that's far from the 300 that in my opinion are true datasets.



### End
Feel free to fork and modify either repository (linked in the examples above) to set up your own Facebook Marketplace alerts!
