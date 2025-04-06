import itertools
import re

from bs4 import BeautifulSoup
import genanki
import requests

page = requests.get("https://culture-crunch.com/2019/08/16/noms-dhabitants-de-villes-les-irreguliers-et-les-plus-insolites/")
soup = BeautifulSoup(page.content, "html.parser")

ret = []

for i, el in enumerate(itertools.chain(
    *(table.find_all("td") for table in soup.find_all(class_="wp-block-table"))
)):
    if i < 2:
        continue
    if i % 2 == 0:
        parts = [[part.strip()] for part in el.text.split("/")]
        ret.extend(parts)
    else:
        el_parts = [el.strip() for el in el.text.split("/")]
        index = -len(el_parts)
        for el_text in el_parts:
            parts = [re.sub(r"\(.*?\)", "", x).strip().removesuffix("s").strip() + "s" for x in el_text.split(", ")]
            answer = ", ".join(parts) if len(parts) < 2 else ", ".join(parts[:-1]) + " ou " + parts[-1]
            ret[index].append(answer)
            if len(parts) >= 2:
                ret[index][0] += f" ({len(parts)})"
            index += 1

from pprint import pp
pp(ret)

my_deck = genanki.Deck(1604655315, "Noms des habitants (Python)")
my_model = genanki.Model(
  1607392319,
  'Simple Model',
  fields=[
    {'name': 'Question'},
    {'name': 'Answer'},
  ],
  templates=[
    {
      'name': 'Card 1',
      'qfmt': '{{Question}}',
      'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
    },
  ])

for q in ret:
    my_deck.add_note(genanki.Note(model=my_model, fields=q))

genanki.Package(my_deck).write_to_file("output.apkg")
