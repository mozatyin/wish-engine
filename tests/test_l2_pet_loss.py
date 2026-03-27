"""Tests for PetLossFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_pet_loss import PetLossFulfiller, PET_LOSS_CATALOG


class TestPetLossCatalog:
    def test_catalog_has_10_entries(self):
        assert len(PET_LOSS_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in PET_LOSS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestPetLossFulfiller:
    def _make_wish(self, text="My dog passed away") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="pet_loss",
        )

    def test_returns_l2_result(self):
        f = PetLossFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = PetLossFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_pet_loss_keyword(self):
        f = PetLossFulfiller()
        result = f.fulfill(self._make_wish("pet loss grief"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("pet_loss" in t for t in tags)

    def test_rainbow_bridge_keyword(self):
        f = PetLossFulfiller()
        result = f.fulfill(self._make_wish("rainbow bridge"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_chinese_keyword(self):
        f = PetLossFulfiller()
        result = f.fulfill(self._make_wish("宠物去世了"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = PetLossFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = PetLossFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
