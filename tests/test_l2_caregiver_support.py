"""Tests for CaregiverSupportFulfiller — support groups and resources."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_caregiver_support import CaregiverSupportFulfiller, CAREGIVER_SUPPORT_CATALOG


class TestCaregiverSupportCatalog:
    def test_catalog_has_10_entries(self):
        assert len(CAREGIVER_SUPPORT_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in CAREGIVER_SUPPORT_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_are_calming(self):
        for item in CAREGIVER_SUPPORT_CATALOG:
            assert item["mood"] == "calming", f"{item['title']} should be calming"


class TestCaregiverSupportFulfiller:
    def _make_wish(self, text="照护者支持小组") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="caregiver_support",
        )

    def test_returns_l2_result(self):
        f = CaregiverSupportFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = CaregiverSupportFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_burnout_keyword_match(self):
        f = CaregiverSupportFulfiller()
        result = f.fulfill(self._make_wish("caregiver burnout help"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "burnout_recovery" in categories

    def test_has_reminder(self):
        f = CaregiverSupportFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = CaregiverSupportFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = CaregiverSupportFulfiller()
        result = f.fulfill(self._make_wish("دعم مقدمي الرعاية"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_therapy_keyword(self):
        f = CaregiverSupportFulfiller()
        result = f.fulfill(self._make_wish("caregiver therapy sessions"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "caregiver_therapy" in categories
