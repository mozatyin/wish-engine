"""Tests for MedicalFulfiller — medical resource navigation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_medical import MedicalFulfiller, MEDICAL_CATALOG, _match_candidates


class TestMedicalCatalog:
    def test_catalog_has_15_entries(self):
        assert len(MEDICAL_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in MEDICAL_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestMedicalFulfiller:
    def _make_wish(self, text="I need a doctor") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="medical",
        )

    def test_returns_l2_result(self):
        f = MedicalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = MedicalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = MedicalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "hospital"

    def test_has_reminder(self):
        f = MedicalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_traditional_values_boost_traditional_medicine(self):
        f = MedicalFulfiller()
        det = DetectorResults(values={"top_values": ["tradition"]})
        result = f.fulfill(self._make_wish("I want traditional medicine"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("traditional", "holistic", "cultural") for t in tags)

    def test_dental_keyword_matching(self):
        candidates = _match_candidates("I need a dentist", DetectorResults())
        dental = [c for c in candidates if c["category"] == "dental"]
        assert len(dental) >= 1
        assert dental[0]["_emotion_boost"] > 0

    def test_gentle_language_in_descriptions(self):
        """All descriptions should use gentle/calming language."""
        gentle_words = {"gentle", "caring", "safe", "compassionate", "warm", "reassuring",
                       "comfort", "soothing", "calm", "peaceful", "welcome", "good hands",
                       "help", "heal", "nourish", "restful", "understanding"}
        for item in MEDICAL_CATALOG:
            desc_lower = item["description"].lower()
            assert any(w in desc_lower for w in gentle_words), \
                f"{item['title']} description lacks gentle language"
