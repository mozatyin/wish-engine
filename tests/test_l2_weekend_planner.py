"""Tests for WeekendPlannerFulfiller — MBTI + emotion-aware weekend plans."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_weekend_planner import WeekendPlannerFulfiller, WEEKEND_CATALOG


class TestWeekendCatalog:
    def test_catalog_has_15_entries(self):
        assert len(WEEKEND_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in WEEKEND_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestWeekendPlannerFulfiller:
    def _make_wish(self, text="周末做什么") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = WeekendPlannerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = WeekendPlannerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_quiet_plans(self):
        f = WeekendPlannerFulfiller()
        det = DetectorResults(mbti={"type": "INTP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish("weekend plan"), det)
        for r in result.recommendations:
            assert r.category not in ("night_out",) or r.score < 0.6

    def test_spa_keyword(self):
        f = WeekendPlannerFulfiller()
        result = f.fulfill(self._make_wish("weekend spa day"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "spa_day" in categories

    def test_brunch_keyword(self):
        f = WeekendPlannerFulfiller()
        result = f.fulfill(self._make_wish("weekend brunch plan"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "social_brunch" in categories

    def test_has_reminder(self):
        f = WeekendPlannerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = WeekendPlannerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_family_keyword(self):
        f = WeekendPlannerFulfiller()
        result = f.fulfill(self._make_wish("family weekend plan"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "family_outing" in categories
