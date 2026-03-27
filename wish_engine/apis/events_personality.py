"""Maps events to personality-compatible attributes for PersonalityFilter.

Converts event data to the noise/social/mood/tags format.
Zero LLM.
"""

from __future__ import annotations

from typing import Any

# Event category -> personality attributes
_CATEGORY_MAP: dict[str, dict[str, Any]] = {
    # Performing arts
    "theatre": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "theater", "culture", "traditional"]},
    "opera": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "opera", "culture", "traditional", "classical"]},
    "ballet": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "dance", "culture", "traditional", "classical"]},
    "classical": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["music", "classical", "culture", "traditional", "calming"]},
    "jazz": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["music", "jazz", "culture", "calming"]},
    "comedy": {"noise": "moderate", "social": "high", "mood": "calming", "tags": ["comedy", "social", "fun", "humor"]},
    # Music
    "rock": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["music", "rock", "noisy", "intense", "social"]},
    "pop": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["music", "pop", "noisy", "social"]},
    "hip-hop": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["music", "hiphop", "noisy", "intense"]},
    "electronic": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["music", "electronic", "noisy", "intense", "dance"]},
    "folk": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["music", "folk", "traditional", "calming"]},
    "world": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["music", "world", "culture"]},
    # Visual arts
    "exhibition": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "exhibition", "quiet", "calming", "culture"]},
    "gallery": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "gallery", "quiet", "calming"]},
    "photography": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "photography", "quiet", "calming"]},
    # Learning & workshops
    "workshop": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["learning", "hands-on", "practical", "small-group"]},
    "lecture": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["learning", "theory", "quiet", "self-paced"]},
    "masterclass": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["learning", "expert", "small-group"]},
    "book_signing": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["reading", "quiet", "calming", "author"]},
    # Wellness
    "yoga": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["exercise", "yoga", "calming", "quiet", "wellness"]},
    "meditation": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["meditation", "calming", "quiet", "wellness"]},
    "fitness": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["exercise", "fitness", "intense", "social"]},
    # Social & community
    "meetup": {"noise": "moderate", "social": "high", "mood": "calming", "tags": ["social", "community", "group", "networking"]},
    "networking": {"noise": "moderate", "social": "high", "mood": "calming", "tags": ["social", "professional", "networking"]},
    "festival": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["social", "festival", "noisy", "fun", "outdoor"]},
    "market": {"noise": "moderate", "social": "high", "mood": "calming", "tags": ["shopping", "social", "outdoor", "food"]},
    # Food & drink
    "food_festival": {"noise": "moderate", "social": "high", "mood": "calming", "tags": ["food", "social", "outdoor", "fun"]},
    "wine_tasting": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["food", "wine", "quiet", "calming"]},
    "cooking_class": {"noise": "moderate", "social": "medium", "mood": "calming", "tags": ["food", "cooking", "hands-on", "practical", "social"]},
    # Sports
    "sports": {"noise": "loud", "social": "high", "mood": "intense", "tags": ["sports", "noisy", "intense", "social"]},
    "running": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["exercise", "running", "outdoor", "calming"]},
    # Religious/spiritual
    "religious": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["spiritual", "traditional", "calming", "quiet"]},
    # Film
    "film": {"noise": "quiet", "social": "medium", "mood": "calming", "tags": ["film", "culture", "quiet", "calming"]},
    "documentary": {"noise": "quiet", "social": "low", "mood": "calming", "tags": ["film", "documentary", "learning", "quiet"]},
    # Kids/family
    "family": {"noise": "moderate", "social": "high", "mood": "calming", "tags": ["family", "social", "fun"]},
    # Charity
    "charity": {"noise": "moderate", "social": "high", "mood": "calming", "tags": ["charity", "community", "helping", "social"]},
}

_DEFAULT = {"noise": "moderate", "social": "medium", "mood": "calming", "tags": []}

# Keywords for category inference from event name/description
_KEYWORD_CATEGORIES: dict[str, str] = {
    # Chinese
    "京剧": "opera", "昆曲": "opera", "话剧": "theatre", "歌剧": "opera",
    "芭蕾": "ballet", "交响": "classical", "音乐会": "classical",
    "相声": "comedy", "脱口秀": "comedy", "喜剧": "comedy",
    "画展": "exhibition", "摄影展": "photography", "书法": "exhibition",
    "红楼梦": "opera", "西游记": "theatre", "三国": "theatre",
    "读书会": "book_signing", "讲座": "lecture", "工作坊": "workshop",
    "瑜伽": "yoga", "冥想": "meditation", "跑步": "running",
    "市集": "market", "夜市": "market", "美食节": "food_festival",
    "电影": "film", "纪录片": "documentary",
    # Arabic
    "مسرح": "theatre", "أوبرا": "opera", "موسيقى": "classical",
    "معرض": "exhibition", "ورشة": "workshop", "محاضرة": "lecture",
    "يوغا": "yoga", "تأمل": "meditation",
    "مهرجان": "festival", "سوق": "market",
    # English
    "opera": "opera", "ballet": "ballet", "symphony": "classical",
    "jazz": "jazz", "comedy": "comedy", "stand-up": "comedy",
    "exhibition": "exhibition", "gallery": "gallery",
    "workshop": "workshop", "lecture": "lecture", "masterclass": "masterclass",
    "yoga": "yoga", "meditation": "meditation",
    "meetup": "meetup", "networking": "networking",
    "festival": "festival", "market": "market",
    "wine tasting": "wine_tasting", "cooking": "cooking_class",
    "film": "film", "documentary": "documentary",
    "book": "book_signing", "reading": "book_signing",
    "charity": "charity", "volunteer": "charity",
    "rock": "rock", "pop": "pop", "hip hop": "hip-hop",
    "electronic": "electronic", "folk": "folk",
}


def _infer_category(event: dict) -> str:
    """Infer event category from name + description + source category."""
    # Use source category first
    cat = event.get("category", "").lower()
    if cat in _CATEGORY_MAP:
        return cat

    # Keyword match on name + description
    text = (event.get("name", "") + " " + event.get("description", "")).lower()
    for keyword, category in _KEYWORD_CATEGORIES.items():
        if keyword in text:
            return category

    return ""


def enrich_event(event: dict[str, Any]) -> dict[str, Any]:
    """Add personality attributes to a normalized event dict."""
    category = _infer_category(event)
    personality = dict(_CATEGORY_MAP.get(category, _DEFAULT))

    enriched = {
        "title": event.get("name", "Unknown Event"),
        "description": event.get("description", "")[:150] or event.get("name", ""),
        "category": category or "event",
        "noise": personality["noise"],
        "social": personality["social"],
        "mood": personality["mood"],
        "tags": list(personality["tags"]),
        "relevance_reason": "Matches your interests",
        "action_url": event.get("url"),
        # Event-specific fields
        "_start_time": event.get("start_time", ""),
        "_end_time": event.get("end_time", ""),
        "_venue_name": event.get("venue_name", ""),
        "_venue_address": event.get("venue_address", ""),
        "_lat": event.get("lat"),
        "_lng": event.get("lng"),
        "_is_free": event.get("is_free", False),
        "_source": event.get("source", ""),
    }

    if event.get("is_free"):
        enriched["tags"].append("free")

    return enriched


def enrich_events(events: list[dict]) -> list[dict]:
    return [enrich_event(e) for e in events]
