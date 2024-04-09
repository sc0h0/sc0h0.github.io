---
layout: post
title: "A 'sophisticated' Facebook Marketplace alert system using GitHub Actions and ChatGPT's API"
image: /assets/fbmp/castle.png
---



<img class="small right" src="/assets/fbmp/castle.png" alt="A scene from The Castle" loading="lazy">

If The Castle (1997) was filmed today, would <a href="https://www.youtube.com/watch?v=dik_wnOE4dk">Steve Kerrigan</a> instead be endlessly scrolling through Facebook Marketplace and forever sending screenshots of jousting sticks to the Kerrigan family WhatsApp group?

The Facebook Marketplace app includes a feature that notifies you when a listing matches a specified keyword.

Unfortunately this feature is poorly executed, appearing more intent on driving app engagement with false positive alerts than truly helping users find what they're searching for.

### Defining the problem
The Facebook Marketplace 'new listing' notification feature:
- Is inaccurate
- Is untimely
- Only notifies you through the app or by visiting the website

### The solution
Drawing inspiration from Simon Willison's brilliant post on (and coining of) <a href="https://simonwillison.net/2020/Oct/9/git-scraping/">Git scraping</a>, I built an open source alert system running on GitHub Actions and applied 'innovative' filtering using ChatGPT's API. 

<figure>
  <img src="/assets/fbmp/img02.png" alt="" loading="lazy">
  <figcaption>
    A process flow illustrates a complete solution operating on GitHub Actions. A cron job activates a Python script every few hours to scrape recent listings. These listings are processed through basic logic and then analysed by the ChatGPT API as a final step to discern additional attributes that contribute to the alert criteria. If a listing matches, an email notification is triggered.
  </figcaption>
</figure>

### Example: Hali Rugs
<a href="https://github.com/sc0h0/fb_mp_hali">This configuration</a> will monitor and alert for Hali rug listings that are 2.8m by 2.3m with a 20% tolerance in dimensions.

Basic filtering (shown in the first yellow diamond) is applied to ensure that either the listing title or description contains the word `'hali'`. 

This is required because Facebook Marketplace will sometimes insert 'relevant' listings that don't necessarily match the specific keyword, and so these can be filtered out using basic string matching.

_Side note: a simple string filter is also a way to save on usage costs of the ChatGPT API in the next step._

{% highlight python %}
def heading_details_keyword(details_collected_text, title_collected_text):
    # Check if the lowercase text contains 'hali'
    essential_word = 'hali'
    if essential_word in text_lower or essential_word in title_lower:
        return True   
    else:
        return False  
{% endhighlight %}

Then (shown in the second yellow diamond), the ChatGPT API is used to transform the listing title and description into a more structured format that can be used by Python.

The prompt sent to the ChatGPT API is shown below. It also defines how the API must return a response.

{% highlight python %}
prompt = f"""
Based on the following description and title for an item listed on Facebook Marketplace, determine if the item is a rug or floor runner. 
Respond strictly in the format 'yes|d1|d2' if it is a rug or floor runner, with 'd1' and 'd2' as the dimensions in meters. 
If the item is not a rug or floor runner, respond with 'no'. If dimensions cannot be determined, use 'na' for 'd1' and 'd2'.

Description: {description}
|||
Title: {heading}

Note: Your response should strictly follow the 'yes|d1|d2' or 'no' format without additional explanations.
"""
{% endhighlight %}

The dimensions can then be tested against the target dimensions.
{% highlight python %}
# Calculate the minimum and maximum dimensions with tolerance for both width and length
min_width = desired_width * (1 - tolerance)
max_width = desired_width * (1 + tolerance)
min_length = desired_length * (1 - tolerance)
max_length = desired_length * (1 + tolerance)

# Check if either combination of dimensions are within the desired range
if ((min_width <= dimension1 <= max_width and min_length <= dimension2 <= max_length) or
   (min_width <= dimension2 <= max_width and min_length <= dimension1 <= max_length)):
    return True
else:
    return False
{% endhighlight %}

If the listing meets the target dimensions, an email notification containing the URL to the Facebook listing is triggered.

{% highlight python %}
# Email body - HTML version
html = f"""\
<html>
  <body>
    <p>Hi,<br>
       Check out this heli rug item with dimensions we want: <a href="https://www.facebook.com/marketplace/item/{item_id}">Item Link</a>
    </p>
  </body>
</html>
"""
{% endhighlight %}

### Example: Grange Furniture
<a href="https://github.com/sc0h0/fb_mp_watch">This configuration</a> will monitor and alert for any Grange furniture listings. 

Unfortunately, there is a furniture store located on `Grange Rd`, Cheltenham and some other furniture is listed as `Grange style`. This would otherwise result in false-positive listings making it through to the second-stage filter and racking up unnecessary ChatGPT API usage costs.

The preliminary filter below ensures that API costs are kept to a minimum.

{% highlight python %}
def details_are_exclude(details_collected_text):
    # Convert the collected text to lowercase for case-insensitive comparison
    text_lower = details_collected_text.lower()
    keywords = ['grange rd', 'grange road', 'near grange', 'grange style', 'grange-style', 'grange view']
    # Check if the lowercase text contains
    return any(keyword in text_lower for keyword in keywords)
{% endhighlight %}

Next, given the term `'grange'` is popular amongst wine and Holden Special Vehicle (HSV) enthusiasts, the ChatGPT API is used to indicate whether the listing is a piece of furniture. 

{% highlight python %}
prompt = f"""
Consider the following description and title for an item listed on Facebook Marketplace. 
Your task is to determine if the content suggests that the item is NOT a piece of furniture. 
The item description is provided first, followed by the title, separated by '|||' for clarity.
Description: {description}
|||
Title: {heading}
Based on the description and title, is the item a piece of furniture? Please respond with 'yes' if it is a piece of furniture, and 'no' otherwise.
"""
{% endhighlight %}



### End
Feel free to fork and modify either repository (linked in the examples above) to set up your own Facebook Marketplace alerts!
