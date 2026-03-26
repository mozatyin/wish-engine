"""Tests for Trigger Engine — decides when to surface shells to the user."""

import time
import pytest
from wish_engine.compass.models import (
    ContradictionPattern,
    Shell,
    ShellStage,
    TriggerEvent,
    TriggerType,
    Interaction,
    InteractionType,
)
from wish_engine.compass.trigger import TriggerEngine


class TestDecisionRequest:
    def test_triggers_on_decision_language(self):
        engine = TriggerEngine()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="career", confidence=0.55)
        context = {
            "current_text": "我该不该换工作？",
            "session_id": "s1",
            "distress": 0.2,
            "topics_mentioned": ["career"],
        }
        result = engine.should_trigger(shell, context)
        assert result is not None
        assert result.trigger_type == TriggerType.DECISION_REQUEST

    def test_no_trigger_without_decision_language(self):
        engine = TriggerEngine()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="career", confidence=0.55)
        context = {
            "current_text": "今天天气不错",
            "session_id": "s1",
            "distress": 0.2,
            "topics_mentioned": [],
        }
        result = engine.should_trigger(shell, context)
        assert result is None


class TestTopicRelated:
    def test_triggers_when_topic_matches(self):
        engine = TriggerEngine()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.55)
        context = {
            "current_text": "Rhett came by today",
            "session_id": "s1",
            "distress": 0.2,
            "topics_mentioned": ["Rhett"],
        }
        result = engine.should_trigger(shell, context)
        assert result is not None
        assert result.trigger_type == TriggerType.TOPIC_RELATED


class TestOverdue:
    def test_triggers_when_high_confidence_and_old(self):
        engine = TriggerEngine()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="hidden", confidence=0.88)
        shell.created_at = time.time() - 8 * 86400  # 8 days old
        context = {
            "current_text": "hello",
            "session_id": "s1",
            "distress": 0.2,
            "topics_mentioned": [],
        }
        result = engine.should_trigger(shell, context)
        assert result is not None
        assert result.trigger_type == TriggerType.OVERDUE

    def test_no_overdue_if_recent(self):
        engine = TriggerEngine()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="hidden", confidence=0.88)
        # shell.created_at defaults to now
        context = {
            "current_text": "hello",
            "session_id": "s1",
            "distress": 0.2,
            "topics_mentioned": [],
        }
        result = engine.should_trigger(shell, context)
        # Should not trigger as overdue since it was just created
        assert result is None or result.trigger_type != TriggerType.OVERDUE


class TestSafetyGates:
    def test_no_trigger_during_crisis(self):
        engine = TriggerEngine()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.6)
        context = {
            "current_text": "我该选谁？",
            "session_id": "s1",
            "distress": 0.85,  # crisis
            "topics_mentioned": ["Rhett"],
        }
        assert engine.should_trigger(shell, context) is None

    def test_no_trigger_for_seed(self):
        engine = TriggerEngine()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.15)
        context = {
            "current_text": "该不该做x？",
            "session_id": "s1",
            "distress": 0.1,
            "topics_mentioned": ["x"],
        }
        assert engine.should_trigger(shell, context) is None

    def test_no_trigger_if_recently_denied(self):
        engine = TriggerEngine()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.6)
        shell.user_interactions.append(
            Interaction(interaction_type=InteractionType.DENY, timestamp=time.time() - 86400)  # 1 day ago
        )
        context = {
            "current_text": "Rhett来了",
            "session_id": "s1",
            "distress": 0.2,
            "topics_mentioned": ["Rhett"],
        }
        assert engine.should_trigger(shell, context) is None  # cooldown 7 days

    def test_trigger_after_cooldown(self):
        engine = TriggerEngine()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.6)
        shell.user_interactions.append(
            Interaction(interaction_type=InteractionType.DENY, timestamp=time.time() - 8 * 86400)  # 8 days ago
        )
        context = {
            "current_text": "Rhett来了",
            "session_id": "s1",
            "distress": 0.2,
            "topics_mentioned": ["Rhett"],
        }
        result = engine.should_trigger(shell, context)
        assert result is not None

    def test_max_one_per_session(self):
        engine = TriggerEngine()
        s1 = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="A", confidence=0.6)
        s2 = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="B", confidence=0.6)
        context = {
            "current_text": "选A还是B？",
            "session_id": "s1",
            "distress": 0.2,
            "topics_mentioned": ["A", "B"],
        }
        r1 = engine.should_trigger(s1, context)
        assert r1 is not None
        engine.mark_triggered("s1")
        r2 = engine.should_trigger(s2, context)
        assert r2 is None  # already triggered in this session
