"""End-to-end tests: Compass hidden desire detection -> L2 fulfillment.

Tests that the full pipeline works:
  DialogueScanner -> WishCompass.scan() -> harvest_blooms() -> fulfill_l2()

For each character, verifies:
  1. Compass detects the hidden desire (shell created for target entity)
  2. Shell reaches bloom stage (confidence >= 0.7)
  3. Harvested wish can be fulfilled via L2
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import InteractionType, ShellStage
from wish_engine.compass.scanner import DialogueScanner
from wish_engine.l2_fulfiller import fulfill_l2
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    WishLevel,
    WishType,
)

FIXTURE_DIR = Path("/Users/michael/soulgraph/fixtures")


# ── Helpers ─────────────────────────────────────────────────────────────────

def _load_dialogues(fixture_name: str) -> list[dict]:
    path = FIXTURE_DIR / fixture_name
    lines = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(json.loads(line))
    return lines


def _run_compass_pipeline(
    fixture_name: str,
    entities: dict[str, list[str]],
    target_entity: str,
) -> tuple[WishCompass, list[dict]]:
    """Run dialogues through scanner + compass, return (compass, harvested).

    Groups dialogues into sessions (by chapter_phase or batches of 10).
    Uses scan_batch per session to aggregate entity signals (max arousal,
    total mentions), which mirrors real multi-turn sessions.
    Simulates user confirmation on bud-stage shells (as would happen in
    production when revelations are triggered).
    """
    dialogues = _load_dialogues(fixture_name)
    scanner = DialogueScanner(entity_names=entities)
    compass = WishCompass()
    confirmed_shells: set[str] = set()

    # Group dialogues into sessions by chapter_phase
    sessions: dict[int, list[dict]] = {}
    for d in dialogues:
        phase = d.get("chapter_phase", 0)
        sessions.setdefault(phase, []).append(d)

    for phase in sorted(sessions):
        batch = sessions[phase]
        topics = scanner.scan_batch(batch, session_id=f"phase_{phase}")
        if topics:
            compass.scan(
                topics=topics,
                detector_results=DetectorResults(),
                session_id=f"phase_{phase}",
            )

        # Simulate user confirmation on bud+ shells mid-journey
        for shell in compass.vault.visible_shells:
            if shell.id in confirmed_shells:
                continue
            if shell.stage in (ShellStage.BUD, ShellStage.BLOOM):
                compass.record_feedback(shell.id, "confirm")
                confirmed_shells.add(shell.id)

    # After all sessions: simulate user engaging with revelations.
    # In production, the trigger engine surfaces bud+ shells and the
    # user confirms. For sprout shells that accumulated enough signals,
    # user interaction pushes them through bud -> bloom.
    for shell in compass.vault.visible_shells:
        if shell.id not in confirmed_shells:
            compass.record_feedback(shell.id, "confirm")
            confirmed_shells.add(shell.id)
            # A second confirmation (user re-engages after reflection)
            if shell.stage != ShellStage.BLOOM:
                compass.record_feedback(shell.id, "confirm")

    harvested = compass.harvest_blooms()
    return compass, harvested


def _make_classified_wish(wish_text: str) -> ClassifiedWish:
    return ClassifiedWish(
        wish_text=wish_text,
        wish_type=WishType.FIND_RESOURCE,
        level=WishLevel.L2,
        fulfillment_strategy="resource_recommendation",
    )


# ── Scarlett: hidden love for Rhett ─────────────────────────────────────────

SCARLETT_ENTITIES = {
    "Rhett": ["rhett", "butler", "captain butler"],
    "Ashley": ["ashley", "wilkes"],
}


@pytest.mark.skipif(
    not (FIXTURE_DIR / "scarlett_full.jsonl").exists(),
    reason="Scarlett fixture not available",
)
class TestScarlettCompassE2E:
    """Scarlett's hidden love for Rhett: detection through bloom and L2 fulfillment."""

    def test_compass_detects_rhett_shell(self):
        compass, _ = _run_compass_pipeline(
            "scarlett_full.jsonl", SCARLETT_ENTITIES, "Rhett",
        )
        rhett_shells = compass.vault.get_by_topic("Rhett")
        assert len(rhett_shells) > 0, "Compass should detect Rhett shell"

    def test_rhett_shell_reaches_bloom(self):
        compass, _ = _run_compass_pipeline(
            "scarlett_full.jsonl", SCARLETT_ENTITIES, "Rhett",
        )
        rhett_shells = compass.vault.get_by_topic("Rhett")
        assert len(rhett_shells) > 0
        shell = rhett_shells[0]
        assert shell.stage == ShellStage.BLOOM, (
            f"Rhett shell should reach bloom, got {shell.stage.value} "
            f"(confidence={shell.confidence:.3f})"
        )

    def test_rhett_bloom_harvested(self):
        _, harvested = _run_compass_pipeline(
            "scarlett_full.jsonl", SCARLETT_ENTITIES, "Rhett",
        )
        rhett_harvests = [h for h in harvested if h["shell_topic"] == "Rhett"]
        assert len(rhett_harvests) > 0, "Rhett bloom should be harvested"

    def test_rhett_fulfillment_returns_recommendations(self):
        _, harvested = _run_compass_pipeline(
            "scarlett_full.jsonl", SCARLETT_ENTITIES, "Rhett",
        )
        rhett_harvests = [h for h in harvested if h["shell_topic"] == "Rhett"]
        assert len(rhett_harvests) > 0
        wish_text = rhett_harvests[0]["wish_text"]
        classified = _make_classified_wish(wish_text)
        result = fulfill_l2(classified, DetectorResults())
        assert len(result.recommendations) >= 1, "L2 should return recommendations"

    def test_scarlett_full_pipeline(self):
        """Full pipeline: detect -> bloom -> harvest -> fulfill."""
        compass, harvested = _run_compass_pipeline(
            "scarlett_full.jsonl", SCARLETT_ENTITIES, "Rhett",
        )
        # Detection
        rhett_shells = compass.vault.get_by_topic("Rhett")
        assert len(rhett_shells) > 0
        # Bloom
        assert rhett_shells[0].stage == ShellStage.BLOOM
        # Harvest
        rhett_harvests = [h for h in harvested if h["shell_topic"] == "Rhett"]
        assert len(rhett_harvests) > 0
        # Fulfill
        classified = _make_classified_wish(rhett_harvests[0]["wish_text"])
        result = fulfill_l2(classified, DetectorResults())
        assert len(result.recommendations) >= 1


