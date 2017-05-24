from contextlib import redirect_stdout
import json
import os

import assistscraper


text = assistscraper.fetch_articulation_text_from_codes('DAC', 'SJSU', 'ENGRCOMPTR')
tree = assistscraper.course_tree(text)

if not os.path.exists("sample"):
    os.makedirs("sample")

with open("sample/articulation.txt", 'w') as f:
    f.write(text)

with open('sample/tree.txt', 'w') as f:
    with redirect_stdout(f):
        tree.show()

with open('sample/tree.json', 'w') as f:
    f.write(json.dumps(tree.to_dict(with_data=True, sort=False), indent=4))
