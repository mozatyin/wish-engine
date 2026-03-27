"""OpenWeatherMap API client — current weather lookup.

Requires OPENWEATHER_API_KEY environment variable.
Falls back to default clear weather when API key is not available.
Zero LLM.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError


WEATHER_API_KEY_ENV = "OPENWEATHER_API_KEY"
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

_DEFAULT_WEATHER: dict[str, Any] = {
    "condition": "clear",
    "temp_c": 25,
    "humidity": 50,
    "wind_speed_ms": 3.0,
}


def _get_api_key() -> str | None:
    return os.environ.get(WEATHER_API_KEY_ENV)


def is_available() -> bool:
    """Check if OpenWeatherMap API is configured."""
    return _get_api_key() is not None


def get_weather(lat: float, lng: float) -> dict[str, Any]:
    """Get current weather for a location.

    Args:
        lat: Latitude
        lng: Longitude

    Returns:
        Dict with: condition (rain/snow/clear/cloudy), temp_c, humidity, wind_speed_ms
    """
    api_key = _get_api_key()
    if not api_key:
        return dict(_DEFAULT_WEATHER)

    params = {
        "lat": lat,
        "lon": lng,
        "appid": api_key,
        "units": "metric",
    }
    url = f"{CURRENT_WEATHER_URL}?{urlencode(params)}"

    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        # Extract main weather condition
        weather_list = data.get("weather", [])
        raw_main = weather_list[0].get("main", "Clear").lower() if weather_list else "clear"
        condition = _normalize_condition(raw_main)

        main = data.get("main", {})
        wind = data.get("wind", {})

        return {
            "condition": condition,
            "temp_c": main.get("temp", 25),
            "humidity": main.get("humidity", 50),
            "wind_speed_ms": wind.get("speed", 3.0),
        }
    except (URLError, json.JSONDecodeError, OSError, IndexError, KeyError):
        return dict(_DEFAULT_WEATHER)


def _normalize_condition(raw: str) -> str:
    """Normalize OpenWeatherMap condition to one of: rain, snow, clear, cloudy."""
    if raw in ("rain", "drizzle", "thunderstorm"):
        return "rain"
    if raw in ("snow",):
        return "snow"
    if raw in ("clouds", "mist", "fog", "haze", "smoke", "dust", "sand", "ash", "squall", "tornado"):
        return "cloudy"
    return "clear"
