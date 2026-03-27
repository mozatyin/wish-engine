"""Tests for OralHistoryFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_oral_history import OralHistoryFulfiller, ORAL_HISTORY_CATALOG


class TestOralHistoryCatalog:
    def test_catalog_has_10_entries(self):
        assert len(ORAL_HISTORY_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in ORAL_HISTORY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestOralHistoryFulfiller:
    def _make_wish(self, text="record oral history") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="oral_history",
        )

    def test_returns_l2_result(self):
        f = OralHistoryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = OralHistoryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_recipe_keyword(self):
        f = OralHistoryFulfiller()
        result = f.fulfill(self._make_wish("preserve family recipes"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "recipe" in tags or "food" in tags

    def test_photo_keyword(self):
        f = OralHistoryFulfiller()
        result = f.fulfill(self._make_wish("digitize old photos"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "photo" in tags or "digitization" in tags

    def test_has_reminder(self):
        f = OralHistoryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = OralHistoryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
