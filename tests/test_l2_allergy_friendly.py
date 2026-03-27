"""Tests for AllergyFriendlyFulfiller — allergy-safe dining recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_allergy_friendly import (
    AllergyFriendlyFulfiller,
    ALLERGY_CATALOG,
    _match_candidates,
)


class TestAllergyCatalog:
    def test_catalog_has_12_entries(self):
        assert len(ALLERGY_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in ALLERGY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_have_tags(self):
        for item in ALLERGY_CATALOG:
            assert len(item["tags"]) >= 2, f"{item['title']} needs more tags"


class TestAllergyFriendlyFulfiller:
    def _make_wish(self, text="I need gluten free restaurants") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="allergy_friendly",
        )

    def test_returns_l2_result(self):
        f = AllergyFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = AllergyFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = AllergyFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "allergy_friendly"

    def test_gluten_keyword_boosts(self):
        candidates = _match_candidates("gluten free restaurant", DetectorResults())
        gf = [c for c in candidates if c["category"] == "gluten_free_restaurant"]
        assert len(gf) >= 1
        assert gf[0]["_emotion_boost"] > 0

    def test_vegan_keyword_boosts(self):
        candidates = _match_candidates("vegan plant-based dining", DetectorResults())
        vegan = [c for c in candidates if c["category"] == "vegan_restaurant"]
        assert len(vegan) >= 1
        assert vegan[0]["_emotion_boost"] > 0

    def test_halal_keyword_boosts(self):
        candidates = _match_candidates("halal certified food", DetectorResults())
        halal = [c for c in candidates if c["category"] == "halal_certified"]
        assert len(halal) >= 1
        assert halal[0]["_emotion_boost"] > 0

    def test_has_reminder(self):
        f = AllergyFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
