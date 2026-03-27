"""Tests for EatingDisorderFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_eating_disorder import EatingDisorderFulfiller, ED_CATALOG


class TestEDCatalog:
    def test_catalog_has_10_entries(self):
        assert len(ED_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in ED_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_calming(self):
        """Highest sensitivity — all entries must be calming."""
        for item in ED_CATALOG:
            assert item["mood"] == "calming", f"{item['title']} must be calming"

    def test_all_gentle(self):
        """Highest sensitivity — all entries should have gentle tag."""
        for item in ED_CATALOG:
            assert "gentle" in item["tags"], f"{item['title']} should be gentle"


class TestEatingDisorderFulfiller:
    def _make_wish(self, text="I think I have an eating disorder") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="eating_disorder",
        )

    def test_returns_l2_result(self):
        f = EatingDisorderFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = EatingDisorderFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_crisis_keyword(self):
        f = EatingDisorderFulfiller()
        result = f.fulfill(self._make_wish("I need crisis help"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "crisis" in tags or "immediate" in tags

    def test_has_reminder(self):
        f = EatingDisorderFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = EatingDisorderFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = EatingDisorderFulfiller()
        result = f.fulfill(self._make_wish("اضطراب الأكل"), DetectorResults())
        assert len(result.recommendations) >= 1
