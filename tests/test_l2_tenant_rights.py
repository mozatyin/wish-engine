"""Tests for TenantRightsFulfiller — tenant rights and rental protections."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_tenant_rights import TenantRightsFulfiller, TENANT_RIGHTS_CATALOG


class TestTenantRightsCatalog:
    def test_catalog_has_10_entries(self):
        assert len(TENANT_RIGHTS_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in TENANT_RIGHTS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_are_calming(self):
        for item in TENANT_RIGHTS_CATALOG:
            assert item["mood"] == "calming", f"{item['title']} should be calming"


class TestTenantRightsFulfiller:
    def _make_wish(self, text="租客权益保护") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="tenant_rights",
        )

    def test_returns_l2_result(self):
        f = TenantRightsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = TenantRightsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_eviction_keyword_match(self):
        f = TenantRightsFulfiller()
        result = f.fulfill(self._make_wish("facing eviction what are my rights"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "eviction_defense" in categories

    def test_has_reminder(self):
        f = TenantRightsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = TenantRightsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = TenantRightsFulfiller()
        result = f.fulfill(self._make_wish("حقوق إيجار"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_deposit_keyword(self):
        f = TenantRightsFulfiller()
        result = f.fulfill(self._make_wish("how to get my deposit back"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "deposit_recovery" in categories

    def test_landlord_keyword(self):
        f = TenantRightsFulfiller()
        result = f.fulfill(self._make_wish("房东不退押金"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
