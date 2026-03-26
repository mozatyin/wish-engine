"""Tests for Secret Vault — shell storage and confidence management."""

import time
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


class TestTimeDecay:
    def test_decay_after_one_week(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="old", confidence=0.5)
        shell.last_updated = time.time() - 8 * 86400  # 8 days ago
        vault.add(shell)
        decayed = vault.apply_decay()
        assert decayed == 1
        assert vault.get(shell.id).confidence < 0.5

    def test_no_decay_if_recent(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="fresh", confidence=0.5)
        vault.add(shell)
        decayed = vault.apply_decay()
        assert decayed == 0
        assert vault.get(shell.id).confidence == 0.5

    def test_very_low_confidence_shell_removed(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="dying", confidence=0.04)
        shell.last_updated = time.time() - 14 * 86400  # 2 weeks ago
        vault.add(shell)
        vault.apply_decay()
        assert vault.get(shell.id) is None  # removed


class TestConfidenceHistory:
    def test_history_recorded(self):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.3)
        vault.add(shell)
        vault.record_interaction(shell.id, InteractionType.CONFIRM)
        updated = vault.get(shell.id)
        assert len(updated.confidence_history) >= 1
