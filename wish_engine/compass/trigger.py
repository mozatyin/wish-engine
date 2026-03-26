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
