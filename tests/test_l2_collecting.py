"""Tests for CollectingFulfiller — values-aware collecting hobby recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_collecting import CollectingFulfiller, COLLECTING_CATALOG


class TestCollectingCatalog:
    def test_catalog_has_12_entries(self):
        assert len(COLLECTING_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in COLLECTING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestCollectingFulfiller:
    def _make_wish(self, text="I want to start collecting") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = CollectingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = CollectingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_tradition_values_get_antiques(self):
        f = CollectingFulfiller()
        det = DetectorResults(values={"top_values": ["tradition"]})
        result = f.fulfill(self._make_wish("collecting hobby"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in categories for c in ("antiques", "stamps", "coins", "tea_sets"))

    def test_vinyl_keyword(self):
        f = CollectingFulfiller()
        result = f.fulfill(self._make_wish("vinyl record collection"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "vinyl_records" in categories

    def test_sneaker_keyword(self):
        f = CollectingFulfiller()
        result = f.fulfill(self._make_wish("sneaker collection"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "sneakers" in categories

    def test_has_reminder(self):
        f = CollectingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = CollectingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_chinese_keyword(self):
        f = CollectingFulfiller()
        result = f.fulfill(self._make_wish("想收藏一些东西"), DetectorResults())
        assert len(result.recommendations) >= 1
