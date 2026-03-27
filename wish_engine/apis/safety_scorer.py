"""Safety Scorer — local-compute safety scoring for route/time/place.

Scores safety 0-1 based on time of day, gender, and nearby place types.
Zero API calls. Zero LLM.
"""

from __future__ import annotations


def is_available() -> bool:
    """Always True — pure local computation."""
    return True


def score_safety(
    hour: int,
    is_female: bool = False,
    place_types_nearby: list[str] | None = None,
) -> float:
    """Score safety from 0 to 1 based on time, gender, and nearby places.

    Args:
        hour: Hour of day (0-23).
        is_female: Whether the user is female (additional late-night penalty).
        place_types_nearby: List of nearby place types (e.g. "police_station").

    Returns:
        Float 0-1 where 1 = safest.
    """
    # Time-based base score
    if 0 <= hour < 5:
        base = 0.3
    elif 5 <= hour < 7:
        base = 0.6
    elif 7 <= hour < 22:
        base = 0.9
    else:  # 22-23
        base = 0.5

    # Gender adjustment
    if is_female and (hour >= 22 or hour < 5):
        base -= 0.2

    # Nearby place type boosts
    if place_types_nearby:
        types = set(place_types_nearby)
        if "police_station" in types:
            base += 0.1
        if "hospital" in types:
            base += 0.05
        if "24h_store" in types:
            base += 0.05

    return max(0.0, min(1.0, base))


def suggest_safe_places(lat: float, lng: float, hour: int) -> list[str]:
    """Suggest safe haven place types to look for based on time.

    Args:
        lat: Latitude (reserved for future proximity filtering).
        lng: Longitude (reserved for future proximity filtering).
        hour: Current hour (0-23).

    Returns:
        List of safe place type strings to search for nearby.
    """
    always_safe = ["police_station", "hospital", "fire_station"]

    if 0 <= hour < 5:
        # Deep night: prioritize 24h places
        return always_safe + [
            "24h_convenience_store",
            "24h_pharmacy",
            "24h_cafe",
            "hotel_lobby",
            "airport_terminal",
        ]
    elif 5 <= hour < 7:
        # Early morning
        return always_safe + [
            "24h_convenience_store",
            "mosque",
            "early_cafe",
        ]
    elif hour >= 22:
        # Late evening
        return always_safe + [
            "24h_convenience_store",
            "24h_cafe",
            "well_lit_street",
            "hotel_lobby",
        ]
    else:
        # Daytime: general safe spaces
        return ["cafe", "library", "mall", "park"]


def get_safety_tags(hour: int, is_female: bool = False) -> list[str]:
    """Get descriptive safety tags for the current time and user.

    Returns:
        List of tag strings like "late-night", "caution", "well-lit-preferred".
    """
    tags: list[str] = []

    if 0 <= hour < 5:
        tags.extend(["late-night", "caution", "well-lit-preferred", "buddy-recommended"])
    elif 5 <= hour < 7:
        tags.extend(["early-morning", "low-traffic"])
    elif 7 <= hour < 22:
        tags.append("daytime-safe")
    else:
        tags.extend(["late-evening", "caution", "well-lit-preferred"])

    if is_female and (hour >= 22 or hour < 7):
        tags.append("extra-caution")
        if "buddy-recommended" not in tags:
            tags.append("buddy-recommended")

    return tags
