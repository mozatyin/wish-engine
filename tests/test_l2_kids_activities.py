"""Tests for KidsActivityFulfiller — age-aware family activity recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_kids_activities import KidsActivityFulfiller, KIDS_CATALOG


class TestKidsCatalog:
    def test_catalog_has_15_entries(self):
        assert len(KIDS_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in KIDS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestKidsActivityFulfiller:
    def _make_wish(self, text="带孩子去玩") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="kids_activities",
        )

    def test_returns_l2_result(self):
        f = KidsActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = KidsActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_zoo_keyword_match(self):
        f = KidsActivityFulfiller()
        result = f.fulfill(self._make_wish("带孩子去动物园"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "zoo" in categories

    def test_playground_keyword_match(self):
        f = KidsActivityFulfiller()
        result = f.fulfill(self._make_wish("find a playground for kids"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "playground" in categories

    def test_has_reminder(self):
        f = KidsActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = KidsActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = KidsActivityFulfiller()
        result = f.fulfill(self._make_wish("أنشطة أطفال"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_no_map_data(self):
        f = KidsActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None
