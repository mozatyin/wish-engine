"""MindfulnessFulfiller — meditation/mindfulness calendar with duration options.

15 practices with 5min/10min/20min duration tiers. Emotion-aware selection.
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

# ── Mindfulness Catalog (15 entries) ─────────────────────────────────────────

MINDFULNESS_CATALOG: list[dict] = [
    {
        "title": "Morning Meditation",
        "description": "Start the day with 10 minutes of stillness — set your intention.",
        "category": "morning_meditation",
        "tags": ["meditation", "morning", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [5, 10, 20],
        "emotion_match": ["anxiety", "fatigue"],
    },
    {
        "title": "Body Scan",
        "description": "Slowly scan from head to toe — notice tension, release it.",
        "category": "body_scan",
        "tags": ["body", "calming", "quiet", "relaxation"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [10, 20],
        "emotion_match": ["anxiety"],
    },
    {
        "title": "Walking Meditation",
        "description": "Slow, mindful steps — feel each footfall, breathe with the rhythm.",
        "category": "walking_meditation",
        "tags": ["walking", "nature", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [10, 20],
        "emotion_match": ["anxiety", "sadness"],
    },
    {
        "title": "Loving Kindness",
        "description": "Send compassion to yourself and others — 'May you be happy, may you be well.'",
        "category": "loving_kindness",
        "tags": ["compassion", "calming", "quiet", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [5, 10, 20],
        "emotion_match": ["sadness", "loneliness"],
    },
    {
        "title": "Breath Counting",
        "description": "Count breaths 1 to 10, then restart — the simplest meditation there is.",
        "category": "breath_counting",
        "tags": ["breathing", "calming", "quiet", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [5, 10],
        "emotion_match": ["anxiety", "anger"],
    },
    {
        "title": "Progressive Relaxation",
        "description": "Tense and release each muscle group — total body relaxation.",
        "category": "progressive_relaxation",
        "tags": ["body", "calming", "quiet", "relaxation", "sleep"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [10, 20],
        "emotion_match": ["anxiety", "fatigue"],
    },
    {
        "title": "Gratitude Meditation",
        "description": "Close your eyes and think of 3 things you're grateful for — feel each one.",
        "category": "gratitude_meditation",
        "tags": ["gratitude", "calming", "quiet", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [5, 10],
        "emotion_match": ["sadness"],
    },
    {
        "title": "Sleep Meditation",
        "description": "Guided relaxation to drift into sleep — let go of the day.",
        "category": "sleep_meditation",
        "tags": ["sleep", "calming", "quiet", "relaxation"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [10, 20],
        "emotion_match": ["anxiety", "fatigue"],
    },
    {
        "title": "Mindful Eating",
        "description": "Eat one meal with full attention — taste, texture, gratitude.",
        "category": "mindful_eating",
        "tags": ["mindfulness", "calming", "quiet", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [10, 20],
        "emotion_match": [],
    },
    {
        "title": "Nature Contemplation",
        "description": "Sit outside and observe — clouds, trees, birds. Just notice.",
        "category": "nature_contemplation",
        "tags": ["nature", "calming", "quiet", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [5, 10, 20],
        "emotion_match": ["anxiety", "sadness"],
    },
    {
        "title": "Journaling Reflection",
        "description": "Write without editing — let your thoughts flow onto the page.",
        "category": "journaling_reflection",
        "tags": ["journaling", "calming", "quiet", "creative", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [10, 20],
        "emotion_match": ["sadness", "anger"],
    },
    {
        "title": "Sound Meditation",
        "description": "Close your eyes and listen — every sound is a bell of mindfulness.",
        "category": "sound_meditation",
        "tags": ["sound", "calming", "quiet", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [5, 10],
        "emotion_match": ["anxiety"],
    },
    {
        "title": "Candle Gazing",
        "description": "Focus on a candle flame — ancient practice for deep concentration.",
        "category": "candle_gazing",
        "tags": ["focus", "calming", "quiet", "traditional"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [5, 10],
        "emotion_match": ["anxiety"],
    },
    {
        "title": "Mantra Practice",
        "description": "Repeat a word or phrase — 'Om', 'peace', or your own anchor word.",
        "category": "mantra_practice",
        "tags": ["mantra", "calming", "quiet", "traditional"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [5, 10, 20],
        "emotion_match": ["anxiety", "anger"],
    },
    {
        "title": "Visualization",
        "description": "Picture your safe place — a beach, mountain, or cozy room. Go there in your mind.",
        "category": "visualization",
        "tags": ["visualization", "calming", "quiet", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "durations": [5, 10, 20],
        "emotion_match": ["anxiety", "sadness"],
    },
]


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
    """Select candidates based on emotion matching."""
    dominant = _get_dominant_emotion(detector_results)
    text_lower = wish_text.lower()

    # Detect duration preference
    preferred_duration = None
    if any(kw in text_lower for kw in ["5分钟", "5min", "quick", "快", "短"]):
        preferred_duration = 5
    elif any(kw in text_lower for kw in ["20分钟", "20min", "long", "深度", "长"]):
        preferred_duration = 20

    # Detect sleep keywords
    sleep_mode = any(kw in text_lower for kw in ["sleep", "失眠", "睡", "نوم"])

    candidates: list[dict] = []
    for item in MINDFULNESS_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Emotion matching
        if dominant and dominant in item.get("emotion_match", []):
            score_boost += 0.2
            item_copy["relevance_reason"] = f"Recommended for {dominant} relief"

        # Duration matching
        if preferred_duration and preferred_duration in item.get("durations", []):
            score_boost += 0.1

        # Sleep mode
        if sleep_mode and "sleep" in item.get("tags", []):
            score_boost += 0.25
            item_copy["relevance_reason"] = "Designed to help you sleep better"

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


class MindfulnessFulfiller(L2Fulfiller):
    """L2 fulfiller for mindfulness/meditation wishes — emotion-aware practice selection.

    15-entry curated catalog with duration options. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "A mindfulness practice to center you"

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
                text="Time for your mindfulness practice",
                delay_hours=24,
            ),
        )
