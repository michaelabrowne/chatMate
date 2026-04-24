from __future__ import annotations

import json
import urllib.parse
import urllib.request

_cache: dict[str, dict] = {}


def geocode(location: str) -> dict | None:
    """Return {lat, lon, country_code, name, country} for a location string, or None."""
    if location in _cache:
        return _cache[location]

    url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={urllib.parse.quote(location)}&count=1&language=en&format=json"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read())

    results = data.get("results")
    if not results:
        return None

    r = results[0]
    result = {
        "lat": r["latitude"],
        "lon": r["longitude"],
        "country_code": r.get("country_code", "").upper(),
        "name": r.get("name", location),
        "country": r.get("country", ""),
    }
    _cache[location] = result
    return result
