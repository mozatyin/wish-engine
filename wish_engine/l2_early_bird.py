"""EarlyBirdFulfiller — local-compute early morning activity recommendation.

12-entry curated catalog of early morning activities. Zero LLM.
Only active 5am-9am. Keyword matching (English/Chinese/Arabic) routes wish
text to relevant categories, then PersonalityFilter scores and ranks candidates.

Tags: sunrise/exercise/meditation/food/nature.
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

# ── Early Bird Catalog (12 entries) ───────────────────────────────────────────

EARLY_BIRD_CATALOG: list[dict] = [
    {
        "title": "Sunrise Viewing Spot",
        "description": "The best hilltops and waterfronts to watch the sun rise.",
        "category": "sunrise_spot",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sunrise", "outdoor", "quiet", "calming", "nature"],
    },
    {
        "title": "Morning Yoga Class",
        "description": "Start the day with a gentle or power yoga session at dawn.",
        "category": "morning_yoga",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["exercise", "quiet", "calming", "structured", "indoor"],
    },
    {
        "title": "Dawn Run",
        "description": "Empty paths and crisp morning air — the best time to run.",
        "category": "dawn_run",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["exercise", "outdoor", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Early Bird Cafe",
        "description": "Cafes that open before 7am — fresh pastries and the first brew.",
        "category": "early_bird_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["food", "quiet", "calming", "cafe", "self-paced"],
    },
    {
        "title": "Farmers Market (Morning)",
        "description": "Fresh produce straight from the farm — best selection arrives early.",
        "category": "farmers_market_morning",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["food", "outdoor", "calming", "social", "practical"],
    },
    {
        "title": "Morning Meditation",
        "description": "Guided or silent meditation sessions in the peaceful early hours.",
        "category": "morning_meditation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meditation", "quiet", "calming", "self-paced", "indoor"],
    },
    {
        "title": "Sunrise Photography",
        "description": "Golden hour photography — capture dawn's magical light.",
        "category": "sunrise_photography",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "outdoor", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Early Morning Swim",
        "description": "Lap swimming in near-empty pools — peaceful and energizing.",
        "category": "early_swim",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["exercise", "quiet", "calming", "self-paced", "indoor"],
    },
    {
        "title": "Morning Tai Chi",
        "description": "Join the dawn tai chi group in the park — moving meditation.",
        "category": "morning_tai_chi",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["exercise", "outdoor", "quiet", "calming", "traditional"],
    },
    {
        "title": "Breakfast Special",
        "description": "Early bird breakfast deals — rewarding those who rise first.",
        "category": "breakfast_special",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["food", "calming", "social", "practical", "indoor"],
    },
    {
        "title": "Morning Prayer Spot",
        "description": "Peaceful places for fajr and early morning spiritual practice.",
        "category": "morning_prayer",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meditation", "quiet", "calming", "traditional", "indoor"],
    },
    {
        "title": "Bird Watching at Dawn",
        "description": "Dawn is peak bird activity — binoculars, field guide, and patience.",
        "category": "bird_watching_dawn",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nature", "outdoor", "quiet", "calming", "self-paced"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

EARLY_BIRD_KEYWORDS: set[str] = {
    "早起", "early bird", "sunrise", "日出", "صباحي",
    "morning", "晨", "dawn", "清晨", "فجر",
    "早晨", "早", "wake up early",
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "sunrise_spot": ["sunrise", "日出", "شروق"],
    "morning_yoga": ["yoga", "瑜伽", "يوغا"],
    "dawn_run": ["run", "jog", "跑步", "ركض"],
    "early_bird_cafe": ["cafe", "coffee", "咖啡", "قهوة"],
    "farmers_market_morning": ["market", "farmer", "集市", "سوق"],
    "morning_meditation": ["meditation", "meditate", "冥想", "تأمل"],
    "sunrise_photography": ["photo", "拍照", "تصوير", "camera"],
    "early_swim": ["swim", "游泳", "سباحة", "pool"],
    "morning_tai_chi": ["tai chi", "太极", "تاي تشي"],
    "breakfast_special": ["breakfast", "早餐", "فطور"],
    "morning_prayer": ["prayer", "祈祷", "صلاة", "fajr"],
    "bird_watching_dawn": ["bird", "鸟", "طيور", "birding"],
}


def is_early_bird_hour(hour: int | None = None) -> bool:
    """Check if current time is early bird active time (5am-9am)."""
    if hour is None:
        hour = datetime.now().hour
    return 5 <= hour < 9


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
    current_hour: int | None = None,
) -> list[dict]:
    """Select catalog candidates based on keyword and time matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    is_active = is_early_bird_hour(current_hour)

    for item in EARLY_BIRD_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Time-aware boosting
        if is_active:
            score_boost += 0.1

        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        # Exercise preference boost
        if any(kw in text_lower for kw in ["exercise", "运动", "workout", "رياضة"]):
            if "exercise" in item.get("tags", []):
                score_boost += 0.1

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item, is_active)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict, is_active: bool) -> str:
    """Build a relevance reason for early bird recommendations."""
    time_prefix = "Perfect right now — " if is_active else ""
    reasons = {
        "sunrise_spot": f"{time_prefix}Catch the sunrise at this beautiful spot",
        "morning_yoga": f"{time_prefix}Start your day with mindful movement",
        "dawn_run": f"{time_prefix}Fresh air and empty paths await",
        "early_bird_cafe": f"{time_prefix}First coffee of the day, freshly brewed",
        "farmers_market_morning": f"{time_prefix}Best picks arrive with the early birds",
        "morning_meditation": f"{time_prefix}Morning stillness for a calm mind",
        "sunrise_photography": f"{time_prefix}Golden hour light is waiting",
        "early_swim": f"{time_prefix}Near-empty pool for peaceful laps",
        "morning_tai_chi": f"{time_prefix}Dawn movement in the park",
        "breakfast_special": f"{time_prefix}Early bird gets the breakfast deal",
        "morning_prayer": f"{time_prefix}A peaceful place for morning reflection",
        "bird_watching_dawn": f"{time_prefix}Peak birding hour — listen closely",
    }
    return reasons.get(item["category"], "An early bird activity nearby")


class EarlyBirdFulfiller(L2Fulfiller):
    """L2 fulfiller for early morning lifestyle wishes.

    12-entry curated catalog. Only active 5am-9am.
    Tags: sunrise/exercise/meditation/food/nature. Zero LLM.
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
                relevance_reason=c.get("relevance_reason", "An early bird activity nearby"),
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
            map_data=MapData(place_type="early_bird", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Set alarm for sunrise tomorrow?",
                delay_hours=18,
            ),
        )
