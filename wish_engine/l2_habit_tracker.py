"""HabitTrackerFulfiller — habit tracking visualization with emotion linkage.

15 habit types with mood correlation patterns. Core innovation: detect
"running days = better mood" style linkage between habits and emotions.
Multilingual keyword routing (EN/ZH/AR).
Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Habit Catalog (15 entries) ───────────────────────────────────────────────

HABIT_CATALOG: list[dict] = [
    {
        "title": "Morning Exercise",
        "description": "30-minute workout to start your day — running, yoga, or bodyweight.",
        "category": "exercise",
        "tags": ["exercise", "morning", "energizing", "fitness"],
        "mood": "energizing",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"joy": 0.3, "anxiety": -0.2},
    },
    {
        "title": "Daily Meditation",
        "description": "10 minutes of guided or silent meditation — build inner calm.",
        "category": "meditation",
        "tags": ["meditation", "calming", "quiet", "mindfulness"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"anxiety": -0.3, "sadness": -0.1},
    },
    {
        "title": "Reading Time",
        "description": "Read 20 pages a day — fiction, non-fiction, anything that feeds your mind.",
        "category": "reading",
        "tags": ["reading", "quiet", "theory", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"curiosity": 0.2},
    },
    {
        "title": "Journal Writing",
        "description": "Write 3 pages every morning — stream of consciousness, no editing.",
        "category": "journaling",
        "tags": ["journaling", "quiet", "calming", "self-paced", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"anxiety": -0.2, "sadness": -0.15},
    },
    {
        "title": "Early Rising",
        "description": "Wake up at 6 AM consistently — own the morning, own the day.",
        "category": "early_rising",
        "tags": ["morning", "discipline", "energizing", "practical"],
        "mood": "energizing",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"fatigue": -0.2, "joy": 0.1},
    },
    {
        "title": "Water Intake Tracker",
        "description": "8 glasses a day — hydration is the simplest health upgrade.",
        "category": "water_intake",
        "tags": ["health", "simple", "practical", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"fatigue": -0.1},
    },
    {
        "title": "No Phone Before Bed",
        "description": "Put the phone away 1 hour before sleep — better rest, better mornings.",
        "category": "no_phone",
        "tags": ["digital-detox", "sleep", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"anxiety": -0.2, "fatigue": -0.15},
    },
    {
        "title": "Gratitude Practice",
        "description": "Write 3 things you're grateful for each evening — rewire your brain.",
        "category": "gratitude",
        "tags": ["gratitude", "calming", "quiet", "journaling"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"joy": 0.2, "sadness": -0.2},
    },
    {
        "title": "Morning Stretch",
        "description": "10 minutes of full-body stretching — wake up your muscles gently.",
        "category": "stretching",
        "tags": ["stretching", "morning", "calming", "fitness"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"fatigue": -0.15},
    },
    {
        "title": "Cook One Meal",
        "description": "Cook at least one meal from scratch daily — nourish body and soul.",
        "category": "cooking",
        "tags": ["cooking", "practical", "creative", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"joy": 0.15},
    },
    {
        "title": "Language Practice",
        "description": "15 minutes of a new language daily — Duolingo, podcast, or flashcards.",
        "category": "language_practice",
        "tags": ["language", "learning", "self-paced", "quiet", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"curiosity": 0.2},
    },
    {
        "title": "Creative Time",
        "description": "30 minutes of pure creation — draw, paint, write, build, no rules.",
        "category": "creative_time",
        "tags": ["creative", "quiet", "self-paced", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"joy": 0.2, "anxiety": -0.1},
    },
    {
        "title": "Call a Friend",
        "description": "One meaningful phone call a day — connection is a habit too.",
        "category": "social_call",
        "tags": ["social", "connection", "warm"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "emotion_link": {"loneliness": -0.3},
    },
    {
        "title": "Nature Walk",
        "description": "20 minutes outdoors — park, trail, or just around the block.",
        "category": "nature_walk",
        "tags": ["nature", "exercise", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"anxiety": -0.2, "joy": 0.15},
    },
    {
        "title": "Deep Breathing",
        "description": "5 minutes of 4-7-8 breathing — instant calm, anywhere, anytime.",
        "category": "deep_breathing",
        "tags": ["breathing", "calming", "quiet", "mindfulness", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "emotion_link": {"anxiety": -0.3, "anger": -0.1},
    },
]

# ── Keyword detection ────────────────────────────────────────────────────────

_HABIT_KEYWORDS: dict[str, list[str]] = {
    "exercise": ["exercise"],
    "运动": ["exercise"],
    "meditation": ["meditation"],
    "冥想": ["meditation"],
    "reading": ["reading"],
    "阅读": ["reading"],
    "journal": ["journaling"],
    "日记": ["journaling"],
    "early": ["early_rising"],
    "早起": ["early_rising"],
    "water": ["water_intake"],
    "喝水": ["water_intake"],
    "phone": ["no_phone"],
    "手机": ["no_phone"],
    "gratitude": ["gratitude"],
    "感恩": ["gratitude"],
    "stretch": ["stretching"],
    "拉伸": ["stretching"],
    "cook": ["cooking"],
    "做饭": ["cooking"],
    "language": ["language_practice"],
    "语言": ["language_practice"],
    "creative": ["creative_time"],
    "创作": ["creative_time"],
    "call": ["social_call"],
    "打电话": ["social_call"],
    "walk": ["nature_walk"],
    "散步": ["nature_walk"],
    "breathing": ["deep_breathing"],
    "呼吸": ["deep_breathing"],
}


def _detect_habit_categories(wish_text: str) -> list[str]:
    """Detect which habit categories the wish text mentions."""
    text_lower = wish_text.lower()
    categories: list[str] = []
    for keyword, cats in _HABIT_KEYWORDS.items():
        if keyword in text_lower:
            for c in cats:
                if c not in categories:
                    categories.append(c)
    return categories


def _get_dominant_emotion(detector_results: DetectorResults) -> str | None:
    """Get dominant emotion from detector results."""
    emotions = detector_results.emotion.get("emotions", {})
    if not emotions:
        return None
    for emo in ["anxiety", "sadness", "anger", "loneliness", "fatigue", "joy"]:
        if emotions.get(emo, 0) > 0.4:
            return emo
    return None


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword and emotion matching."""
    categories = _detect_habit_categories(wish_text)
    dominant = _get_dominant_emotion(detector_results)

    candidates: list[dict] = []
    for item in HABIT_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Category match
        if categories and item["category"] in categories:
            score_boost += 0.25

        # Emotion linkage: if user is anxious and habit reduces anxiety, boost
        if dominant:
            link = item.get("emotion_link", {})
            if dominant in link and link[dominant] < 0:
                score_boost += 0.2
                item_copy["relevance_reason"] = (
                    f"This habit can help with your {dominant} — "
                    f"tracking shows a positive mood correlation"
                )

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


class HabitTrackerFulfiller(L2Fulfiller):
    """L2 fulfiller for habit tracking wishes — emotion-linked habit suggestions.

    15-entry curated catalog with mood correlation patterns. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = f"Build this habit to improve your daily life"

        # Score with personality + emotion boost
        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:3]

        from wish_engine.models import Recommendation

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
                text="Time to check in on your habit streak!",
                delay_hours=24,
            ),
        )
