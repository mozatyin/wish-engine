"""OpenStreetMap Overpass API -- free, global place search. No API key needed.

Queries the Overpass API to find real places near any coordinates.
Returns actual place names, categories, and coordinates — sorted nearest-first,
open places ranked before closed ones.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import URLError


OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line distance in metres between two GPS coordinates."""
    dlat = (lat2 - lat1) * 111_000
    dlng = (lng2 - lng1) * 111_000 * math.cos(math.radians(lat1))
    return math.sqrt(dlat ** 2 + dlng ** 2)


def is_open_now(opening_hours: str | None) -> bool | None:
    """Check whether a place is currently open based on its OSM opening_hours string.

    Returns:
        True   — place is open right now
        False  — place is closed right now
        None   — cannot determine (missing or unparseable hours string)

    Handles the most common OSM formats:
        "24/7"                   → always open
        "Mo-Su 09:00-23:00"      → every day within hours
        "09:00-23:00"            → any day within hours
        "Mo-Fr 08:00-20:00"      → weekdays only (partial day-of-week support)
    """
    if not opening_hours:
        return None
    oh = opening_hours.strip().lower()

    if oh == "24/7":
        return True

    now = datetime.now()
    current_hour = now.hour + now.minute / 60.0

    # Day-of-week check (partial — only "Mo-Fr" vs "Sa,Su" distinction)
    weekday = now.weekday()  # 0=Mon … 6=Sun
    is_weekend = weekday >= 5

    if "mo-fr" in oh and is_weekend:
        return False
    if ("sa" in oh or "su" in oh) and not is_weekend:
        # Only open on weekends — rough heuristic
        pass  # let hour check decide; don't return False outright

    # Find ALL HH:MM-HH:MM time ranges — handles lunch breaks like "09:00-13:00,15:00-19:00"
    ranges = re.findall(r'(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})', oh)
    if not ranges:
        return None

    for (oh1, om1, ch1, cm1) in ranges:
        open_h  = int(oh1) + int(om1) / 60.0
        close_h = int(ch1) + int(cm1) / 60.0

        if close_h == 0.0:      # "23:00-00:00" means closes at midnight
            close_h = 24.0
        if close_h < open_h:    # overnight span e.g. "22:00-03:00"
            if current_hour >= open_h or current_hour < close_h:
                return True
        else:
            if open_h <= current_hour < close_h:
                return True

    return False  # Checked all ranges — not open in any of them


def nearby_places(
    lat: float,
    lng: float,
    radius_m: int = 2000,
    place_types: list[str] | None = None,
    max_results: int = 15,
) -> list[dict[str, Any]]:
    """Search for real places near coordinates using OpenStreetMap.

    Args:
        lat: Latitude
        lng: Longitude
        radius_m: Search radius in meters
        place_types: OSM amenity types to search (e.g., ["cafe", "library", "park"])
                    If None, searches common useful types.
        max_results: Max results to return

    Returns:
        List of place dicts with: name, category, lat, lng, tags
    """
    if place_types is None:
        place_types = [
            "cafe", "library", "park", "restaurant", "place_of_worship",
            "community_centre", "arts_centre", "theatre", "cinema",
            "gym", "swimming_pool", "hospital", "pharmacy",
            "bookshop", "museum", "gallery",
        ]

    # Build Overpass QL query
    amenity_filter = "|".join(place_types)
    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"~"^({amenity_filter})$"]["name"](around:{radius_m},{lat},{lng});
      node["leisure"~"^(park|garden|nature_reserve|fitness_centre|yoga)$"]["name"](around:{radius_m},{lat},{lng});
      node["shop"~"^(books|supermarket)$"]["name"](around:{radius_m},{lat},{lng});
    );
    out body {max_results};
    """

    try:
        data = f"data={quote(query)}"
        req = Request(OVERPASS_URL, data=data.encode(), headers={"Accept": "application/json"})
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())

        places = []
        for element in result.get("elements", [])[:max_results]:
            tags = element.get("tags", {})
            name = tags.get("name", "")
            if not name:
                continue

            category = tags.get("amenity") or tags.get("leisure") or tags.get("shop") or "place"

            place_lat = element.get("lat")
            place_lng = element.get("lon")
            dist = _haversine_m(lat, lng, place_lat, place_lng) if (place_lat and place_lng) else None
            places.append({
                "name": name,
                "category": category,
                "lat": place_lat,
                "lng": place_lng,
                "osm_tags": tags,
                "address": tags.get("addr:street", ""),
                "opening_hours": tags.get("opening_hours", ""),
                "website": tags.get("website", ""),
                "phone": tags.get("phone", ""),
                "_distance_m": dist,
            })

        return places

    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []


def nearby_events_venues(
    lat: float,
    lng: float,
    radius_m: int = 5000,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Find event venues (theaters, concert halls, galleries, community centers) nearby."""
    venue_types = [
        "theatre", "cinema", "arts_centre", "community_centre",
        "nightclub", "events_venue", "conference_centre",
    ]
    return nearby_places(lat, lng, radius_m, venue_types, max_results)


