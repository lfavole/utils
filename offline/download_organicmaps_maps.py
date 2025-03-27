import base64
from dataclasses import dataclass
import hashlib
import json
import logging
import os.path
from pathlib import Path
import sys

import requests
from tqdm import tqdm

CHUNK_SIZE = 65536
CURRENT_DIR = Path(__file__).parent

# set up logging


def handle_exception(exc_type, exc_value, exc_traceback):
    """Log or re-raise any exception."""
    if issubclass(exc_type, Exception):
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = handle_exception

logging.basicConfig(
    filename=CURRENT_DIR / "action.log",
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logging.root.setLevel(logging.INFO)

COUNTRIES_FILE = CURRENT_DIR / "countries.txt"
try:
    # try to download the latest countries file
    logging.info("Fetching countries.txt from GitHub")
    req = requests.get("https://raw.githubusercontent.com/organicmaps/organicmaps/master/data/countries.txt")
    data = req.text
    countries_data = json.loads(data)

    logging.info("Writing countries.txt to disk (%s)", COUNTRIES_FILE)
    COUNTRIES_FILE.write_text(data, "utf-8")
except OSError as err:
    # if there is no countries file, stop here
    if not COUNTRIES_FILE.exists():
        raise RuntimeError("Failed to fetch countries.txt and the file doesn't exist") from err

    # fall back to the downloaded file
    logging.warning("Failed to fetch countries.txt")
    logging.info("Reading countries.txt from disk (%s)", COUNTRIES_FILE)
    countries_data = json.loads(COUNTRIES_FILE.read_text("utf-8"))

MAP_VERSION = str(countries_data["v"])
MAPS_FOLDER = CURRENT_DIR / MAP_VERSION
logging.info("Maps folder: %s", MAPS_FOLDER)
MAPS_FOLDER.mkdir(exist_ok=True)


@dataclass
class Map:
    """A country."""

    name: str
    size: int
    hash: str


maps: list[Map] = []

countries_to_download = ["France", "Andorra", "Italy", "San Marino", "Germany", "Spain", "Gibraltar"]


def parse_countries(countries_group):
    """
    Recursively check the countries list
    and populate the `maps` list with all the files to download.
    """
    for country in countries_group:
        if any(
            # check if the region matches
            country["id"].startswith(target_country)
            # or if it is in the country
            or any(aff.startswith(target_country) for aff in country.get("affiliations", []))
            for target_country in countries_to_download
        ):
            if "sha1_base64" in country:
                # if it's a country, add it
                maps.append(Map(name=country["id"], size=country["s"], hash=country["sha1_base64"]))
            else:
                # otherwise, check all the subregions
                parse_countries(country["g"])


parse_countries(countries_data["g"])
logging.info("%d maps found", len(maps))


def check_hash(map: Map, file: Path):
    """
    Check the hash of a map and remove the map file if the hash doesn't match.
    Return `True` in case of success, `False` otherwise.
    """
    h = hashlib.sha1()
    with file.open("rb") as f:
        while (chunk := f.read(CHUNK_SIZE)) != b"":
            h.update(chunk)

    expected_hash = base64.b64decode(map.hash).hex()
    if h.hexdigest() == expected_hash:
        return True

    logging.warning(
        "Removing map file %s because of hash mismatch (expected %r, got %r)",
        file,
        expected_hash,
        h.hexdigest(),
    )
    file.unlink()
    return False


pb = tqdm(total=sum(map.size for map in maps), unit_scale=True, unit="B")
for map in maps:
    pb.set_description(map.name)
    file = MAPS_FOLDER / f"{map.name}.mwm"

    file_size = 0
    if file.exists():
        # if the file exists, check its size
        file_size = os.path.getsize(file)
        if file_size > map.size:
            # remove the file if it is too big
            logging.warning("Removing map file %s because it is too big", file)
            file.unlink()

        elif file_size == map.size:
            # if the file has the good size, check its hash
            # (and possibly remove the file)
            if check_hash(map, file):
                # if everything is correct, update the progress bar
                pb.update(map.size)
                continue

    # try to download the map until the hash matches
    while True:
        url = f"http://cdn.organicmaps.app/maps/{MAP_VERSION}/{map.name}.mwm"
        logging.info("Downloading map file %s", file)

        # ask for the good range if the file has already been downloaded
        req = requests.get(url, headers={"Range": f"bytes={file_size}-"} if file_size else {}, stream=True)
        length_header = int(req.headers.get("Content-Length", "0"))

        # if the size from the length header doesn't match, stop here
        if length_header and length_header != map.size and length_header != (map.size - file_size):
            raise RuntimeError(
                f"Can't download {url} because of size mismatch: expected {map.size}, got {length_header}"
            )

        # check the range header
        range_header = req.headers.get("Content-Range", "*").rsplit("/", 1)[0].removeprefix("bytes ").split("-")
        if range_header != ["*"]:
            range_header_size = (int(range_header[1]) + 1) - int(range_header[0])
            total_length = range_header_size + file_size
            # if the total size (from the range header) doesn't match, stop here
            if all(range_header) and range_header_size and file_size and total_length != map.size:
                raise RuntimeError(
                    f"Can't download {url} because of size mismatch: expected {map.size}, got {total_length}"
                )

        # download the file
        with file.open("ab") as f:
            for data in req.iter_content(CHUNK_SIZE):
                f.write(data)
                pb.update(len(data))

        logging.info("Downloading of %s has ended", map.name)

        # if the hash is correct, stop here for this file
        if check_hash(map, file):
            break

        # otherwise, the file is deleted
        # make the progress bar go back and retry
        pb.update(-map.size)
