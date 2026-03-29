"""Free event discovery -- combines OSM venues + calendar heuristics.

When no Eventbrite/Ticketmaster key available:
1. Find event VENUES near user (theatres, galleries, community centers) via OSM
2. Infer likely events from venue type + day of week
3. Return "probable events" with venue info

Not as good as real event APIs, but works everywhere for free.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from wish_engine.apis.osm_api import nearby_places


# Day-of-week -> likely events at venue types
VENUE_EVENT_HEURISTICS: dict[str, dict[int, str]] = {
    "theatre": {
        4: "Weekend show likely tonight",  # Friday
        5: "Saturday matinee and evening shows",
        6: "Sunday matinee",
    },
    "arts_centre": {
        0: "Gallery exhibitions usually open Mon-Sat",
        5: "Saturday exhibition openings common",
        6: "Sunday gallery walk",
    },
    "community_centre": {
        0: "Community events and classes throughout the week",
        2: "Mid-week workshops common",
        5: "Weekend community events",
    },
    "cinema": {
        4: "New releases on Friday",
        5: "Saturday screenings",
        6: "Sunday family matinee",
    },
}


def discover_events_free(
    lat: float,
    lng: float,
    radius_m: int = 5000,
    day_of_week: int | None = None,
) -> list[dict[str, Any]]:
    """Discover probable events from nearby venues. FREE, no key."""
    if day_of_week is None:
        day_of_week = datetime.now().weekday()

    venue_types = [
        "theatre", "arts_centre", "community_centre",
        "cinema", "nightclub", "events_venue",
    ]
    venues = nearby_places(lat, lng, radius_m, venue_types, max_results=10)

    events: list[dict[str, Any]] = []
    for venue in venues:
        category = venue.get("category", "")
        name = venue.get("name", "")
        if not name:
            continue

        heuristics = VENUE_EVENT_HEURISTICS.get(category, {})
        event_hint = heuristics.get(day_of_week, "Check venue for current events")

        events.append({
            "venue_name": name,
            "venue_category": category,
            "event_hint": event_hint,
            "lat": venue.get("lat"),
            "lng": venue.get("lng"),
            "address": venue.get("address", ""),
            "website": venue.get("website", ""),
            "opening_hours": venue.get("opening_hours", ""),
        })

    return events


def is_available() -> bool:
    """Uses OSM which is always free."""
    return True
