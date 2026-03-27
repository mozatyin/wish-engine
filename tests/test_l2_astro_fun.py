"""Tests for AstroFunFulfiller — fun astrology and personality quiz recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_astro_fun import AstroFunFulfiller, ASTRO_FUN_CATALOG


class TestAstroFunCatalog:
    def test_catalog_has_12_entries(self):
        assert len(ASTRO_FUN_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in ASTRO_FUN_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestAstroFunFulfiller:
    def _make_wish(self, text="今天星座运势") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = AstroFunFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = AstroFunFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_tarot_keyword(self):
        f = AstroFunFulfiller()
        result = f.fulfill(self._make_wish("tarot card reading"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "tarot_reading" in categories

    def test_zodiac_keyword(self):
        f = AstroFunFulfiller()
        result = f.fulfill(self._make_wish("zodiac compatibility"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "zodiac_compatibility" in categories

    def test_chinese_zodiac_keyword(self):
        f = AstroFunFulfiller()
        result = f.fulfill(self._make_wish("生肖运势"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "chinese_zodiac" in categories

    def test_has_reminder(self):
        f = AstroFunFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = AstroFunFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = AstroFunFulfiller()
        result = f.fulfill(self._make_wish("أبراج اليوم"), DetectorResults())
        assert len(result.recommendations) >= 1
