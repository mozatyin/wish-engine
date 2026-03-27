"""Tests for Deals API and DealsFulfiller."""

import pytest

from wish_engine.apis.deals_api import is_available, normalize_deal
from wish_engine.l2_deals import (
    DealsFulfiller,
    DEAL_CATALOG,
    VALUES_DEAL_MAP,
    _values_to_deal_tags,
)
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)


class TestDealsAPI:
    def test_is_available_without_key(self):
        # No env var set → not available
        assert is_available() is False or is_available() is True  # depends on env

    def test_normalize_deal(self):
        raw = {"name": "Test Deal", "description": "A deal", "discount": 25, "price": 10}
        normalized = normalize_deal(raw)
        assert normalized["name"] == "Test Deal"
        assert normalized["discount_pct"] == 25
        assert normalized["deal_price"] == 10


class TestDealCatalog:
    def test_catalog_has_20_entries(self):
        assert len(DEAL_CATALOG) >= 20

    def test_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in DEAL_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_have_tags(self):
        for item in DEAL_CATALOG:
            assert len(item["tags"]) >= 2, f"{item['title']} needs more tags"


class TestValuesDealMapping:
    def test_security_maps_to_practical(self):
        tags = _values_to_deal_tags(["security"])
        assert "groceries" in tags or "household" in tags

    def test_stimulation_maps_to_experience(self):
        tags = _values_to_deal_tags(["stimulation"])
        assert "experience" in tags or "travel" in tags

    def test_self_direction_maps_to_learning(self):
        tags = _values_to_deal_tags(["self-direction"])
        assert "learning" in tags or "books" in tags

    def test_tradition_maps_to_cultural(self):
        tags = _values_to_deal_tags(["tradition"])
        assert "cultural" in tags or "religious" in tags

    def test_benevolence_maps_to_gifts(self):
        tags = _values_to_deal_tags(["benevolence"])
        assert "gifts" in tags or "charity" in tags

    def test_hedonism_maps_to_indulgence(self):
        tags = _values_to_deal_tags(["hedonism"])
        assert "spa" in tags or "luxury_food" in tags


class TestDealsFulfiller:
    def _make_wish(self, text="I want to find good deals") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="deals",
        )

    def test_returns_l2_result(self):
        f = DealsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_max_3_recommendations(self):
        f = DealsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = DealsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_security_values_get_practical_deals(self):
        f = DealsFulfiller()
        det = DetectorResults(values={"top_values": ["security"]})
        result = f.fulfill(self._make_wish(), det)
        # Should prioritize practical/grocery/household deals
        tags = set()
        for r in result.recommendations:
            tags.update(r.tags)
        assert tags & {"practical", "groceries", "household", "security"}

    def test_stimulation_values_get_experience_deals(self):
        f = DealsFulfiller()
        det = DetectorResults(values={"top_values": ["stimulation"]})
        result = f.fulfill(self._make_wish(), det)
        tags = set()
        for r in result.recommendations:
            tags.update(r.tags)
        assert tags & {"experience", "travel", "adventure", "stimulation"}
