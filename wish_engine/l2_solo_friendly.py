"""SoloFriendlyFulfiller — solo-friendly place recommendations with comfort scores.

15-entry curated catalog of solo-friendly place types, each rated on
'solo comfort score' (how comfortable is it to go alone). Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Solo Comfort Score: 1.0 = totally normal alone, 0.3 = a bit awkward ──────

SOLO_CATALOG: list[dict] = [
    {
        "title": "Solo-Friendly Cafe",
        "description": "Bring a book or laptop. Cafes are the ultimate solo-friendly zone.",
        "category": "solo_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 1.0,
        "tags": ["cafe", "quiet", "calming", "reading", "self-paced", "everyday"],
    },
    {
        "title": "Single Dining — Counter Seat",
        "description": "Ramen bar, sushi counter, or tapas bar — designed for solo diners.",
        "category": "single_dining",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "solo_comfort": 0.85,
        "tags": ["dining", "food", "calming", "practical", "everyday"],
    },
    {
        "title": "Solo Movie — Weekday Matinee",
        "description": "Weekday afternoon screenings are half empty. Bring your own popcorn.",
        "category": "solo_movie",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 0.9,
        "tags": ["movie", "quiet", "calming", "entertainment", "self-paced"],
    },
    {
        "title": "Museum Alone — Your Own Pace",
        "description": "No one rushing you. Spend 30 minutes at one painting if you want.",
        "category": "museum_alone",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 0.95,
        "tags": ["museum", "quiet", "calming", "cultural", "reflective", "self-paced"],
    },
    {
        "title": "Park Bench with a View",
        "description": "Just sit, watch, breathe. The simplest form of being alone well.",
        "category": "park_bench",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 1.0,
        "tags": ["park", "quiet", "calming", "nature", "everyday", "reflective"],
    },
    {
        "title": "Library Nook",
        "description": "Find the quietest corner. Libraries are built for solitude.",
        "category": "library_nook",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 1.0,
        "tags": ["library", "quiet", "calming", "reading", "self-paced", "reflective"],
    },
    {
        "title": "Solo Travel Hostel — Common Area",
        "description": "Everyone there is also alone. Instant community without obligation.",
        "category": "solo_travel_hostel",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "solo_comfort": 0.8,
        "tags": ["travel", "social", "community", "adventure"],
    },
    {
        "title": "One-Person Workshop",
        "description": "Pottery, candle-making, painting — solo workshops are normal and meditative.",
        "category": "one_person_workshop",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 0.85,
        "tags": ["workshop", "quiet", "calming", "creative", "hands_on", "self-paced"],
    },
    {
        "title": "Solo Hiking",
        "description": "Just you and the trail. Some of the best conversations happen with yourself.",
        "category": "solo_hiking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 0.9,
        "tags": ["hiking", "quiet", "nature", "adventure", "reflective", "self-paced"],
    },
    {
        "title": "Solo Spa Day",
        "description": "Robes, silence, and zero social obligations. Peak solo luxury.",
        "category": "solo_spa",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 0.95,
        "tags": ["spa", "quiet", "calming", "self-paced", "luxury"],
    },
    {
        "title": "Window Seat Cafe",
        "description": "People-watch from a cozy window seat with your drink of choice.",
        "category": "window_seat_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 1.0,
        "tags": ["cafe", "quiet", "calming", "reflective", "everyday"],
    },
    {
        "title": "Garden Reading Spot",
        "description": "Botanical garden or community garden with a bench and a book.",
        "category": "garden_reading",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 1.0,
        "tags": ["garden", "quiet", "calming", "nature", "reading", "reflective"],
    },
    {
        "title": "Solo Concert — Standing Section",
        "description": "Standing section at a concert. Everyone faces the stage — no one notices you are alone.",
        "category": "solo_concert",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "solo_comfort": 0.7,
        "tags": ["concert", "social", "entertainment", "adventure"],
    },
    {
        "title": "Solo Cooking Class",
        "description": "Everyone is focused on their station. Being alone is the norm.",
        "category": "solo_cooking_class",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "solo_comfort": 0.8,
        "tags": ["cooking", "calming", "creative", "hands_on", "practical"],
    },
    {
        "title": "Beach Alone — Early Morning",
        "description": "Dawn beach walk or sunrise swim. The ocean does not care if you came alone.",
        "category": "beach_alone",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "solo_comfort": 0.95,
        "tags": ["beach", "quiet", "calming", "nature", "reflective", "self-paced"],
    },
]


def _match_solo_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    kw_map = {
        "cafe": ["cafe"],
        "咖啡": ["cafe"],
        "eat": ["dining", "food"],
        "吃": ["dining", "food"],
        "movie": ["movie", "entertainment"],
        "电影": ["movie", "entertainment"],
        "museum": ["museum", "cultural"],
        "博物馆": ["museum", "cultural"],
        "park": ["park", "nature"],
        "公园": ["park", "nature"],
        "library": ["library", "reading"],
        "图书馆": ["library", "reading"],
        "hike": ["hiking", "nature"],
        "spa": ["spa", "luxury"],
        "beach": ["beach", "nature"],
        "read": ["reading", "quiet"],
        "看书": ["reading", "quiet"],
        "nature": ["nature", "quiet"],
        "自然": ["nature", "quiet"],
    }
    for keyword, tags in kw_map.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class SoloFriendlyFulfiller(L2Fulfiller):
    """L2 fulfiller for solo activity wishes — comfort-scored solo place types.

    15 solo-friendly places with comfort scores. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_solo_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in SOLO_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in SOLO_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in SOLO_CATALOG]

        # Boost by solo comfort score
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)
            # Blend solo comfort into personality score later
            c.setdefault("_solo_boost", c.get("solo_comfort", 0.8))

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Being alone is not lonely — it is freedom.",
                delay_hours=48,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    comfort = item.get("solo_comfort", 0.8)
    category = item.get("category", "").replace("_", " ")
    if comfort >= 0.95:
        return f"Perfectly natural to do alone — {category}"
    if comfort >= 0.8:
        return f"Very solo-friendly — {category}"
    return f"Solo-doable with confidence — {category}"
