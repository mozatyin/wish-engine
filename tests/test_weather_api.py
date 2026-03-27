"""Tests for Weather API — client, outdoor filter, and weather tags."""

import pytest
from unittest.mock import patch

from wish_engine.apis.weather_api import get_weather, is_available, _normalize_condition, _DEFAULT_WEATHER
from wish_engine.apis.weather_filter import should_exclude_outdoor, adjust_recommendations, get_weather_tags


class TestWeatherApiAvailability:
    def test_not_available_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert not is_available()

    def test_available_with_key(self):
        with patch.dict("os.environ", {"OPENWEATHER_API_KEY": "test"}):
            assert is_available()

    def test_fallback_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            weather = get_weather(25.0, 55.0)
            assert weather["condition"] == "clear"
            assert weather["temp_c"] == 25


class TestNormalizeCondition:
    def test_rain_conditions(self):
        assert _normalize_condition("rain") == "rain"
        assert _normalize_condition("drizzle") == "rain"
        assert _normalize_condition("thunderstorm") == "rain"

    def test_snow(self):
        assert _normalize_condition("snow") == "snow"

    def test_cloudy_conditions(self):
        assert _normalize_condition("clouds") == "cloudy"
        assert _normalize_condition("mist") == "cloudy"
        assert _normalize_condition("fog") == "cloudy"

    def test_clear(self):
        assert _normalize_condition("clear") == "clear"


class TestShouldExcludeOutdoor:
    def test_rain_excludes(self):
        assert should_exclude_outdoor({"condition": "rain", "temp_c": 25}) is True

    def test_snow_excludes(self):
        assert should_exclude_outdoor({"condition": "snow", "temp_c": -5}) is True

    def test_extreme_heat_excludes(self):
        assert should_exclude_outdoor({"condition": "clear", "temp_c": 45}) is True

    def test_extreme_cold_excludes(self):
        assert should_exclude_outdoor({"condition": "clear", "temp_c": -5}) is True

    def test_clear_moderate_does_not_exclude(self):
        assert should_exclude_outdoor({"condition": "clear", "temp_c": 22}) is False

    def test_cloudy_moderate_does_not_exclude(self):
        assert should_exclude_outdoor({"condition": "cloudy", "temp_c": 18}) is False


class TestAdjustRecommendations:
    def test_removes_outdoor_in_rain(self):
        candidates = [
            {"title": "Park Walk", "tags": ["outdoor", "walking"], "_personality_score": 0.7},
            {"title": "Cozy Cafe", "tags": ["indoor", "coffee"], "_personality_score": 0.6},
        ]
        weather = {"condition": "rain", "temp_c": 15}
        result = adjust_recommendations(candidates, weather)
        assert len(result) == 1
        assert result[0]["title"] == "Cozy Cafe"

    def test_boosts_indoor_in_bad_weather(self):
        candidates = [
            {"title": "Library", "tags": ["quiet", "reading"], "_personality_score": 0.5},
        ]
        weather = {"condition": "snow", "temp_c": -2}
        result = adjust_recommendations(candidates, weather)
        assert result[0]["_personality_score"] == 0.6  # 0.5 + 0.1 boost

    def test_no_change_in_good_weather(self):
        candidates = [
            {"title": "Park Walk", "tags": ["outdoor", "walking"], "_personality_score": 0.7},
        ]
        weather = {"condition": "clear", "temp_c": 22}
        result = adjust_recommendations(candidates, weather)
        assert len(result) == 1
        assert result[0]["_personality_score"] == 0.7


class TestGetWeatherTags:
    def test_rainy_tags(self):
        tags = get_weather_tags({"condition": "rain", "temp_c": 15})
        assert "rainy" in tags
        assert "indoor-preferred" in tags

    def test_clear_tags(self):
        tags = get_weather_tags({"condition": "clear", "temp_c": 22})
        assert "clear" in tags
        assert "outdoor-friendly" in tags

    def test_hot_tags(self):
        tags = get_weather_tags({"condition": "clear", "temp_c": 45})
        assert "hot" in tags
        assert "stay-cool" in tags

    def test_cold_tags(self):
        tags = get_weather_tags({"condition": "clear", "temp_c": -5})
        assert "cold" in tags
        assert "warm-up" in tags
