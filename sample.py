from contextlib import redirect_stdout
import json
import os
import urllib.request

import assistscraper
from assistscraper.courses_parser import articulation_tree


url = assistscraper.articulation_url('AHC', 'CSUB', 'SOC')
with urllib.request.urlopen(url) as response:
   articulation_page = response.read()
inner_html = assistscraper.articulation_html_from_page(articulation_page)
text = assistscraper.articulation_text_from_html(inner_html)
tree = articulation_tree(text)

if not os.path.exists("sample"):
    os.makedirs("sample")

with open("sample/articulation.html", 'w') as f:
    f.write(inner_html)

with open("sample/articulation.txt", 'w') as f:
    f.write(text)

with open('sample/tree.txt', 'w') as f:
    with redirect_stdout(f):
        tree.show()

with open('sample/tree.json', 'w') as f:
    f.write(json.dumps(tree.to_dict(with_data=True, sort=False), indent=4))
