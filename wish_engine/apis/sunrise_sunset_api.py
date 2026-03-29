"""Sunrise/sunset times. Free, no key. sunrise-sunset.org"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_sun_times(lat: float, lng: float) -> dict | None:
    url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&formatted=0"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            r = data.get("results", {})
            return {"sunrise": r.get("sunrise", ""), "sunset": r.get("sunset", ""), "day_length": r.get("day_length", 0), "solar_noon": r.get("solar_noon", ""), "civil_twilight_begin": r.get("civil_twilight_begin", ""), "civil_twilight_end": r.get("civil_twilight_end", "")}
    except: return None

def is_available() -> bool: return True
