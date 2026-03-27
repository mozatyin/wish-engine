"""Tests for VolunteerFulfiller — values-driven volunteer opportunity matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_volunteer import VolunteerFulfiller, VOLUNTEER_CATALOG


class TestVolunteerCatalog:
    def test_catalog_has_15_entries(self):
        assert len(VOLUNTEER_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in VOLUNTEER_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestVolunteerFulfiller:
    def _make_wish(self, text="想做志愿者") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = VolunteerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = VolunteerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_benevolence_values_match_helping(self):
        f = VolunteerFulfiller()
        det = DetectorResults(values={"top_values": ["benevolence"]})
        result = f.fulfill(self._make_wish("I want to volunteer"), det)
        all_tags = []
        for r in result.recommendations:
            all_tags.extend(r.tags)
        assert "helping" in all_tags

    def test_universalism_matches_systemic(self):
        f = VolunteerFulfiller()
        det = DetectorResults(values={"top_values": ["universalism"]})
        result = f.fulfill(self._make_wish("volunteer"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in ("environmental", "refugee_support", "coding_for_good", "disaster_relief") for c in categories)

    def test_environment_keyword_match(self):
        f = VolunteerFulfiller()
        result = f.fulfill(self._make_wish("环保志愿"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "environmental" in categories

    def test_has_reminder(self):
        f = VolunteerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_no_map_data(self):
        f = VolunteerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_relevance_reason_not_empty(self):
        f = VolunteerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
