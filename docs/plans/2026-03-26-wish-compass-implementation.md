# Wish Compass Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the Wish Compass — a system that detects hidden desires from behavioral contradictions in 16-dimension personality data, tracks them as "shells" (贝壳) through a maturity lifecycle, and surfaces them at the right moment.

**Architecture:** 6 modules in a `compass/` subpackage inside wish-engine. Daily Scanner reads TriSoul+detector data, Contradiction Detector finds behavioral anomalies, Secret Vault stores shells with confidence tracking, Maturity Model manages seed→sprout→bud→bloom lifecycle, Trigger Engine decides when to surface, Revelation Renderer generates B+C style text. All zero-LLM except Revelation (1× Haiku for sensitive topics).

**Tech Stack:** Python 3.12+, Pydantic v2, pytest. Reuses `DetectorResults` and `EmotionState` from `wish_engine.models`.

---

### Task 1: Compass data models

**Files:**
- Create: `wish_engine/compass/models.py`
- Create: `wish_engine/compass/__init__.py`
- Test: `tests/test_compass_models.py`

**Step 1: Write the failing test**

Create `tests/test_compass_models.py`:

```python
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
        shell = Shell(
            pattern=ContradictionPattern.EMOTION_ANOMALY,
            topic="Rhett Butler",
            confidence=0.25,
        )
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
        """seed = not visible, sprout+ = visible."""
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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'wish_engine.compass'`

**Step 3: Write minimal implementation**

Create `wish_engine/compass/__init__.py`:

```python
"""Wish Compass — detects hidden desires from behavioral contradictions."""
```

Create `wish_engine/compass/models.py`:

```python
"""Compass data models — Shell, Signal, Interaction, TriggerEvent."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ContradictionPattern(str, Enum):
    """The 7 contradiction patterns that produce shells."""

    MOUTH_HARD_HEART_SOFT = "mouth_hard_heart_soft"
    SAY_ONE_DO_OTHER = "say_one_do_other"
    REPEATED_PROBING = "repeated_probing"
    VALUE_CONFLICT = "value_conflict"
    EMOTION_ANOMALY = "emotion_anomaly"
    AVOIDANCE_SIGNAL = "avoidance_signal"
    GROWTH_GAP = "growth_gap"


class ShellStage(str, Enum):
    """Maturity stages of a shell (贝壳)."""

    SEED = "seed"        # 0.0 - 0.3: just discovered, not shown
    SPROUT = "sprout"    # 0.3 - 0.5: faint star, barely visible
    BUD = "bud"          # 0.5 - 0.7: visible pulsing star, awaiting trigger
    BLOOM = "bloom"      # 0.7+: mature, enters Wish Engine fulfillment


class InteractionType(str, Enum):
    CONFIRM = "confirm"    # user says "好像是"
    DENY = "deny"          # user says "不对"
    IGNORE = "ignore"      # user opened but gave no feedback
    TAP = "tap"            # user tapped the star (curiosity)


class TriggerType(str, Enum):
    DECISION_REQUEST = "decision_request"  # user asking for advice
    TOPIC_RELATED = "topic_related"        # current topic matches shell
    EMOTIONAL_READY = "emotional_ready"    # distress low, openness high
    OVERDUE = "overdue"                    # high confidence, waiting too long


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
    """A single signal detected by Daily Scanner."""

    signal_type: str
    topic: str
    data: dict[str, Any] = Field(default_factory=dict)
    session_id: str = ""
    timestamp: float = Field(default_factory=time.time)


class Interaction(BaseModel):
    """User interaction with a shell revelation."""

    interaction_type: InteractionType
    timestamp: float = Field(default_factory=time.time)
    feedback_text: str = ""


class TriggerEvent(BaseModel):
    """Record of a shell being surfaced to the user."""

    trigger_type: TriggerType
    session_id: str
    shell_id: str
    revelation_text: str
    timestamp: float = Field(default_factory=time.time)


class Shell(BaseModel):
    """A shell (贝壳) — a hidden desire detected from behavioral contradictions.

    Lifecycle: seed → sprout → bud → bloom
    """

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
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_models.py -v`
Expected: All 11 tests PASS

**Step 5: Run full suite for regressions**

Run: `cd /Users/michael/wish-engine && python3 -m pytest --ignore=tests/test_agent_negotiator.py --ignore=tests/test_e2e.py --ignore=tests/test_l3_matcher.py --tb=short -q`
Expected: 561+ passed

**Step 6: Commit**

```bash
cd /Users/michael/wish-engine && git add wish_engine/compass/ tests/test_compass_models.py && git commit -m "feat: add Compass data models (Shell, Signal, ContradictionPattern, maturity stages)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Contradiction Detector — 7 patterns

**Files:**
- Create: `wish_engine/compass/contradiction.py`
- Test: `tests/test_compass_contradiction.py`

**Step 1: Write the failing test**

Create `tests/test_compass_contradiction.py`:

```python
"""Tests for Contradiction Detector — 7 behavioral contradiction patterns."""

import pytest
from wish_engine.models import DetectorResults, EmotionState
from wish_engine.compass.models import Shell, ContradictionPattern, Signal
from wish_engine.compass.contradiction import ContradictionDetector


