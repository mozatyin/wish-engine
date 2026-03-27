"""Tests for EstateItemsFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_estate_items import EstateItemsFulfiller, ESTATE_ITEMS_CATALOG


class TestEstateItemsCatalog:
    def test_catalog_has_10_entries(self):
        assert len(ESTATE_ITEMS_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in ESTATE_ITEMS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestEstateItemsFulfiller:
    def _make_wish(self, text="I need to sort through belongings") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="estate_items",
        )

    def test_returns_l2_result(self):
        f = EstateItemsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = EstateItemsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_estate_keyword(self):
        f = EstateItemsFulfiller()
        result = f.fulfill(self._make_wish("estate planning"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("estate" in t for t in tags)

    def test_chinese_keyword(self):
        f = EstateItemsFulfiller()
        result = f.fulfill(self._make_wish("遗物整理"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = EstateItemsFulfiller()
        result = f.fulfill(self._make_wish("تركة"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = EstateItemsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = EstateItemsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
