"""Wish Classifier — routes wishes to L1/L2/L3. Zero LLM, pure rule-based."""

from __future__ import annotations

from wish_engine.models import (
    ClassifiedWish,
    DetectedWish,
    WishLevel,
    WishType,
)

# ── Type → Level mapping (from V10 design doc) ──────────────────────────────

WISH_TYPES: dict[WishType, WishLevel] = {
    # L1: AI can fulfill directly
    WishType.SELF_UNDERSTANDING: WishLevel.L1,
    WishType.SELF_EXPRESSION: WishLevel.L1,
    WishType.RELATIONSHIP_INSIGHT: WishLevel.L1,
    WishType.EMOTIONAL_PROCESSING: WishLevel.L1,
    WishType.LIFE_REFLECTION: WishLevel.L1,
    # L2: Internet services
    WishType.LEARN_SKILL: WishLevel.L2,
    WishType.FIND_PLACE: WishLevel.L2,
    WishType.FIND_RESOURCE: WishLevel.L2,
    WishType.CAREER_DIRECTION: WishLevel.L2,
    WishType.HEALTH_WELLNESS: WishLevel.L2,
    # L3: Another user
    WishType.FIND_COMPANION: WishLevel.L3,
    WishType.FIND_MENTOR: WishLevel.L3,
    WishType.SKILL_EXCHANGE: WishLevel.L3,
    WishType.SHARED_EXPERIENCE: WishLevel.L3,
    WishType.EMOTIONAL_SUPPORT: WishLevel.L3,
}

# ── Fulfillment strategies per type ──────────────────────────────────────────

FULFILLMENT_STRATEGIES: dict[WishType, str] = {
    # L1
    WishType.SELF_UNDERSTANDING: "personalized_insight",
    WishType.SELF_EXPRESSION: "assisted_writing",
    WishType.RELATIONSHIP_INSIGHT: "bond_analysis",
    WishType.EMOTIONAL_PROCESSING: "emotion_trace",
    WishType.LIFE_REFLECTION: "soul_portrait",
    # L2
    WishType.LEARN_SKILL: "course_recommendation",
    WishType.FIND_PLACE: "place_search",
    WishType.FIND_RESOURCE: "resource_recommendation",
    WishType.CAREER_DIRECTION: "career_guidance",
    WishType.HEALTH_WELLNESS: "wellness_recommendation",
    # L3
    WishType.FIND_COMPANION: "user_matching",
    WishType.FIND_MENTOR: "mentor_matching",
    WishType.SKILL_EXCHANGE: "skill_exchange_matching",
    WishType.SHARED_EXPERIENCE: "experience_matching",
    WishType.EMOTIONAL_SUPPORT: "support_matching",
}


def classify(wish: DetectedWish) -> ClassifiedWish:
    """Classify a detected wish into L1/L2/L3 with fulfillment strategy.

    Zero LLM — pure dictionary lookup.

    Args:
        wish: A detected wish from WishDetector.

    Returns:
        ClassifiedWish with level and fulfillment_strategy.
    """
    level = WISH_TYPES[wish.wish_type]
    strategy = FULFILLMENT_STRATEGIES[wish.wish_type]

    return ClassifiedWish(
        wish_text=wish.wish_text,
        wish_type=wish.wish_type,
        level=level,
        fulfillment_strategy=strategy,
    )


def classify_batch(wishes: list[DetectedWish]) -> list[ClassifiedWish]:
    """Classify multiple wishes at once."""
    return [classify(w) for w in wishes]