def _make_session_signals(
    topics: list[dict],
    emotion: dict | None = None,
    detector_results: DetectorResults | None = None,
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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_contradiction.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `wish_engine/compass/contradiction.py`:

```python
"""Contradiction Detector — finds behavioral contradictions from session signals.

7 patterns:
  1. Mouth hard, heart soft — stated negative, arousal high
  2. Say one, do other — explicit denial but detector data says otherwise
  3. Repeated probing — same topic, multiple sessions, always dismissed
  4. Value conflict — stated values vs actual choices diverge
  5. Emotion anomaly — emotion pattern for entity differs from baseline
  6. Avoidance signal — fragility spike + topic change near sensitive area
  7. Growth gap — one dimension jumps while others flat

Zero LLM. Pure statistics + pattern matching.
"""

from __future__ import annotations

from typing import Any

from wish_engine.compass.models import (
    ContradictionPattern,
    Shell,
    Signal,
)

# ── Thresholds ───────────────────────────────────────────────────────────────

AROUSAL_ANOMALY_THRESHOLD = 0.25       # arousal above baseline by this much
MOUTH_HARD_AROUSAL_THRESHOLD = 0.6     # high arousal with negative sentiment
REPEATED_SESSION_THRESHOLD = 3         # topic in 3+ sessions = repeated
EQ_JUMP_THRESHOLD = 0.15              # EQ change > 0.15 = growth gap
SEED_CONFIDENCE = 0.20                # default confidence for new shells


class ContradictionDetector:
    """Detects behavioral contradictions from session signals and history."""

    def detect(
        self,
        signals: dict[str, Any],
        history: dict[str, Any],
        known_wishes: list[dict[str, Any]],
    ) -> list[Shell]:
        """Run all 7 contradiction patterns on session signals.

        Args:
            signals: Current session data with 'topics', 'emotion_state',
                     'detector_results', 'session_id'.
            history: Historical data with 'average_arousal', 'entity_history',
                     optional 'behavioral_choices', 'previous_eq', etc.
            known_wishes: Already expressed wishes to filter out.

        Returns:
            List of newly discovered Shell objects.
        """
        shells: list[Shell] = []
        topics = signals.get("topics", [])
        det = signals.get("detector_results")
        session_id = signals.get("session_id", "")
        avg_arousal = history.get("average_arousal", 0.35)
        entity_hist = history.get("entity_history", {})

        # ── Pattern 5: Emotion anomaly ─────────────────────────────────
        for topic in topics:
            entity = topic.get("entity", "")
            arousal = topic.get("arousal", 0.0)
            if arousal - avg_arousal > AROUSAL_ANOMALY_THRESHOLD:
                shells.append(Shell(
                    pattern=ContradictionPattern.EMOTION_ANOMALY,
                    topic=entity,
                    confidence=min((arousal - avg_arousal) / 0.5 * SEED_CONFIDENCE, 0.4),
                    raw_signals=[Signal(
                        signal_type="emotion_anomaly",
                        topic=entity,
                        data={"arousal": arousal, "baseline": avg_arousal},
                        session_id=session_id,
                    )],
                ))

        # ── Pattern 1: Mouth hard, heart soft ──────────────────────────
        for topic in topics:
            entity = topic.get("entity", "")
            sentiment = topic.get("sentiment", "")
            arousal = topic.get("arousal", 0.0)
            if sentiment == "negative" and arousal >= MOUTH_HARD_AROUSAL_THRESHOLD:
                shells.append(Shell(
                    pattern=ContradictionPattern.MOUTH_HARD_HEART_SOFT,
                    topic=entity,
                    confidence=SEED_CONFIDENCE,
                    raw_signals=[Signal(
                        signal_type="mouth_hard_heart_soft",
                        topic=entity,
                        data={"sentiment": sentiment, "arousal": arousal},
                        session_id=session_id,
                    )],
                ))

        # ── Pattern 3: Repeated probing ────────────────────────────────
        for topic in topics:
            entity = topic.get("entity", "")
            sentiment = topic.get("sentiment", "")
            ent_hist = entity_hist.get(entity, {})
            session_count = ent_hist.get("session_count", 0)
            if session_count >= REPEATED_SESSION_THRESHOLD and sentiment in ("dismissive", "denial"):
                shells.append(Shell(
                    pattern=ContradictionPattern.REPEATED_PROBING,
                    topic=entity,
                    confidence=min(session_count * 0.05 + 0.15, 0.45),
                    raw_signals=[Signal(
                        signal_type="repeated_probing",
                        topic=entity,
                        data={"session_count": session_count, "sentiment": sentiment},
                        session_id=session_id,
                    )],
                ))

        # ── Pattern 2: Say one, do other ───────────────────────────────
        for topic in topics:
            entity = topic.get("entity", "")
            sentiment = topic.get("sentiment", "")
            if sentiment != "denial":
                continue
            # Check if detector data contradicts the denial
            ent_hist = entity_hist.get(entity, {})
            if ent_hist.get("session_count", 0) >= 2:
                # Repeated denial + detector evidence
                if det:
                    emotions = getattr(det, "emotion", {}) if hasattr(det, "emotion") else {}
                    if isinstance(emotions, dict) and emotions.get("emotions", {}).get(entity, 0) > 0.4:
                        shells.append(Shell(
                            pattern=ContradictionPattern.SAY_ONE_DO_OTHER,
                            topic=entity,
                            confidence=0.25,
                            raw_signals=[Signal(
                                signal_type="say_one_do_other",
                                topic=entity,
                                data={"sentiment": sentiment, "detector_signal": True},
                                session_id=session_id,
                            )],
                        ))

        # ── Pattern 4: Value conflict ──────────────────────────────────
        behavioral_choices = history.get("behavioral_choices", [])
        if behavioral_choices and det:
            stated_vals = set(history.get("stated_values", []))
            if not stated_vals:
                det_vals = getattr(det, "values", {}) if hasattr(det, "values") else {}
                if isinstance(det_vals, dict):
                    stated_vals = set(det_vals.get("top_values", []))
            # Check for contradictions
            security_behaviors = {"chose_stable_job", "avoided_risk", "stayed_in_comfort_zone"}
            freedom_values = {"self-direction", "stimulation"}
            if stated_vals & freedom_values and set(behavioral_choices) & security_behaviors:
                shells.append(Shell(
                    pattern=ContradictionPattern.VALUE_CONFLICT,
                    topic="values_vs_behavior",
                    confidence=0.30,
                    raw_signals=[Signal(
                        signal_type="value_conflict",
                        topic="values_vs_behavior",
                        data={"stated": list(stated_vals), "behaviors": behavioral_choices},
                        session_id=session_id,
                    )],
                ))

        # ── Pattern 6: Avoidance signal ────────────────────────────────
        for topic in topics:
            entity = topic.get("entity", "")
            if topic.get("fragility_spike") and topic.get("topic_changed"):
                shells.append(Shell(
                    pattern=ContradictionPattern.AVOIDANCE_SIGNAL,
                    topic=entity,
                    confidence=0.25,
                    raw_signals=[Signal(
                        signal_type="avoidance_signal",
                        topic=entity,
                        data={"fragility_spike": True, "topic_changed": True},
                        session_id=session_id,
                    )],
                ))

        # ── Pattern 7: Growth gap ──────────────────────────────────────
        prev_eq = history.get("previous_eq")
        if prev_eq is not None and det:
            current_eq = getattr(det, "eq", {}) if hasattr(det, "eq") else {}
            if isinstance(current_eq, dict):
                eq_val = current_eq.get("overall")
                if eq_val is not None and eq_val - prev_eq > EQ_JUMP_THRESHOLD:
                    # Check if behavior hasn't changed
                    prev_conflict = history.get("previous_conflict")
                    curr_conflict = history.get("current_conflict")
                    if prev_conflict and curr_conflict and prev_conflict == curr_conflict:
                        shells.append(Shell(
                            pattern=ContradictionPattern.GROWTH_GAP,
                            topic="eq_growth_without_behavior_change",
                            confidence=0.20,
                            raw_signals=[Signal(
                                signal_type="growth_gap",
                                topic="eq_growth",
                                data={"prev_eq": prev_eq, "current_eq": eq_val, "conflict_unchanged": True},
                                session_id=session_id,
                            )],
                        ))

        # ── Filter known wishes ────────────────────────────────────────
        if known_wishes:
            known_topics = set()
            for w in known_wishes:
                known_topics.update(w.get("topic_keywords", []))
                known_topics.add(w.get("wish_text", "").lower())
            shells = [s for s in shells if s.topic.lower() not in known_topics]

        return shells
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_contradiction.py -v`
Expected: All 13 tests PASS

**Step 5: Commit**

```bash
cd /Users/michael/wish-engine && git add wish_engine/compass/contradiction.py tests/test_compass_contradiction.py && git commit -m "feat: add Contradiction Detector with 7 behavioral patterns

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Secret Vault — shell storage + confidence management

**Files:**
- Create: `wish_engine/compass/vault.py`
- Test: `tests/test_compass_vault.py`

**Step 1: Write the failing test**

Create `tests/test_compass_vault.py`:

```python
"""Tests for Secret Vault — shell storage and confidence management."""

import pytest
from wish_engine.compass.models import (
    ContradictionPattern,
    Interaction,
    InteractionType,
    Shell,
    ShellStage,
    Signal,
)
from wish_engine.compass.vault import SecretVault


class TestVaultBasics:
    def test_add_shell(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.2)
        vault.add(shell)
        assert len(vault.all_shells) == 1

    def test_get_by_id(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.2)
        vault.add(shell)
        found = vault.get(shell.id)
        assert found is not None
        assert found.topic == "Rhett"

    def test_get_missing_returns_none(self):
        vault = SecretVault()
        assert vault.get("nonexistent") is None

    def test_get_by_topic(self):
        vault = SecretVault()
        vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.2))
        vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Ashley", confidence=0.3))
        rhett_shells = vault.get_by_topic("Rhett")
        assert len(rhett_shells) == 1


class TestConfidenceUpdate:
    def test_add_evidence_increases_confidence(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.2)
        vault.add(shell)
        sig = Signal(signal_type="emotion_anomaly", topic="Rhett", data={"arousal": 0.8}, session_id="s2")
        vault.add_evidence(shell.id, sig, strength=0.7)
        updated = vault.get(shell.id)
        assert updated.confidence > 0.2

    def test_user_confirm_increases_confidence(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.5)
        vault.add(shell)
        vault.record_interaction(shell.id, InteractionType.CONFIRM)
        updated = vault.get(shell.id)
        assert updated.confidence > 0.5

    def test_user_deny_decreases_confidence(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.5)
        vault.add(shell)
        vault.record_interaction(shell.id, InteractionType.DENY)
        updated = vault.get(shell.id)
        assert updated.confidence < 0.5

    def test_user_ignore_slight_increase(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.4)
        vault.add(shell)
        vault.record_interaction(shell.id, InteractionType.IGNORE)
        updated = vault.get(shell.id)
        assert updated.confidence == pytest.approx(0.42, abs=0.01)

    def test_confidence_capped_at_095(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.93)
        vault.add(shell)
        vault.add_evidence(shell.id, Signal(signal_type="test", topic="x", data={}, session_id="s1"), strength=1.0)
        assert vault.get(shell.id).confidence <= 0.95

    def test_confidence_cannot_go_below_zero(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.05)
        vault.add(shell)
        vault.record_interaction(shell.id, InteractionType.DENY)
        assert vault.get(shell.id).confidence >= 0.0


