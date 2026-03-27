"""Tests for FoodFulfiller — restaurant recommendation with emotion-to-food mapping."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_food import FoodFulfiller, FOOD_CATALOG, _match_candidates


class TestFoodCatalog:
    def test_catalog_not_empty(self):
        assert len(FOOD_CATALOG) >= 25

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags", "cuisine", "emotion_match"}
        for item in FOOD_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_catalog_has_diverse_cuisines(self):
        cuisines = {item["cuisine"] for item in FOOD_CATALOG}
        assert len(cuisines) >= 5

    def test_catalog_has_halal_options(self):
        halal_items = [i for i in FOOD_CATALOG if "halal" in i.get("tags", []) or "halal-option" in i.get("tags", [])]
        assert len(halal_items) >= 3


class TestFoodFulfiller:
    def _make_wish(self, text="想吃饭") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="food_recommendation",
        )

    def test_returns_l2_result(self):
        f = FoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_anxiety_gets_comfort_food(self):
        f = FoodFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        result = f.fulfill(self._make_wish("想吃comfort food"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in ("comfort_food", "dessert", "energizing") for c in categories)

    def test_joy_gets_celebration(self):
        f = FoodFulfiller()
        det = DetectorResults(emotion={"emotions": {"joy": 0.8}})
        result = f.fulfill(self._make_wish("想庆祝"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("celebration", "fancy", "social", "fun") for t in tags)

    def test_introvert_no_loud_social(self):
        f = FoodFulfiller()
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            # Introvert filter should remove loud+high social combos
            assert not ("loud" == rec.tags and "social" in rec.tags and "high" in rec.tags)

    def test_halal_tag_for_arabic_request(self):
        f = FoodFulfiller()
        result = f.fulfill(self._make_wish("أبي مطعم حلال"), DetectorResults())
        all_tags = []
        for r in result.recommendations:
            all_tags.extend(r.tags)
        assert any(t in ("halal", "halal-option", "arabic") for t in all_tags)

    def test_max_3(self):
        f = FoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = FoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_has_map_data(self):
        f = FoodFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "restaurant"

    def test_sadness_gets_sweet(self):
        f = FoodFulfiller()
        det = DetectorResults(emotion={"emotions": {"sadness": 0.7}})
        result = f.fulfill(self._make_wish("想吃甜点"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("sweet", "dessert", "indulgent", "chocolate") for t in tags)

    def test_anger_gets_spicy(self):
        f = FoodFulfiller()
        det = DetectorResults(emotion={"emotions": {"anger": 0.7}})
        result = f.fulfill(self._make_wish("想吃辣"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("spicy", "intense", "bbq", "curry") for t in tags)

    def test_chinese_cuisine_filter(self):
        candidates = _match_candidates("想吃中餐", DetectorResults())
        chinese = [c for c in candidates if "chinese" in c.get("tags", [])]
        assert len(chinese) >= 1
