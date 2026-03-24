"""Shared models for the Wish Engine pipeline."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────


class WishType(str, Enum):
    # L1: AI can fulfill directly
    SELF_UNDERSTANDING = "self_understanding"
    SELF_EXPRESSION = "self_expression"
    RELATIONSHIP_INSIGHT = "relationship_insight"
    EMOTIONAL_PROCESSING = "emotional_processing"
    LIFE_REFLECTION = "life_reflection"
    # L2: Internet services
    LEARN_SKILL = "learn_skill"
    FIND_PLACE = "find_place"
    FIND_RESOURCE = "find_resource"
    CAREER_DIRECTION = "career_direction"
    HEALTH_WELLNESS = "health_wellness"
    # L3: Another user
    FIND_COMPANION = "find_companion"
    FIND_MENTOR = "find_mentor"
    SKILL_EXCHANGE = "skill_exchange"
    SHARED_EXPERIENCE = "shared_experience"
    EMOTIONAL_SUPPORT = "emotional_support"


class WishLevel(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class WishState(str, Enum):
    BORN = "born"
    SEARCHING = "searching"
    FOUND = "found"
    RECOMMENDED = "recommended"
    CONFIRMED = "confirmed"
    FULFILLED = "fulfilled"
    ARCHIVED = "archived"


class CardType(str, Enum):
    INSIGHT = "insight"
    RELATIONSHIP_ANALYSIS = "relationship_analysis"
    EMOTION_TRACE = "emotion_trace"
    SOUL_PORTRAIT = "soul_portrait"
    SELF_DIALOGUE = "self_dialogue"


# ── Input Models ─────────────────────────────────────────────────────────────


class Intention(BaseModel):
    """A single intention extracted by Deep Soul / SoulGraph."""

    id: str
    text: str
    source: str = ""


class EmotionState(BaseModel):
    """Current emotion snapshot."""

    emotions: dict[str, float] = Field(default_factory=dict)
    valence: float = 0.0
    distress: float = 0.0


class CrossDetectorPattern(BaseModel):
    """A cross-detector synthesized pattern."""

    pattern_name: str
    confidence: float = 0.0
    signals: dict[str, Any] = Field(default_factory=dict)


class DetectorResults(BaseModel):
    """Aggregated results from all 16 detectors — passed as dict payloads."""

    emotion: dict[str, Any] = Field(default_factory=dict)
    conflict: dict[str, Any] = Field(default_factory=dict)
    humor: dict[str, Any] = Field(default_factory=dict)
    mbti: dict[str, Any] = Field(default_factory=dict)
    love_language: dict[str, Any] = Field(default_factory=dict)
    eq: dict[str, Any] = Field(default_factory=dict)
    fragility: dict[str, Any] = Field(default_factory=dict)
    connection_response: dict[str, Any] = Field(default_factory=dict)
    attachment: dict[str, Any] = Field(default_factory=dict)
    values: dict[str, Any] = Field(default_factory=dict)
    super_brain: dict[str, Any] = Field(default_factory=dict)
    communication_dna: dict[str, Any] = Field(default_factory=dict)
    crisis: dict[str, Any] = Field(default_factory=dict)


# ── Output Models ────────────────────────────────────────────────────────────


class DetectedWish(BaseModel):
    """Output of WishDetector — a single detected wish."""

    wish_text: str
    wish_type: WishType
    confidence: float = Field(ge=0.0, le=1.0)
    source_intention_id: str


class ClassifiedWish(BaseModel):
    """Output of WishClassifier — wish with level and strategy."""

    wish_text: str
    wish_type: WishType
    level: WishLevel
    fulfillment_strategy: str


class L1FulfillmentResult(BaseModel):
    """Output of L1Fulfiller — personalized insight content."""

    fulfillment_text: str
    related_stars: list[str] = Field(default_factory=list)
    card_type: CardType


class RenderOutput(BaseModel):
    """Output of WishRenderer — visual state for the star map."""

    star_state: WishState
    color: str
    animation: str
    card_data: dict[str, Any] = Field(default_factory=dict)