class TestMerging:
    def test_merge_same_topic_shells(self):
        """Two shells about same topic should merge, keeping higher confidence."""
        vault = SecretVault()
        s1 = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.25)
        s2 = Shell(pattern=ContradictionPattern.MOUTH_HARD_HEART_SOFT, topic="Rhett", confidence=0.20)
        vault.add(s1)
        vault.merge_or_add(s2)
        rhett_shells = vault.get_by_topic("Rhett")
        assert len(rhett_shells) == 1
        assert rhett_shells[0].confidence > 0.25  # merged confidence should be higher

    def test_different_topic_no_merge(self):
        vault = SecretVault()
        s1 = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.25)
        s2 = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="career", confidence=0.20)
        vault.add(s1)
        vault.merge_or_add(s2)
        assert len(vault.all_shells) == 2


class TestVisibleShells:
    def test_visible_returns_sprout_and_above(self):
        vault = SecretVault()
        vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="seed", confidence=0.15))
        vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="sprout", confidence=0.35))
        vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="bud", confidence=0.55))
        visible = vault.visible_shells
        assert len(visible) == 2
        topics = [s.topic for s in visible]
        assert "seed" not in topics
        assert "sprout" in topics
        assert "bud" in topics

    def test_bloom_shells(self):
        vault = SecretVault()
        vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="mature", confidence=0.75))
        vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="young", confidence=0.2))
        blooms = vault.bloom_shells
        assert len(blooms) == 1
        assert blooms[0].topic == "mature"


class TestConfidenceHistory:
    def test_history_recorded(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.3)
        vault.add(shell)
        vault.record_interaction(shell.id, InteractionType.CONFIRM)
        updated = vault.get(shell.id)
        assert len(updated.confidence_history) >= 1
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_vault.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `wish_engine/compass/vault.py`:

```python
"""Secret Vault — stores shells (贝壳) with confidence tracking and lifecycle management.

Manages the shell collection, confidence updates from evidence and user feedback,
merging of related shells, and lifecycle queries.
Zero LLM.
"""

from __future__ import annotations

import time

from wish_engine.compass.models import (
    Interaction,
    InteractionType,
    Shell,
    ShellStage,
    Signal,
)

# ── Confidence update deltas ─────────────────────────────────────────────────

EVIDENCE_BASE_DELTA = 0.05       # per evidence signal
CONFIRM_DELTA = 0.10             # user says "好像是"
DENY_DELTA = -0.15               # user says "不对"
IGNORE_DELTA = 0.02              # user opened but no feedback
MERGE_BONUS = 0.05               # bonus when merging same-topic shells
CONFIDENCE_MAX = 0.95
CONFIDENCE_MIN = 0.0


class SecretVault:
    """In-memory store for shells with confidence management."""

    def __init__(self):
        self._shells: dict[str, Shell] = {}

    @property
    def all_shells(self) -> list[Shell]:
        return list(self._shells.values())

    @property
    def visible_shells(self) -> list[Shell]:
        """Shells at sprout stage or above (visible on star map)."""
        return [s for s in self._shells.values() if s.is_visible]

    @property
    def bloom_shells(self) -> list[Shell]:
        """Shells that have reached bloom — ready for Wish Engine."""
        return [s for s in self._shells.values() if s.stage == ShellStage.BLOOM]

    def add(self, shell: Shell) -> None:
        self._shells[shell.id] = shell

    def get(self, shell_id: str) -> Shell | None:
        return self._shells.get(shell_id)

    def get_by_topic(self, topic: str) -> list[Shell]:
        return [s for s in self._shells.values() if s.topic == topic]

    def add_evidence(self, shell_id: str, signal: Signal, strength: float = 0.5) -> None:
        """Add evidence signal to a shell, increasing confidence."""
        shell = self._shells.get(shell_id)
        if not shell:
            return
        shell.raw_signals.append(signal)
        delta = EVIDENCE_BASE_DELTA * strength
        self._update_confidence(shell, delta, f"evidence: {signal.signal_type}")

    def record_interaction(self, shell_id: str, interaction_type: InteractionType, feedback_text: str = "") -> None:
        """Record user interaction and update confidence accordingly."""
        shell = self._shells.get(shell_id)
        if not shell:
            return
        interaction = Interaction(interaction_type=interaction_type, feedback_text=feedback_text)
        shell.user_interactions.append(interaction)

        delta_map = {
            InteractionType.CONFIRM: CONFIRM_DELTA,
            InteractionType.DENY: DENY_DELTA,
            InteractionType.IGNORE: IGNORE_DELTA,
            InteractionType.TAP: IGNORE_DELTA,
        }
        delta = delta_map.get(interaction_type, 0.0)
        self._update_confidence(shell, delta, f"interaction: {interaction_type.value}")

    def merge_or_add(self, new_shell: Shell) -> Shell:
        """If a shell with same topic exists, merge. Otherwise add."""
        existing = self.get_by_topic(new_shell.topic)
        if existing:
            target = existing[0]
            # Merge: combine signals, boost confidence
            target.raw_signals.extend(new_shell.raw_signals)
            delta = MERGE_BONUS + (new_shell.confidence * 0.2)
            self._update_confidence(target, delta, f"merged with {new_shell.pattern.value}")
            if new_shell.pattern != target.pattern:
                target.related_shells.append(f"{new_shell.pattern.value}")
            return target
        else:
            self.add(new_shell)
            return new_shell

    def _update_confidence(self, shell: Shell, delta: float, reason: str) -> None:
        old = shell.confidence
        shell.confidence = max(CONFIDENCE_MIN, min(CONFIDENCE_MAX, shell.confidence + delta))
        shell.confidence_history.append((time.time(), shell.confidence, reason))
        shell.last_updated = time.time()
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_vault.py -v`
Expected: All 14 tests PASS

**Step 5: Commit**

```bash
cd /Users/michael/wish-engine && git add wish_engine/compass/vault.py tests/test_compass_vault.py && git commit -m "feat: add Secret Vault with confidence management and shell merging

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Trigger Engine — decides when to surface shells

**Files:**
- Create: `wish_engine/compass/trigger.py`
- Test: `tests/test_compass_trigger.py`

**Step 1: Write the failing test**

Create `tests/test_compass_trigger.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_trigger.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `wish_engine/compass/trigger.py`:

