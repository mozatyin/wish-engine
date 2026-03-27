"""Persistence — save/load SecretVault state to JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from wish_engine.compass.models import (
    ContradictionPattern,
    Shell,
    Signal,
    Interaction,
    InteractionType,
    TriggerEvent,
    TriggerType,
)
from wish_engine.compass.vault import SecretVault


def save_vault(vault: SecretVault, path: str | Path) -> None:
    """Save vault state to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    shells_data = []
    for shell in vault.all_shells:
        shells_data.append(shell.model_dump(mode="json"))
    with open(path, "w") as f:
        json.dump({"shells": shells_data}, f, indent=2, ensure_ascii=False)


def load_vault(path: str | Path) -> SecretVault:
    """Load vault state from a JSON file."""
    path = Path(path)
    if not path.exists():
        return SecretVault()
    with open(path) as f:
        data = json.load(f)
    vault = SecretVault()
    for shell_data in data.get("shells", []):
        shell = Shell.model_validate(shell_data)
        vault.add(shell)
    return vault
