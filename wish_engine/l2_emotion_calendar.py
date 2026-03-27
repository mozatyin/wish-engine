"""EmotionCalendarFulfiller — monthly emotion themes with daily logging prompts.

12 monthly themes with curated prompts. Personality-filtered. Zero LLM.
"""

from __future__ import annotations

import datetime

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    Recommendation,
    ReminderOption,
)

# ── Emotion Calendar Catalog (12 entries) ────────────────────────────────────

CALENDAR_CATALOG: list[dict] = [
    {
        "title": "January: Fresh Start Reset",
        "description": "Log one emotion each morning this month — track how your new year energy shifts.",
        "category": "january_fresh_start",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 1,
    },
    {
        "title": "February: Love & Connection",
        "description": "Track feelings about the people you love — gratitude, longing, warmth, all valid.",
        "category": "february_love",
        "tags": ["warm", "social", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 2,
    },
    {
        "title": "March: Renewal & Growth",
        "description": "Notice what's blooming inside you — log moments of hope and new energy.",
        "category": "march_renewal",
        "tags": ["quiet", "self-paced", "calming", "energizing"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 3,
    },
    {
        "title": "April: Seeds of Growth",
        "description": "Track small wins daily — each one is a seed planted for your future self.",
        "category": "april_growth",
        "tags": ["quiet", "self-paced", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 4,
    },
    {
        "title": "May: Gratitude Bloom",
        "description": "Write 3 things you're grateful for each night — watch your perspective shift.",
        "category": "may_gratitude",
        "tags": ["quiet", "self-paced", "calming", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 5,
    },
    {
        "title": "June: Adventure & Curiosity",
        "description": "Log one new thing you tried each week — curiosity is an emotion too.",
        "category": "june_adventure",
        "tags": ["energizing", "self-paced", "practical"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "moderate",
        "month": 6,
    },
    {
        "title": "July: Mid-Year Reflection",
        "description": "Pause and review — which emotions visited most? Which do you want more of?",
        "category": "july_reflection",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 7,
    },
    {
        "title": "August: Energy & Vitality",
        "description": "Track your energy peaks and valleys — when do you feel most alive?",
        "category": "august_energy",
        "tags": ["energizing", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 8,
    },
    {
        "title": "September: Learning & Discovery",
        "description": "Log one thing you learned each day — knowledge lights up different emotions.",
        "category": "september_learning",
        "tags": ["quiet", "self-paced", "calming", "practical", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 9,
    },
    {
        "title": "October: Harvest & Celebration",
        "description": "Celebrate what you've built this year — log pride, satisfaction, even relief.",
        "category": "october_harvest",
        "tags": ["quiet", "self-paced", "calming", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 10,
    },
    {
        "title": "November: Deep Gratitude",
        "description": "Go deeper — who shaped you this year? Write one name and one feeling daily.",
        "category": "november_gratitude",
        "tags": ["quiet", "self-paced", "calming", "warm", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 11,
    },
    {
        "title": "December: Year in Review",
        "description": "Review your emotion journey — what patterns emerged? What do you carry forward?",
        "category": "december_review",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "month": 12,
    },
]


def _get_current_month() -> int:
    """Get current month (1-12)."""
    return datetime.date.today().month


def _match_candidates(detector_results: DetectorResults) -> list[dict]:
    """Score candidates — current month gets highest boost."""
    current_month = _get_current_month()
    candidates: list[dict] = []

    for item in CALENDAR_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Current month gets big boost
        if item["month"] == current_month:
            score_boost += 0.35
        # Adjacent months get small boost
        elif abs(item["month"] - current_month) <= 1 or abs(item["month"] - current_month) >= 11:
            score_boost += 0.10

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_reason(item, current_month)
        candidates.append(item_copy)

    return candidates


def _build_reason(item: dict, current_month: int) -> str:
    """Build relevance reason."""
    if item["month"] == current_month:
        return f"Perfect timing — this month's theme matches right now"
    return f"A theme to explore: {item['category'].replace('_', ' ')}"


class EmotionCalendarFulfiller(L2Fulfiller):
    """L2 fulfiller for emotion calendar wishes — monthly themes with daily prompts.

    12-entry curated catalog. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(detector_results)

        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:3]

        recommendations = [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "Matches your profile"),
                score=c.get("_personality_score", 0.5),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Have you logged today's emotion?",
                delay_hours=12,
            ),
        )
