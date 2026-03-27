"""Tests for PersonalityGrowthFulfiller — growth exercises by weakest dimensions."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_personality_growth import PersonalityGrowthFulfiller, GROWTH_CATALOG


class TestGrowthCatalog:
    def test_catalog_has_15_entries(self):
        assert len(GROWTH_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty"}
        for item in GROWTH_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_15_categories(self):
        cats = {item["category"] for item in GROWTH_CATALOG}
        assert len(cats) == 15


class TestPersonalityGrowthFulfiller:
    def _make_wish(self, text="I want to grow") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="personality_growth",
        )

    def test_returns_l2_result(self):
        f = PersonalityGrowthFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = PersonalityGrowthFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_low_eq_targets_awareness(self):
        f = PersonalityGrowthFulfiller()
        det = DetectorResults(eq={"score": 0.2})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        # Should include at least one EQ-related category
        eq_cats = {"emotional_awareness", "empathy_building", "active_listening"}
        assert any(c in eq_cats for c in cats)

    def test_fragile_gets_gentle(self):
        f = PersonalityGrowthFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            assert rec.relevance_reason is not None

    def test_avoidant_attachment_targets_trust(self):
        f = PersonalityGrowthFulfiller()
        det = DetectorResults(attachment={"style": "avoidant"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        trust_cats = {"attachment_healing", "trust_building", "vulnerability_practice"}
        assert any(c in trust_cats for c in cats)

    def test_has_reminder(self):
        f = PersonalityGrowthFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_defensive_targets_anger(self):
        f = PersonalityGrowthFulfiller()
        det = DetectorResults(fragility={"pattern": "defensive"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        anger_cats = {"anger_management", "conflict_resolution", "forgiveness_practice"}
        assert any(c in anger_cats for c in cats)
