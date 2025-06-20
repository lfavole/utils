"""Check if the weather is stormy in a given location using the OpenWeatherMap API."""

import datetime as dt
from urllib.parse import urlencode
import urllib.request
import json

# https://github.com/hacf-fr/meteofrance-api/blob/f733544/src/meteofrance_api/const.py#L3
METEOFRANCE_API_URL = "https://webservice.meteofrance.com"
METEOFRANCE_API_TOKEN = "__Wj7dVSTjV9YGu1guveLyDq0g7S7TfTjaHBTPTpO0kj8__"  # noqa: S105

def round_date(date):
    return date.replace(minute=0, second=0, microsecond=0)

def is_storm(lat, lon):
    # Météo-France API endpoint for current weather data
    url = METEOFRANCE_API_URL + "/forecast?" + urlencode({
        "lat": lat,
        "lon": lon,
        "lang": "fr",
        "token": METEOFRANCE_API_TOKEN,
    })
    now = round_date(dt.datetime.now())
    limit = dt.timedelta(hours=12)

    # Make the request to the Météo-France API
    with urllib.request.urlopen(url) as f:
        # Parse the JSON data in the response
        weather_data = json.load(f)

    # Check for storm conditions
    for item in weather_data["forecast"]:
        date = round_date(dt.datetime.fromtimestamp(item["dt"]))
        if not (now <= date <= now + limit):
            continue
        if "orage" in item.get("weather", {}).get("desc", "").lower():
            return True

    return False
