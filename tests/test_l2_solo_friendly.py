"""Tests for SoloFriendlyFulfiller — solo-friendly place recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_solo_friendly import SoloFriendlyFulfiller, SOLO_CATALOG


class TestSoloCatalog:
    def test_catalog_has_15_entries(self):
        assert len(SOLO_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "solo_comfort"}
        for item in SOLO_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_solo_comfort_range(self):
        for item in SOLO_CATALOG:
            assert 0.0 <= item["solo_comfort"] <= 1.0


class TestSoloFriendlyFulfiller:
    def _make_wish(self, text="一个人能去哪") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="solo_recommendation",
        )

    def test_returns_l2_result(self):
        f = SoloFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = SoloFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_cafe_keyword(self):
        f = SoloFriendlyFulfiller()
        result = f.fulfill(self._make_wish("solo cafe visit"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "cafe" in tags

    def test_museum_keyword(self):
        f = SoloFriendlyFulfiller()
        result = f.fulfill(self._make_wish("go to museum alone"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "museum" in tags

    def test_has_reminder(self):
        f = SoloFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_personalized_or_fallback(self):
        f = SoloFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            # With no detector data, personalization falls back to title-based reason
            assert len(r.relevance_reason) > 5
            assert r.title in r.relevance_reason or "solo" in r.relevance_reason.lower()

    def test_relevance_reason_not_empty(self):
        f = SoloFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
