"""Tests for PetFriendlyFulfiller — pet-friendly place recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_pet_friendly import PetFriendlyFulfiller, PET_CATALOG, _match_candidates


class TestPetCatalog:
    def test_catalog_has_15_entries(self):
        assert len(PET_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in PET_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_has_outdoor_and_indoor_tags(self):
        outdoor = [i for i in PET_CATALOG if "outdoor" in i["tags"]]
        indoor = [i for i in PET_CATALOG if "indoor" in i["tags"]]
        assert len(outdoor) >= 3
        assert len(indoor) >= 3


class TestPetFriendlyFulfiller:
    def _make_wish(self, text="I want to take my dog somewhere") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="pet_friendly",
        )

    def test_returns_l2_result(self):
        f = PetFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = PetFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = PetFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "pet_friendly"

    def test_has_reminder(self):
        f = PetFriendlyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_outdoor_keyword_boosts_outdoor(self):
        candidates = _match_candidates("I want to go to a dog park", DetectorResults())
        dog_park = [c for c in candidates if c["category"] == "dog_park"]
        assert len(dog_park) >= 1
        assert dog_park[0]["_emotion_boost"] > 0
