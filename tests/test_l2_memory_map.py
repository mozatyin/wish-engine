"""Tests for MemoryMapFulfiller — personal memory place recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_memory_map import MemoryMapFulfiller, MEMORY_MAP_CATALOG


class TestMemoryMapCatalog:
    def test_catalog_has_12_entries(self):
        assert len(MEMORY_MAP_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in MEMORY_MAP_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestMemoryMapFulfiller:
    def _make_wish(self, text="想记录回忆") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="memory_map",
        )

    def test_returns_l2_result(self):
        f = MemoryMapFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = MemoryMapFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_childhood_keyword_match(self):
        f = MemoryMapFulfiller()
        result = f.fulfill(self._make_wish("childhood memories童年"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "childhood_place" in categories

    def test_first_date_keyword(self):
        f = MemoryMapFulfiller()
        result = f.fulfill(self._make_wish("remember our first date"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "first_date_spot" in categories

    def test_has_reminder(self):
        f = MemoryMapFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = MemoryMapFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = MemoryMapFulfiller()
        result = f.fulfill(self._make_wish("ذكرى جميلة"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_no_map_data(self):
        f = MemoryMapFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None
