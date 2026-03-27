"""Tests for CaregiverEmotionalFulfiller — emotional first aid for caregivers."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_caregiver_emotional import CaregiverEmotionalFulfiller, CAREGIVER_EMOTIONAL_CATALOG


class TestCaregiverEmotionalCatalog:
    def test_catalog_has_10_entries(self):
        assert len(CAREGIVER_EMOTIONAL_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in CAREGIVER_EMOTIONAL_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_are_quiet_and_calming(self):
        for item in CAREGIVER_EMOTIONAL_CATALOG:
            assert item["noise"] == "quiet", f"{item['title']} should be quiet"
            assert item["mood"] == "calming", f"{item['title']} should be calming"


class TestCaregiverEmotionalFulfiller:
    def _make_wish(self, text="照护者情绪急救") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.EMOTIONAL_PROCESSING,
            level=WishLevel.L2, fulfillment_strategy="caregiver_emotional",
        )

    def test_returns_l2_result(self):
        f = CaregiverEmotionalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = CaregiverEmotionalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_guilt_keyword_match(self):
        f = CaregiverEmotionalFulfiller()
        result = f.fulfill(self._make_wish("I feel so much guilt as a caregiver"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "guilt_processing" in categories

    def test_has_reminder(self):
        f = CaregiverEmotionalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = CaregiverEmotionalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_chinese_guilt_keyword(self):
        f = CaregiverEmotionalFulfiller()
        result = f.fulfill(self._make_wish("照护内疚感太强了"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "guilt_processing" in categories

    def test_breathing_keyword(self):
        f = CaregiverEmotionalFulfiller()
        result = f.fulfill(self._make_wish("caregiver breathing exercise"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "caregiver_breathing" in categories

    def test_burnout_keyword(self):
        f = CaregiverEmotionalFulfiller()
        result = f.fulfill(self._make_wish("我太疲惫了"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "compassion_fatigue_help" in categories
