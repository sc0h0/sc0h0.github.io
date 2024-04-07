---
layout: post
title: "A 'sophisticated' Facebook Marketplace alert system using Github Actions and ChatGPT's API"
image: /assets/fbmp/castle.png
---



<img class="small right" src="/assets/fbmp/castle.png" alt="A scene from The Castle" loading="lazy">

If The Castle (1997) was filmed today, would <a href="https://www.youtube.com/watch?v=dik_wnOE4dk">Steve Kerrigan</a> instead be endlessly scrolling through Facebook Marketplace and forever sending screenshots of jousting sticks to the Kerrigan family WhatsApp group?

The Facebook Marketplace app includes a feature that notifies you when a listing matches a specified keyword.

Unfortunately, this feature is poorly executed, appearing more intent on driving app engagement with false positive alerts than truly helping users find what they're searching for.

To address the issues of:

- Inaccurate alerts,
- Untimely alerts, and
- Alerts only observed within Facebook app,
  
I built an open source alert system running on Github Actions and applying advanced filtering using ChatGPT's API. 

<figure>
  <img src="/assets/fbmp/img02.png" alt="" loading="lazy">
  <figcaption>
    Process flow to generate accurate alerts when new Facebook Marketplace listings are created.
  </figcaption>
</figure>

### Example: Hali Rugs
<a href="https://github.com/sc0h0/fb_mp_hali">This configuration</a> will monitor and alert for Hali rug listings that are 2.8m by 2.3m with a 20% tolerance in dimensions.

Basic filtering (shown in the first yellow diamond) is applied to ensure that either the listing title or description contains the word `'hali'`. 

This is because Facebook Marketplace will sometimes insert 'relevant' listings that don't necessarily match the specific keyword, and so these must be filtered. Filtering at this stage is also a way to save on usage costs of the ChatGPI API in the next step. 

{% highlight python %}
def heading_details_keyword(details_collected_text, title_collected_text):
    # Check if the lowercase text contains 'hali'
    essential_word = 'hali'
    if essential_word in text_lower or essential_word in title_lower:
        return True   
    else:
        return False  
{% endhighlight %}

Then (shown in the second yellow diamond), the ChatGPT API is used to transform the listing title and description into a more structured format that can be used by Python. The ChatGPT prompt sent the API is shown below.

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
