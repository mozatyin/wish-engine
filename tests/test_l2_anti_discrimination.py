"""Tests for AntiDiscriminationFulfiller — anti-discrimination resources."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_anti_discrimination import AntiDiscriminationFulfiller, ANTI_DISCRIMINATION_CATALOG


class TestAntiDiscriminationCatalog:
    def test_catalog_has_10_entries(self):
        assert len(ANTI_DISCRIMINATION_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in ANTI_DISCRIMINATION_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_are_calming(self):
        for item in ANTI_DISCRIMINATION_CATALOG:
            assert item["mood"] == "calming", f"{item['title']} should be calming"


class TestAntiDiscriminationFulfiller:
    def _make_wish(self, text="遭遇歧视怎么办") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="anti_discrimination",
        )

    def test_returns_l2_result(self):
        f = AntiDiscriminationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = AntiDiscriminationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_racism_keyword_match(self):
        f = AntiDiscriminationFulfiller()
        result = f.fulfill(self._make_wish("I experienced racism at work"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert any(c in categories for c in ["filing_complaint", "hate_crime_report"])

    def test_has_reminder(self):
        f = AntiDiscriminationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = AntiDiscriminationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = AntiDiscriminationFulfiller()
        result = f.fulfill(self._make_wish("تمييز عنصري"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_bias_keyword(self):
        f = AntiDiscriminationFulfiller()
        result = f.fulfill(self._make_wish("report a bias incident"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "bias_incident_report" in categories

    def test_hate_crime_keyword(self):
        f = AntiDiscriminationFulfiller()
        result = f.fulfill(self._make_wish("how to report a hate crime"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "hate_crime_report" in categories
