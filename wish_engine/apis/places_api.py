"""Google Places API client — Nearby Search + Place Details.

Requires GOOGLE_PLACES_API_KEY environment variable.
Falls back gracefully when API key is not available.
Zero LLM.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError


PLACES_API_KEY_ENV = "GOOGLE_PLACES_API_KEY"
NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def _get_api_key() -> str | None:
    return os.environ.get(PLACES_API_KEY_ENV)


def is_available() -> bool:
    """Check if Google Places API is configured."""
    return _get_api_key() is not None


def nearby_search(
    lat: float,
    lng: float,
    radius_m: int = 5000,
    place_type: str | None = None,
    keyword: str | None = None,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """Search for nearby places using Google Places Nearby Search API.

    Args:
        lat: Latitude
        lng: Longitude
        radius_m: Search radius in meters (default 5km)
        place_type: Google Places type (e.g. "gym", "park", "cafe")
        keyword: Additional keyword filter
        max_results: Max results to return

    Returns:
        List of place dicts with: name, place_id, types, rating, vicinity,
        geometry (lat/lng), opening_hours, price_level
    """
    api_key = _get_api_key()
    if not api_key:
        return []

    params: dict[str, Any] = {
        "location": f"{lat},{lng}",
        "radius": radius_m,
        "key": api_key,
    }
    if place_type:
        params["type"] = place_type
    if keyword:
        params["keyword"] = keyword

    url = f"{NEARBY_SEARCH_URL}?{urlencode(params)}"

    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results", [])
        return results[:max_results]
    except (URLError, json.JSONDecodeError, OSError):
        return []


def place_details(place_id: str) -> dict[str, Any] | None:
    """Get detailed info for a specific place.

    Returns dict with: name, formatted_address, formatted_phone_number,
    website, opening_hours, reviews, rating, price_level, types
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,opening_hours,reviews,rating,price_level,types,geometry",
        "key": api_key,
    }
    url = f"{PLACE_DETAILS_URL}?{urlencode(params)}"

    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data.get("result")
    except (URLError, json.JSONDecodeError, OSError):
        return None
