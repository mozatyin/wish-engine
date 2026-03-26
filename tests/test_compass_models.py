"""Tests for Compass data models — Shell, Signal, Interaction, TriggerEvent."""

import time
import pytest
from wish_engine.compass.models import (
    Shell,
    ShellStage,
    Signal,
    Interaction,
    InteractionType,
    TriggerEvent,
    TriggerType,
    ContradictionPattern,
)


class TestSignal:
    def test_create(self):
        s = Signal(
            signal_type="emotion_anomaly",
            topic="Rhett Butler",
            data={"arousal": 0.75, "valence": -0.2},
            session_id="s1",
        )
        assert s.signal_type == "emotion_anomaly"
        assert s.topic == "Rhett Butler"
        assert s.timestamp > 0

    def test_default_timestamp(self):
        s = Signal(signal_type="test", topic="x", data={}, session_id="s1")
        assert abs(s.timestamp - time.time()) < 2


class TestShell:
    def test_create_seed(self):
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett Butler", confidence=0.25)
        assert shell.stage == ShellStage.SEED
        assert shell.confidence == 0.25
        assert len(shell.id) > 0

    def test_stage_from_confidence(self):
        assert Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.15).stage == ShellStage.SEED
        assert Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.35).stage == ShellStage.SPROUT
        assert Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.55).stage == ShellStage.BUD
        assert Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.75).stage == ShellStage.BLOOM

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=1.5)
        with pytest.raises(Exception):
            Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=-0.1)

    def test_add_evidence(self):
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.2)
        sig = Signal(signal_type="test", topic="x", data={}, session_id="s1")
        shell.raw_signals.append(sig)
        assert len(shell.raw_signals) == 1

    def test_is_visible(self):
        seed = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.2)
        sprout = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.4)
        assert not seed.is_visible
        assert sprout.is_visible


class TestInteraction:
    def test_confirm(self):
        i = Interaction(interaction_type=InteractionType.CONFIRM)
        assert i.interaction_type == InteractionType.CONFIRM

    def test_deny(self):
        i = Interaction(interaction_type=InteractionType.DENY)
        assert i.interaction_type == InteractionType.DENY


class TestTriggerEvent:
    def test_create(self):
        t = TriggerEvent(
            trigger_type=TriggerType.DECISION_REQUEST,
            session_id="s5",
            shell_id="shell_1",
            revelation_text="Have you noticed...",
        )
        assert t.trigger_type == TriggerType.DECISION_REQUEST


class TestContradictionPattern:
    def test_all_seven_patterns(self):
        patterns = list(ContradictionPattern)
        assert len(patterns) == 7
        assert ContradictionPattern.MOUTH_HARD_HEART_SOFT in patterns
        assert ContradictionPattern.SAY_ONE_DO_OTHER in patterns
        assert ContradictionPattern.REPEATED_PROBING in patterns
        assert ContradictionPattern.VALUE_CONFLICT in patterns
        assert ContradictionPattern.EMOTION_ANOMALY in patterns
        assert ContradictionPattern.AVOIDANCE_SIGNAL in patterns
        assert ContradictionPattern.GROWTH_GAP in patterns
