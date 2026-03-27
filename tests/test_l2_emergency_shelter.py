"""Tests for EmergencyShelterFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_emergency_shelter import EmergencyShelterFulfiller, SHELTER_CATALOG


class TestShelterCatalog:
    def test_catalog_has_10_entries(self):
        assert len(SHELTER_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in SHELTER_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestEmergencyShelterFulfiller:
    def _make_wish(self, text="I need emergency shelter") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="emergency_shelter",
        )

    def test_returns_l2_result(self):
        f = EmergencyShelterFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = EmergencyShelterFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_shelter_keyword(self):
        f = EmergencyShelterFulfiller()
        result = f.fulfill(self._make_wish("find shelter"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("shelter" in t for t in tags)

    def test_homeless_keyword(self):
        f = EmergencyShelterFulfiller()
        result = f.fulfill(self._make_wish("I am homeless"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_chinese_keyword(self):
        f = EmergencyShelterFulfiller()
        result = f.fulfill(self._make_wish("庇护所"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = EmergencyShelterFulfiller()
        result = f.fulfill(self._make_wish("مأوى"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = EmergencyShelterFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
