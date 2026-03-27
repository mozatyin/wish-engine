"""Tests for NeighborhoodFulfiller — local community connection recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_neighborhood import NeighborhoodFulfiller, NEIGHBORHOOD_CATALOG


class TestNeighborhoodCatalog:
    def test_catalog_has_12_entries(self):
        assert len(NEIGHBORHOOD_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in NEIGHBORHOOD_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestNeighborhoodFulfiller:
    def _make_wish(self, text="想融入社区") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="neighborhood",
        )

    def test_returns_l2_result(self):
        f = NeighborhoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = NeighborhoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_garden_keyword_match(self):
        f = NeighborhoodFulfiller()
        result = f.fulfill(self._make_wish("community garden"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "community_garden" in categories

    def test_carpool_keyword(self):
        f = NeighborhoodFulfiller()
        result = f.fulfill(self._make_wish("邻里拼车"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "carpool_group" in categories

    def test_has_reminder(self):
        f = NeighborhoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = NeighborhoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = NeighborhoodFulfiller()
        result = f.fulfill(self._make_wish("جيران"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_no_map_data(self):
        f = NeighborhoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None
