"""Foursquare Places API v3 — free tier, no credit card. 50 requests/day."""

from __future__ import annotations
import json, os
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError

FSQ_KEY_ENV = "FOURSQUARE_API_KEY"
FSQ_URL = "https://api.foursquare.com/v3/places/search"

def is_available() -> bool:
    return os.environ.get(FSQ_KEY_ENV) is not None

def search_places(lat: float, lng: float, query: str = "", categories: str = "", radius: int = 2000, limit: int = 10) -> list[dict[str, Any]]:
    """Search Foursquare for nearby places. Free tier: 50 req/day."""
    key = os.environ.get(FSQ_KEY_ENV)
    if not key:
        return []
    params = {"ll": f"{lat},{lng}", "radius": radius, "limit": limit}
    if query: params["query"] = query
    if categories: params["categories"] = categories
    url = f"{FSQ_URL}?{urlencode(params)}"
    try:
        req = Request(url, headers={"Authorization": key, "Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        results = []
        for place in data.get("results", []):
            loc = place.get("location", {})
            cats = place.get("categories", [{}])
            results.append({
                "name": place.get("name", ""),
                "address": loc.get("formatted_address", ""),
                "lat": loc.get("latitude"),
                "lng": loc.get("longitude"),
                "distance_m": place.get("distance", 0),
                "category": cats[0].get("name", "") if cats else "",
                "category_id": cats[0].get("id", 0) if cats else 0,
            })
        return results
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []
