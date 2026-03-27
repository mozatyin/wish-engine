"""Calendar-aware filtering for time-appropriate recommendations.

Prevents absurd suggestions like gym at 2am or lectures on Sunday morning.
No external calendar API needed — pure rule-based time logic.
Zero LLM.
"""

from __future__ import annotations

from typing import Any


# ── Time period definitions ──────────────────────────────────────────────────

def get_time_context(hour: int, day_of_week: int) -> dict[str, Any]:
    """Get contextual information about the current time.

    Args:
        hour: Hour of day (0-23)
        day_of_week: Day of week (0=Monday, 6=Sunday)

    Returns:
        Dict with period, is_weekend, activity_window
    """
    period = _get_period(hour)
    is_weekend = day_of_week >= 5  # Saturday=5, Sunday=6

    activity_window = _get_activity_window(period, is_weekend)

    return {
        "period": period,
        "is_weekend": is_weekend,
        "activity_window": activity_window,
    }


def _get_period(hour: int) -> str:
    """Map hour to time period."""
    if 5 <= hour < 9:
        return "early_morning"
    elif 9 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 22:
        return "evening"
    else:
        return "late_night"


def _get_activity_window(period: str, is_weekend: bool) -> list[str]:
    """Return suitable activity types for a given period."""
    base: dict[str, list[str]] = {
        "early_morning": ["cafe", "exercise", "meditation", "walking"],
        "morning": ["cafe", "exercise", "shopping", "museum", "class", "lecture", "library"],
        "afternoon": ["shopping", "museum", "park", "cafe", "class", "lecture", "library", "exercise", "outdoor"],
        "evening": ["restaurant", "bar", "movie", "concert", "social", "shopping", "exercise"],
        "late_night": ["bar", "restaurant", "social", "movie"],
    }
    activities = list(base.get(period, []))

    # Weekend allows more flexibility
    if is_weekend:
        if period == "early_morning":
            activities.extend(["brunch", "outdoor"])
        elif period == "morning":
            activities.extend(["brunch", "outdoor", "park", "social"])
        elif period == "late_night":
            activities.extend(["club", "concert"])
    return activities


# ── Time-appropriateness check ───────────────────────────────────────────────

# Recommendation types mapped to unsuitable periods
_UNSUITABLE: dict[str, set[str]] = {
    "gym": {"late_night"},
    "exercise": {"late_night"},
    "lecture": {"late_night", "early_morning"},
    "class": {"late_night"},
    "library": {"late_night"},
    "museum": {"late_night"},
    "nightclub": {"early_morning", "morning", "afternoon"},
    "club": {"early_morning", "morning", "afternoon"},
    "bar": {"early_morning", "morning"},
    "outdoor": {"late_night"},
    "park": {"late_night"},
    "hiking": {"late_night"},
    "shopping": {"late_night"},
}

# Weekend overrides — some restrictions are relaxed
_WEEKEND_ALLOW: dict[str, set[str]] = {
    "gym": {"late_night"},  # Still no gym at 2am on weekends
    "bar": set(),  # Bars OK anytime on weekends (empty = remove all restrictions? No, keep morning)
    "shopping": {"late_night"},  # Still no shopping late night
}


def is_good_time(hour: int, day_of_week: int, recommendation_type: str) -> bool:
    """Check if a recommendation type is appropriate for the given time.

    Args:
        hour: Hour of day (0-23)
        day_of_week: Day of week (0=Monday, 6=Sunday)
        recommendation_type: Type of activity (e.g., "gym", "lecture", "bar")

    Returns:
        True if the recommendation is appropriate for the time
    """
    period = _get_period(hour)
    is_weekend = day_of_week >= 5
    rec_type = recommendation_type.lower()

    unsuitable = _UNSUITABLE.get(rec_type)
    if unsuitable is None:
        # Unknown type — allow by default
        return True

    if period not in unsuitable:
        return True

    # Check weekend relaxation
    if is_weekend and rec_type in _WEEKEND_ALLOW:
        weekend_still_bad = _WEEKEND_ALLOW[rec_type]
        if period not in weekend_still_bad:
            return True

    return False


# ── Candidate filtering ─────────────────────────────────────────────────────

def filter_by_time(
    candidates: list[dict[str, Any]],
    hour: int,
    day_of_week: int,
) -> list[dict[str, Any]]:
    """Filter recommendation candidates based on time appropriateness.

    Removes candidates whose type is inappropriate for the current time.
    Candidates should have a "type" or "tags" field indicating their category.

    Args:
        candidates: List of recommendation dicts
        hour: Hour of day (0-23)
        day_of_week: Day of week (0=Monday, 6=Sunday)

    Returns:
        Filtered list with inappropriate candidates removed
    """
    result: list[dict[str, Any]] = []
    for c in candidates:
        # Check by explicit type
        rec_type = c.get("type", "")
        if rec_type and not is_good_time(hour, day_of_week, rec_type):
            continue

        # Check by tags
        tags = c.get("tags", [])
        excluded = False
        for tag in tags:
            if not is_good_time(hour, day_of_week, tag):
                excluded = True
                break
        if excluded:
            continue

        result.append(c)
    return result
