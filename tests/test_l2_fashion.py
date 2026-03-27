"""Tests for FashionFulfiller — MBTI + values-aware fashion recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_fashion import FashionFulfiller, FASHION_CATALOG


class TestFashionCatalog:
    def test_catalog_has_12_entries(self):
        assert len(FASHION_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in FASHION_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestFashionFulfiller:
    def _make_wish(self, text="想看穿搭推荐") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = FashionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = FashionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_minimalist(self):
        f = FashionFulfiller()
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish("fashion style advice"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in categories for c in ("minimalist", "classic", "vintage", "smart_casual"))

    def test_tradition_values_get_modest(self):
        f = FashionFulfiller()
        det = DetectorResults(values={"top_values": ["tradition"]})
        result = f.fulfill(self._make_wish("fashion advice"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in categories for c in ("modest_fashion", "classic", "vintage"))

    def test_sustainable_keyword(self):
        f = FashionFulfiller()
        result = f.fulfill(self._make_wish("sustainable fashion brands"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "sustainable" in categories

    def test_has_reminder(self):
        f = FashionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = FashionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_vintage_keyword(self):
        f = FashionFulfiller()
        result = f.fulfill(self._make_wish("vintage clothing"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "vintage" in categories
