"""EventFulfiller — discovers events matching user personality and interests.

Aggregates from Eventbrite + Ticketmaster, filters through PersonalityFilter,
falls back to curated event types when no API available.
Zero LLM.
"""

from __future__ import annotations

from typing import Any

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
)
from wish_engine.apis import events_api, events_personality


# ── Curated event types (fallback when no API) ──────────────────────────────

EVENT_CATALOG: list[dict[str, Any]] = [
    # Performing arts
    {"title": "Classical Concert", "description": "Orchestra performing classical masterpieces", "category": "classical", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["music", "classical", "culture", "traditional", "calming"]},
    {"title": "Opera Performance", "description": "Traditional opera in historic theater", "category": "opera", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "opera", "culture", "traditional", "classical"]},
    {"title": "Theater Play", "description": "Drama performance by local theater company", "category": "theatre", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "theater", "culture"]},
    {"title": "Comedy Night", "description": "Stand-up comedy show with local comedians", "category": "comedy", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["comedy", "social", "fun", "humor"]},
    {"title": "Jazz Evening", "description": "Live jazz in intimate venue", "category": "jazz", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["music", "jazz", "culture", "calming"]},
    {"title": "Ballet Performance", "description": "Classical ballet showcase", "category": "ballet", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["art", "dance", "culture", "traditional", "classical"]},
    # Visual arts
    {"title": "Art Exhibition", "description": "Contemporary art gallery opening", "category": "exhibition", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "exhibition", "quiet", "calming", "culture"]},
    {"title": "Photography Show", "description": "Photography exhibition featuring local artists", "category": "photography", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "photography", "quiet", "calming"]},
    # Learning
    {"title": "Creative Workshop", "description": "Hands-on creative skills workshop", "category": "workshop", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["learning", "hands-on", "practical", "small-group", "creative"]},
    {"title": "Author Talk / Book Signing", "description": "Meet the author and get your book signed", "category": "book_signing", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["reading", "quiet", "calming", "author"]},
    {"title": "Public Lecture", "description": "Expert lecture on trending topics", "category": "lecture", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["learning", "theory", "quiet"]},
    # Music
    {"title": "Live Music Night", "description": "Local bands performing live", "category": "rock", "noise": "loud", "social": "high", "mood": "intense", "tags": ["music", "rock", "noisy", "intense", "social"]},
    {"title": "Folk Music Concert", "description": "Acoustic folk music in cozy venue", "category": "folk", "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["music", "folk", "traditional", "calming"]},
    # Social & community
    {"title": "Community Meetup", "description": "Local interest group gathering", "category": "meetup", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["social", "community", "group", "networking"]},
    {"title": "Weekend Market", "description": "Local artisan market with food and crafts", "category": "market", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["shopping", "social", "outdoor", "food"]},
    {"title": "Food Festival", "description": "Local food vendors and cooking demos", "category": "food_festival", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["food", "social", "outdoor", "fun"]},
    # Wellness
    {"title": "Group Yoga Session", "description": "Outdoor yoga in the park", "category": "yoga", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["exercise", "yoga", "calming", "quiet", "wellness"]},
    {"title": "Meditation Circle", "description": "Guided group meditation session", "category": "meditation", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["meditation", "calming", "quiet", "wellness"]},
    # Film
    {"title": "Film Screening", "description": "Independent or classic film showing", "category": "film", "noise": "quiet", "social": "medium", "mood": "calming", "tags": ["film", "culture", "quiet", "calming"]},
    {"title": "Documentary Night", "description": "Documentary screening with discussion", "category": "documentary", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["film", "documentary", "learning", "quiet"]},
    # Charity
    {"title": "Charity Event", "description": "Community fundraiser for local cause", "category": "charity", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["charity", "community", "helping", "social"]},
    {"title": "Volunteer Day", "description": "Community service and volunteering opportunity", "category": "charity", "noise": "moderate", "social": "high", "mood": "calming", "tags": ["charity", "community", "helping", "social", "volunteer"]},
]

# ── Keyword matching for wish text ───────────────────────────────────────────

_EVENT_KEYWORDS: dict[str, list[str]] = {
    "concert": ["classical", "jazz", "rock", "folk", "pop"],
    "音乐会": ["classical", "jazz", "folk"],
    "演出": ["theatre", "opera", "ballet", "comedy"],
    "表演": ["theatre", "opera", "ballet"],
    "话剧": ["theatre"],
    "歌剧": ["opera"],
    "theater": ["theatre"],
    "theatre": ["theatre"],
    "opera": ["opera"],
    "ballet": ["ballet"],
    "芭蕾": ["ballet"],
    "展览": ["exhibition", "photography", "gallery"],
    "exhibition": ["exhibition", "photography"],
    "画展": ["exhibition"],
    "comedy": ["comedy"],
    "喜剧": ["comedy"],
    "脱口秀": ["comedy"],
    "workshop": ["workshop"],
    "工作坊": ["workshop"],
    "meetup": ["meetup", "networking"],
    "聚会": ["meetup"],
    "market": ["market"],
    "市集": ["market"],
    "film": ["film", "documentary"],
    "电影": ["film"],
    "yoga": ["yoga"],
    "meditation": ["meditation"],
    "冥想": ["meditation"],
    "volunteer": ["charity"],
    "志愿者": ["charity"],
    "读书": ["book_signing"],
    "book": ["book_signing"],
    "红楼梦": ["opera", "theatre"],
    "京剧": ["opera"],
    "昆曲": ["opera"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: set[str] = set()
    for keyword, cats in _EVENT_KEYWORDS.items():
        if keyword in text_lower:
            matched.update(cats)
    return list(matched)


class EventFulfiller(L2Fulfiller):
    """Discovers events matching user personality and interests."""

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
        location: tuple[float, float] | None = None,
    ) -> L2FulfillmentResult:
        target_cats = _match_categories(wish.wish_text)

        # Try real event APIs first
        if location and events_api.is_available():
            # Build keyword from wish text
            keyword = wish.wish_text[:50] if not target_cats else None
            raw_events = events_api.search_all(
                lat=location[0], lng=location[1],
                keyword=keyword, max_results=15,
            )
            if raw_events:
                candidates = events_personality.enrich_events(raw_events)
                if target_cats:
                    candidates = [c for c in candidates if c["category"] in target_cats] or candidates
                recs = self._build_recommendations(candidates, detector_results, max_results=3)
                if recs:
                    return L2FulfillmentResult(
                        recommendations=recs,
                        map_data=MapData(place_type="event_venue", radius_km=25.0),
                        reminder_option=ReminderOption(text="Want a reminder before the event?", delay_hours=24),
                    )

        # Fallback to curated catalog
        if target_cats:
            candidates = [e for e in EVENT_CATALOG if e["category"] in target_cats]
        else:
            candidates = list(EVENT_CATALOG)

        if not candidates:
            candidates = list(EVENT_CATALOG)

        recs = self._build_recommendations(candidates, detector_results, max_results=3)

        return L2FulfillmentResult(
            recommendations=recs,
            map_data=MapData(place_type="event_venue", radius_km=25.0),
            reminder_option=ReminderOption(text="Want a reminder before the event?", delay_hours=24),
        )
