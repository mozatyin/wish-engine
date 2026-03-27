"""Tests for ImmigrationFulfiller — immigration services and integration."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_immigration import ImmigrationFulfiller, IMMIGRATION_CATALOG


class TestImmigrationCatalog:
    def test_catalog_has_12_entries(self):
        assert len(IMMIGRATION_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in IMMIGRATION_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_are_calming(self):
        for item in IMMIGRATION_CATALOG:
            assert item["mood"] == "calming", f"{item['title']} should be calming"


class TestImmigrationFulfiller:
    def _make_wish(self, text="移民签证咨询") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="immigration",
        )

    def test_returns_l2_result(self):
        f = ImmigrationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = ImmigrationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_visa_keyword_match(self):
        f = ImmigrationFulfiller()
        result = f.fulfill(self._make_wish("I need visa information"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "visa_info" in categories

    def test_has_reminder(self):
        f = ImmigrationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = ImmigrationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = ImmigrationFulfiller()
        result = f.fulfill(self._make_wish("هجرة ولجوء"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_refugee_keyword(self):
        f = ImmigrationFulfiller()
        result = f.fulfill(self._make_wish("refugee services needed"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "refugee_services" in categories

    def test_chinese_visa_keyword(self):
        f = ImmigrationFulfiller()
        result = f.fulfill(self._make_wish("签证申请流程"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "visa_info" in categories
