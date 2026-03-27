"""HealthSyncFulfiller — health signal cross-referencing with recommendations.

15 health signals with cross-reference logic: bad_sleep + anxiety -> sleep hygiene.
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

# ── Health Signal Catalog (15 entries) ───────────────────────────────────────

HEALTH_CATALOG: list[dict] = [
    {
        "title": "Sleep Quality Improvement",
        "description": "Track and improve your sleep — consistent schedule, dark room, no screens.",
        "category": "sleep_quality",
        "tags": ["sleep", "calming", "quiet", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "sleep",
        "cross_ref": {"anxiety": "Try sleep hygiene + calm evening routine"},
    },
    {
        "title": "Daily Step Counter",
        "description": "Aim for 8,000-10,000 steps — walking is the most underrated exercise.",
        "category": "step_count",
        "tags": ["exercise", "practical", "simple", "nature"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "steps",
        "cross_ref": {"sadness": "Walking outdoors boosts both steps and mood"},
    },
    {
        "title": "Heart Rate Awareness",
        "description": "Know your resting heart rate — lower is generally healthier.",
        "category": "heart_rate",
        "tags": ["health", "practical", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "heart_rate",
        "cross_ref": {"anxiety": "High resting HR + anxiety? Try deep breathing exercises"},
    },
    {
        "title": "Stress Level Monitor",
        "description": "Track stress patterns — know your triggers, plan your recovery.",
        "category": "stress_level",
        "tags": ["calming", "practical", "quiet", "mindfulness"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "stress",
        "cross_ref": {"anxiety": "Stress + anxiety pattern detected — prioritize rest today"},
    },
    {
        "title": "Exercise Minutes Tracker",
        "description": "150 minutes per week is the WHO recommendation — are you there?",
        "category": "exercise_minutes",
        "tags": ["exercise", "practical", "fitness", "energizing"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "low",
        "health_signal": "exercise",
        "cross_ref": {"fatigue": "Low exercise + fatigue? Start with 10-minute walks"},
    },
    {
        "title": "Hydration Tracker",
        "description": "8 glasses a day — dehydration causes headaches, fatigue, and poor focus.",
        "category": "hydration",
        "tags": ["health", "simple", "practical", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "hydration",
        "cross_ref": {"fatigue": "Dehydration + fatigue — drink water first, coffee second"},
    },
    {
        "title": "Screen Time Awareness",
        "description": "Track your screen time — digital wellness matters for eyes and mind.",
        "category": "screen_time",
        "tags": ["digital-detox", "practical", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "screen_time",
        "cross_ref": {"anxiety": "High screen time + anxiety? Set app limits and take breaks"},
    },
    {
        "title": "Standing Hours Goal",
        "description": "Stand for at least 1 minute every hour — your spine will thank you.",
        "category": "standing_hours",
        "tags": ["health", "simple", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "standing",
        "cross_ref": {},
    },
    {
        "title": "Calorie Awareness",
        "description": "Not about restriction — about knowing what fuels you best.",
        "category": "calories",
        "tags": ["health", "practical", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "calories",
        "cross_ref": {},
    },
    {
        "title": "Weight Trend Tracker",
        "description": "Weekly trends, not daily fluctuations — focus on the direction.",
        "category": "weight_trend",
        "tags": ["health", "practical", "quiet", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "weight",
        "cross_ref": {},
    },
    {
        "title": "Blood Pressure Log",
        "description": "Track morning and evening readings — consistency reveals patterns.",
        "category": "blood_pressure",
        "tags": ["health", "practical", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "blood_pressure",
        "cross_ref": {"anxiety": "Elevated BP + anxiety — talk to your doctor about stress management"},
    },
    {
        "title": "Menstrual Cycle Tracker",
        "description": "Understand your cycle — energy, mood, and health patterns throughout the month.",
        "category": "menstrual_cycle",
        "tags": ["health", "practical", "quiet", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "cycle",
        "cross_ref": {"sadness": "Mood changes may correlate with your cycle — be gentle with yourself"},
    },
    {
        "title": "Medication Reminder",
        "description": "Never miss a dose — set reminders for consistent medication adherence.",
        "category": "medication_reminder",
        "tags": ["health", "practical", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "medication",
        "cross_ref": {},
    },
    {
        "title": "Allergy Season Alert",
        "description": "Track pollen counts and allergy triggers — prepare before symptoms hit.",
        "category": "allergy_season",
        "tags": ["health", "practical", "nature"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "allergy",
        "cross_ref": {},
    },
    {
        "title": "Vitamin D & Sunlight",
        "description": "15 minutes of sunlight daily — essential for mood, bones, and immunity.",
        "category": "vitamin_d",
        "tags": ["health", "nature", "simple", "calming", "energizing"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "health_signal": "vitamin_d",
        "cross_ref": {"sadness": "Low sunlight + sadness — vitamin D and outdoor time help"},
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


def _detect_health_signals(wish_text: str) -> list[str]:
    """Detect health signal keywords from text."""
    text_lower = wish_text.lower()
    signal_map = {
        "sleep": ["sleep", "失眠", "睡", "نوم"],
        "steps": ["步数", "steps", "walking", "走路", "خطوات"],
        "heart_rate": ["心率", "heart", "heartrate", "نبض"],
        "stress": ["stress", "压力", "توتر"],
        "exercise": ["exercise", "运动", "تمارين"],
        "hydration": ["water", "喝水", "ماء"],
        "screen_time": ["screen", "屏幕", "شاشة"],
    }
    signals = []
    for signal, keywords in signal_map.items():
        if any(kw in text_lower for kw in keywords):
            signals.append(signal)
    return signals


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates with cross-reference logic."""
    dominant = _get_dominant_emotion(detector_results)
    signals = _detect_health_signals(wish_text)

    candidates: list[dict] = []
    for item in HEALTH_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Signal keyword match
        if signals and item["health_signal"] in signals:
            score_boost += 0.25

        # Cross-reference: emotion + health signal
        if dominant and dominant in item.get("cross_ref", {}):
            score_boost += 0.2
            item_copy["relevance_reason"] = item["cross_ref"][dominant]

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


class HealthSyncFulfiller(L2Fulfiller):
    """L2 fulfiller for health sync wishes — cross-referencing health signals with emotions.

    15-entry curated catalog with cross-reference logic. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "Track this health signal for better self-awareness"

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
                text="Time to check your health stats!",
                delay_hours=24,
            ),
        )
