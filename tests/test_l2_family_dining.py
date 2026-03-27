"""Tests for FamilyDiningFulfiller — large-group and kids-friendly dining."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_family_dining import FamilyDiningFulfiller, FAMILY_DINING_CATALOG


class TestFamilyDiningCatalog:
    def test_catalog_has_12_entries(self):
        assert len(FAMILY_DINING_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in FAMILY_DINING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestFamilyDiningFulfiller:
    def _make_wish(self, text="家庭聚餐") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="family_dining",
        )

    def test_returns_l2_result(self):
        f = FamilyDiningFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = FamilyDiningFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_hotpot_keyword_match(self):
        f = FamilyDiningFulfiller()
        result = f.fulfill(self._make_wish("家庭火锅聚餐"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "hotpot_family" in categories

    def test_private_room_keyword(self):
        f = FamilyDiningFulfiller()
        result = f.fulfill(self._make_wish("需要包间聚餐"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "private_room" in categories

    def test_has_reminder(self):
        f = FamilyDiningFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = FamilyDiningFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_halal_keyword(self):
        f = FamilyDiningFulfiller()
        result = f.fulfill(self._make_wish("halal family restaurant"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "halal_family" in categories

    def test_no_map_data(self):
        f = FamilyDiningFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None
