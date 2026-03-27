"""Tests for RootsJourneyFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_roots_journey import RootsJourneyFulfiller, ROOTS_CATALOG


class TestRootsCatalog:
    def test_catalog_has_10_entries(self):
        assert len(ROOTS_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in ROOTS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestRootsJourneyFulfiller:
    def _make_wish(self, text="I want to find my roots") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="roots_journey",
        )

    def test_returns_l2_result(self):
        f = RootsJourneyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = RootsJourneyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_dna_keyword(self):
        f = RootsJourneyFulfiller()
        result = f.fulfill(self._make_wish("dna ancestry test"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "dna" in tags or "ancestry" in tags

    def test_homeland_keyword(self):
        f = RootsJourneyFulfiller()
        result = f.fulfill(self._make_wish("visit my homeland"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "homeland" in tags or "travel" in tags

    def test_has_reminder(self):
        f = RootsJourneyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = RootsJourneyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_chinese_keyword(self):
        f = RootsJourneyFulfiller()
        result = f.fulfill(self._make_wish("我想寻根"), DetectorResults())
        assert len(result.recommendations) >= 1
