"""Multi-character Compass validation — Darcy, Gatsby, Walter White."""

import json
import pytest
from pathlib import Path
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.scanner import DialogueScanner
from wish_engine.compass.models import ShellStage
from wish_engine.models import DetectorResults

FIXTURES = Path("/Users/michael/soulgraph/fixtures")


def _run_character(dialogue_file: str, entity_names: dict) -> WishCompass:
    """Run compass on a character's full dialogue."""
    path = FIXTURES / dialogue_file
    if not path.exists():
        pytest.skip(f"{dialogue_file} not available")
    compass = WishCompass()
    scanner = DialogueScanner(entity_names)
    with open(path) as f:
        for i, line in enumerate(f):
            d = json.loads(line.strip())
            topics = scanner.scan_dialogue(d["text"])
            if topics:
                compass.scan(topics=topics, detector_results=DetectorResults(), session_id=f"s_{i}")
    return compass


class TestDarcy:
    ENTITIES = {
        "Elizabeth": ["elizabeth", "miss bennet", "eliza", "her eyes", "her wit"],
        "Bingley": ["bingley"],
        "Wickham": ["wickham"],
    }

    def test_elizabeth_shell_emerges(self):
        compass = _run_character("darcy_full.jsonl", self.ENTITIES)
        eliz = compass.vault.get_by_topic("Elizabeth")
        assert len(eliz) >= 1, "Darcy's hidden feelings for Elizabeth not detected"

    def test_elizabeth_detected_before_end(self):
        compass = _run_character("darcy_full.jsonl", self.ENTITIES)
        eliz = compass.vault.get_by_topic("Elizabeth")
        assert eliz[0].confidence > 0.15, f"Confidence too low: {eliz[0].confidence}"

    def test_reasonable_shell_count(self):
        compass = _run_character("darcy_full.jsonl", self.ENTITIES)
        assert compass.summary()["total_shells"] <= 10


class TestGatsby:
    ENTITIES = {
        "Daisy": ["daisy", "her voice", "she said", "her eyes", "her hand"],
        "Past": ["james gatz", "north dakota", "parents", "origins", "farm", "poverty", "nothing"],
        "Nick": ["nick", "old sport"],
    }

    def test_any_shell_emerges(self):
        """Gatsby's restrained literary tone makes contradiction detection harder.
        At minimum one entity shell should emerge from emotional spikes."""
        compass = _run_character("gatsby_full.jsonl", self.ENTITIES)
        all_shells = compass.vault.all_shells
        assert len(all_shells) >= 1, "No shells detected for Gatsby at all"

    def test_reasonable_shell_count(self):
        compass = _run_character("gatsby_full.jsonl", self.ENTITIES)
        assert compass.summary()["total_shells"] <= 10


class TestWalterWhite:
    ENTITIES = {
        "Family": ["family", "skyler", "junior", "holly", "son", "wife"],
        "Power": ["empire", "heisenberg", "respect", "control", "king", "genius", "brilliant", "power"],
        "Gray_Matter": ["gray matter", "elliott", "gretchen"],
    }

    def test_power_shell_emerges(self):
        compass = _run_character("walter_white_full.jsonl", self.ENTITIES)
        power = compass.vault.get_by_topic("Power")
        assert len(power) >= 1, "Walter's hidden power desire not detected"

    def test_power_detected_with_reasonable_confidence(self):
        compass = _run_character("walter_white_full.jsonl", self.ENTITIES)
        power = compass.vault.get_by_topic("Power")
        if power:
            assert power[0].confidence > 0.2

    def test_reasonable_shell_count(self):
        compass = _run_character("walter_white_full.jsonl", self.ENTITIES)
        assert compass.summary()["total_shells"] <= 10
