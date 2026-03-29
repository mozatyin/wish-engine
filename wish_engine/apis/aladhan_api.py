"""Aladhan API — accurate Islamic prayer times. Free, no key."""
from __future__ import annotations
import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_prayer_times(lat: float, lng: float, method: int = 2) -> dict[str, str] | None:
    """Get today's prayer times. Method: 1=University of Islamic Sciences Karachi, 2=ISNA, 3=MWL, 4=Makkah, 5=Egypt."""
    url = f"https://api.aladhan.com/v1/timings?latitude={lat}&longitude={lng}&method={method}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        timings = data.get("data", {}).get("timings", {})
        return {
            "fajr": timings.get("Fajr", ""),
            "sunrise": timings.get("Sunrise", ""),
            "dhuhr": timings.get("Dhuhr", ""),
            "asr": timings.get("Asr", ""),
            "maghrib": timings.get("Maghrib", ""),
            "isha": timings.get("Isha", ""),
            "date": data.get("data", {}).get("date", {}).get("readable", ""),
        }
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return None

def is_available() -> bool:
    return True
