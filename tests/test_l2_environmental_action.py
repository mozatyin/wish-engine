"""Tests for EnvironmentalActionFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_environmental_action import EnvironmentalActionFulfiller, ENVIRONMENTAL_CATALOG


class TestEnvironmentalCatalog:
    def test_catalog_has_10_entries(self):
        assert len(ENVIRONMENTAL_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in ENVIRONMENTAL_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestEnvironmentalActionFulfiller:
    def _make_wish(self, text="I want to help the environment") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="environmental_action",
        )

    def test_returns_l2_result(self):
        f = EnvironmentalActionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = EnvironmentalActionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_carbon_keyword(self):
        f = EnvironmentalActionFulfiller()
        result = f.fulfill(self._make_wish("calculate my carbon footprint"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "carbon" in tags or "calculator" in tags

    def test_tree_keyword(self):
        f = EnvironmentalActionFulfiller()
        result = f.fulfill(self._make_wish("plant a tree"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "trees" in tags or "planting" in tags

    def test_has_reminder(self):
        f = EnvironmentalActionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = EnvironmentalActionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
