"""VirtualCompanionFulfiller — AI companion mode recommendation.

15-entry curated catalog of companion modes for walks, study, bedtime, etc.
Personality matching: I->quiet companion, E->chatty companion.
Emotion matching: anxiety->calming_voice, loneliness->warm_presence.
Multilingual keyword routing (EN/ZH/AR). Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Virtual Companion Catalog (15 entries) ───────────────────────────────────

COMPANION_CATALOG: list[dict] = [
    {
        "title": "Study Buddy",
        "description": "A focused companion for study sessions — Pomodoro timers, gentle reminders, and encouragement.",
        "category": "virtual_companion",
        "companion_style": "focused",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "practical", "calming", "self-paced"],
        "emotion_match": ["anxiety", "fatigue"],
    },
    {
        "title": "Walk Companion",
        "description": "A friendly voice for your walks — shares fun facts, plays music, keeps you company.",
        "category": "virtual_companion",
        "companion_style": "chatty",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["social", "outdoor", "calming"],
        "emotion_match": ["loneliness"],
    },
    {
        "title": "Bedtime Storyteller",
        "description": "A soothing voice to read you bedtime stories and guide you gently to sleep.",
        "category": "virtual_companion",
        "companion_style": "soothing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "calming", "self-paced"],
        "emotion_match": ["anxiety", "sadness"],
    },
    {
        "title": "Morning Motivator",
        "description": "Start your day with energy — affirmations, goals review, and upbeat encouragement.",
        "category": "virtual_companion",
        "companion_style": "energetic",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "social", "modern"],
        "emotion_match": ["fatigue", "sadness"],
    },
    {
        "title": "Cooking Together",
        "description": "A companion who reads recipes aloud, sets timers, and cheers on your culinary creations.",
        "category": "virtual_companion",
        "companion_style": "chatty",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "creative", "social"],
        "emotion_match": ["loneliness"],
    },
    {
        "title": "Meditation Guide",
        "description": "A calm presence guiding you through breathing exercises and body scans.",
        "category": "virtual_companion",
        "companion_style": "soothing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "calming", "self-paced", "traditional"],
        "emotion_match": ["anxiety"],
    },
    {
        "title": "Workout Partner",
        "description": "Counts reps, tracks sets, and pushes you to finish strong — your virtual gym buddy.",
        "category": "virtual_companion",
        "companion_style": "energetic",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["physical", "practical", "social"],
        "emotion_match": ["fatigue"],
    },
    {
        "title": "Creative Partner",
        "description": "Brainstorms ideas, gives feedback, and celebrates your creative breakthroughs.",
        "category": "virtual_companion",
        "companion_style": "chatty",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "quiet", "modern"],
        "emotion_match": [],
    },
    {
        "title": "Brainstorm Buddy",
        "description": "Rapid-fire idea generation partner — no bad ideas, just creative flow.",
        "category": "virtual_companion",
        "companion_style": "chatty",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "social", "modern", "intellectual"],
        "emotion_match": [],
    },
    {
        "title": "Emotional Support Companion",
        "description": "A warm, patient listener when you need someone to just be there.",
        "category": "virtual_companion",
        "companion_style": "soothing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "quiet", "helping"],
        "emotion_match": ["sadness", "loneliness", "anxiety"],
    },
    {
        "title": "Accountability Partner",
        "description": "Keeps you honest about your goals — gentle but firm daily check-ins.",
        "category": "virtual_companion",
        "companion_style": "focused",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "quiet", "calming"],
        "emotion_match": [],
    },
    {
        "title": "Language Practice Buddy",
        "description": "Conversational partner for language learning — patient corrections, encouraging feedback.",
        "category": "virtual_companion",
        "companion_style": "chatty",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "social", "calming"],
        "emotion_match": [],
    },
    {
        "title": "Reading Buddy",
        "description": "Reads along with you, discusses chapters, and keeps you motivated to finish the book.",
        "category": "virtual_companion",
        "companion_style": "focused",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "intellectual", "calming", "self-paced"],
        "emotion_match": [],
    },
    {
        "title": "Journaling Guide",
        "description": "Daily prompts, reflective questions, and gentle encouragement to write.",
        "category": "virtual_companion",
        "companion_style": "soothing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "creative", "calming", "self-paced"],
        "emotion_match": ["anxiety", "sadness"],
    },
    {
        "title": "Mindful Eating Companion",
        "description": "Guides you through mindful eating — slow down, savor, and appreciate every bite.",
        "category": "virtual_companion",
        "companion_style": "soothing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "quiet", "traditional", "self-paced"],
        "emotion_match": ["anxiety"],
    },
]

# ── Keywords ──────────────────────────────────────────────────────────────────

_COMPANION_KEYWORDS: set[str] = {
    "陪伴", "companion", "陪我", "一起", "virtual", "虚拟", "مرافق",
    "buddy", "partner", "陪",
}


def _get_dominant_emotion(detector_results: DetectorResults) -> str | None:
    """Get user's dominant negative emotion from detector results."""
    emotions = detector_results.emotion.get("emotions", {})
    if not emotions:
        return None
    for emo in ["anxiety", "sadness", "loneliness", "fatigue"]:
        if emotions.get(emo, 0) > 0.4:
            return emo
    return None


def _match_companions(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select and score companion candidates based on emotion + personality."""
    candidates = [dict(item) for item in COMPANION_CATALOG]

    dominant = _get_dominant_emotion(detector_results)

    # Score by emotion matching
    for c in candidates:
        boost = 0.0
        if dominant and dominant in c.get("emotion_match", []):
            boost += 0.2
        c["_emotion_boost"] = boost

    # MBTI: introverts prefer quiet/soothing, extraverts prefer chatty/energetic
    mbti = detector_results.mbti
    if mbti.get("type"):
        ei = mbti.get("dimensions", {}).get("E_I", 0.5)
        is_introvert = ei < 0.4
        for c in candidates:
            style = c.get("companion_style", "")
            if is_introvert and style in ("soothing", "focused"):
                c["_emotion_boost"] = c.get("_emotion_boost", 0) + 0.1
            elif not is_introvert and style in ("chatty", "energetic"):
                c["_emotion_boost"] = c.get("_emotion_boost", 0) + 0.1

    # Add relevance reasons based on emotion
    emotion_reasons = {
        "anxiety": "A calming presence to ease your mind",
        "sadness": "Warm company to brighten your day",
        "loneliness": "You're not alone — a companion is here",
        "fatigue": "Gentle support to recharge your energy",
    }
    for c in candidates:
        if dominant and dominant in c.get("emotion_match", []):
            c["relevance_reason"] = emotion_reasons.get(dominant, "A companion matched to your mood")
        else:
            c["relevance_reason"] = "A virtual companion tailored to your personality"

    return candidates


class VirtualCompanionFulfiller(L2Fulfiller):
    """L2 fulfiller for virtual companion wishes — AI companionship modes.

    15-entry curated catalog with personality + emotion matching. Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
        """Filter, score with personality + emotion boost, convert to Recommendations."""
        from wish_engine.models import Recommendation

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
                relevance_reason=c.get("relevance_reason", "Matches your profile"),
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
        # 1. Match companions
        candidates = _match_companions(wish.wish_text, detector_results)

        # 2. Build recommendations with emotion boost
        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Spend time with your virtual companion today?",
                delay_hours=4,
            ),
        )