```python
"""Trigger Engine — decides when to surface shells to the user.

4 trigger conditions:
  1. Decision request — user uses decision language
  2. Topic related — current conversation matches shell topic
  3. Emotional ready — low distress, high openness
  4. Overdue — high confidence shell waiting too long

Safety gates:
  - No trigger during crisis (distress > 0.8)
  - No trigger for seed-stage shells
  - Cooldown after denial (7 days)
  - Max 1 trigger per session

Zero LLM.
"""

from __future__ import annotations

import re
import time
from typing import Any

from wish_engine.compass.models import (
    InteractionType,
    Shell,
    ShellStage,
    TriggerEvent,
    TriggerType,
)

# ── Constants ────────────────────────────────────────────────────────────────

CRISIS_DISTRESS_THRESHOLD = 0.8
DENY_COOLDOWN_DAYS = 7
OVERDUE_DAYS = 7
OVERDUE_CONFIDENCE_THRESHOLD = 0.85
MIN_TRIGGER_STAGE = ShellStage.BUD  # only bud+ can be triggered

# Decision language patterns (multilingual)
_DECISION_PATTERNS = re.compile(
    r"该不该|应不应该|要不要|选.还是.|should\s+I|"
    r"or\s+should|what\s+should|هل\s+يجب|"
    r"是否应该|我在犹豫|I'm\s+torn|can't\s+decide",
    re.IGNORECASE,
)


class TriggerEngine:
    """Decides when to surface shells to the user."""

    def __init__(self):
        self._triggered_sessions: set[str] = set()

    def should_trigger(self, shell: Shell, context: dict[str, Any]) -> TriggerEvent | None:
        """Check if a shell should be surfaced given current context.

        Args:
            shell: The shell to evaluate.
            context: Current session context with keys:
                - current_text: str (user's latest message)
                - session_id: str
                - distress: float
                - topics_mentioned: list[str]

        Returns:
            TriggerEvent if should trigger, None otherwise.
        """
        session_id = context.get("session_id", "")

        # ── Safety gates ──────────────────────────────────────────────
        if not self._passes_safety(shell, context):
            return None

        # ── Check trigger conditions ──────────────────────────────────
        text = context.get("current_text", "")
        topics = context.get("topics_mentioned", [])

        # 1. Decision request
        if _DECISION_PATTERNS.search(text):
            # Check topic relevance for decision
            if self._topic_overlap(shell.topic, text, topics):
                return TriggerEvent(
                    trigger_type=TriggerType.DECISION_REQUEST,
                    session_id=session_id,
                    shell_id=shell.id,
                    revelation_text="",  # filled by Revelation Renderer
                )

        # 2. Topic related
        if self._topic_overlap(shell.topic, text, topics):
            return TriggerEvent(
                trigger_type=TriggerType.TOPIC_RELATED,
                session_id=session_id,
                shell_id=shell.id,
                revelation_text="",
            )

        # 3. Overdue
        age_days = (time.time() - shell.created_at) / 86400
        if shell.confidence >= OVERDUE_CONFIDENCE_THRESHOLD and age_days >= OVERDUE_DAYS:
            return TriggerEvent(
                trigger_type=TriggerType.OVERDUE,
                session_id=session_id,
                shell_id=shell.id,
                revelation_text="",
            )

        return None

    def mark_triggered(self, session_id: str) -> None:
        """Mark session as having received a trigger (max 1 per session)."""
        self._triggered_sessions.add(session_id)

    def _passes_safety(self, shell: Shell, context: dict[str, Any]) -> bool:
        """Check all safety gates."""
        session_id = context.get("session_id", "")
        distress = context.get("distress", 0.0)

        # Crisis gate
        if distress >= CRISIS_DISTRESS_THRESHOLD:
            return False

        # Stage gate — only bud+ can be triggered
        if shell.stage in (ShellStage.SEED, ShellStage.SPROUT):
            return False

        # Session limit
        if session_id in self._triggered_sessions:
            return False

        # Denial cooldown
        for interaction in shell.user_interactions:
            if interaction.interaction_type == InteractionType.DENY:
                days_since = (time.time() - interaction.timestamp) / 86400
                if days_since < DENY_COOLDOWN_DAYS:
                    return False

        return True

    def _topic_overlap(self, shell_topic: str, text: str, topics: list[str]) -> bool:
        """Check if shell topic appears in current text or mentioned topics."""
        topic_lower = shell_topic.lower()
        if topic_lower in text.lower():
            return True
        for t in topics:
            if topic_lower in t.lower() or t.lower() in topic_lower:
                return True
        return False
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_trigger.py -v`
Expected: All 10 tests PASS

**Step 5: Commit**

```bash
cd /Users/michael/wish-engine && git add wish_engine/compass/trigger.py tests/test_compass_trigger.py && git commit -m "feat: add Trigger Engine with 4 conditions and safety gates

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Revelation Renderer — B+C style text generation

**Files:**
- Create: `wish_engine/compass/revelation.py`
- Test: `tests/test_compass_revelation.py`

**Step 1: Write the failing test**

Create `tests/test_compass_revelation.py`:

```python
"""Tests for Revelation Renderer — B+C style text generation."""

import pytest
from wish_engine.compass.models import (
    ContradictionPattern,
    Shell,
    ShellStage,
)
from wish_engine.compass.revelation import (
    RevelationRenderer,
    RevelationStyle,
    Revelation,
)


class TestRevelationStyle:
    def test_sprout_gets_metaphor(self):
        renderer = RevelationRenderer()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.35)
        rev = renderer.render(shell)
        assert rev.style == RevelationStyle.METAPHOR

    def test_bud_gets_question(self):
        renderer = RevelationRenderer()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.55)
        rev = renderer.render(shell)
        assert rev.style == RevelationStyle.QUESTION

    def test_bloom_gets_gentle_statement(self):
        renderer = RevelationRenderer()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.75)
        rev = renderer.render(shell)
        assert rev.style == RevelationStyle.GENTLE_STATEMENT


class TestRevelationContent:
    def test_metaphor_is_vague(self):
        renderer = RevelationRenderer()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="hidden_topic", confidence=0.35)
        rev = renderer.render(shell)
        # Metaphor should NOT mention the topic directly
        assert "hidden_topic" not in rev.text

    def test_question_mentions_topic(self):
        renderer = RevelationRenderer()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.55)
        rev = renderer.render(shell)
        assert "Rhett" in rev.text or "?" in rev.text or "？" in rev.text

    def test_gentle_statement_has_content(self):
        renderer = RevelationRenderer()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.75)
        rev = renderer.render(shell)
        assert len(rev.text) > 20

    def test_different_patterns_different_text(self):
        renderer = RevelationRenderer()
        s1 = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="X", confidence=0.6)
        s2 = Shell(pattern=ContradictionPattern.VALUE_CONFLICT, topic="X", confidence=0.6)
        r1 = renderer.render(s1)
        r2 = renderer.render(s2)
        assert r1.text != r2.text


class TestSensitivity:
    def test_high_sensitivity_stays_question(self):
        renderer = RevelationRenderer()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.8)
        rev = renderer.render(shell, sensitivity="high")
        # High sensitivity should use question style even at bloom
        assert rev.style == RevelationStyle.QUESTION

    def test_low_sensitivity_allows_statement(self):
        renderer = RevelationRenderer()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="cooking", confidence=0.75)
        rev = renderer.render(shell, sensitivity="low")
        assert rev.style == RevelationStyle.GENTLE_STATEMENT


class TestRevelationModel:
    def test_revelation_fields(self):
        renderer = RevelationRenderer()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="test", confidence=0.5)
        rev = renderer.render(shell)
        assert isinstance(rev, Revelation)
        assert rev.shell_id == shell.id
        assert rev.style is not None
        assert len(rev.text) > 0
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_revelation.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `wish_engine/compass/revelation.py`:

