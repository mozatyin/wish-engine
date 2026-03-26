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
MERGE_BONUS = 0.06               # bonus when merging same-topic shells
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
            # Diminishing returns — bonus shrinks as signals accumulate
            signal_count = len(target.raw_signals)
            diminish = 1.0 / (1.0 + signal_count * 0.02)
            delta = MERGE_BONUS * diminish
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
