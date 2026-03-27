"""Tests for SafeSpaceFulfiller — inclusive/safe venue recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_safe_spaces import SafeSpaceFulfiller, SAFE_SPACE_CATALOG


class TestSafeSpaceCatalog:
    def test_catalog_has_15_entries(self):
        assert len(SAFE_SPACE_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in SAFE_SPACE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_catalog_has_diverse_categories(self):
        categories = {item["category"] for item in SAFE_SPACE_CATALOG}
        expected = {"lgbtq_friendly", "women_only", "disability_accessible", "multicultural", "quiet_space", "therapy_friendly"}
        assert categories == expected

    def test_all_entries_have_safe_or_inclusive_tag(self):
        for item in SAFE_SPACE_CATALOG:
            tags = set(item.get("tags", []))
            assert tags & {"safe", "inclusive"}, f"{item['title']} missing safe/inclusive tag"


class TestSafeSpaceFulfiller:
    def _make_wish(self, text="I need a safe space") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="safe_space",
        )

    def test_returns_l2_result(self):
        f = SafeSpaceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = SafeSpaceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = SafeSpaceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_has_map_data(self):
        f = SafeSpaceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "safe_space"
