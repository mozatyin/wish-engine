"""Tests for PetTrainingFulfiller — pet behavior and training recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_pet_training import PetTrainingFulfiller, PET_TRAINING_CATALOG


class TestPetTrainingCatalog:
    def test_catalog_has_10_entries(self):
        assert len(PET_TRAINING_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in PET_TRAINING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestPetTrainingFulfiller:
    def _make_wish(self, text="想训练我的狗") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="pet_training",
        )

    def test_returns_l2_result(self):
        f = PetTrainingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = PetTrainingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_obedience_keyword_match(self):
        f = PetTrainingFulfiller()
        result = f.fulfill(self._make_wish("dog obedience training"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "dog_obedience" in categories

    def test_cat_keyword_match(self):
        f = PetTrainingFulfiller()
        result = f.fulfill(self._make_wish("cat behavior problem猫"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "cat_behavior" in categories

    def test_has_reminder(self):
        f = PetTrainingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = PetTrainingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = PetTrainingFulfiller()
        result = f.fulfill(self._make_wish("تدريب الكلب"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_no_map_data(self):
        f = PetTrainingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None
