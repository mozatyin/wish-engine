"""Tests for LegalAidFulfiller — legal aid navigation."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_legal_aid import LegalAidFulfiller, LEGAL_AID_CATALOG


class TestLegalAidCatalog:
    def test_catalog_has_15_entries(self):
        assert len(LEGAL_AID_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in LEGAL_AID_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_are_calming(self):
        for item in LEGAL_AID_CATALOG:
            assert item["mood"] == "calming", f"{item['title']} should be calming"


class TestLegalAidFulfiller:
    def _make_wish(self, text="我需要法律援助") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="legal_aid",
        )

    def test_returns_l2_result(self):
        f = LegalAidFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = LegalAidFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_tenant_keyword_match(self):
        f = LegalAidFulfiller()
        result = f.fulfill(self._make_wish("I need a tenant lawyer"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "tenant_lawyer" in categories

    def test_has_reminder(self):
        f = LegalAidFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = LegalAidFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = LegalAidFulfiller()
        result = f.fulfill(self._make_wish("أحتاج محامي"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_immigration_keyword(self):
        f = LegalAidFulfiller()
        result = f.fulfill(self._make_wish("immigration lawyer needed"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "immigration_lawyer" in categories

    def test_mediation_keyword(self):
        f = LegalAidFulfiller()
        result = f.fulfill(self._make_wish("mediation for neighbor dispute"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "mediation_service" in categories