```python
"""Revelation Renderer — generates B+C style text for shell revelations.

Three styles based on maturity and sensitivity:
  C (Metaphor): "有一颗很远的星在靠近你..." — vague, poetic, for sprout
  B (Question): "你有没有注意到...?" — suggestive, for bud
  Gentle Statement: "你的星星发现了..." — warm, for bloom

High-sensitivity topics always cap at Question style.
Zero LLM for template rendering. 1× Haiku optional for personalization (future).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from wish_engine.compass.models import (
    ContradictionPattern,
    Shell,
    ShellStage,
)


class RevelationStyle(str, Enum):
    METAPHOR = "metaphor"             # C style — vague, poetic
    QUESTION = "question"             # B style — suggestive question
    GENTLE_STATEMENT = "gentle_statement"  # warm statement


class Revelation(BaseModel):
    """The text output shown to the user."""

    shell_id: str
    style: RevelationStyle
    text: str


# ── Template bank ────────────────────────────────────────────────────────────

_METAPHOR_TEMPLATES = [
    "有一颗很远的星正在靠近你...它带着一个你还没注意到的信号。",
    "星图深处有一点微光在闪烁，像是某个还没成形的念头。",
    "A distant star is drawing closer... it carries something you haven't noticed yet.",
]

_QUESTION_TEMPLATES: dict[ContradictionPattern, str] = {
    ContradictionPattern.EMOTION_ANOMALY: "你有没有注意到，每次提到{topic}，你的感受和提到其他人时很不一样？",
    ContradictionPattern.MOUTH_HARD_HEART_SOFT: "你说你不在意{topic}，但你提到它时的情绪似乎在说另一件事？",
    ContradictionPattern.SAY_ONE_DO_OTHER: "你说你不需要{topic}，但你的选择好像一直在靠近它？",
    ContradictionPattern.REPEATED_PROBING: "你已经好几次提到{topic}了，每次都说不重要——但它好像一直在你心里？",
    ContradictionPattern.VALUE_CONFLICT: "你看重自由，但最近的选择好像都在追求安全感——你有注意到这个矛盾吗？",
    ContradictionPattern.AVOIDANCE_SIGNAL: "每次聊到{topic}附近的话题，你好像会不自觉地转开——有什么让你不想面对的吗？",
    ContradictionPattern.GROWTH_GAP: "你最近在某个方面成长了很多，但行动上好像还没跟上——你有感觉到这个缝隙吗？",
}

_GENTLE_TEMPLATES: dict[ContradictionPattern, str] = {
    ContradictionPattern.EMOTION_ANOMALY: "你的星星发现了一件事：你对{topic}的在意，可能远超你意识到的。",
    ContradictionPattern.MOUTH_HARD_HEART_SOFT: "你的星星替你记住了一个秘密：关于{topic}，你嘴上说的和心里感受的不太一样。",
    ContradictionPattern.SAY_ONE_DO_OTHER: "你的星星注意到，{topic}在你的生活中比你承认的重要得多。",
    ContradictionPattern.REPEATED_PROBING: "有一件事你反复提起又反复放下——关于{topic}，也许是时候认真想想了。",
    ContradictionPattern.VALUE_CONFLICT: "你的星星发现了一个内心拉扯：你想要的和你选择的之间，有一段距离。",
    ContradictionPattern.AVOIDANCE_SIGNAL: "你的星星发现你一直在回避某个方向——也许那里有你需要面对的东西。",
    ContradictionPattern.GROWTH_GAP: "你内心的某一部分已经在成长了——你的行动准备好跟上了吗？",
}


def _select_style(shell: Shell, sensitivity: str = "medium") -> RevelationStyle:
    """Select revelation style based on shell stage and topic sensitivity."""
    stage = shell.stage

    # High sensitivity caps at Question even for bloom
    if sensitivity == "high":
        if stage == ShellStage.SPROUT:
            return RevelationStyle.METAPHOR
        return RevelationStyle.QUESTION

    # Normal progression
    if stage == ShellStage.SPROUT:
        return RevelationStyle.METAPHOR
    elif stage == ShellStage.BUD:
        return RevelationStyle.QUESTION
    else:  # BLOOM
        return RevelationStyle.GENTLE_STATEMENT


class RevelationRenderer:
    """Generates revelation text for shells based on maturity and sensitivity."""

    def render(self, shell: Shell, sensitivity: str = "medium") -> Revelation:
        """Generate revelation text for a shell.

        Args:
            shell: The shell to render.
            sensitivity: "low", "medium", or "high" — affects style selection.

        Returns:
            Revelation with style and text.
        """
        style = _select_style(shell, sensitivity)

        if style == RevelationStyle.METAPHOR:
            text = _METAPHOR_TEMPLATES[0]
        elif style == RevelationStyle.QUESTION:
            template = _QUESTION_TEMPLATES.get(
                shell.pattern,
                "你有没有注意到，关于{topic}，你的感受可能比你以为的更复杂？",
            )
            text = template.format(topic=shell.topic)
        else:  # GENTLE_STATEMENT
            template = _GENTLE_TEMPLATES.get(
                shell.pattern,
                "你的星星发现了一件关于{topic}的事——它可能比你想的更重要。",
            )
            text = template.format(topic=shell.topic)

        return Revelation(
            shell_id=shell.id,
            style=style,
            text=text,
        )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_revelation.py -v`
Expected: All 9 tests PASS

**Step 5: Commit**

```bash
cd /Users/michael/wish-engine && git add wish_engine/compass/revelation.py tests/test_compass_revelation.py && git commit -m "feat: add Revelation Renderer with B+C style templates per pattern

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Star rendering for compass shells

**Files:**
- Create: `wish_engine/compass/star_render.py`
- Test: `tests/test_compass_star_render.py`

**Step 1: Write the failing test**

Create `tests/test_compass_star_render.py`:

```python
"""Tests for Compass star rendering — visual state for shells on the star map."""

import pytest
from wish_engine.compass.models import ContradictionPattern, Shell, ShellStage
from wish_engine.compass.star_render import render_shell_star, CompassStarOutput


class TestShellStarRendering:
    def test_seed_not_rendered(self):
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.15)
        result = render_shell_star(shell)
        assert result is None  # seed = invisible

    def test_sprout_rendered(self):
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.35)
        result = render_shell_star(shell)
        assert result is not None
        assert result.color == "#2A2035"
        assert result.animation == "flicker_rare"

    def test_bud_rendered(self):
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.55)
        result = render_shell_star(shell)
        assert result is not None
        assert result.color == "#5B4A8A"
        assert result.animation == "pulse_slow"

    def test_bloom_rendered(self):
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="x", confidence=0.75)
        result = render_shell_star(shell)
        assert result is not None
        assert result.color == "#E8A0BF"
        assert result.animation == "glow_warm"

    def test_output_has_shell_id(self):
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="test", confidence=0.5)
        result = render_shell_star(shell)
        assert result.shell_id == shell.id

    def test_output_has_stage(self):
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="test", confidence=0.6)
        result = render_shell_star(shell)
        assert result.stage == ShellStage.BUD
```

**Step 2: Run test to verify it fails**

**Step 3: Write minimal implementation**

Create `wish_engine/compass/star_render.py`:

```python
"""Compass star rendering — visual state for shells on the star map.

Shell-specific colors distinguish compass stars from L1/L2/L3 wish stars:
  - sprout: deep purple #2A2035, rare flicker
  - bud: dark purple #5B4A8A, slow pulse
  - bloom: rose gold #E8A0BF, warm glow

Zero LLM.
"""

from __future__ import annotations

from pydantic import BaseModel

from wish_engine.compass.models import Shell, ShellStage

# ── Visual mapping ───────────────────────────────────────────────────────────

_STAGE_COLORS: dict[ShellStage, str] = {
    ShellStage.SPROUT: "#2A2035",   # deep purple
    ShellStage.BUD: "#5B4A8A",      # dark purple
    ShellStage.BLOOM: "#E8A0BF",    # rose gold
}

_STAGE_ANIMATIONS: dict[ShellStage, str] = {
    ShellStage.SPROUT: "flicker_rare",   # 10s interval
    ShellStage.BUD: "pulse_slow",        # 4s cycle
    ShellStage.BLOOM: "glow_warm",       # 2s cycle
}

_STAGE_DURATION_MS: dict[ShellStage, int] = {
    ShellStage.SPROUT: 10000,
    ShellStage.BUD: 4000,
    ShellStage.BLOOM: 2000,
}


class CompassStarOutput(BaseModel):
    """Visual output for a compass shell on the star map."""

    shell_id: str
    stage: ShellStage
    color: str
    animation: str
    animation_duration_ms: int


def render_shell_star(shell: Shell) -> CompassStarOutput | None:
    """Render a shell as a star map visual. Returns None for seed (invisible)."""
    if shell.stage == ShellStage.SEED:
        return None

    return CompassStarOutput(
        shell_id=shell.id,
        stage=shell.stage,
        color=_STAGE_COLORS[shell.stage],
        animation=_STAGE_ANIMATIONS[shell.stage],
        animation_duration_ms=_STAGE_DURATION_MS[shell.stage],
    )
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_star_render.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
cd /Users/michael/wish-engine && git add wish_engine/compass/star_render.py tests/test_compass_star_render.py && git commit -m "feat: add Compass star rendering (sprout/bud/bloom visual states)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Compass facade — unified entry point

