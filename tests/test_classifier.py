"""Tests for Wish Classifier — pure rule-based routing."""

import pytest

from wish_engine.models import (
    ClassifiedWish,
    DetectedWish,
    WishLevel,
    WishType,
)
from wish_engine.classifier import classify, classify_batch, WISH_TYPES, FULFILLMENT_STRATEGIES


# ── Level routing ────────────────────────────────────────────────────────────


class TestLevelRouting:
    """Every WishType maps to exactly one level."""

    @pytest.mark.parametrize("wish_type,expected_level", [
        (WishType.SELF_UNDERSTANDING, WishLevel.L1),
        (WishType.SELF_EXPRESSION, WishLevel.L1),
        (WishType.RELATIONSHIP_INSIGHT, WishLevel.L1),
        (WishType.EMOTIONAL_PROCESSING, WishLevel.L1),
        (WishType.LIFE_REFLECTION, WishLevel.L1),
        (WishType.LEARN_SKILL, WishLevel.L2),
        (WishType.FIND_PLACE, WishLevel.L2),
        (WishType.FIND_RESOURCE, WishLevel.L2),
        (WishType.CAREER_DIRECTION, WishLevel.L2),
        (WishType.HEALTH_WELLNESS, WishLevel.L2),
        (WishType.FIND_COMPANION, WishLevel.L3),
        (WishType.FIND_MENTOR, WishLevel.L3),
        (WishType.SKILL_EXCHANGE, WishLevel.L3),
        (WishType.SHARED_EXPERIENCE, WishLevel.L3),
        (WishType.EMOTIONAL_SUPPORT, WishLevel.L3),
    ])
    def test_type_to_level(self, wish_type, expected_level):
        wish = DetectedWish(
            wish_text="test",
            wish_type=wish_type,
            confidence=0.9,
            source_intention_id="test_id",
        )
        result = classify(wish)
        assert result.level == expected_level

    def test_all_types_covered(self):
        """Every WishType has a mapping."""
        for wt in WishType:
            assert wt in WISH_TYPES, f"Missing mapping for {wt}"

    def test_all_types_have_strategy(self):
        """Every WishType has a fulfillment strategy."""
        for wt in WishType:
            assert wt in FULFILLMENT_STRATEGIES, f"Missing strategy for {wt}"


# ── Strategy mapping ─────────────────────────────────────────────────────────


class TestStrategyMapping:
    @pytest.mark.parametrize("wish_type,expected_strategy", [
        (WishType.SELF_UNDERSTANDING, "personalized_insight"),
        (WishType.SELF_EXPRESSION, "assisted_writing"),
        (WishType.RELATIONSHIP_INSIGHT, "bond_analysis"),
        (WishType.EMOTIONAL_PROCESSING, "emotion_trace"),
        (WishType.LIFE_REFLECTION, "soul_portrait"),
        (WishType.LEARN_SKILL, "course_recommendation"),
        (WishType.FIND_PLACE, "place_search"),
        (WishType.FIND_RESOURCE, "resource_recommendation"),
        (WishType.CAREER_DIRECTION, "career_guidance"),
        (WishType.HEALTH_WELLNESS, "wellness_recommendation"),
        (WishType.FIND_COMPANION, "user_matching"),
        (WishType.FIND_MENTOR, "mentor_matching"),
        (WishType.SKILL_EXCHANGE, "skill_exchange_matching"),
        (WishType.SHARED_EXPERIENCE, "experience_matching"),
        (WishType.EMOTIONAL_SUPPORT, "support_matching"),
    ])
    def test_strategy(self, wish_type, expected_strategy):
        wish = DetectedWish(
            wish_text="test",
            wish_type=wish_type,
            confidence=0.9,
            source_intention_id="test_id",
        )
        result = classify(wish)
        assert result.fulfillment_strategy == expected_strategy


# ── Output structure ─────────────────────────────────────────────────────────


class TestOutputStructure:
    def test_classified_wish_preserves_text(self):
        wish = DetectedWish(
            wish_text="I want to understand myself",
            wish_type=WishType.SELF_UNDERSTANDING,
            confidence=0.9,
            source_intention_id="i1",
        )
        result = classify(wish)
        assert result.wish_text == "I want to understand myself"
        assert result.wish_type == WishType.SELF_UNDERSTANDING

    def test_classified_wish_is_pydantic(self):
        wish = DetectedWish(
            wish_text="test",
            wish_type=WishType.SELF_UNDERSTANDING,
            confidence=0.9,
            source_intention_id="i1",
        )
        result = classify(wish)
        assert isinstance(result, ClassifiedWish)
        # Can serialize to JSON
        data = result.model_dump()
        assert data["level"] == "L1"


# ── Batch classification ────────────────────────────────────────────────────


class TestBatchClassification:
    def test_empty_batch(self):
        assert classify_batch([]) == []

    def test_batch_preserves_order(self):
        wishes = [
            DetectedWish(wish_text="a", wish_type=WishType.SELF_UNDERSTANDING, confidence=0.9, source_intention_id="1"),
            DetectedWish(wish_text="b", wish_type=WishType.FIND_PLACE, confidence=0.8, source_intention_id="2"),
            DetectedWish(wish_text="c", wish_type=WishType.FIND_COMPANION, confidence=0.7, source_intention_id="3"),
        ]
        results = classify_batch(wishes)
        assert len(results) == 3
        assert results[0].level == WishLevel.L1
        assert results[1].level == WishLevel.L2
        assert results[2].level == WishLevel.L3

    def test_batch_mixed_levels(self):
        wishes = [
            DetectedWish(wish_text="x", wish_type=wt, confidence=0.9, source_intention_id=f"id_{i}")
            for i, wt in enumerate(WishType)
        ]
        results = classify_batch(wishes)
        levels = {r.level for r in results}
        assert levels == {WishLevel.L1, WishLevel.L2, WishLevel.L3}


# ── V10 design doc routing accuracy ─────────────────────────────────────────


class TestV10RoutingAccuracy:
    """Routing accuracy should be 100% since it's a lookup table."""

    def test_l1_count(self):
        l1_types = [wt for wt, lv in WISH_TYPES.items() if lv == WishLevel.L1]
        assert len(l1_types) == 5

    def test_l2_count(self):
        l2_types = [wt for wt, lv in WISH_TYPES.items() if lv == WishLevel.L2]
        assert len(l2_types) == 5

    def test_l3_count(self):
        l3_types = [wt for wt, lv in WISH_TYPES.items() if lv == WishLevel.L3]
        assert len(l3_types) == 5

    def test_total_types(self):
        assert len(WISH_TYPES) == 15
        assert len(WishType) == 15
