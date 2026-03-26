"""Tests for Contradiction Detector — 7 behavioral contradiction patterns."""

from __future__ import annotations

import pytest
from wish_engine.models import DetectorResults, EmotionState
from wish_engine.compass.models import Shell, ContradictionPattern, Signal
from wish_engine.compass.contradiction import ContradictionDetector

from typing import Optional


def _make_session_signals(
    topics: list[dict],
    emotion: Optional[dict] = None,
    detector_results: Optional[DetectorResults] = None,
) -> dict:
    """Build a session signals dict for the detector."""
    return {
        "topics": topics,
        "emotion_state": emotion or {},
        "detector_results": detector_results or DetectorResults(),
        "session_id": "test_session",
    }


class TestEmotionAnomaly:
    """Pattern #5: emotion pattern for specific entity differs from baseline."""

    def test_detects_arousal_spike(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[
                {"entity": "Rhett Butler", "sentiment": "negative", "arousal": 0.8, "mentions": 3},
                {"entity": "Ashley Wilkes", "sentiment": "positive", "arousal": 0.3, "mentions": 2},
            ],
        )
        history = {
            "average_arousal": 0.35,
            "entity_history": {},
        }
        shells = det.detect(signals, history, known_wishes=[])
        rhett_shells = [s for s in shells if s.topic == "Rhett Butler"]
        assert len(rhett_shells) >= 1
        assert rhett_shells[0].pattern == ContradictionPattern.EMOTION_ANOMALY

    def test_no_anomaly_when_arousal_normal(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[
                {"entity": "Normal Person", "sentiment": "positive", "arousal": 0.35, "mentions": 1},
            ],
        )
        history = {"average_arousal": 0.35, "entity_history": {}}
        shells = det.detect(signals, history, known_wishes=[])
        assert len(shells) == 0


class TestMouthHardHeartSoft:
    """Pattern #1: stated sentiment contradicts emotional arousal."""

    def test_negative_words_positive_arousal(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[
                {"entity": "Rhett", "sentiment": "negative", "arousal": 0.75, "mentions": 2},
            ],
        )
        history = {"average_arousal": 0.3, "entity_history": {}}
        shells = det.detect(signals, history, known_wishes=[])
        matching = [s for s in shells if s.pattern == ContradictionPattern.MOUTH_HARD_HEART_SOFT]
        assert len(matching) >= 1

    def test_consistent_sentiment_no_contradiction(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[
                {"entity": "Friend", "sentiment": "positive", "arousal": 0.6, "mentions": 1},
            ],
        )
        history = {"average_arousal": 0.3, "entity_history": {}}
        shells = det.detect(signals, history, known_wishes=[])
        matching = [s for s in shells if s.pattern == ContradictionPattern.MOUTH_HARD_HEART_SOFT]
        assert len(matching) == 0


class TestRepeatedProbing:
    """Pattern #3: same topic appears across multiple sessions with denial."""

    def test_detects_repeated_topic(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[
                {"entity": "career_change", "sentiment": "dismissive", "arousal": 0.5, "mentions": 2},
            ],
        )
        history = {
            "average_arousal": 0.35,
            "entity_history": {
                "career_change": {
                    "session_count": 4,
                    "avg_sentiment": "dismissive",
                    "avg_arousal": 0.55,
                },
            },
        }
        shells = det.detect(signals, history, known_wishes=[])
        matching = [s for s in shells if s.pattern == ContradictionPattern.REPEATED_PROBING]
        assert len(matching) >= 1

    def test_no_repeated_if_first_time(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[
                {"entity": "new_topic", "sentiment": "dismissive", "arousal": 0.5, "mentions": 1},
            ],
        )
        history = {"average_arousal": 0.35, "entity_history": {}}
        shells = det.detect(signals, history, known_wishes=[])
        matching = [s for s in shells if s.pattern == ContradictionPattern.REPEATED_PROBING]
        assert len(matching) == 0


