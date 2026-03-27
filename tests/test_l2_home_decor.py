"""Tests for HomeDecorFulfiller — home decor style recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_home_decor import HomeDecorFulfiller, STYLE_CATALOG


class TestStyleCatalog:
    def test_catalog_has_15_entries(self):
        assert len(STYLE_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in STYLE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestHomeDecorFulfiller:
    def _make_wish(self, text="想装修房子") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="decor_recommendation",
        )

    def test_returns_l2_result(self):
        f = HomeDecorFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = HomeDecorFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_quiet_styles(self):
        f = HomeDecorFulfiller()
        det = DetectorResults(mbti={"type": "INTJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("minimalist", "japanese_wabi_sabi", "quiet") for t in tags)

    def test_tradition_values_boost_traditional(self):
        f = HomeDecorFulfiller()
        det = DetectorResults(values={"top_values": ["tradition"]})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        assert any(c in ("traditional_chinese", "traditional_arabic", "rustic", "cottage_core") for c in cats)

    def test_minimalist_keyword(self):
        f = HomeDecorFulfiller()
        result = f.fulfill(self._make_wish("I want a minimalist home"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "minimalist" in tags

    def test_has_reminder(self):
        f = HomeDecorFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = HomeDecorFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
