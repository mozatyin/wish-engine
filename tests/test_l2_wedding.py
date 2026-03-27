"""Tests for WeddingFulfiller — cultural-aware wedding service recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_wedding import WeddingFulfiller, WEDDING_CATALOG


class TestWeddingCatalog:
    def test_catalog_has_15_entries(self):
        assert len(WEDDING_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in WEDDING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestWeddingFulfiller:
    def _make_wish(self, text="准备婚礼") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="wedding",
        )

    def test_returns_l2_result(self):
        f = WeddingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = WeddingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_photographer_keyword(self):
        f = WeddingFulfiller()
        result = f.fulfill(self._make_wish("wedding photographer"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "photographer" in categories

    def test_islamic_ceremony_keyword(self):
        f = WeddingFulfiller()
        result = f.fulfill(self._make_wish("islamic wedding"), DetectorResults())
        # Should get results with islamic_ceremony tag
        assert len(result.recommendations) >= 1

    def test_honeymoon_keyword(self):
        f = WeddingFulfiller()
        result = f.fulfill(self._make_wish("planning honeymoon蜜月"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "honeymoon_destination" in categories

    def test_has_reminder(self):
        f = WeddingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = WeddingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = WeddingFulfiller()
        result = f.fulfill(self._make_wish("تحضيرات زفاف"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
