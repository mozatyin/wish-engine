"""NightOwlFulfiller — local-compute night owl activity recommendation.

12-entry curated catalog of late-night lifestyle activities. Zero LLM.
Only active 10pm-6am. Keyword matching (English/Chinese/Arabic) routes wish
text to relevant categories, then PersonalityFilter scores and ranks candidates.

Tags: nightlife/creative/fitness/food/nature.
"""

from __future__ import annotations

from datetime import datetime

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
)

# ── Night Owl Catalog (12 entries) ────────────────────────────────────────────

NIGHT_OWL_CATALOG: list[dict] = [
    {
        "title": "Late Night Cafe",
        "description": "Cozy cafes open past midnight — perfect for night owls who love coffee and quiet.",
        "category": "late_night_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nightlife", "quiet", "calming", "cafe", "self-paced"],
    },
    {
        "title": "24-Hour Gym",
        "description": "Burn energy at any hour — late-night workouts with fewer crowds.",
        "category": "24h_gym",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["fitness", "nightlife", "calming", "self-paced", "practical"],
    },
    {
        "title": "Night Market",
        "description": "Street food, local crafts, and night energy — open-air markets after dark.",
        "category": "night_market",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["nightlife", "food", "social", "energetic", "outdoor"],
    },
    {
        "title": "Midnight Cinema",
        "description": "Late screenings of cult classics and new releases — popcorn at midnight.",
        "category": "midnight_cinema",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nightlife", "quiet", "calming", "entertainment", "indoor"],
    },
    {
        "title": "Stargazing Spot",
        "description": "Dark-sky locations away from city lights — galaxies visible to the naked eye.",
        "category": "stargazing_spot",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nature", "quiet", "calming", "outdoor", "self-paced"],
    },
    {
        "title": "Night Photography Walk",
        "description": "Capture cityscapes and light trails — guided or solo night photography.",
        "category": "night_photography",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "quiet", "calming", "outdoor", "self-paced"],
    },
    {
        "title": "Late Night Bookshop",
        "description": "Bookshops that stay open late — browse shelves in midnight quiet.",
        "category": "late_night_bookshop",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nightlife", "quiet", "calming", "self-paced", "indoor"],
    },
    {
        "title": "Overnight Onsen / Spa",
        "description": "Hot springs and spas open through the night — soak away the hours.",
        "category": "overnight_onsen",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nightlife", "quiet", "calming", "self-paced", "indoor"],
    },
    {
        "title": "Night Fishing",
        "description": "Peaceful lakeside or pier fishing under the stars.",
        "category": "night_fishing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nature", "quiet", "calming", "outdoor", "self-paced"],
    },
    {
        "title": "Late Night Ramen",
        "description": "Steaming bowls of ramen when the city sleeps — night owl comfort food.",
        "category": "late_night_ramen",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["food", "nightlife", "calming", "social", "practical"],
    },
    {
        "title": "Rooftop Bar",
        "description": "City views and cocktails high above the streets — nightlife elevated.",
        "category": "rooftop_bar",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["nightlife", "social", "calming", "scenic", "outdoor"],
    },
    {
        "title": "Night Run",
        "description": "Cool air, empty streets, city lights — running hits different at night.",
        "category": "night_run",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["fitness", "quiet", "calming", "outdoor", "self-paced"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

NIGHT_OWL_KEYWORDS: set[str] = {
    "夜猫子", "night owl", "late night", "深夜", "ليلي",
    "insomnia", "睡不着", "midnight", "半夜", "凌晨",
    "夜", "night", "can't sleep", "awake",
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "late_night_cafe": ["cafe", "coffee", "咖啡", "قهوة"],
    "24h_gym": ["gym", "workout", "健身", "رياضة"],
    "night_market": ["market", "夜市", "سوق", "street food"],
    "midnight_cinema": ["cinema", "movie", "电影", "سينما"],
    "stargazing_spot": ["star", "星星", "نجوم", "galaxy", "天文"],
    "night_photography": ["photo", "拍照", "تصوير", "camera"],
    "late_night_bookshop": ["book", "书", "كتاب", "read"],
    "overnight_onsen": ["onsen", "spa", "温泉", "سبا", "bath"],
    "night_fishing": ["fish", "钓鱼", "صيد"],
    "late_night_ramen": ["ramen", "noodle", "面", "拉面"],
    "rooftop_bar": ["rooftop", "bar", "天台", "cocktail"],
    "night_run": ["run", "jog", "跑步", "ركض"],
}


def is_night_owl_hour(hour: int | None = None) -> bool:
    """Check if current time is night owl active time (10pm-6am)."""
    if hour is None:
        hour = datetime.now().hour
    return hour >= 22 or hour < 6


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
    current_hour: int | None = None,
) -> list[dict]:
    """Select catalog candidates based on keyword and time matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    is_active = is_night_owl_hour(current_hour)

    for item in NIGHT_OWL_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Time-aware boosting
        if is_active:
            score_boost += 0.1

        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        # Insomnia/can't sleep boost for calming activities
        if any(kw in text_lower for kw in ["insomnia", "睡不着", "can't sleep"]):
            if "calming" in item.get("tags", []):
                score_boost += 0.1

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item, is_active)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict, is_active: bool) -> str:
    """Build a relevance reason for night owl recommendations."""
    time_prefix = "Perfect right now — " if is_active else ""
    reasons = {
        "late_night_cafe": f"{time_prefix}A quiet cafe for night owl energy",
        "24h_gym": f"{time_prefix}Work out when the gym is all yours",
        "night_market": f"{time_prefix}Night market buzz and street food",
        "midnight_cinema": f"{time_prefix}Late-night movie magic",
        "stargazing_spot": f"{time_prefix}The stars are out for you",
        "night_photography": f"{time_prefix}City lights make the best subjects",
        "late_night_bookshop": f"{time_prefix}Midnight browsing in quiet aisles",
        "overnight_onsen": f"{time_prefix}Soak away the night in warm water",
        "night_fishing": f"{time_prefix}Peaceful fishing under the stars",
        "late_night_ramen": f"{time_prefix}Hot ramen when the world sleeps",
        "rooftop_bar": f"{time_prefix}City views from above",
        "night_run": f"{time_prefix}Empty streets, cool air, your pace",
    }
    return reasons.get(item["category"], "A night owl activity nearby")


class NightOwlFulfiller(L2Fulfiller):
    """L2 fulfiller for night owl lifestyle wishes.

    12-entry curated catalog. Only active 10pm-6am.
    Tags: nightlife/creative/fitness/food/nature. Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:max_results]

        return [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "A night owl activity nearby"),
                score=c.get("_personality_score", 0.5),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)
        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="night_owl", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Night owl picks refresh at 10pm!",
                delay_hours=12,
            ),
        )
