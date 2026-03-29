"""Nominatim API -- free geocoding. Address <-> coordinates. Part of OpenStreetMap."""

from __future__ import annotations

import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError


NOMINATIM_URL = "https://nominatim.openstreetmap.org"


def geocode(address: str) -> dict[str, Any] | None:
    """Address -> coordinates. FREE, no key."""
    params = {"q": address, "format": "json", "limit": 1}
    url = f"{NOMINATIM_URL}/search?{urlencode(params)}"
    try:
        req = Request(url, headers={"User-Agent": "SoulMap/1.0", "Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lng": float(data[0]["lon"]),
                "display_name": data[0].get("display_name", ""),
            }
        return None
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return None


def reverse_geocode(lat: float, lng: float) -> dict[str, Any] | None:
    """Coordinates -> address. FREE, no key."""
    params = {"lat": lat, "lon": lng, "format": "json"}
    url = f"{NOMINATIM_URL}/reverse?{urlencode(params)}"
    try:
        req = Request(url, headers={"User-Agent": "SoulMap/1.0", "Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        addr = data.get("address", {})
        return {
            "display_name": data.get("display_name", ""),
            "city": addr.get("city") or addr.get("town") or addr.get("village", ""),
            "country": addr.get("country", ""),
            "country_code": addr.get("country_code", ""),
            "postcode": addr.get("postcode", ""),
        }
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return None


def is_available() -> bool:
    """Always free, no key needed."""
    return True
