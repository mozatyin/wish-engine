"""Tests for ExtremeWeatherFulfiller — extreme weather preparedness."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_extreme_weather import (
    ExtremeWeatherFulfiller,
    EXTREME_WEATHER_CATALOG,
    _match_candidates,
)


class TestExtremeWeatherCatalog:
    def test_catalog_has_10_entries(self):
        assert len(EXTREME_WEATHER_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in EXTREME_WEATHER_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_have_tags(self):
        for item in EXTREME_WEATHER_CATALOG:
            assert len(item["tags"]) >= 2, f"{item['title']} needs more tags"


class TestExtremeWeatherFulfiller:
    def _make_wish(self, text="extreme heat where can I cool down") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="extreme_weather",
        )

    def test_returns_l2_result(self):
        f = ExtremeWeatherFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = ExtremeWeatherFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = ExtremeWeatherFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "weather_shelter"

    def test_heat_keyword_boosts_cooling(self):
        candidates = _match_candidates("extreme heat heatwave", DetectorResults())
        cooling = [c for c in candidates if c["category"] == "cooling_center"]
        assert len(cooling) >= 1
        assert cooling[0]["_emotion_boost"] > 0

    def test_earthquake_keyword_boosts(self):
        candidates = _match_candidates("earthquake safety shelter", DetectorResults())
        eq = [c for c in candidates if c["category"] == "earthquake_safety"]
        assert len(eq) >= 1
        assert eq[0]["_emotion_boost"] > 0

    def test_emergency_boosts_shelter(self):
        candidates = _match_candidates("emergency urgent shelter", DetectorResults())
        shelters = [c for c in candidates if "shelter" in c.get("tags", []) or "safe" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in shelters)

    def test_has_reminder(self):
        f = ExtremeWeatherFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
