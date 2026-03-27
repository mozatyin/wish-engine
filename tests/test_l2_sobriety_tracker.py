"""Tests for SobrietyTrackerFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_sobriety_tracker import SobrietyTrackerFulfiller, SOBRIETY_CATALOG


class TestSobrietyCatalog:
    def test_catalog_has_10_entries(self):
        assert len(SOBRIETY_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in SOBRIETY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestSobrietyTrackerFulfiller:
    def _make_wish(self, text="Track my sober days") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="sobriety_tracker",
        )

    def test_returns_l2_result(self):
        f = SobrietyTrackerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = SobrietyTrackerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_sober_keyword(self):
        f = SobrietyTrackerFulfiller()
        result = f.fulfill(self._make_wish("sober milestone"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("sobriety" in t or "milestone" in t for t in tags)

    def test_chinese_keyword(self):
        f = SobrietyTrackerFulfiller()
        result = f.fulfill(self._make_wish("清醒天数"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = SobrietyTrackerFulfiller()
        result = f.fulfill(self._make_wish("نظافة"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = SobrietyTrackerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = SobrietyTrackerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
