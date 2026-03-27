"""Transit-time filtering for location-based recommendations.

Removes candidates that are too far away and annotates remaining
candidates with transit time information.
Zero LLM.
"""

from __future__ import annotations

from typing import Any

from wish_engine.apis.transit_api import estimate_transit


def filter_by_transit(
    candidates: list[dict[str, Any]],
    origin: tuple[float, float],
    max_minutes: int = 30,
    mode: str = "transit",
) -> list[dict[str, Any]]:
    """Filter candidates by transit time from origin.

    Candidates must have "lat" and "lng" fields (or "geometry.location").
    Removes candidates that exceed max_minutes travel time.
    Adds _transit_time and _transit_summary to each passing candidate.

    Args:
        candidates: List of place/event dicts with location info
        origin: (lat, lng) tuple of user's current location
        max_minutes: Maximum acceptable travel time in minutes
        mode: Travel mode — "walking", "transit", or "driving"

    Returns:
        Filtered list with transit annotations added
    """
    origin_lat, origin_lng = origin
    result: list[dict[str, Any]] = []

    for c in candidates:
        dest_lat, dest_lng = _extract_coords(c)
        if dest_lat is None or dest_lng is None:
            # No coordinates — keep candidate but skip transit annotation
            result.append(c)
            continue

        transit = estimate_transit(origin_lat, origin_lng, dest_lat, dest_lng, mode=mode)
        if transit["duration_minutes"] > max_minutes:
            continue

        # Annotate and keep
        annotated = dict(c)
        annotated["_transit_time"] = transit["duration_minutes"]
        annotated["_transit_summary"] = transit["summary"]
        result.append(annotated)

    return result


def _extract_coords(candidate: dict[str, Any]) -> tuple[float | None, float | None]:
    """Extract lat/lng from a candidate dict.

    Supports flat format {"lat": ..., "lng": ...} and
    Google Places format {"geometry": {"location": {"lat": ..., "lng": ...}}}.
    """
    # Flat format
    if "lat" in candidate and "lng" in candidate:
        return candidate["lat"], candidate["lng"]

    # Google Places format
    geometry = candidate.get("geometry", {})
    location = geometry.get("location", {})
    if "lat" in location and "lng" in location:
        return location["lat"], location["lng"]

    return None, None
