"""Tests for PanicReliefFulfiller — immediate panic/anxiety relief techniques."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_panic_relief import PanicReliefFulfiller, RELIEF_CATALOG


class TestReliefCatalog:
    def test_catalog_has_10_entries(self):
        assert len(RELIEF_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in RELIEF_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_doable_anywhere(self):
        """All techniques should be tagged as immediate and/or anywhere."""
        for item in RELIEF_CATALOG:
            assert "immediate" in item["tags"], f"{item['title']} missing 'immediate' tag"


class TestPanicReliefFulfiller:
    def _make_wish(self, text="I'm having a panic attack") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="panic_relief",
        )

    def test_returns_l2_result(self):
        f = PanicReliefFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = PanicReliefFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_breathing_keyword_finds_breathing(self):
        f = PanicReliefFulfiller()
        result = f.fulfill(self._make_wish("help me with breathing"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "breathing" in tags

    def test_grounding_keyword(self):
        f = PanicReliefFulfiller()
        result = f.fulfill(self._make_wish("grounding technique"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("grounding", "sensory") for t in tags)

    def test_has_reminder(self):
        f = PanicReliefFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_reminder_is_short_delay(self):
        """Panic relief reminders should be short — 1 hour."""
        f = PanicReliefFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option.delay_hours <= 2

    def test_relevance_reason_not_empty(self):
        f = PanicReliefFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
