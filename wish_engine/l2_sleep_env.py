"""SleepEnvFulfiller — emotion-linked sleep environment optimization.

15-entry curated sleep aid catalog. Emotion-linked: anxiety→meditation+breathing,
agitation→exercise+cool_room. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Emotion → Sleep Aid Mapping ──────────────────────────────────────────────

EMOTION_SLEEP_MAP: dict[str, list[str]] = {
    "anxiety": ["meditation", "breathing", "routine", "calming_scent", "guided"],
    "sadness": ["comfort", "warmth", "guided", "gentle", "routine"],
    "anger": ["exercise", "cool", "breathing", "routine"],
    "stress": ["meditation", "breathing", "comfort", "calming_scent"],
    "restlessness": ["exercise", "cool", "routine", "screen_free"],
}

# ── Sleep Aid Catalog (15 entries) ───────────────────────────────────────────

SLEEP_CATALOG: list[dict] = [
    {
        "title": "White Noise / Nature Sounds App",
        "description": "Rain, ocean waves, or fan sounds to mask distracting noise.",
        "category": "white_noise_app",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["comfort", "calming", "guided", "self-paced", "screen_free"],
    },
    {
        "title": "Blackout Curtains",
        "description": "Block all light for deeper sleep — especially for city dwellers.",
        "category": "blackout_curtains",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["comfort", "practical", "routine"],
    },
    {
        "title": "Weighted Blanket",
        "description": "Deep pressure stimulation reduces anxiety and promotes calm sleep.",
        "category": "weighted_blanket",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["comfort", "warmth", "calming", "gentle"],
    },
    {
        "title": "Sleep Meditation App",
        "description": "Guided body scan or sleep story to ease you into rest.",
        "category": "sleep_meditation_app",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meditation", "guided", "calming", "breathing", "self-paced"],
    },
    {
        "title": "Herbal Tea Ritual",
        "description": "Chamomile, valerian, or lavender tea 30 minutes before bed.",
        "category": "herbal_tea",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming_scent", "routine", "gentle", "comfort", "calming"],
    },
    {
        "title": "Blue Light Blocking Glasses",
        "description": "Wear after sunset to protect your melatonin production.",
        "category": "blue_light_glasses",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["screen_free", "practical", "routine"],
    },
    {
        "title": "Cool Room Strategy (16-19C)",
        "description": "Lower thermostat, use a fan, or crack a window. Cool body = faster sleep.",
        "category": "cool_room_tips",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cool", "practical", "routine"],
    },
    {
        "title": "Consistent Sleep Schedule",
        "description": "Same time to bed, same time to wake — even weekends. Your circadian rhythm will thank you.",
        "category": "sleep_schedule",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["routine", "practical", "structured"],
    },
    {
        "title": "Aromatherapy — Lavender",
        "description": "Lavender pillow spray or diffuser to signal your brain: time to rest.",
        "category": "aromatherapy_lavender",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming_scent", "comfort", "gentle", "calming"],
    },
    {
        "title": "Reading Before Bed",
        "description": "Paper book only — 15-30 minutes of fiction to transport your mind.",
        "category": "reading_before_bed",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["screen_free", "gentle", "routine", "calming", "self-paced"],
    },
    {
        "title": "No Screen Routine (1 hour)",
        "description": "All screens off 60 minutes before bed. Read, stretch, or just sit.",
        "category": "no_screen_routine",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["screen_free", "routine", "practical", "structured"],
    },
    {
        "title": "Exercise Timing Optimization",
        "description": "Vigorous exercise 4-6 hours before bed, never within 2 hours.",
        "category": "exercise_timing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["exercise", "routine", "practical", "structured"],
    },
    {
        "title": "Caffeine Cutoff (2pm Rule)",
        "description": "No caffeine after 2pm. Half-life is 5 hours — that 4pm coffee hits at 9pm.",
        "category": "caffeine_cutoff",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["routine", "practical", "structured"],
    },
    {
        "title": "Sleep Tracker Analysis",
        "description": "Use a wearable or app to identify patterns — data-driven improvement.",
        "category": "sleep_tracker",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "routine", "structured", "self-paced"],
    },
    {
        "title": "Mattress & Pillow Upgrade",
        "description": "Invest in your sleep surface — 8 hours a night, 2920 hours a year.",
        "category": "mattress_upgrade",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["comfort", "practical", "warmth"],
    },
]


def _match_sleep_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    kw_map = {
        "meditation": ["meditation", "guided"],
        "冥想": ["meditation", "guided"],
        "breathing": ["breathing", "calming"],
        "呼吸": ["breathing", "calming"],
        "noise": ["comfort"],
        "blanket": ["comfort", "warmth"],
        "tea": ["calming_scent", "gentle"],
        "茶": ["calming_scent", "gentle"],
        "screen": ["screen_free"],
        "屏幕": ["screen_free"],
        "exercise": ["exercise", "routine"],
        "运动": ["exercise", "routine"],
        "schedule": ["routine", "structured"],
        "routine": ["routine", "structured"],
        "cool": ["cool"],
        "lavender": ["calming_scent"],
    }
    for keyword, tags in kw_map.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


def _emotion_to_sleep_tags(det: DetectorResults) -> list[str]:
    tags: list[str] = []
    emotions = det.emotion.get("emotions", {})
    for emotion in ("anxiety", "sadness", "anger", "stress", "restlessness"):
        if emotions.get(emotion, 0) > 0.3:
            for t in EMOTION_SLEEP_MAP.get(emotion, []):
                if t not in tags:
                    tags.append(t)
    return tags


class SleepEnvFulfiller(L2Fulfiller):
    """L2 fulfiller for sleep wishes — emotion-linked sleep environment optimization.

    15 sleep aids, emotion-aware recommendations. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_sleep_tags(wish.wish_text)
        emotion_tags = _emotion_to_sleep_tags(detector_results)

        all_tags = list(keyword_tags)
        for t in emotion_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in SLEEP_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in SLEEP_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in SLEEP_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Try one of these tonight. Good sleep compounds!",
                delay_hours=12,
            ),
        )


def _build_relevance_reason(item: dict, det: DetectorResults) -> str:
    tags = set(item.get("tags", []))
    emotions = det.emotion.get("emotions", {})

    if emotions.get("anxiety", 0) > 0.3 and "meditation" in tags:
        return "Meditation helps calm anxious thoughts before sleep"
    if emotions.get("anxiety", 0) > 0.3 and "breathing" in tags:
        return "Breathing exercises reduce anxiety for better sleep"
    if emotions.get("anger", 0) > 0.3 and "cool" in tags:
        return "Cooling down your body helps release agitation"
    if emotions.get("anger", 0) > 0.3 and "exercise" in tags:
        return "Exercise earlier in the day burns off restless energy"
    if "comfort" in tags:
        return "Physical comfort is the foundation of good sleep"

    return f"Sleep optimization tip: {item.get('category', '').replace('_', ' ')}"
