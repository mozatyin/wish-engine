"""Tests for LegacyPlanningFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_legacy_planning import LegacyPlanningFulfiller, LEGACY_CATALOG


class TestLegacyCatalog:
    def test_catalog_has_10_entries(self):
        assert len(LEGACY_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in LEGACY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestLegacyPlanningFulfiller:
    def _make_wish(self, text="I want to leave a legacy") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.LIFE_REFLECTION,
            level=WishLevel.L2, fulfillment_strategy="legacy_planning",
        )

    def test_returns_l2_result(self):
        f = LegacyPlanningFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = LegacyPlanningFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_mentor_keyword(self):
        f = LegacyPlanningFulfiller()
        result = f.fulfill(self._make_wish("mentor the next generation"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "mentoring" in tags or "youth" in tags

    def test_has_reminder(self):
        f = LegacyPlanningFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = LegacyPlanningFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_chinese_keyword(self):
        f = LegacyPlanningFulfiller()
        result = f.fulfill(self._make_wish("我想留下遗产"), DetectorResults())
        assert len(result.recommendations) >= 1
