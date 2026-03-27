"""Tests for ElderlyCareFulfiller — gentle, accessible activity recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_elderly_care import ElderlyCareFulfiller, ELDERLY_CATALOG


class TestElderlyCatalog:
    def test_catalog_has_12_entries(self):
        assert len(ELDERLY_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in ELDERLY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_are_gentle(self):
        for item in ELDERLY_CATALOG:
            assert item["noise"] in ("quiet", "moderate"), f"{item['title']} too noisy for elderly"


class TestElderlyCareFulfiller:
    def _make_wish(self, text="带老人出去走走") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="elderly_care",
        )

    def test_returns_l2_result(self):
        f = ElderlyCareFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = ElderlyCareFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_tai_chi_keyword_match(self):
        f = ElderlyCareFulfiller()
        result = f.fulfill(self._make_wish("想带爸妈去打太极"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "tai_chi" in categories

    def test_has_reminder(self):
        f = ElderlyCareFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = ElderlyCareFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = ElderlyCareFulfiller()
        result = f.fulfill(self._make_wish("أنشطة كبار السن"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_park_keyword(self):
        f = ElderlyCareFulfiller()
        result = f.fulfill(self._make_wish("take senior to the park"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert any(c in categories for c in ["quiet_park_bench", "slow_walk_trail"])

    def test_no_map_data(self):
        f = ElderlyCareFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None
