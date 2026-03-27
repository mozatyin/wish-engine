"""Tests for LaborRightsFulfiller — labor rights and worker protections."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_labor_rights import LaborRightsFulfiller, LABOR_RIGHTS_CATALOG


class TestLaborRightsCatalog:
    def test_catalog_has_12_entries(self):
        assert len(LABOR_RIGHTS_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in LABOR_RIGHTS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_are_calming(self):
        for item in LABOR_RIGHTS_CATALOG:
            assert item["mood"] == "calming", f"{item['title']} should be calming"


class TestLaborRightsFulfiller:
    def _make_wish(self, text="劳动权益咨询") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="labor_rights",
        )

    def test_returns_l2_result(self):
        f = LaborRightsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = LaborRightsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_overtime_keyword_match(self):
        f = LaborRightsFulfiller()
        result = f.fulfill(self._make_wish("加班费怎么算"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "overtime_calculator" in categories

    def test_has_reminder(self):
        f = LaborRightsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = LaborRightsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = LaborRightsFulfiller()
        result = f.fulfill(self._make_wish("حقوق عمال"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_harassment_keyword(self):
        f = LaborRightsFulfiller()
        result = f.fulfill(self._make_wish("workplace harassment help"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "harassment_report" in categories

    def test_wage_keyword(self):
        f = LaborRightsFulfiller()
        result = f.fulfill(self._make_wish("欠薪举报"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "wage_theft_report" in categories
