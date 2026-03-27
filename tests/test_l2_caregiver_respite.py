"""Tests for CaregiverRespiteFulfiller — respite care services."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_caregiver_respite import CaregiverRespiteFulfiller, RESPITE_CATALOG


class TestRespiteCatalog:
    def test_catalog_has_12_entries(self):
        assert len(RESPITE_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in RESPITE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_are_calming(self):
        for item in RESPITE_CATALOG:
            assert item["mood"] == "calming", f"{item['title']} should be calming"


class TestCaregiverRespiteFulfiller:
    def _make_wish(self, text="我需要照护喘息服务") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="caregiver_respite",
        )

    def test_returns_l2_result(self):
        f = CaregiverRespiteFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = CaregiverRespiteFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_nurse_keyword_match(self):
        f = CaregiverRespiteFulfiller()
        result = f.fulfill(self._make_wish("I need a temporary nurse"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "temporary_nurse" in categories

    def test_has_reminder(self):
        f = CaregiverRespiteFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = CaregiverRespiteFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = CaregiverRespiteFulfiller()
        result = f.fulfill(self._make_wish("أحتاج رعاية مؤقتة"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_weekend_keyword(self):
        f = CaregiverRespiteFulfiller()
        result = f.fulfill(self._make_wish("weekend respite care"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "weekend_respite" in categories
