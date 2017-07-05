from contextlib import redirect_stdout
import json
import os
import urllib.request

import assistscraper


url = assistscraper.articulation_url('AHC', 'CSUB', 'SOC')
with urllib.request.urlopen(url) as response:
   articulation_page = response.read()
inner_html = assistscraper.articulation_html_from_page(articulation_page)
text = assistscraper.articulation_text_from_html(inner_html)

if not os.path.exists("sample"):
    os.makedirs("sample")

with open("sample/articulation.html", 'w') as f:
    f.write(inner_html)

with open("sample/articulation.txt", 'w') as f:
    f.write(text)
