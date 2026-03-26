#!/usr/bin/env python3
"""Scarlett Compass Experiment — validates Wish Compass on Gone with the Wind.

Feeds scarlett_full.jsonl through the Compass pipeline and records:
- When Rhett shell first appears (seed)
- When it reaches sprout, bud, bloom
- Confidence curve over dialogues
- Trigger events and revelations

Usage:
    python3 scripts/scarlett_experiment.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import DetectorResults
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import ShellStage

FIXTURE_PATH = Path("/Users/michael/soulgraph/fixtures/scarlett_full.jsonl")
OUTPUT_DIR = Path("/Users/michael/wish-engine/experiment_results")


def load_dialogues() -> list[dict]:
    lines = []
    with open(FIXTURE_PATH) as f:
        for line in f:
            lines.append(json.loads(line.strip()))
    return lines


def simulate_topic(dialogue: dict) -> Optional[dict]:
    """Convert dialogue to topic signal. Returns None for irrelevant lines."""
    text = dialogue["text"].lower()
    entity = None
    arousal = 0.3
    sentiment = "neutral"

    # Rhett detection
    rhett_words = ["rhett", "butler", "captain butler"]
    ashley_words = ["ashley", "wilkes", "mr. wilkes"]
    negative_words = ["hate", "horrible", "fool", "cad", "don't care", "never", "furious", "dare"]
    positive_words = ["love", "want", "need", "miss", "beautiful", "admire"]

    is_rhett = any(w in text for w in rhett_words)
    is_ashley = any(w in text for w in ashley_words)

    if is_rhett:
        entity = "Rhett"
        has_negative = any(w in text for w in negative_words)
        has_positive = any(w in text for w in positive_words)
        # Key insight: negative words about Rhett with high emotional content = contradiction
        arousal = 0.75 if has_negative else (0.6 if has_positive else 0.45)
        sentiment = "negative" if has_negative else ("positive" if has_positive else "mixed")
    elif is_ashley:
        entity = "Ashley"
        has_positive = any(w in text for w in positive_words)
        arousal = 0.45 if has_positive else 0.3
        sentiment = "positive" if has_positive else "neutral"
    else:
        return None

    return {
        "entity": entity,
        "sentiment": sentiment,
        "arousal": arousal,
        "mentions": 1,
    }


def run_experiment():
    dialogues = load_dialogues()
    compass = WishCompass()

    timeline = []
    rhett_milestones = {}

    print(f"Loaded {len(dialogues)} dialogues from scarlett_full.jsonl")
    print("=" * 60)

    for i, dialogue in enumerate(dialogues):
        topic = simulate_topic(dialogue)
        if not topic:
            continue

        result = compass.scan(
            topics=[topic],
            detector_results=DetectorResults(),
            session_id=f"session_{i}",
        )

        # Track Rhett shell
        rhett_shells = compass.vault.get_by_topic("Rhett")
        rhett_conf = rhett_shells[0].confidence if rhett_shells else 0.0
        rhett_stage = rhett_shells[0].stage.value if rhett_shells else "none"

        entry = {
            "dialogue_num": i,
            "phase": dialogue.get("chapter_phase", 0),
            "text_preview": dialogue["text"][:60],
            "topic_entity": topic["entity"],
            "topic_sentiment": topic["sentiment"],
            "topic_arousal": topic["arousal"],
            "rhett_confidence": rhett_conf,
            "rhett_stage": rhett_stage,
            "new_shells": result.new_shells,
            "total_shells": result.total_shells,
        }
        timeline.append(entry)

        # Record milestones
        if rhett_shells:
            stage = rhett_shells[0].stage.value
            if stage not in rhett_milestones:
                rhett_milestones[stage] = i
                print(f"  * Rhett shell reached {stage.upper()} at dialogue #{i} "
                      f"(confidence={rhett_conf:.2f}, phase={dialogue.get('chapter_phase', '?')})")

        # Check trigger on decision-like dialogue
        if any(w in dialogue["text"].lower() for w in ["should", "choose", "which"]):
            revelation = compass.check_trigger(
                current_text=dialogue["text"],
                session_id=f"session_{i}",
                distress=0.2,
                topics_mentioned=[topic["entity"]],
            )
            if revelation:
                print(f"  -> TRIGGER at dialogue #{i}: {revelation.text[:80]}...")

    # -- Results -----------------------------------------------------------
    print("\n" + "=" * 60)
    print("EXPERIMENT RESULTS")
    print("=" * 60)

    print(f"\nTotal dialogues processed: {len(dialogues)}")
    print(f"Total shells found: {compass.summary()['total_shells']}")
    print(f"\nRhett milestones:")
    for stage, dial_num in sorted(rhett_milestones.items(), key=lambda x: x[1]):
        pct = dial_num / len(dialogues) * 100
        print(f"  {stage:8s} at dialogue #{dial_num:3d} ({pct:.0f}%)")

    # Phase 5 starts at ~80% of dialogues
    phase5_start = int(len(dialogues) * 0.8)
    bud_num = rhett_milestones.get("bud")
    if bud_num and bud_num < phase5_start:
        lead = phase5_start - bud_num
        print(f"\nSUCCESS: Rhett bud reached {lead} dialogues before Phase 5 (Scarlett's self-awareness)")
    elif bud_num:
        print(f"\nWARNING: Rhett bud reached at dialogue #{bud_num} (Phase 5 starts at #{phase5_start})")
    else:
        print("\nFAIL: Rhett never reached bud stage")

    print(f"\nCompass summary: {compass.summary()}")

    # Save results
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_DIR / "scarlett_compass_timeline.json", "w") as f:
        json.dump(timeline, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_DIR / "scarlett_shells.json", "w") as f:
        shells_data = [
            {"id": s.id, "topic": s.topic, "pattern": s.pattern.value,
             "confidence": s.confidence, "stage": s.stage.value,
             "signals_count": len(s.raw_signals)}
            for s in compass.vault.all_shells
        ]
        json.dump(shells_data, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    run_experiment()
