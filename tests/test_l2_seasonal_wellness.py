"""Tests for SeasonalWellnessFulfiller — culture-aware seasonal wellness."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_seasonal_wellness import SeasonalWellnessFulfiller, SEASONAL_WELLNESS_CATALOG


class TestSeasonalWellnessCatalog:
    def test_catalog_has_12_entries(self):
        assert len(SEASONAL_WELLNESS_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in SEASONAL_WELLNESS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestSeasonalWellnessFulfiller:
    def _make_wish(self, text="seasonal wellness tips") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="wellness",
        )

    def test_returns_l2_result(self):
        f = SeasonalWellnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = SeasonalWellnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_ramadan_keyword(self):
        f = SeasonalWellnessFulfiller()
        result = f.fulfill(self._make_wish("ramadan fasting tips"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "ramadan_fasting_tips" in categories

    def test_chinese_solar_terms_keyword(self):
        f = SeasonalWellnessFulfiller()
        result = f.fulfill(self._make_wish("二十四节气养生"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "chinese_solar_terms" in categories

    def test_winter_keyword(self):
        f = SeasonalWellnessFulfiller()
        result = f.fulfill(self._make_wish("winter wellness"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert any(c in categories for c in ("winter_warmth", "winter_blues"))

    def test_has_reminder(self):
        f = SeasonalWellnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = SeasonalWellnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_allergy_keyword(self):
        f = SeasonalWellnessFulfiller()
        result = f.fulfill(self._make_wish("allergy season help"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "hay_fever_season" in categories