def _osm_to_personality(place: dict) -> dict[str, Any]:
    """Convert OSM place to personality-compatible format for PersonalityFilter."""
    category = place.get("category", "")
    name = place.get("name", "")

    # Map OSM categories to noise/social/mood/tags
    category_map = {
        "cafe": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["coffee", "calming", "wifi"]},
        "library": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "reading", "calming", "study", "free"]},
        "park": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "outdoor", "free"]},
        "garden": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "peaceful"]},
        "restaurant": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["dining", "social"]},
        "place_of_worship": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["spiritual", "quiet", "calming", "traditional"]},
        "community_centre": {"noise": "moderate", "social": "high", "mood": "calming", "tags": ["social", "community", "events"]},
        "arts_centre": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "quiet", "calming", "culture", "creative"]},
        "theatre": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "culture", "theater"]},
        "cinema": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["entertainment", "quiet"]},
        "gym": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["exercise", "intense", "fitness"]},
        "fitness_centre": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["exercise", "intense", "fitness"]},
        "swimming_pool": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["exercise", "swimming", "calming"]},
        "hospital": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["medical", "calming"]},
        "pharmacy": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["medical", "24h"]},
        "bookshop": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["reading", "quiet", "calming", "books"]},
        "books": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["reading", "quiet", "calming", "books"]},
        "museum": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["culture", "quiet", "calming", "learning"]},
        "gallery": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "quiet", "calming", "culture"]},
        "yoga": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["yoga", "calming", "exercise", "quiet"]},
        "nature_reserve": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "hiking"]},
        "nightclub": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["nightlife", "social", "noisy", "dance"]},
        "supermarket": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["shopping", "practical"]},
    }

    defaults = {"noise": "moderate", "social": "medium", "mood": "calming", "tags": []}
    attrs = category_map.get(category, defaults)

    return {
        "title": name,
        "description": f"{name} — {place.get('address') or category}",
        "category": category,
        "noise": attrs["noise"],
        "social": attrs["social"],
        "mood": attrs["mood"],
        "tags": list(attrs["tags"]),
        "action_url": place.get("website"),
        "_lat": place.get("lat"),
        "_lng": place.get("lng"),
        "_distance_m": place.get("_distance_m"),
        "_opening_hours": place.get("opening_hours"),
        "_is_open": is_open_now(place.get("opening_hours")),
        "_phone": place.get("phone"),
    }


def search_and_enrich(
    lat: float,
    lng: float,
    radius_m: int = 2000,
    place_types: list[str] | None = None,
    max_results: int = 15,
) -> list[dict[str, Any]]:
    """Search OSM and return personality-compatible place dicts.

    Results are sorted: open-now first, then by distance (nearest first).
    Unknown opening hours are treated as potentially open (ranked after confirmed open).
    Confirmed-closed places rank last.
    """
    raw = nearby_places(lat, lng, radius_m, place_types, max_results)
    enriched = [_osm_to_personality(p) for p in raw]

    def _sort_key(place: dict) -> tuple:
        is_open = place.get("_is_open")
        # open=True → 0, unknown=None → 1, closed=False → 2
        open_rank = 0 if is_open is True else (1 if is_open is None else 2)
        dist = place.get("_distance_m") or float("inf")
        return (open_rank, dist)

    enriched.sort(key=_sort_key)
    return enriched