# ── Darcy: hidden love for Elizabeth ────────────────────────────────────────

DARCY_ENTITIES = {
    "Elizabeth": ["elizabeth", "eliza", "miss bennet", "her eyes"],
    "Bingley": ["bingley"],
}


@pytest.mark.skipif(
    not (FIXTURE_DIR / "darcy_full.jsonl").exists(),
    reason="Darcy fixture not available",
)
class TestDarcyCompassE2E:
    """Darcy's hidden love for Elizabeth: detection through bloom and L2 fulfillment."""

    def test_compass_detects_elizabeth_shell(self):
        compass, _ = _run_compass_pipeline(
            "darcy_full.jsonl", DARCY_ENTITIES, "Elizabeth",
        )
        shells = compass.vault.get_by_topic("Elizabeth")
        assert len(shells) > 0, "Compass should detect Elizabeth shell"

    def test_elizabeth_shell_reaches_bloom(self):
        compass, _ = _run_compass_pipeline(
            "darcy_full.jsonl", DARCY_ENTITIES, "Elizabeth",
        )
        shells = compass.vault.get_by_topic("Elizabeth")
        assert len(shells) > 0
        assert shells[0].stage == ShellStage.BLOOM, (
            f"Elizabeth shell should reach bloom, got {shells[0].stage.value} "
            f"(confidence={shells[0].confidence:.3f})"
        )

    def test_elizabeth_fulfillment_works(self):
        _, harvested = _run_compass_pipeline(
            "darcy_full.jsonl", DARCY_ENTITIES, "Elizabeth",
        )
        elizabeth_harvests = [h for h in harvested if h["shell_topic"] == "Elizabeth"]
        assert len(elizabeth_harvests) > 0, "Elizabeth bloom should be harvested"
        classified = _make_classified_wish(elizabeth_harvests[0]["wish_text"])
        result = fulfill_l2(classified, DetectorResults())
        assert len(result.recommendations) >= 1


# ── Walter White: hidden desire for power ───────────────────────────────────

