"""Weather-aware filtering for outdoor recommendations.

Adjusts place/activity recommendations based on current weather conditions.
Zero LLM. Pure rule-based logic.
"""

from __future__ import annotations

from typing import Any


# Tags that indicate an outdoor activity/place
_OUTDOOR_TAGS = {"outdoor", "nature", "walking", "park", "scenic", "campground", "running", "hiking"}


def should_exclude_outdoor(weather: dict[str, Any]) -> bool:
    """Return True if weather conditions make outdoor activities inadvisable.

    Excludes when:
      - Rain or snow
      - Extreme heat (>40 C)
      - Extreme cold (<0 C)
    """
    condition = weather.get("condition", "clear")
    temp_c = weather.get("temp_c", 25)

    if condition in ("rain", "snow"):
        return True
    if temp_c > 40:
        return True
    if temp_c < 0:
        return True
    return False


def adjust_recommendations(
    candidates: list[dict[str, Any]],
    weather: dict[str, Any],
) -> list[dict[str, Any]]:
    """Remove outdoor places in bad weather and boost indoor ones.

    If weather is fine, returns candidates unchanged.
    If weather is bad:
      - Removes candidates tagged as outdoor
      - Adds +0.1 score boost to remaining (indoor) candidates
    """
    if not should_exclude_outdoor(weather):
        return candidates

    result = []
    for c in candidates:
        tags = set(c.get("tags", []))
        if tags & _OUTDOOR_TAGS:
            continue
        # Boost indoor candidates
        c = dict(c)
        c["_personality_score"] = c.get("_personality_score", 0.5) + 0.1
        result.append(c)
    return result


def get_weather_tags(weather: dict[str, Any]) -> list[str]:
    """Generate descriptive tags for current weather conditions.

    Returns tags like: ["rainy", "indoor-preferred"], ["hot", "stay-cool"],
    ["cold", "warm-up"], ["clear", "outdoor-friendly"].
    """
    tags: list[str] = []
    condition = weather.get("condition", "clear")
    temp_c = weather.get("temp_c", 25)

    # Condition tags
    if condition == "rain":
        tags.extend(["rainy", "indoor-preferred"])
    elif condition == "snow":
        tags.extend(["snowy", "indoor-preferred"])
    elif condition == "cloudy":
        tags.append("cloudy")
    else:
        tags.extend(["clear", "outdoor-friendly"])

    # Temperature tags
    if temp_c > 40:
        tags.extend(["hot", "stay-cool", "indoor-preferred"])
    elif temp_c > 30:
        tags.append("warm")
    elif temp_c < 0:
        tags.extend(["cold", "warm-up", "indoor-preferred"])
    elif temp_c < 10:
        tags.append("chilly")
    else:
        tags.append("comfortable")

    # Wind tags
    wind = weather.get("wind_speed_ms", 3.0)
    if wind > 15:
        tags.append("windy")

    return tags
