"""Tests for AirQualityFulfiller — air quality recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_air_quality import (
    AirQualityFulfiller,
    AIR_QUALITY_CATALOG,
    _match_candidates,
)


class TestAirQualityCatalog:
    def test_catalog_has_10_entries(self):
        assert len(AIR_QUALITY_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in AIR_QUALITY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_have_tags(self):
        for item in AIR_QUALITY_CATALOG:
            assert len(item["tags"]) >= 2, f"{item['title']} needs more tags"


class TestAirQualityFulfiller:
    def _make_wish(self, text="air quality is bad today") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="air_quality",
        )

    def test_returns_l2_result(self):
        f = AirQualityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = AirQualityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = AirQualityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "air_quality"

    def test_pollution_keyword_boosts(self):
        candidates = _match_candidates("PM2.5 pollution is high", DetectorResults())
        clean = [c for c in candidates if "clean-air" in c.get("tags", []) or "alert" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in clean)

    def test_forest_keyword_boosts(self):
        candidates = _match_candidates("I want forest clean air", DetectorResults())
        forest = [c for c in candidates if c["category"] == "forest_air"]
        assert len(forest) >= 1
        assert forest[0]["_emotion_boost"] > 0

    def test_chinese_smog_keyword(self):
        candidates = _match_candidates("雾霾很严重 空气", DetectorResults())
        boosted = [c for c in candidates if c["_emotion_boost"] > 0]
        assert len(boosted) > 0

    def test_has_reminder(self):
        f = AirQualityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
