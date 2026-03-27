"""Maps Google Places types to personality-compatible attributes.

Converts raw Google Places API results into the format PersonalityFilter expects:
  noise: quiet/moderate/loud
  social: low/medium/high
  mood: calming/intense/confrontational
  tags: list[str]

Zero LLM. Pure mapping tables.
"""

from __future__ import annotations

from typing import Any

# Google Places type -> personality attributes
_TYPE_PERSONALITY_MAP: dict[str, dict[str, Any]] = {
    # Quiet, low social
    "library": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "reading", "calming", "study"]},
    "park": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "peaceful", "calming", "walking"]},
    "cemetery": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "peaceful", "reflection"]},
    "church": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "spiritual", "traditional", "calming"]},
    "mosque": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "spiritual", "traditional", "calming"]},
    "hindu_temple": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "spiritual", "traditional", "calming"]},
    "spa": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["relaxation", "quiet", "calming", "self-care"]},
    "art_gallery": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "creative", "calming", "art"]},
    "museum": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "culture", "calming", "learning"]},
    "book_store": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "reading", "calming"]},

    # Quiet-moderate, medium social
    "cafe": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["coffee", "calming", "social"]},
    "restaurant": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["dining", "social"]},
    "yoga_studio": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["exercise", "yoga", "calming", "quiet", "small-group"]},
    "physiotherapist": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["health", "calming", "therapy"]},
    "doctor": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["health", "calming"]},

    # Moderate, medium-high social
    "gym": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["exercise", "noisy", "intense", "equipment", "social"]},
    "swimming_pool": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["exercise", "swimming", "calming", "solo"]},
    "bowling_alley": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["fun", "social", "noisy", "group"]},
    "movie_theater": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["entertainment", "quiet", "calming"]},
    "shopping_mall": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["shopping", "noisy", "social"]},

    # Loud, high social
    "night_club": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["social", "noisy", "intense", "dance", "loud"]},
    "bar": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["social", "noisy", "drinking", "loud"]},
    "stadium": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["sports", "noisy", "social", "intense", "loud"]},
    "amusement_park": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["fun", "noisy", "social", "intense"]},

    # Nature & outdoor
    "campground": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "outdoor"]},
    "natural_feature": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "scenic"]},

    # Community
    "community_center": {"noise": "moderate", "social": "high", "mood": "calming", "tags": ["social", "community", "group"]},
    "university": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["learning", "social", "study"]},
}

# Default for unknown types
_DEFAULT_PERSONALITY = {"noise": "moderate", "social": "medium", "mood": "calming", "tags": []}


def enrich_place(place: dict[str, Any]) -> dict[str, Any]:
    """Add personality attributes to a Google Places API result.

    Takes a raw Google Places result dict and adds:
      noise, social, mood, tags -- compatible with PersonalityFilter

    Also normalizes fields for L2Fulfiller consumption:
      title, description, category, relevance_reason
    """
    types = place.get("types", [])
    name = place.get("name", "Unknown")
    vicinity = place.get("vicinity", "")
    rating = place.get("rating", 0)

    # Find best matching type
    personality = dict(_DEFAULT_PERSONALITY)
    matched_type = ""
    for t in types:
        if t in _TYPE_PERSONALITY_MAP:
            personality = dict(_TYPE_PERSONALITY_MAP[t])
            matched_type = t
            break

    # Build enriched place dict
    enriched = {
        "title": name,
        "description": f"{name} — {vicinity}" if vicinity else name,
        "category": matched_type or (types[0] if types else "place"),
        "noise": personality["noise"],
        "social": personality["social"],
        "mood": personality["mood"],
        "tags": list(personality["tags"]),
        "relevance_reason": "Found nearby based on your current location",
        # Preserve original data
        "_place_id": place.get("place_id", ""),
        "_rating": rating,
        "_types": types,
        "_lat": place.get("geometry", {}).get("location", {}).get("lat"),
        "_lng": place.get("geometry", {}).get("location", {}).get("lng"),
    }

    # Add rating to tags
    if rating >= 4.5:
        enriched["tags"].append("highly-rated")
    if rating >= 4.0:
        enriched["tags"].append("well-rated")

    return enriched


def enrich_places(places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Enrich a list of Google Places results with personality attributes."""
    return [enrich_place(p) for p in places]


# Wish keyword -> Google Places type mapping
WISH_TO_PLACE_TYPE: dict[str, str] = {
    "meditation": "spa",
    "冥想": "spa",
    "تأمل": "spa",
    "yoga": "gym",
    "瑜伽": "gym",
    "exercise": "gym",
    "运动": "gym",
    "رياضة": "gym",
    "gym": "gym",
    "健身": "gym",
    "swim": "swimming_pool",
    "游泳": "swimming_pool",
    "quiet": "park",
    "安静": "park",
    "هادئ": "park",
    "park": "park",
    "公园": "park",
    "café": "cafe",
    "咖啡": "cafe",
    "قهوة": "cafe",
    "library": "library",
    "图书馆": "library",
    "مكتبة": "library",
    "art": "art_gallery",
    "画画": "art_gallery",
    "therapy": "doctor",
    "咨询": "doctor",
    "spa": "spa",
    "按摩": "spa",
    "restaurant": "restaurant",
    "吃饭": "restaurant",
    "مطعم": "restaurant",
    "mosque": "mosque",
    "مسجد": "mosque",
    "清真寺": "mosque",
    "church": "church",
    "教堂": "church",
    "كنيسة": "church",
    "temple": "hindu_temple",
    "寺庙": "hindu_temple",
}


def wish_to_search_params(wish_text: str) -> dict[str, str]:
    """Convert wish text to Google Places search parameters.

    Returns dict with optional 'place_type' and 'keyword' for nearby_search.
    """
    text_lower = wish_text.lower()
    params: dict[str, str] = {}

    for keyword, place_type in WISH_TO_PLACE_TYPE.items():
        if keyword in text_lower:
            params["place_type"] = place_type
            params["keyword"] = keyword
            break

    return params
