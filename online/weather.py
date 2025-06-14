"""Check if the weather is stormy in a given location using the OpenWeatherMap API."""

import datetime as dt
from urllib.parse import urlencode
import urllib.request
import json

def is_storm(lat, lon, api_key):
    # OpenWeatherMap API endpoint for current weather data
    url = "https://api.openweathermap.org/data/2.5/forecast?" + urlencode({
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "appid": api_key,
    })
    now = dt.datetime.now()
    limit = dt.timedelta(hours=12)

    # Make the request to the OpenWeatherMap API
    with urllib.request.urlopen(url) as f:
        # Parse the JSON data in the response
        weather_data = json.load(f)

    # Check for storm conditions
    for item in weather_data["list"]:
        if dt.datetime.fromtimestamp(item["dt"]) - now > limit:
            continue
        weather_conditions = item.get('weather', [])
        for condition in weather_conditions:
            if 'storm' in condition['description'].lower():
                return True

    return False
