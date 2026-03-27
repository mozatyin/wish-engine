"""Tests for TravelFulfiller — travel destination recommendations with personality matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_travel import TravelFulfiller, DESTINATION_CATALOG


class TestDestinationCatalog:
    def test_catalog_has_20_entries(self):
        assert len(DESTINATION_CATALOG) == 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in DESTINATION_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestTravelFulfiller:
    def _make_wish(self, text="想去旅行") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="travel_recommendation",
        )

    def test_returns_l2_result(self):
        f = TravelFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = TravelFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_quiet_destinations(self):
        f = TravelFulfiller()
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("solitude", "quiet", "nature") for t in tags)

    def test_tradition_values_boost_heritage(self):
        f = TravelFulfiller()
        det = DetectorResults(values={"top_values": ["tradition"]})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("heritage", "ancient", "spiritual") for t in tags)

    def test_adventure_keyword_finds_adventure(self):
        f = TravelFulfiller()
        result = f.fulfill(self._make_wish("I want adventure travel"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "adventure" in tags

    def test_has_reminder(self):
        f = TravelFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = TravelFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
