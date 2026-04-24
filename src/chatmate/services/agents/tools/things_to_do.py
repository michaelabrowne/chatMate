from __future__ import annotations

import json
import urllib.parse
import urllib.request

from .geocoding import geocode


def get_things_to_do(location: str, month: str = "") -> str:
    geo = geocode(location)
    if not geo:
        return f"Could not geocode location: {location}"

    lat, lon = geo["lat"], geo["lon"]
    url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&list=geosearch&gsradius=10000"
        f"&gscoord={lat}%7C{lon}&gslimit=20&format=json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "ChatMate/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())

    places = [p["title"] for p in data.get("query", {}).get("geosearch", [])]
    if not places:
        return f"No nearby landmarks found for {location}."

    month_ctx = f" in {month}" if month else ""
    lines = [
        f"Nearby landmarks and attractions in {geo['name']}, {geo['country']}{month_ctx}:",
        *(f"  - {p}" for p in places[:15]),
        "",
        "Use your knowledge to recommend the top 10 activities, "
        "considering the season and any weather context available.",
    ]
    return "\n".join(lines)
