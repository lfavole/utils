from collections import defaultdict
import hashlib
import html
import re
import time
import zipfile
from pathlib import Path

import genanki
import requests
from province_db import get_db, sigle
from tqdm import tqdm

# tweak for forcing the compression

zipfile.ZipFile.__old_init__ = zipfile.ZipFile.__init__


def init(self, *args, **kwargs):
    self.__old_init__(*args, **kwargs)
    self.compression = zipfile.ZIP_DEFLATED
    self.compresslevel = 9


zipfile.ZipFile.__init__ = init


# https://stackoverflow.com/a/64323021
def get_wc_thumb(image, width=300):  # image = e.g. from Wikidata, width in pixels
    if image.endswith("2016.svg"):
        image = image.removesuffix("2016.svg") + "(as of 2016).svg"
    image = image.replace(" ", "_")  # need to replace spaces with underline
    m = hashlib.md5()
    m.update(image.encode("utf-8"))
    d = m.hexdigest()
    return (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/"
        + d[0]
        + "/"
        + d[0:2]
        + "/"
        + image
        + "/"
        + str(width)
        + "px-"
        + image
        + (".png" if image.endswith(".svg") else "")
    )


def cleanup(wikitext):
    wikitext = re.sub(r"\{\{.*?\}\}\s*", "", wikitext)
    wikitext = re.sub(r"\[\[(?:.*?\|)?(.*?)\]\]", r"\1", wikitext)
    wikitext = re.sub(r"<br ?/?>", "-", wikitext)
    wikitext = re.sub(r"<ref.*?>(?:.*?</ref>)?", "", wikitext)
    return wikitext


with get_db(write=False) as db:
    data = db

templates = []
for file in (Path(__file__).parent / "questions").iterdir():
    card = file.read_text(encoding="utf-8")
    name, qfmt, afmt = card.split("---")
    templates.append(
        {
            "name": name.strip(),
            "qfmt": qfmt.lstrip(),
            "afmt": afmt.lstrip(),
        }
    )

deck = genanki.Deck(2206197569, "Province italiane")
model = genanki.Model(
    3322718282,
    "Provincia italiana",
    fields=[
        {"name": "Provincia"},
        {"name": "Domanda nome"},
        {"name": "Capoluogo"},
        {"name": "Sigla"},
        {"name": "Mappa"},
        {"name": "Regione"},
    ],
    templates=templates,
    css="""\
@import "_style.css";
""",
    sort_field_index=0,
)

normal_model = genanki.Model(
    1704735824299,  # AnkiDroid ID
    "Basique",
    fields=[
        {"name": "Recto"},
        {"name": "Verso"},
    ],
    templates=[
        {
            "name": "Carte 1",
            "qfmt": "{{Recto}}",
            "afmt": '{{FrontSide}}\n\n<hr id="answer">\n\n{{Verso}}',
        },
    ],
    css="""\
@import "_style.css";
""",
    sort_field_index=0,
)

media_dir = Path(__file__).parent / "province_media"
media_dir.mkdir(exist_ok=True)
media_files = [media_dir / "_mappa_province_vuota.jpg"]
files_pb = tqdm(total=107)


def download_file(url):
    filename = url.rsplit("/", 1)[-1]
    file = media_dir / filename
    media_files.append(file)
    if file.exists():
        files_pb.update(1)
        return filename
    while True:
        req = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
        )
        try:
            req.raise_for_status()
            break
        except requests.HTTPError:
            files_pb.set_description(f"{req.status_code} error code")
            files_pb.refresh()
            time.sleep(5)
    with file.open("wb") as f:
        f.write(req.content)
    files_pb.update(1)
    return filename


province_regione = defaultdict(lambda: [])

for i, (provincia, text) in enumerate(data.items()):
    # with open("D:/Users/Laurent/Desktop/text.html", "w", encoding="utf-8") as f:
    #     f.write(text)

    nome = re.search(r"(?m)^\|Nome ?= ?(.*)$", text)
    if not nome:
        print(f"Skipping {provincia}, name missing")
        continue
    nome = nome.group(1)

    vero_nome = (
        nome.replace("Città metropolitana di ", "")
        .replace("Libero consorzio comunale di ", "")
        .replace("Provincia dell'", "L'")
        .replace("Provincia del ", "")
        .replace("Provincia della ", "La ")
        .replace("Provincia di ", "")
    )

    capoluogo = re.search(r"(?m)^\|Capoluogo ?= ?(.*?)$", text)
    if not capoluogo:
        print(f"Skipping {provincia}, capital missing")
        continue
    capoluogo = cleanup(capoluogo.group(1))

    if capoluogo == vero_nome:
        domanda_nome = ""
    else:
        domanda_nome = "1"

    sigla = sigle[i]

    mappa = re.search(r"(?m)^\|Immagine localizzazione ?= ?(.*)$", text)
    if not mappa:
        print(f"Skipping {provincia}, map missing")
        continue
    mappa = get_wc_thumb(mappa.group(1), 220)
    mappa = download_file(mappa)
    mappa = f'<img src="{html.escape(mappa)}">'

    regione = re.search(r"(?m)^\|Divisione amm grado 1 ?= ?(.*?)$", text)
    if not regione:
        if nome == "Valle d'Aosta":
            regione = ""
        else:
            print(f"Skipping {provincia}, region missing")
            continue
    else:
        regione = cleanup(regione.group(1))
        province_regione[regione].append(nome.replace(vero_nome, f"<b>{vero_nome}</b>"))

    deck.add_note(
        genanki.Note(
            model=model,
            fields=[
                field if field.startswith("<img") else html.escape(field)
                for field in [nome, domanda_nome, capoluogo, sigla, mappa, regione]
            ],
            guid=genanki.guid_for(provincia),
        )
    )

files_pb.close()

for regione, province in province_regione.items():
    deck.add_note(
        genanki.Note(
            model=normal_model,
            fields=[
                f"Province nella regione {regione} ({len(province)})",
                "<ul>" + "".join(f"<li>{provincia}</li>" for provincia in province) + "</ul>",
            ],
            guid=genanki.guid_for("province_nella_regione", regione),
        )
    )

package = genanki.Package(deck)
package.media_files = media_files
package.write_to_file(Path(__file__).parent / "Province italiane.apkg")
