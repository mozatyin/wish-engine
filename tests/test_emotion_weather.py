"""Tests for EmotionWeatherFulfiller — local emotion climate broadcast."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_emotion_weather import (
    EmotionWeatherFulfiller,
    EmotionWeather,
    WEATHER_TEMPLATES,
    _select_template,
)


class TestWeatherTemplates:
    def test_has_10_templates(self):
        assert len(WEATHER_TEMPLATES) == 10

    def test_each_template_has_required_fields(self):
        required = {"title", "description", "category", "time_match", "mood_index",
                     "energy_index", "social_index", "dominant_emotion", "noise", "social", "mood", "tags"}
        for t in WEATHER_TEMPLATES:
            missing = required - set(t.keys())
            assert not missing, f"{t['title']} missing: {missing}"

    def test_mood_index_in_range(self):
        for t in WEATHER_TEMPLATES:
            assert 0.0 <= t["mood_index"] <= 1.0
            assert 0.0 <= t["energy_index"] <= 1.0
            assert 0.0 <= t["social_index"] <= 1.0


class TestEmotionWeather:
    def test_model_creation(self):
        w = EmotionWeather("Downtown", 0.7, 0.8, 0.5, "energetic", 42)
        assert w.area == "Downtown"
        assert w.dominant_emotion == "energetic"

    def test_summary(self):
        w = EmotionWeather("Downtown", 0.7, 0.8, 0.5, "energetic", 42)
        s = w.summary()
        assert "Downtown" in s
        assert "energetic" in s


class TestEmotionWeatherFulfiller:
    def _make_wish(self, text="周围的情绪天气怎样") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="emotion_weather",
        )

    def test_returns_l2_result(self):
        f = EmotionWeatherFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) == 1

    def test_has_reminder(self):
        f = EmotionWeatherFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_has_map_data(self):
        f = EmotionWeatherFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "emotion_zone"

    def test_select_morning_template(self):
        t = _select_template("morning")
        assert t["time_match"] == "morning"

    def test_select_friday_night_template(self):
        t = _select_template("friday_night")
        assert t["time_match"] == "friday_night"

    def test_select_fallback(self):
        t = _select_template("unknown_period")
        assert t is not None  # should not crash
