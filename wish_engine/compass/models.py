"""Compass data models — Shell, Signal, Interaction, TriggerEvent."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ContradictionPattern(str, Enum):
    MOUTH_HARD_HEART_SOFT = "mouth_hard_heart_soft"
    SAY_ONE_DO_OTHER = "say_one_do_other"
    REPEATED_PROBING = "repeated_probing"
    VALUE_CONFLICT = "value_conflict"
    EMOTION_ANOMALY = "emotion_anomaly"
    AVOIDANCE_SIGNAL = "avoidance_signal"
    GROWTH_GAP = "growth_gap"


class ShellStage(str, Enum):
    SEED = "seed"
    SPROUT = "sprout"
    BUD = "bud"
    BLOOM = "bloom"


class InteractionType(str, Enum):
    CONFIRM = "confirm"
    DENY = "deny"
    IGNORE = "ignore"
    TAP = "tap"


class TriggerType(str, Enum):
    DECISION_REQUEST = "decision_request"
    TOPIC_RELATED = "topic_related"
    EMOTIONAL_READY = "emotional_ready"
    OVERDUE = "overdue"


def _stage_from_confidence(confidence: float) -> ShellStage:
    if confidence < 0.3:
        return ShellStage.SEED
    elif confidence < 0.5:
        return ShellStage.SPROUT
    elif confidence < 0.7:
        return ShellStage.BUD
    else:
        return ShellStage.BLOOM


class Signal(BaseModel):
    signal_type: str
    topic: str
    data: dict[str, Any] = Field(default_factory=dict)
    session_id: str = ""
    timestamp: float = Field(default_factory=time.time)


class Interaction(BaseModel):
    interaction_type: InteractionType
    timestamp: float = Field(default_factory=time.time)
    feedback_text: str = ""


class TriggerEvent(BaseModel):
    trigger_type: TriggerType
    session_id: str
    shell_id: str
    revelation_text: str
    timestamp: float = Field(default_factory=time.time)


class Shell(BaseModel):
    id: str = Field(default_factory=lambda: f"shell_{uuid.uuid4().hex[:8]}")
    pattern: ContradictionPattern
    topic: str
    confidence: float = Field(ge=0.0, le=0.95)
    raw_signals: list[Signal] = Field(default_factory=list)
    confidence_history: list[tuple[float, float, str]] = Field(default_factory=list)
    user_interactions: list[Interaction] = Field(default_factory=list)
    trigger_history: list[TriggerEvent] = Field(default_factory=list)
    related_shells: list[str] = Field(default_factory=list)
    related_wishes: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    last_updated: float = Field(default_factory=time.time)

    @property
    def stage(self) -> ShellStage:
        return _stage_from_confidence(self.confidence)

    @property
    def is_visible(self) -> bool:
        return self.stage != ShellStage.SEED
