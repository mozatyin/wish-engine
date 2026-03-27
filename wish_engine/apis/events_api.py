"""Event Discovery API client — aggregates events from multiple sources.

Supports: Eventbrite, Meetup, Ticketmaster, and generic event feeds.
Requires env vars: EVENTBRITE_API_KEY, MEETUP_API_KEY, TICKETMASTER_API_KEY
Falls back gracefully when keys unavailable.
Zero LLM.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib.error import URLError
from datetime import datetime, timedelta


# ── API endpoints ────────────────────────────────────────────────────────────

EVENTBRITE_KEY_ENV = "EVENTBRITE_API_KEY"
EVENTBRITE_SEARCH_URL = "https://www.eventbriteapi.com/v3/events/search/"

TICKETMASTER_KEY_ENV = "TICKETMASTER_API_KEY"
TICKETMASTER_SEARCH_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


def _get_key(env: str) -> str | None:
    return os.environ.get(env)


def is_available() -> bool:
    """Check if any event API is configured."""
    return any(os.environ.get(k) for k in [EVENTBRITE_KEY_ENV, TICKETMASTER_KEY_ENV])


def search_eventbrite(
    lat: float, lng: float, radius_km: int = 25,
    keyword: str | None = None,
    categories: list[str] | None = None,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """Search Eventbrite for nearby events."""
    key = _get_key(EVENTBRITE_KEY_ENV)
    if not key:
        return []
    params: dict[str, Any] = {
        "location.latitude": lat,
        "location.longitude": lng,
        "location.within": f"{radius_km}km",
        "expand": "venue,category",
        "sort_by": "date",
    }
    if keyword:
        params["q"] = keyword
    if categories:
        params["categories"] = ",".join(categories)
    url = f"{EVENTBRITE_SEARCH_URL}?{urlencode(params)}"
    try:
        req = Request(url, headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return [_normalize_eventbrite(e) for e in data.get("events", [])[:max_results]]
    except (URLError, json.JSONDecodeError, OSError):
        return []


def search_ticketmaster(
    lat: float, lng: float, radius_km: int = 25,
    keyword: str | None = None,
    classification: str | None = None,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """Search Ticketmaster for nearby events."""
    key = _get_key(TICKETMASTER_KEY_ENV)
    if not key:
        return []
    params: dict[str, Any] = {
        "apikey": key,
        "latlong": f"{lat},{lng}",
        "radius": radius_km,
        "unit": "km",
        "size": max_results,
        "sort": "date,asc",
    }
    if keyword:
        params["keyword"] = keyword
    if classification:
        params["classificationName"] = classification
    url = f"{TICKETMASTER_SEARCH_URL}?{urlencode(params)}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        embedded = data.get("_embedded", {})
        return [_normalize_ticketmaster(e) for e in embedded.get("events", [])[:max_results]]
    except (URLError, json.JSONDecodeError, OSError):
        return []


def search_all(
    lat: float, lng: float, radius_km: int = 25,
    keyword: str | None = None, max_results: int = 20,
) -> list[dict[str, Any]]:
    """Search all available event sources, merge and deduplicate."""
    results: list[dict[str, Any]] = []
    results.extend(search_eventbrite(lat, lng, radius_km, keyword, max_results=max_results))
    results.extend(search_ticketmaster(lat, lng, radius_km, keyword, max_results=max_results))
    # Dedupe by name similarity
    seen_names: set[str] = set()
    deduped = []
    for r in results:
        name_key = r.get("name", "").lower()[:30]
        if name_key not in seen_names:
            seen_names.add(name_key)
            deduped.append(r)
    return deduped[:max_results]


# ── Normalization ────────────────────────────────────────────────────────────

def _normalize_eventbrite(event: dict) -> dict[str, Any]:
    venue = event.get("venue", {}) or {}
    return {
        "name": event.get("name", {}).get("text", ""),
        "description": (event.get("description", {}) or {}).get("text", "")[:200],
        "url": event.get("url", ""),
        "start_time": event.get("start", {}).get("local", ""),
        "end_time": event.get("end", {}).get("local", ""),
        "venue_name": venue.get("name", ""),
        "venue_address": venue.get("address", {}).get("localized_address_display", ""),
        "lat": float(venue.get("latitude", 0) or 0),
        "lng": float(venue.get("longitude", 0) or 0),
        "category": (event.get("category", {}) or {}).get("name", ""),
        "is_free": event.get("is_free", False),
        "source": "eventbrite",
    }


def _normalize_ticketmaster(event: dict) -> dict[str, Any]:
    venues = event.get("_embedded", {}).get("venues", [{}])
    venue = venues[0] if venues else {}
    location = venue.get("location", {})
    dates = event.get("dates", {}).get("start", {})
    classifications = event.get("classifications", [{}])
    genre = classifications[0].get("genre", {}).get("name", "") if classifications else ""
    return {
        "name": event.get("name", ""),
        "description": event.get("info", event.get("pleaseNote", ""))[:200],
        "url": event.get("url", ""),
        "start_time": dates.get("localDate", "") + "T" + dates.get("localTime", ""),
        "end_time": "",
        "venue_name": venue.get("name", ""),
        "venue_address": f"{venue.get('city', {}).get('name', '')}, {venue.get('country', {}).get('name', '')}",
        "lat": float(location.get("latitude", 0) or 0),
        "lng": float(location.get("longitude", 0) or 0),
        "category": genre,
        "is_free": False,
        "source": "ticketmaster",
    }
