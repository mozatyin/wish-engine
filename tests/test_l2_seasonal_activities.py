"""Tests for SeasonalActivityFulfiller — season + location-aware activities."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_seasonal_activities import SeasonalActivityFulfiller, SEASONAL_ACTIVITY_CATALOG


class TestSeasonalActivityCatalog:
    def test_catalog_has_15_entries(self):
        assert len(SEASONAL_ACTIVITY_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in SEASONAL_ACTIVITY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestSeasonalActivityFulfiller:
    def _make_wish(self, text="what to do this season") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = SeasonalActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = SeasonalActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_spring_keyword(self):
        f = SeasonalActivityFulfiller()
        result = f.fulfill(self._make_wish("spring activities"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert any(c.startswith("spring") for c in categories)

    def test_camping_keyword(self):
        f = SeasonalActivityFulfiller()
        result = f.fulfill(self._make_wish("summer camping trip"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "summer_camping" in categories

    def test_cherry_blossom_keyword(self):
        f = SeasonalActivityFulfiller()
        result = f.fulfill(self._make_wish("cherry blossom viewing"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "cherry_blossom_viewing" in categories

    def test_has_reminder(self):
        f = SeasonalActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = SeasonalActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_skating_keyword(self):
        f = SeasonalActivityFulfiller()
        result = f.fulfill(self._make_wish("ice skating"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "ice_skating" in categories
