"""Tests for StartupResourceFulfiller — startup resource recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_startup_resources import StartupResourceFulfiller, STARTUP_CATALOG


class TestStartupCatalog:
    def test_catalog_has_15_entries(self):
        assert len(STARTUP_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in STARTUP_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestStartupResourceFulfiller:
    def _make_wish(self, text="想创业") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.CAREER_DIRECTION,
            level=WishLevel.L2, fulfillment_strategy="startup_recommendation",
        )

    def test_returns_l2_result(self):
        f = StartupResourceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = StartupResourceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_self_direction_values_boost(self):
        f = StartupResourceFulfiller()
        det = DetectorResults(values={"top_values": ["self-direction"]})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("solo_founder", "mentorship", "community") for t in tags)

    def test_funding_keyword(self):
        f = StartupResourceFulfiller()
        result = f.fulfill(self._make_wish("need startup funding"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "funding" in tags

    def test_accelerator_keyword(self):
        f = StartupResourceFulfiller()
        result = f.fulfill(self._make_wish("looking for accelerator program"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "accelerator" in tags

    def test_has_reminder(self):
        f = StartupResourceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = StartupResourceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
