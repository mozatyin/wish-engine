"""Tests for CyberbullyingFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_cyberbullying import CyberbullyingFulfiller, CYBERBULLYING_CATALOG


class TestCyberbullyingCatalog:
    def test_catalog_has_10_entries(self):
        assert len(CYBERBULLYING_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in CYBERBULLYING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestCyberbullyingFulfiller:
    def _make_wish(self, text="I am being cyberbullied") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="cyberbullying",
        )

    def test_returns_l2_result(self):
        f = CyberbullyingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = CyberbullyingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_evidence_keyword(self):
        f = CyberbullyingFulfiller()
        result = f.fulfill(self._make_wish("how to collect evidence"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "evidence" in tags or "documentation" in tags

    def test_block_keyword(self):
        f = CyberbullyingFulfiller()
        result = f.fulfill(self._make_wish("how to block someone"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "blocking" in tags or "safety" in tags

    def test_has_reminder(self):
        f = CyberbullyingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = CyberbullyingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