**Files:**
- Create: `wish_engine/compass/compass.py`
- Modify: `wish_engine/compass/__init__.py`
- Test: `tests/test_compass_integration.py`

**Step 1: Write the failing test**

Create `tests/test_compass_integration.py`:

```python
"""Integration tests for the Wish Compass — full pipeline."""

import pytest
from wish_engine.models import DetectorResults, EmotionState
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import ShellStage, ContradictionPattern


class TestCompassScan:
    def test_scan_detects_emotion_anomaly(self):
        compass = WishCompass()
        result = compass.scan(
            topics=[
                {"entity": "Rhett", "sentiment": "negative", "arousal": 0.8, "mentions": 3},
            ],
            detector_results=DetectorResults(),
            session_id="s1",
        )
        assert result.new_shells >= 1
        assert len(compass.vault.all_shells) >= 1

    def test_scan_accumulates_over_sessions(self):
        compass = WishCompass()
        compass.scan(
            topics=[{"entity": "Rhett", "sentiment": "negative", "arousal": 0.75, "mentions": 2}],
            detector_results=DetectorResults(),
            session_id="s1",
        )
        compass.scan(
            topics=[{"entity": "Rhett", "sentiment": "negative", "arousal": 0.80, "mentions": 3}],
            detector_results=DetectorResults(),
            session_id="s2",
        )
        rhett_shells = compass.vault.get_by_topic("Rhett")
        assert len(rhett_shells) == 1  # merged, not duplicated
        assert rhett_shells[0].confidence > 0.25  # grew from evidence

    def test_no_shells_for_normal_conversation(self):
        compass = WishCompass()
        result = compass.scan(
            topics=[{"entity": "weather", "sentiment": "neutral", "arousal": 0.2, "mentions": 1}],
            detector_results=DetectorResults(),
            session_id="s1",
        )
        assert result.new_shells == 0


class TestCompassTrigger:
    def test_trigger_at_bud_stage(self):
        compass = WishCompass()
        # Manually add a bud-stage shell
        from wish_engine.compass.models import Shell
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.6)
        compass.vault.add(shell)

        revelation = compass.check_trigger(
            current_text="我该选 Ashley 还是 Rhett？",
            session_id="s5",
            distress=0.2,
            topics_mentioned=["Rhett", "Ashley"],
        )
        assert revelation is not None
        assert "Rhett" in revelation.text or "？" in revelation.text

    def test_no_trigger_during_crisis(self):
        compass = WishCompass()
        from wish_engine.compass.models import Shell
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.6)
        compass.vault.add(shell)

        revelation = compass.check_trigger(
            current_text="我该选谁？",
            session_id="s5",
            distress=0.9,
            topics_mentioned=["Rhett"],
        )
        assert revelation is None


class TestCompassFeedback:
    def test_confirm_increases_confidence(self):
        compass = WishCompass()
        from wish_engine.compass.models import Shell
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="test", confidence=0.5)
        compass.vault.add(shell)
        old_conf = shell.confidence
        compass.record_feedback(shell.id, "confirm")
        assert compass.vault.get(shell.id).confidence > old_conf

    def test_deny_decreases_confidence(self):
        compass = WishCompass()
        from wish_engine.compass.models import Shell
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="test", confidence=0.5)
        compass.vault.add(shell)
        compass.record_feedback(shell.id, "deny")
        assert compass.vault.get(shell.id).confidence < 0.5


class TestCompassStarMap:
    def test_get_visible_stars(self):
        compass = WishCompass()
        from wish_engine.compass.models import Shell
        compass.vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="seed", confidence=0.15))
        compass.vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="visible", confidence=0.4))
        stars = compass.get_star_renders()
        assert len(stars) == 1
        assert stars[0].stage == ShellStage.SPROUT


class TestCompassSummary:
    def test_summary(self):
        compass = WishCompass()
        from wish_engine.compass.models import Shell
        compass.vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="a", confidence=0.15))
        compass.vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="b", confidence=0.4))
        compass.vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="c", confidence=0.75))
        s = compass.summary()
        assert s["total_shells"] == 3
        assert s["seeds"] == 1
        assert s["sprouts"] == 1
        assert s["blooms"] == 1
```

**Step 2: Run test to verify it fails**

**Step 3: Write minimal implementation**

Create `wish_engine/compass/compass.py`:

```python
"""WishCompass — unified facade for the Compass pipeline.

Usage:
    compass = WishCompass()

    # After each session
    result = compass.scan(topics=[...], detector_results=det, session_id="s1")

    # During conversation (check if should surface a shell)
    revelation = compass.check_trigger(current_text="...", session_id="s1", distress=0.2, topics_mentioned=[...])

    # After user feedback
    compass.record_feedback(shell_id, "confirm")

    # For star map rendering
    stars = compass.get_star_renders()
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from wish_engine.models import DetectorResults
from wish_engine.compass.models import (
    InteractionType,
    Shell,
    ShellStage,
)
from wish_engine.compass.contradiction import ContradictionDetector
from wish_engine.compass.vault import SecretVault
from wish_engine.compass.trigger import TriggerEngine
from wish_engine.compass.revelation import RevelationRenderer, Revelation
from wish_engine.compass.star_render import CompassStarOutput, render_shell_star


class ScanResult(BaseModel):
    """Result of a compass scan."""

    new_shells: int = 0
    updated_shells: int = 0
    total_shells: int = 0


class WishCompass:
    """Unified facade for the Wish Compass pipeline."""

    def __init__(self):
        self.vault = SecretVault()
        self._detector = ContradictionDetector()
        self._trigger = TriggerEngine()
        self._renderer = RevelationRenderer()
        self._history: dict[str, Any] = {
            "average_arousal": 0.35,
            "entity_history": {},
        }

    def scan(
        self,
        topics: list[dict[str, Any]],
        detector_results: DetectorResults,
        session_id: str = "",
        known_wishes: list[dict[str, Any]] | None = None,
    ) -> ScanResult:
        """Run daily scan on session data to discover new shells.

        Args:
            topics: List of discussed topics with entity, sentiment, arousal, mentions.
            detector_results: Current 16-dimension detector results.
            session_id: Current session ID.
            known_wishes: Already expressed wishes to filter out.

        Returns:
            ScanResult with counts of new/updated shells.
        """
        signals = {
            "topics": topics,
            "detector_results": detector_results,
            "session_id": session_id,
        }
        shells = self._detector.detect(signals, self._history, known_wishes or [])

        new_count = 0
        updated_count = 0
        for shell in shells:
            existing = self.vault.get_by_topic(shell.topic)
            if existing:
                self.vault.merge_or_add(shell)
                updated_count += 1
            else:
                self.vault.add(shell)
                new_count += 1

        # Update history with entity info for future scans
        for topic in topics:
            entity = topic.get("entity", "")
            if entity:
                ent_hist = self._history["entity_history"].setdefault(entity, {
                    "session_count": 0,
                    "avg_sentiment": "",
                    "avg_arousal": 0.0,
                })
                ent_hist["session_count"] += 1
                ent_hist["avg_sentiment"] = topic.get("sentiment", "")
                ent_hist["avg_arousal"] = topic.get("arousal", 0.0)

        return ScanResult(
            new_shells=new_count,
            updated_shells=updated_count,
            total_shells=len(self.vault.all_shells),
        )

    def check_trigger(
        self,
        current_text: str,
        session_id: str,
        distress: float = 0.0,
        topics_mentioned: list[str] | None = None,
    ) -> Revelation | None:
        """Check if any shell should be surfaced in current context.

        Returns Revelation if triggered, None otherwise.
        """
        context = {
            "current_text": current_text,
            "session_id": session_id,
            "distress": distress,
            "topics_mentioned": topics_mentioned or [],
        }

        # Check all bud+ shells for trigger
        for shell in self.vault.visible_shells:
            event = self._trigger.should_trigger(shell, context)
            if event:
                self._trigger.mark_triggered(session_id)
                revelation = self._renderer.render(shell)
                shell.trigger_history.append(event)
                return revelation
        return None

    def record_feedback(self, shell_id: str, feedback: str) -> None:
        """Record user feedback on a revelation.

        Args:
            shell_id: The shell that was revealed.
            feedback: "confirm", "deny", or "ignore".
        """
        type_map = {
            "confirm": InteractionType.CONFIRM,
            "deny": InteractionType.DENY,
            "ignore": InteractionType.IGNORE,
        }
        itype = type_map.get(feedback, InteractionType.IGNORE)
        self.vault.record_interaction(shell_id, itype)

    def get_star_renders(self) -> list[CompassStarOutput]:
        """Get star map renders for all visible shells."""
        renders = []
        for shell in self.vault.visible_shells:
            star = render_shell_star(shell)
            if star:
                renders.append(star)
        return renders

    def summary(self) -> dict[str, int]:
        """Summary of compass state."""
        shells = self.vault.all_shells
        return {
            "total_shells": len(shells),
            "seeds": sum(1 for s in shells if s.stage == ShellStage.SEED),
            "sprouts": sum(1 for s in shells if s.stage == ShellStage.SPROUT),
            "buds": sum(1 for s in shells if s.stage == ShellStage.BUD),
            "blooms": sum(1 for s in shells if s.stage == ShellStage.BLOOM),
        }
```

