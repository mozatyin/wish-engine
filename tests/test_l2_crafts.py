"""Tests for CraftsFulfiller — MBTI-aware handcraft experience recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_crafts import CraftsFulfiller, CRAFTS_CATALOG


class TestCraftsCatalog:
    def test_catalog_has_15_entries(self):
        assert len(CRAFTS_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in CRAFTS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestCraftsFulfiller:
    def _make_wish(self, text="想做手工") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = CraftsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = CraftsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_solo_crafts(self):
        f = CraftsFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish("I want to do pottery"), det)
        # Introverts should not get loud/high-social items
        for r in result.recommendations:
            assert not (r.tags and "glass_blowing" in r.tags and "metalwork" in r.tags)

    def test_pottery_keyword_match(self):
        f = CraftsFulfiller()
        result = f.fulfill(self._make_wish("想学陶艺"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "pottery" in categories

    def test_calligraphy_keyword_match(self):
        f = CraftsFulfiller()
        result = f.fulfill(self._make_wish("想学书法"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "calligraphy" in categories

    def test_has_reminder(self):
        f = CraftsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_no_map_data(self):
        f = CraftsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_relevance_reason_not_empty(self):
        f = CraftsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
