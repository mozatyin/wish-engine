"""Tests for Compass persistence — save/load vault to JSON."""

import json
import pytest
from pathlib import Path
from wish_engine.compass.models import (
    ContradictionPattern,
    Shell,
    Signal,
    Interaction,
    InteractionType,
)
from wish_engine.compass.vault import SecretVault
from wish_engine.compass.persistence import save_vault, load_vault


class TestSaveLoad:
    def test_save_and_load_roundtrip(self, tmp_path):
        vault = SecretVault()
        shell = Shell(
            pattern=ContradictionPattern.EMOTION_ANOMALY,
            topic="Rhett",
            confidence=0.55,
            raw_signals=[Signal(signal_type="test", topic="Rhett", data={"a": 1}, session_id="s1")],
        )
        vault.add(shell)

        path = tmp_path / "vault.json"
        save_vault(vault, path)
        loaded = load_vault(path)

        assert len(loaded.all_shells) == 1
        loaded_shell = loaded.all_shells[0]
        assert loaded_shell.topic == "Rhett"
        assert loaded_shell.confidence == 0.55
        assert loaded_shell.pattern == ContradictionPattern.EMOTION_ANOMALY
        assert len(loaded_shell.raw_signals) == 1

    def test_load_nonexistent_returns_empty(self, tmp_path):
        vault = load_vault(tmp_path / "nonexistent.json")
        assert len(vault.all_shells) == 0

    def test_save_empty_vault(self, tmp_path):
        vault = SecretVault()
        path = tmp_path / "empty.json"
        save_vault(vault, path)
        loaded = load_vault(path)
        assert len(loaded.all_shells) == 0

    def test_preserves_multiple_shells(self, tmp_path):
        vault = SecretVault()
        vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="A", confidence=0.3))
        vault.add(Shell(pattern=ContradictionPattern.VALUE_CONFLICT, topic="B", confidence=0.6))
        vault.add(Shell(pattern=ContradictionPattern.GROWTH_GAP, topic="C", confidence=0.8))

        path = tmp_path / "multi.json"
        save_vault(vault, path)
        loaded = load_vault(path)

        assert len(loaded.all_shells) == 3
        topics = {s.topic for s in loaded.all_shells}
        assert topics == {"A", "B", "C"}

    def test_preserves_interactions(self, tmp_path):
        vault = SecretVault()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="test", confidence=0.5)
        shell.user_interactions.append(Interaction(interaction_type=InteractionType.CONFIRM))
        vault.add(shell)

        path = tmp_path / "interactions.json"
        save_vault(vault, path)
        loaded = load_vault(path)

        loaded_shell = loaded.all_shells[0]
        assert len(loaded_shell.user_interactions) == 1
        assert loaded_shell.user_interactions[0].interaction_type == InteractionType.CONFIRM

    def test_json_is_readable(self, tmp_path):
        vault = SecretVault()
        vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="test", confidence=0.5))
        path = tmp_path / "readable.json"
        save_vault(vault, path)
        with open(path) as f:
            data = json.load(f)
        assert "shells" in data
        assert len(data["shells"]) == 1
