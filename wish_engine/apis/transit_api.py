"""Google Directions API client — transit time estimation.

Requires GOOGLE_DIRECTIONS_API_KEY environment variable.
Falls back to haversine straight-line distance estimation when API is unavailable.
Zero LLM.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DIRECTIONS_API_KEY_ENV = "GOOGLE_DIRECTIONS_API_KEY"
DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"

# Fallback speed assumptions (km/h)
_FALLBACK_SPEEDS: dict[str, float] = {
    "walking": 5.0,
    "transit": 30.0,
    "driving": 40.0,
}

EARTH_RADIUS_KM = 6371.0


def _get_api_key() -> str | None:
    return os.environ.get(DIRECTIONS_API_KEY_ENV)


def is_available() -> bool:
    """Check if Google Directions API is configured."""
    return _get_api_key() is not None


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate straight-line distance between two points using haversine formula.

    Args:
        lat1, lng1: Origin coordinates
        lat2, lng2: Destination coordinates

    Returns:
        Distance in kilometers
    """
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def estimate_transit(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    mode: str = "transit",
) -> dict[str, Any]:
    """Estimate transit time between two points.

    Tries Google Directions API first, falls back to haversine estimation.

    Args:
        origin_lat, origin_lng: Origin coordinates
        dest_lat, dest_lng: Destination coordinates
        mode: Travel mode — "walking", "transit", or "driving"

    Returns:
        Dict with duration_minutes, distance_km, mode, summary
    """
    if mode not in _FALLBACK_SPEEDS:
        mode = "transit"

    # Try API first
    api_key = _get_api_key()
    if api_key:
        result = _api_estimate(origin_lat, origin_lng, dest_lat, dest_lng, mode, api_key)
        if result is not None:
            return result

    # Fallback: haversine estimation
    return _haversine_estimate(origin_lat, origin_lng, dest_lat, dest_lng, mode)


def _api_estimate(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    mode: str,
    api_key: str,
) -> dict[str, Any] | None:
    """Estimate using Google Directions API."""
    params = {
        "origin": f"{origin_lat},{origin_lng}",
        "destination": f"{dest_lat},{dest_lng}",
        "mode": mode,
        "key": api_key,
    }
    url = f"{DIRECTIONS_URL}?{urlencode(params)}"

    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        routes = data.get("routes", [])
        if not routes:
            return None

        leg = routes[0].get("legs", [{}])[0]
        duration_s = leg.get("duration", {}).get("value", 0)
        distance_m = leg.get("distance", {}).get("value", 0)

        duration_minutes = max(1, round(duration_s / 60))
        distance_km = round(distance_m / 1000, 1)

        mode_label = {"walking": "walk", "transit": "metro", "driving": "drive"}.get(mode, mode)
        summary = f"{duration_minutes} min by {mode_label}"

        return {
            "duration_minutes": duration_minutes,
            "distance_km": distance_km,
            "mode": mode,
            "summary": summary,
        }
    except (URLError, json.JSONDecodeError, OSError, IndexError, KeyError):
        return None


def _haversine_estimate(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    mode: str,
) -> dict[str, Any]:
    """Estimate transit time using haversine distance and assumed speeds."""
    distance_km = haversine_km(origin_lat, origin_lng, dest_lat, dest_lng)
    speed = _FALLBACK_SPEEDS.get(mode, 30.0)
    duration_minutes = max(1, round(distance_km / speed * 60))

    mode_label = {"walking": "walk", "transit": "metro", "driving": "drive"}.get(mode, mode)
    summary = f"~{duration_minutes} min by {mode_label} (estimated)"

    return {
        "duration_minutes": duration_minutes,
        "distance_km": round(distance_km, 1),
        "mode": mode,
        "summary": summary,
    }