Update `wish_engine/compass/__init__.py`:

```python
"""Wish Compass — detects hidden desires from behavioral contradictions."""

from wish_engine.compass.models import (
    Shell,
    ShellStage,
    Signal,
    ContradictionPattern,
    Interaction,
    InteractionType,
    TriggerEvent,
    TriggerType,
)
from wish_engine.compass.contradiction import ContradictionDetector
from wish_engine.compass.vault import SecretVault
from wish_engine.compass.trigger import TriggerEngine
from wish_engine.compass.revelation import RevelationRenderer, Revelation, RevelationStyle
from wish_engine.compass.star_render import render_shell_star, CompassStarOutput
from wish_engine.compass.compass import WishCompass, ScanResult

__all__ = [
    "Shell",
    "ShellStage",
    "Signal",
    "ContradictionPattern",
    "Interaction",
    "InteractionType",
    "TriggerEvent",
    "TriggerType",
    "ContradictionDetector",
    "SecretVault",
    "TriggerEngine",
    "RevelationRenderer",
    "Revelation",
    "RevelationStyle",
    "render_shell_star",
    "CompassStarOutput",
    "WishCompass",
    "ScanResult",
]
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_integration.py -v`
Expected: All 8 tests PASS

**Step 5: Run full suite**

Run: `cd /Users/michael/wish-engine && python3 -m pytest --ignore=tests/test_agent_negotiator.py --ignore=tests/test_e2e.py --ignore=tests/test_l3_matcher.py --tb=short -q`
Expected: 620+ passed

**Step 6: Commit**

```bash
cd /Users/michael/wish-engine && git add wish_engine/compass/ tests/test_compass_integration.py && git commit -m "feat: add WishCompass facade — unified pipeline for shell discovery and revelation

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Scarlett experiment script

**Files:**
- Create: `scripts/scarlett_experiment.py`
- Test: `tests/test_scarlett_experiment.py`

**Step 1: Write the failing test**

Create `tests/test_scarlett_experiment.py`:

```python
"""Tests for the Scarlett Compass experiment — validates system detects Rhett feelings."""

import json
import pytest
from pathlib import Path
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import ShellStage


FIXTURE_PATH = Path("/Users/michael/soulgraph/fixtures/scarlett_full.jsonl")


