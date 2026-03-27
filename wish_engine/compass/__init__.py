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
from wish_engine.compass.scanner import DialogueScanner
from wish_engine.compass.persistence import save_vault, load_vault

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
    "DialogueScanner",
    "save_vault",
    "load_vault",
]
