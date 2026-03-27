"""EmotionWeatherFulfiller — simulated local emotion climate broadcast.

NOT real API — generates simulated local emotion weather based on time/weather/events.
10 pre-built emotion weather templates. Multilingual keyword routing. Zero LLM.
"""

from __future__ import annotations

from datetime import datetime

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
)

# ── Emotion Weather Model ────────────────────────────────────────────────────


class EmotionWeather:
    """Simulated emotional weather for a local area."""

    __slots__ = ("area", "mood_index", "energy_index", "social_index",
                 "dominant_emotion", "sample_size")

    def __init__(
        self,
        area: str,
        mood_index: float,
        energy_index: float,
        social_index: float,
        dominant_emotion: str,
        sample_size: int,
    ):
        self.area = area
        self.mood_index = mood_index
        self.energy_index = energy_index
        self.social_index = social_index
        self.dominant_emotion = dominant_emotion
        self.sample_size = sample_size

    def summary(self) -> str:
        return (
            f"Area: {self.area} | Mood: {self.mood_index:.1f} | "
            f"Energy: {self.energy_index:.1f} | Social: {self.social_index:.1f} | "
            f"Dominant: {self.dominant_emotion} (n={self.sample_size})"
        )


# ── Pre-built Templates (10) ────────────────────────────────────────────────

WEATHER_TEMPLATES: list[dict] = [
    {
        "title": "Energetic Morning",
        "description": "The neighborhood is buzzing with energy — people are starting their day with optimism.",
        "category": "emotion_weather",
        "time_match": "morning",
        "mood_index": 0.7,
        "energy_index": 0.8,
        "social_index": 0.5,
        "dominant_emotion": "energetic",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["morning", "energetic", "social"],
    },
    {
        "title": "Focused Afternoon",
        "description": "A productive hum in the air — people are deep in work and creative flow.",
        "category": "emotion_weather",
        "time_match": "afternoon",
        "mood_index": 0.6,
        "energy_index": 0.6,
        "social_index": 0.3,
        "dominant_emotion": "focused",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["afternoon", "focused", "quiet", "calming"],
    },
    {
        "title": "Relaxed Evening",
        "description": "The city is winding down — a warm, relaxed vibe fills the streets.",
        "category": "emotion_weather",
        "time_match": "evening",
        "mood_index": 0.7,
        "energy_index": 0.4,
        "social_index": 0.6,
        "dominant_emotion": "relaxed",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["evening", "relaxed", "calming", "social"],
    },
    {
        "title": "Friday Night Excitement",
        "description": "It's Friday night! The area is alive with anticipation and social energy.",
        "category": "emotion_weather",
        "time_match": "friday_night",
        "mood_index": 0.85,
        "energy_index": 0.9,
        "social_index": 0.9,
        "dominant_emotion": "excited",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["friday", "excited", "social"],
    },
    {
        "title": "Monday Morning Blues",
        "description": "A heavy start to the week — collective energy is low, but solidarity is high.",
        "category": "emotion_weather",
        "time_match": "monday_morning",
        "mood_index": 0.35,
        "energy_index": 0.3,
        "social_index": 0.4,
        "dominant_emotion": "low",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["monday", "low", "quiet", "calming"],
    },
    {
        "title": "Rainy Day Melancholy",
        "description": "Rain patters on windows — a gentle melancholy with cozy indoor vibes.",
        "category": "emotion_weather",
        "time_match": "any",
        "weather_match": "rain",
        "mood_index": 0.45,
        "energy_index": 0.3,
        "social_index": 0.3,
        "dominant_emotion": "melancholy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["rain", "melancholy", "quiet", "calming"],
    },
    {
        "title": "Sunny Day Joy",
        "description": "Sunshine brings smiles — parks are full, people are out and happy.",
        "category": "emotion_weather",
        "time_match": "any",
        "weather_match": "sunny",
        "mood_index": 0.8,
        "energy_index": 0.7,
        "social_index": 0.7,
        "dominant_emotion": "joy",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["sunny", "joy", "social", "outdoor"],
    },
    {
        "title": "Late Night Calm",
        "description": "The city sleeps — only the night owls and dreamers remain awake.",
        "category": "emotion_weather",
        "time_match": "late_night",
        "mood_index": 0.5,
        "energy_index": 0.2,
        "social_index": 0.1,
        "dominant_emotion": "contemplative",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["night", "quiet", "calming", "contemplative"],
    },
    {
        "title": "Weekend Morning Ease",
        "description": "No alarm clocks today — the neighborhood wakes up slowly, at its own pace.",
        "category": "emotion_weather",
        "time_match": "weekend_morning",
        "mood_index": 0.75,
        "energy_index": 0.5,
        "social_index": 0.4,
        "dominant_emotion": "content",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["weekend", "relaxed", "calming", "quiet"],
    },
    {
        "title": "Festival Buzz",
        "description": "A local event is happening — the area pulses with curiosity and togetherness.",
        "category": "emotion_weather",
        "time_match": "any",
        "mood_index": 0.8,
        "energy_index": 0.85,
        "social_index": 0.9,
        "dominant_emotion": "excited",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["festival", "excited", "social"],
    },
]

# ── Keywords ──────────────────────────────────────────────────────────────────

_EMOTION_WEATHER_KEYWORDS: set[str] = {
    "情绪天气", "mood", "周围", "atmosphere", "氛围", "مزاج",
    "vibe", "emotion weather", "feeling around",
}


def _get_time_period() -> str:
    """Determine current time period for template matching."""
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()  # 0=Monday, 4=Friday, 5-6=weekend

    if weekday == 0 and hour < 12:
        return "monday_morning"
    if weekday == 4 and hour >= 18:
        return "friday_night"
    if weekday >= 5 and hour < 12:
        return "weekend_morning"
    if hour >= 23 or hour < 5:
        return "late_night"
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def _select_template(time_period: str | None = None) -> dict:
    """Select the best-matching emotion weather template for the current time."""
    if time_period is None:
        time_period = _get_time_period()

    # Try exact time match first
    for t in WEATHER_TEMPLATES:
        if t.get("time_match") == time_period:
            return t

    # Fallback: general time-of-day match
    general_map = {
        "monday_morning": "morning",
        "friday_night": "evening",
        "weekend_morning": "morning",
        "late_night": "evening",
    }
    fallback = general_map.get(time_period, time_period)
    for t in WEATHER_TEMPLATES:
        if t.get("time_match") == fallback:
            return t

    # Final fallback: first template
    return WEATHER_TEMPLATES[0]


class EmotionWeatherFulfiller(L2Fulfiller):
    """L2 fulfiller for emotion weather wishes — local emotion climate broadcast.

    10 pre-built templates with time/weather matching. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Select template based on current time
        template = _select_template()

        # 2. Build emotion weather model
        weather = EmotionWeather(
            area="Your neighborhood",
            mood_index=template["mood_index"],
            energy_index=template["energy_index"],
            social_index=template["social_index"],
            dominant_emotion=template["dominant_emotion"],
            sample_size=42,  # simulated
        )

        # 3. Build recommendation from template
        rec = Recommendation(
            title=template["title"],
            description=template["description"],
            category="emotion_weather",
            relevance_reason=f"Emotional atmosphere: {weather.dominant_emotion} (mood {weather.mood_index:.0%})",
            score=0.8,
            tags=template.get("tags", []),
        )

        return L2FulfillmentResult(
            recommendations=[rec],
            map_data=MapData(place_type="emotion_zone", radius_km=3.0),
            reminder_option=ReminderOption(
                text="Check the emotional weather again later?",
                delay_hours=6,
            ),
        )
