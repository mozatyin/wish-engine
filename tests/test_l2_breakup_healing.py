"""Tests for BreakupHealingFulfiller — attachment-aware healing recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_breakup_healing import BreakupHealingFulfiller, HEALING_CATALOG


class TestHealingCatalog:
    def test_catalog_has_15_entries(self):
        assert len(HEALING_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in HEALING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestBreakupHealingFulfiller:
    def _make_wish(self, text="刚分手，很难过") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="healing_recommendation",
        )

    def test_returns_l2_result(self):
        f = BreakupHealingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = BreakupHealingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_anxious_attachment_gets_structured(self):
        f = BreakupHealingFulfiller()
        det = DetectorResults(attachment={"style": "anxious"})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("structured", "routine", "guided") for t in tags)

    def test_avoidant_attachment_gets_space(self):
        f = BreakupHealingFulfiller()
        det = DetectorResults(attachment={"style": "avoidant"})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("space", "solo", "self_paced") for t in tags)

    def test_sadness_emotion_triggers_gentle(self):
        f = BreakupHealingFulfiller()
        det = DetectorResults(emotion={"emotions": {"sadness": 0.7}})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("gentle", "nature", "creative") for t in tags)

    def test_has_reminder(self):
        f = BreakupHealingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_new_area_tagged(self):
        """Healing activities should include new_area options."""
        has_new_area = any("new_area" in item["tags"] for item in HEALING_CATALOG)
        assert has_new_area

    def test_relevance_reason_not_empty(self):
        f = BreakupHealingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
