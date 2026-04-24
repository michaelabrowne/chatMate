from __future__ import annotations

import json
import urllib.request

from .geocoding import geocode

_WMO: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    61: "Light rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Light snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers", 81: "Showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Heavy thunderstorm with hail",
}


def get_weather(location: str) -> str:
    geo = geocode(location)
    if not geo:
        return f"Could not geocode location: {location}"

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={geo['lat']}&longitude={geo['lon']}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"
        "&forecast_days=7&timezone=auto"
    )
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read())

    daily = data["daily"]
    lines = [f"7-day weather forecast for {geo['name']}, {geo['country']}:"]
    for i in range(7):
        condition = _WMO.get(daily["weathercode"][i], "Unknown")
        lines.append(
            f"  {daily['time'][i]}: {condition}, "
            f"{daily['temperature_2m_min'][i]}°C – {daily['temperature_2m_max'][i]}°C, "
            f"{daily['precipitation_sum'][i]} mm precipitation"
        )
    return "\n".join(lines)
