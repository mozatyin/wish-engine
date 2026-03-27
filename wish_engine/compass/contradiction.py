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

AROUSAL_ANOMALY_THRESHOLD = 0.15       # arousal above baseline by this much
MOUTH_HARD_AROUSAL_THRESHOLD = 0.6     # high arousal with negative sentiment
REPEATED_SESSION_THRESHOLD = 3         # topic in 3+ sessions = repeated
EQ_JUMP_THRESHOLD = 0.15              # EQ change > 0.15 = growth gap
SEED_CONFIDENCE = 0.25                # default confidence for new shells


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
                    confidence=min((arousal - avg_arousal) / 0.4 * SEED_CONFIDENCE + 0.05, 0.45),
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
