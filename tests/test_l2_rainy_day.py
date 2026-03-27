"""Tests for RainyDayFulfiller — rainy day activity recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_rainy_day import (
    RainyDayFulfiller,
    RAINY_DAY_CATALOG,
    _match_candidates,
)


class TestRainyDayCatalog:
    def test_catalog_has_12_entries(self):
        assert len(RAINY_DAY_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in RAINY_DAY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_indoor(self):
        for item in RAINY_DAY_CATALOG:
            assert "indoor" in item["tags"], f"{item['title']} should be indoor"


class TestRainyDayFulfiller:
    def _make_wish(self, text="it's raining what should I do") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="rainy_day",
        )

    def test_returns_l2_result(self):
        f = RainyDayFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = RainyDayFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_raining_boosts_all(self):
        rain = _match_candidates("rainy day", DetectorResults(), is_raining=True)
        dry = _match_candidates("rainy day", DetectorResults(), is_raining=False)
        rain_avg = sum(c["_emotion_boost"] for c in rain) / len(rain)
        dry_avg = sum(c["_emotion_boost"] for c in dry) / len(dry)
        assert rain_avg > dry_avg

    def test_cozy_keyword_boosts(self):
        candidates = _match_candidates("cozy warm rain", DetectorResults())
        cozy = [c for c in candidates if "cozy" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in cozy)

    def test_creative_keyword_boosts(self):
        candidates = _match_candidates("creative rain day", DetectorResults())
        creative = [c for c in candidates if "creative" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in creative)

    def test_no_map_data(self):
        f = RainyDayFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        # Rainy day activities are mostly at-home, no map needed
        assert result.map_data is None

    def test_has_reminder(self):
        f = RainyDayFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
