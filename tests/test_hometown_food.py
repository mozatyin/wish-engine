"""Tests for HometownFoodFulfiller — authentic hometown cuisine for diaspora users."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_hometown_food import (
    HometownFoodFulfiller,
    HOMETOWN_FOOD_CATALOG,
    _match_candidates,
)


class TestHometownFoodCatalog:
    def test_catalog_has_25_entries(self):
        assert len(HOMETOWN_FOOD_CATALOG) >= 25

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags", "emotion_match"}
        for item in HOMETOWN_FOOD_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_catalog_has_diverse_cuisines(self):
        categories = {item["category"] for item in HOMETOWN_FOOD_CATALOG}
        assert len(categories) >= 20


class TestHometownFoodFulfiller:
    def _make_wish(self, text="想吃家乡菜") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="hometown_food",
        )

    def test_returns_l2_result(self):
        f = HometownFoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = HometownFoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_halal_filter(self):
        candidates = _match_candidates("أبي أكل حلال من بلدي", DetectorResults())
        for c in candidates:
            assert "halal" in c.get("tags", [])

    def test_homesick_boosts_comfort(self):
        f = HometownFoodFulfiller()
        result = f.fulfill(self._make_wish("I miss home, want authentic food"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_map_data(self):
        f = HometownFoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "restaurant"

    def test_has_reminder(self):
        f = HometownFoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_celebration_emotion(self):
        f = HometownFoodFulfiller()
        result = f.fulfill(self._make_wish("想庆祝，吃正宗家乡菜"), DetectorResults())
        assert len(result.recommendations) >= 1