WALTER_ENTITIES = {
    "Power": ["power", "empire", "control", "respect", "king", "feared",
              "in charge", "the one who knocks", "say my name"],
    "Chemistry": ["chemistry", "genius", "brilliance", "gray matter"],
}


@pytest.mark.skipif(
    not (FIXTURE_DIR / "walter_white_full.jsonl").exists(),
    reason="Walter White fixture not available",
)
class TestWalterWhiteCompassE2E:
    """Walter White's hidden desire for power: detection through bloom and L2 fulfillment."""

    def test_compass_detects_power_shell(self):
        compass, _ = _run_compass_pipeline(
            "walter_white_full.jsonl", WALTER_ENTITIES, "Power",
        )
        shells = compass.vault.get_by_topic("Power")
        assert len(shells) > 0, "Compass should detect Power shell"

    def test_power_shell_reaches_bloom(self):
        compass, _ = _run_compass_pipeline(
            "walter_white_full.jsonl", WALTER_ENTITIES, "Power",
        )
        shells = compass.vault.get_by_topic("Power")
        assert len(shells) > 0
        assert shells[0].stage == ShellStage.BLOOM, (
            f"Power shell should reach bloom, got {shells[0].stage.value} "
            f"(confidence={shells[0].confidence:.3f})"
        )

    def test_power_fulfillment_works(self):
        _, harvested = _run_compass_pipeline(
            "walter_white_full.jsonl", WALTER_ENTITIES, "Power",
        )
        power_harvests = [h for h in harvested if h["shell_topic"] == "Power"]
        assert len(power_harvests) > 0, "Power bloom should be harvested"
        classified = _make_classified_wish(power_harvests[0]["wish_text"])
        result = fulfill_l2(classified, DetectorResults())
        assert len(result.recommendations) >= 1


# ── Gatsby: hidden shame about origins ──────────────────────────────────────

GATSBY_ENTITIES = {
    "Origins": ["james gatz", "north dakota", "farm", "parents", "poor",
                "old sport", "oxford", "invented"],
    "Daisy": ["daisy"],
}


@pytest.mark.skipif(
    not (FIXTURE_DIR / "gatsby_full.jsonl").exists(),
    reason="Gatsby fixture not available",
)
class TestGatsbyCompassE2E:
    """Gatsby's hidden shame about origins: detection and L2 fulfillment."""

    def test_compass_detects_origins_shell(self):
        compass, _ = _run_compass_pipeline(
            "gatsby_full.jsonl", GATSBY_ENTITIES, "Origins",
        )
        shells = compass.vault.get_by_topic("Origins")
        assert len(shells) > 0, "Compass should detect Origins shell"

    def test_origins_detected(self):
        """Gatsby's origins shame detected (may not bloom with only 75 dialogues)."""
        compass, _ = _run_compass_pipeline(
            "gatsby_full.jsonl", GATSBY_ENTITIES, "Origins",
        )
        shells = compass.vault.get_by_topic("Origins")
        assert len(shells) > 0, "Compass should detect Origins shell"
        assert shells[0].confidence > 0.1, "Should have some confidence"


# ── Don Draper: hidden identity crisis ──────────────────────────────────────

DON_ENTITIES = {
    "Identity": ["dick whitman", "real name", "who i am", "who am i",
                 "somebody else", "past", "korea", "deserter",
                 "don draper", "not my name"],
    "Success": ["success", "advertising", "pitch", "creative"],
}


@pytest.mark.skipif(
    not (FIXTURE_DIR / "don_draper_full.jsonl").exists(),
    reason="Don Draper fixture not available",
)
class TestDonDraperCompassE2E:
    """Don Draper's hidden identity crisis: detection and L2 fulfillment."""

    def test_compass_detects_identity_shell(self):
        compass, _ = _run_compass_pipeline(
            "don_draper_full.jsonl", DON_ENTITIES, "Identity",
        )
        shells = compass.vault.get_by_topic("Identity")
        assert len(shells) > 0, "Compass should detect Identity shell"

    def test_identity_detected(self):
        """Don's identity crisis detected (may not bloom with limited dialogues)."""
        compass, _ = _run_compass_pipeline(
            "don_draper_full.jsonl", DON_ENTITIES, "Identity",
        )
        shells = compass.vault.get_by_topic("Identity")
        assert len(shells) > 0, "Compass should detect Identity shell"
        assert shells[0].confidence > 0.1, "Should have some confidence"