@pytest.mark.skipif(not FIXTURE_PATH.exists(), reason="Scarlett fixture not available")
class TestScarlettExperiment:
    def _load_dialogues(self) -> list[dict]:
        lines = []
        with open(FIXTURE_PATH) as f:
            for line in f:
                lines.append(json.loads(line.strip()))
        return lines

    def _simulate_topic(self, dialogue: dict) -> dict:
        """Convert a dialogue line to a topic signal for the compass."""
        text = dialogue["text"].lower()
        # Detect entity mentions
        entity = "other"
        arousal = 0.3
        sentiment = "neutral"

        if "rhett" in text or "butler" in text:
            entity = "Rhett"
            arousal = 0.7 if any(w in text for w in ["fool", "cad", "hate", "furious", "dare"]) else 0.5
            sentiment = "negative" if any(w in text for w in ["hate", "horrible", "fool", "cad", "don't care"]) else "mixed"
        elif "ashley" in text or "wilkes" in text:
            entity = "Ashley"
            arousal = 0.4 if "love" in text else 0.3
            sentiment = "positive" if "love" in text else "neutral"

        return {
            "entity": entity,
            "sentiment": sentiment,
            "arousal": arousal,
            "mentions": 1,
        }

    def test_rhett_shell_emerges_before_phase5(self):
        """Core validation: system detects Rhett feelings before Scarlett does."""
        compass = WishCompass()
        dialogues = self._load_dialogues()

        rhett_first_detected = None
        rhett_bud_reached = None

        for i, dialogue in enumerate(dialogues):
            topic = self._simulate_topic(dialogue)
            if topic["entity"] == "other":
                continue

            from wish_engine.models import DetectorResults
            compass.scan(
                topics=[topic],
                detector_results=DetectorResults(),
                session_id=f"session_{i}",
            )

            rhett_shells = compass.vault.get_by_topic("Rhett")
            if rhett_shells and rhett_first_detected is None:
                rhett_first_detected = i

            if rhett_shells and rhett_shells[0].stage in (ShellStage.BUD, ShellStage.BLOOM):
                if rhett_bud_reached is None:
                    rhett_bud_reached = i

        # Rhett shell should be detected (at least seed)
        assert rhett_first_detected is not None, "System never detected Rhett feelings"

        # Should be detected before the last 20% of dialogues (Phase 5)
        total = len(dialogues)
        phase5_start = int(total * 0.8)
        assert rhett_first_detected < phase5_start, (
            f"Detected too late: dialogue {rhett_first_detected}/{total}"
        )

    def test_ashley_not_flagged_as_hidden(self):
        """Ashley is a stated wish, not a hidden one — should not become a shell."""
        compass = WishCompass()
        dialogues = self._load_dialogues()

        for i, dialogue in enumerate(dialogues[:30]):  # Phase 1 only
            topic = self._simulate_topic(dialogue)
            if topic["entity"] == "other":
                continue
            from wish_engine.models import DetectorResults
            compass.scan(
                topics=[topic],
                detector_results=DetectorResults(),
                session_id=f"session_{i}",
            )

        ashley_shells = compass.vault.get_by_topic("Ashley")
        # Ashley should NOT become a contradiction shell (her love for Ashley is stated, not hidden)
        # If Ashley shells exist, they should be low confidence
        if ashley_shells:
            assert ashley_shells[0].confidence < 0.3

    def test_compass_summary_reasonable(self):
        """After full run, compass should have reasonable shell counts."""
        compass = WishCompass()
        dialogues = self._load_dialogues()

        for i, dialogue in enumerate(dialogues):
            topic = self._simulate_topic(dialogue)
            if topic["entity"] == "other":
                continue
            from wish_engine.models import DetectorResults
            compass.scan(
                topics=[topic],
                detector_results=DetectorResults(),
                session_id=f"session_{i}",
            )

        summary = compass.summary()
        assert summary["total_shells"] >= 1
        assert summary["total_shells"] <= 10  # not too many (noise control)
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_scarlett_experiment.py -v`
Expected: FAIL — tests should fail since experiment logic doesn't exist yet

**Step 3: Create experiment script**

Create `scripts/scarlett_experiment.py`:

```python
#!/usr/bin/env python3
"""Scarlett Compass Experiment — validates Wish Compass on Gone with the Wind.

Feeds scarlett_full.jsonl through the Compass pipeline and records:
- When Rhett shell first appears (seed)
- When it reaches sprout, bud, bloom
- Confidence curve over dialogues
- Trigger events and revelations

Usage:
    python3 scripts/scarlett_experiment.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import DetectorResults
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import ShellStage

FIXTURE_PATH = Path("/Users/michael/soulgraph/fixtures/scarlett_full.jsonl")
OUTPUT_DIR = Path("/Users/michael/wish-engine/experiment_results")


def load_dialogues() -> list[dict]:
    lines = []
    with open(FIXTURE_PATH) as f:
        for line in f:
            lines.append(json.loads(line.strip()))
    return lines


def simulate_topic(dialogue: dict) -> dict | None:
    """Convert dialogue to topic signal. Returns None for irrelevant lines."""
    text = dialogue["text"].lower()
    entity = None
    arousal = 0.3
    sentiment = "neutral"

    # Rhett detection
    rhett_words = ["rhett", "butler", "captain butler"]
    ashley_words = ["ashley", "wilkes", "mr. wilkes"]
    negative_words = ["hate", "horrible", "fool", "cad", "don't care", "never", "furious", "dare"]
    positive_words = ["love", "want", "need", "miss", "beautiful", "admire"]

    is_rhett = any(w in text for w in rhett_words)
    is_ashley = any(w in text for w in ashley_words)

    if is_rhett:
        entity = "Rhett"
        has_negative = any(w in text for w in negative_words)
        has_positive = any(w in text for w in positive_words)
        # Key insight: negative words about Rhett with high emotional content = contradiction
        arousal = 0.75 if has_negative else (0.6 if has_positive else 0.45)
        sentiment = "negative" if has_negative else ("positive" if has_positive else "mixed")
    elif is_ashley:
        entity = "Ashley"
        has_positive = any(w in text for w in positive_words)
        arousal = 0.45 if has_positive else 0.3
        sentiment = "positive" if has_positive else "neutral"
    else:
        return None

    return {
        "entity": entity,
        "sentiment": sentiment,
        "arousal": arousal,
        "mentions": 1,
    }


def run_experiment():
    dialogues = load_dialogues()
    compass = WishCompass()

    timeline = []
    rhett_milestones = {}

    print(f"Loaded {len(dialogues)} dialogues from scarlett_full.jsonl")
    print("=" * 60)

    for i, dialogue in enumerate(dialogues):
        topic = simulate_topic(dialogue)
        if not topic:
            continue

        result = compass.scan(
            topics=[topic],
            detector_results=DetectorResults(),
            session_id=f"session_{i}",
        )

        # Track Rhett shell
        rhett_shells = compass.vault.get_by_topic("Rhett")
        rhett_conf = rhett_shells[0].confidence if rhett_shells else 0.0
        rhett_stage = rhett_shells[0].stage.value if rhett_shells else "none"

        entry = {
            "dialogue_num": i,
            "phase": dialogue.get("chapter_phase", 0),
            "text_preview": dialogue["text"][:60],
            "topic_entity": topic["entity"],
            "topic_sentiment": topic["sentiment"],
            "topic_arousal": topic["arousal"],
            "rhett_confidence": rhett_conf,
            "rhett_stage": rhett_stage,
            "new_shells": result.new_shells,
            "total_shells": result.total_shells,
        }
        timeline.append(entry)

        # Record milestones
        if rhett_shells:
            stage = rhett_shells[0].stage.value
            if stage not in rhett_milestones:
                rhett_milestones[stage] = i
                print(f"  ★ Rhett shell reached {stage.upper()} at dialogue #{i} "
                      f"(confidence={rhett_conf:.2f}, phase={dialogue.get('chapter_phase', '?')})")

        # Check trigger on decision-like dialogue
        if any(w in dialogue["text"].lower() for w in ["should", "choose", "which", "选", "该"]):
            revelation = compass.check_trigger(
                current_text=dialogue["text"],
                session_id=f"session_{i}",
                distress=0.2,
                topics_mentioned=[topic["entity"]],
            )
            if revelation:
                print(f"  → TRIGGER at dialogue #{i}: {revelation.text[:80]}...")

    # ── Results ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("EXPERIMENT RESULTS")
    print("=" * 60)

    print(f"\nTotal dialogues processed: {len(dialogues)}")
    print(f"Total shells found: {compass.summary()['total_shells']}")
    print(f"\nRhett milestones:")
    for stage, dial_num in sorted(rhett_milestones.items(), key=lambda x: x[1]):
        pct = dial_num / len(dialogues) * 100
        print(f"  {stage:8s} at dialogue #{dial_num:3d} ({pct:.0f}%)")

    # Phase 5 starts at ~80% of dialogues
    phase5_start = int(len(dialogues) * 0.8)
    bud_num = rhett_milestones.get("bud")
    if bud_num and bud_num < phase5_start:
        lead = phase5_start - bud_num
        print(f"\n✅ SUCCESS: Rhett bud reached {lead} dialogues before Phase 5 (Scarlett's self-awareness)")
    elif bud_num:
        print(f"\n⚠️  Rhett bud reached at dialogue #{bud_num} (Phase 5 starts at #{phase5_start})")
    else:
        print("\n❌ FAIL: Rhett never reached bud stage")

    print(f"\nCompass summary: {compass.summary()}")

    # Save results
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_DIR / "scarlett_compass_timeline.json", "w") as f:
        json.dump(timeline, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_DIR / "scarlett_shells.json", "w") as f:
        shells_data = [
            {"id": s.id, "topic": s.topic, "pattern": s.pattern.value,
             "confidence": s.confidence, "stage": s.stage.value,
             "signals_count": len(s.raw_signals)}
            for s in compass.vault.all_shells
        ]
        json.dump(shells_data, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    run_experiment()
```

**Step 4: Run experiment tests**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_scarlett_experiment.py -v`
Expected: Tests should pass (shell emerges, detected before Phase 5)

**Step 5: Run the experiment script**

Run: `cd /Users/michael/wish-engine && python3 scripts/scarlett_experiment.py`
Expected: Console output showing Rhett milestones, trigger events, and success/fail verdict.

**Step 6: Commit**

```bash
cd /Users/michael/wish-engine && git add scripts/scarlett_experiment.py tests/test_scarlett_experiment.py && git commit -m "feat: add Scarlett experiment — validates Compass detects Rhett feelings

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Full test suite verification + final commit

**Step 1: Run all compass tests**

Run: `cd /Users/michael/wish-engine && python3 -m pytest tests/test_compass_models.py tests/test_compass_contradiction.py tests/test_compass_vault.py tests/test_compass_trigger.py tests/test_compass_revelation.py tests/test_compass_star_render.py tests/test_compass_integration.py tests/test_scarlett_experiment.py -v`
Expected: All ~70 compass tests PASS

**Step 2: Run full project suite**

Run: `cd /Users/michael/wish-engine && python3 -m pytest --ignore=tests/test_agent_negotiator.py --ignore=tests/test_e2e.py --ignore=tests/test_l3_matcher.py --tb=short -q`
Expected: 630+ passed, 0 failures

**Step 3: Run experiment**

Run: `cd /Users/michael/wish-engine && python3 scripts/scarlett_experiment.py`
Expected: Rhett bud reached before Phase 5

---

## Summary

| Task | What | New Tests | Files |
|------|------|-----------|-------|
| 1 | Compass data models | 11 | compass/models.py, compass/__init__.py |
| 2 | Contradiction Detector (7 patterns) | 13 | compass/contradiction.py |
| 3 | Secret Vault (confidence mgmt) | 14 | compass/vault.py |
| 4 | Trigger Engine (4 conditions + safety) | 10 | compass/trigger.py |
| 5 | Revelation Renderer (B+C templates) | 9 | compass/revelation.py |
| 6 | Star rendering (visual states) | 6 | compass/star_render.py |
| 7 | Compass facade (unified pipeline) | 8 | compass/compass.py |
| 8 | Scarlett experiment | 3 | scripts/scarlett_experiment.py |
| 9 | Full verification | 0 | — |
| **Total** | | **~74** | **9 new files** |

**Zero LLM (except optional Haiku for revelation personalization). All local-compute.**
