"""Tests for the Scarlett Compass experiment — validates system detects Rhett feelings."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Optional
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import ShellStage
from wish_engine.models import DetectorResults


FIXTURE_PATH = Path("/Users/michael/soulgraph/fixtures/scarlett_full.jsonl")


def _simulate_topic(dialogue: dict) -> Optional[dict]:
    """Convert a dialogue line to a topic signal for the compass."""
    text = dialogue["text"].lower()
    entity = None
    arousal = 0.3
    sentiment = "neutral"

    rhett_words = ["rhett", "butler", "captain butler"]
    negative_words = ["hate", "horrible", "fool", "cad", "don't care", "never", "furious", "dare", "humiliation"]

    if any(w in text for w in rhett_words):
        entity = "Rhett"
        has_negative = any(w in text for w in negative_words)
        arousal = 0.75 if has_negative else 0.5
        sentiment = "negative" if has_negative else "mixed"
    elif "ashley" in text or "wilkes" in text:
        entity = "Ashley"
        arousal = 0.45 if "love" in text else 0.3
        sentiment = "positive" if "love" in text else "neutral"
    else:
        return None

    return {"entity": entity, "sentiment": sentiment, "arousal": arousal, "mentions": 1}


@pytest.mark.skipif(not FIXTURE_PATH.exists(), reason="Scarlett fixture not available")
class TestScarlettExperiment:
    def _load_dialogues(self) -> list[dict]:
        lines = []
        with open(FIXTURE_PATH) as f:
            for line in f:
                lines.append(json.loads(line.strip()))
        return lines

    def test_rhett_shell_emerges_before_phase5(self):
        """Core validation: system detects Rhett feelings before Scarlett does."""
        compass = WishCompass()
        dialogues = self._load_dialogues()
        rhett_first_detected = None

        for i, dialogue in enumerate(dialogues):
            topic = _simulate_topic(dialogue)
            if not topic:
                continue
            compass.scan(topics=[topic], detector_results=DetectorResults(), session_id=f"s_{i}")
            rhett_shells = compass.vault.get_by_topic("Rhett")
            if rhett_shells and rhett_first_detected is None:
                rhett_first_detected = i

        assert rhett_first_detected is not None, "System never detected Rhett feelings"
        phase5_start = int(len(dialogues) * 0.8)
        assert rhett_first_detected < phase5_start, f"Detected too late: {rhett_first_detected}/{len(dialogues)}"

    def test_ashley_not_flagged_as_hidden(self):
        """Ashley is a stated wish, not a hidden one — should not become a shell."""
        compass = WishCompass()
        dialogues = self._load_dialogues()
        for i, dialogue in enumerate(dialogues[:30]):
            topic = _simulate_topic(dialogue)
            if not topic:
                continue
            compass.scan(topics=[topic], detector_results=DetectorResults(), session_id=f"s_{i}")
        ashley_shells = compass.vault.get_by_topic("Ashley")
        if ashley_shells:
            assert ashley_shells[0].confidence < 0.3

    def test_compass_summary_reasonable(self):
        """After full run, compass should have reasonable shell counts."""
        compass = WishCompass()
        dialogues = self._load_dialogues()
        for i, dialogue in enumerate(dialogues):
            topic = _simulate_topic(dialogue)
            if not topic:
                continue
            compass.scan(topics=[topic], detector_results=DetectorResults(), session_id=f"s_{i}")
        summary = compass.summary()
        assert summary["total_shells"] >= 1
        assert summary["total_shells"] <= 10
