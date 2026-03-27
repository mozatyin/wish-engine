"""Tests for HealthSyncFulfiller — health signal cross-referencing."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_health_sync import HealthSyncFulfiller, HEALTH_CATALOG


class TestHealthCatalog:
    def test_catalog_has_15_entries(self):
        assert len(HEALTH_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "health_signal"}
        for item in HEALTH_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestHealthSyncFulfiller:
    def _make_wish(self, text="关注我的健康") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="health_sync",
        )

    def test_returns_l2_result(self):
        f = HealthSyncFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = HealthSyncFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_sleep_keyword_boosts_sleep(self):
        f = HealthSyncFulfiller()
        result = f.fulfill(self._make_wish("track my sleep"), DetectorResults())
        cats = [r.category for r in result.recommendations]
        assert "sleep_quality" in cats

    def test_cross_reference_anxiety_sleep(self):
        f = HealthSyncFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        result = f.fulfill(self._make_wish("sleep problems"), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("sleep hygiene" in r.lower() or "calm" in r.lower() for r in reasons)

    def test_steps_keyword(self):
        f = HealthSyncFulfiller()
        result = f.fulfill(self._make_wish("track my steps"), DetectorResults())
        cats = [r.category for r in result.recommendations]
        assert "step_count" in cats

    def test_has_reminder(self):
        f = HealthSyncFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_no_map_data(self):
        f = HealthSyncFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_chinese_keyword_water(self):
        f = HealthSyncFulfiller()
        result = f.fulfill(self._make_wish("提醒我喝水"), DetectorResults())
        cats = [r.category for r in result.recommendations]
        assert "hydration" in cats
