"""AQICN API — real-time air quality. Free token from aqicn.org."""

from __future__ import annotations
import json, os
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

AQICN_URL = "https://api.waqi.info"
AQICN_KEY_ENV = "AQICN_API_KEY"

def is_available() -> bool:
    return os.environ.get(AQICN_KEY_ENV) is not None

def get_air_quality(lat: float, lng: float) -> dict[str, Any] | None:
    """Get air quality for coordinates. Returns AQI index + pollutants."""
    key = os.environ.get(AQICN_KEY_ENV)
    if not key:
        return None
    url = f"{AQICN_URL}/feed/geo:{lat};{lng}/?token={key}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data.get("status") != "ok":
            return None
        d = data.get("data", {})
        return {
            "aqi": d.get("aqi", 0),
            "station": d.get("city", {}).get("name", ""),
            "dominant_pollutant": d.get("dominentpol", ""),
            "pm25": d.get("iaqi", {}).get("pm25", {}).get("v"),
            "pm10": d.get("iaqi", {}).get("pm10", {}).get("v"),
            "time": d.get("time", {}).get("s", ""),
        }
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return None

def air_quality_advice(aqi: int) -> str:
    """Human-readable advice based on AQI."""
    if aqi <= 50: return "Air is good — great for outdoor activities"
    elif aqi <= 100: return "Moderate — sensitive people should limit prolonged outdoor exertion"
    elif aqi <= 150: return "Unhealthy for sensitive groups — consider indoor activities"
    elif aqi <= 200: return "Unhealthy — avoid prolonged outdoor activity"
    elif aqi <= 300: return "Very unhealthy — stay indoors, use air purifier"
    else: return "Hazardous — stay indoors, seal windows"
