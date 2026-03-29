"""Open Meteo — free weather API, no key needed. Unlimited requests."""
from __future__ import annotations
import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_weather(lat: float, lng: float) -> dict[str, Any] | None:
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current_weather=true"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        cw = data.get("current_weather", {})
        return {
            "temperature_c": cw.get("temperature"),
            "windspeed_kmh": cw.get("windspeed"),
            "weather_code": cw.get("weathercode", 0),
            "is_day": cw.get("is_day", 1),
            "condition": _weather_code_to_condition(cw.get("weathercode", 0)),
        }
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return None

def _weather_code_to_condition(code: int) -> str:
    if code == 0: return "clear"
    elif code in (1, 2, 3): return "cloudy"
    elif code in (45, 48): return "foggy"
    elif code in (51, 53, 55, 56, 57): return "drizzle"
    elif code in (61, 63, 65, 66, 67): return "rain"
    elif code in (71, 73, 75, 77): return "snow"
    elif code in (80, 81, 82): return "rain_showers"
    elif code in (85, 86): return "snow_showers"
    elif code in (95, 96, 99): return "thunderstorm"
    return "unknown"

def should_stay_indoors(weather: dict) -> bool:
    return weather.get("condition", "") in ("rain", "thunderstorm", "snow", "rain_showers", "snow_showers")

def is_available() -> bool:
    return True
