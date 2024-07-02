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
Having recently watched a demonstration of making good use of Google Gemini Pro's large context window, I thought that with some web scraping and data preperation, a large text file profiling all available data files on DataVic might just 
allow me to use Gemini to query the available data.

### The approach
I wrote a script that downloaded every available CSV from the DataVic platform and based on each CSV created a json file that profiled each CSV. For example,
{% highlight javascript %}
{
        "url": "https://discover.data.vic.gov.au/dataset/air-quality-observations",
        "filename": "air-quality-observations.csv",
        "title": "Air Quality Observations",
        "description": "This dataset describes observations made of air quality by sensors distributed in Ballarat.",
        "filesize": 14429.46875,
        "rows": 125492,
        "columns": [
            "device_id",
            "date_time",
            "location_description",
            "latitude",
            "longitude",
            "pm1"
        ],
        "sample_data": [
            {
                "device_id": "ems-b879",
                "date_time": "2020-04-01T01:30:54+00:00",
                "location_description": "Fairyland",
                "latitude": -37.546758,
                "longitude": 143.823172,
                "pm1": 4
            },
            {
                "device_id": "ems-b879",
                "date_time": "2020-04-01T03:30:53+00:00",
                "location_description": "Fairyland",
                "latitude": -37.546758,
                "longitude": 143.823172,
                "pm1": 0
            }
        ]
    }
{% endhighlight %}


### End
Feel free to fork and modify either repository (linked in the examples above) to set up your own Facebook Marketplace alerts!
