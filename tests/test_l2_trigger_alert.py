"""Tests for TriggerAlertFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_trigger_alert import TriggerAlertFulfiller, TRIGGER_ALERT_CATALOG


class TestTriggerAlertCatalog:
    def test_catalog_has_10_entries(self):
        assert len(TRIGGER_ALERT_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in TRIGGER_ALERT_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestTriggerAlertFulfiller:
    def _make_wish(self, text="I need to avoid triggers") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="trigger_alert",
        )

    def test_returns_l2_result(self):
        f = TriggerAlertFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = TriggerAlertFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_trigger_keyword(self):
        f = TriggerAlertFulfiller()
        result = f.fulfill(self._make_wish("trigger warning"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("trigger" in t for t in tags)

    def test_bar_avoidance(self):
        f = TriggerAlertFulfiller()
        result = f.fulfill(self._make_wish("avoid bars"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("alcohol" in t or "avoidance" in t for t in tags)

    def test_chinese_keyword(self):
        f = TriggerAlertFulfiller()
        result = f.fulfill(self._make_wish("触发预警"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = TriggerAlertFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = TriggerAlertFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