class TestValueConflict:
    """Pattern #4: stated values vs actual behavior diverge."""

    def test_freedom_values_security_behavior(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[],
            detector_results=DetectorResults(
                values={"top_values": ["self-direction", "stimulation"]},
            ),
        )
        history = {
            "average_arousal": 0.35,
            "entity_history": {},
            "behavioral_choices": ["chose_stable_job", "avoided_risk", "stayed_in_comfort_zone"],
            "stated_values": ["self-direction", "stimulation"],
        }
        shells = det.detect(signals, history, known_wishes=[])
        matching = [s for s in shells if s.pattern == ContradictionPattern.VALUE_CONFLICT]
        assert len(matching) >= 1


class TestSayOneDoOther:
    """Pattern #2: explicit denial but behavior points to X."""

    def test_deny_but_seek(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[
                {"entity": "loneliness", "sentiment": "denial", "arousal": 0.6, "mentions": 1},
            ],
            detector_results=DetectorResults(
                attachment={"style": "anxious"},
                emotion={"emotions": {"loneliness": 0.6}},
            ),
        )
        history = {
            "average_arousal": 0.35,
            "entity_history": {
                "loneliness": {"session_count": 2, "avg_sentiment": "denial", "avg_arousal": 0.55},
            },
        }
        shells = det.detect(signals, history, known_wishes=[])
        matching = [s for s in shells if s.pattern == ContradictionPattern.SAY_ONE_DO_OTHER]
        assert len(matching) >= 1


class TestAvoidanceSignal:
    """Pattern #6: topic proximity triggers fragility spike and topic change."""

    def test_avoidance_detected(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[
                {"entity": "family_origin", "sentiment": "avoidant", "arousal": 0.4, "mentions": 1,
                 "fragility_spike": True, "topic_changed": True},
            ],
        )
        history = {"average_arousal": 0.35, "entity_history": {}}
        shells = det.detect(signals, history, known_wishes=[])
        matching = [s for s in shells if s.pattern == ContradictionPattern.AVOIDANCE_SIGNAL]
        assert len(matching) >= 1


class TestGrowthGap:
    """Pattern #7: one dimension changes suddenly while others stay flat."""

    def test_eq_jump_detected(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[],
            detector_results=DetectorResults(eq={"overall": 0.75}),
        )
        history = {
            "average_arousal": 0.35,
            "entity_history": {},
            "previous_eq": 0.55,
            "previous_conflict": "avoiding",
            "current_conflict": "avoiding",
        }
        shells = det.detect(signals, history, known_wishes=[])
        matching = [s for s in shells if s.pattern == ContradictionPattern.GROWTH_GAP]
        assert len(matching) >= 1

    def test_no_gap_when_stable(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[],
            detector_results=DetectorResults(eq={"overall": 0.56}),
        )
        history = {
            "average_arousal": 0.35,
            "entity_history": {},
            "previous_eq": 0.55,
            "previous_conflict": "avoiding",
            "current_conflict": "avoiding",
        }
        shells = det.detect(signals, history, known_wishes=[])
        matching = [s for s in shells if s.pattern == ContradictionPattern.GROWTH_GAP]
        assert len(matching) == 0


class TestFiltering:
    def test_excludes_known_wishes(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[
                {"entity": "meditation", "sentiment": "negative", "arousal": 0.8, "mentions": 3},
            ],
        )
        history = {"average_arousal": 0.3, "entity_history": {}}
        known = [{"wish_text": "想学冥想", "topic_keywords": ["meditation"]}]
        shells = det.detect(signals, history, known_wishes=known)
        med_shells = [s for s in shells if s.topic == "meditation"]
        assert len(med_shells) == 0

    def test_multiple_patterns_same_session(self):
        det = ContradictionDetector()
        signals = _make_session_signals(
            topics=[
                {"entity": "Rhett", "sentiment": "negative", "arousal": 0.8, "mentions": 3},
                {"entity": "career_change", "sentiment": "dismissive", "arousal": 0.5, "mentions": 2},
            ],
        )
        history = {
            "average_arousal": 0.3,
            "entity_history": {
                "career_change": {"session_count": 5, "avg_sentiment": "dismissive", "avg_arousal": 0.5},
            },
        }
        shells = det.detect(signals, history, known_wishes=[])
        assert len(shells) >= 2
