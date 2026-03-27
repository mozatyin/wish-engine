#!/usr/bin/env python3
"""Compass End-to-End: hidden desire detection -> L2 fulfillment.

5 literary characters with known hidden desires:
  1. Scarlett  -> hidden love for Rhett (L2: breakup_healing / relationship)
  2. Darcy     -> hidden love for Elizabeth (L2: confidence / deep_social)
  3. Walter White -> hidden desire for power (L2: career / startup)
  4. Gatsby    -> hidden shame about origins (L2: roots_journey / identity)
  5. Don Draper -> hidden identity crisis (L2: roots_journey / identity)

Pipeline: dialogue fixtures -> DialogueScanner -> WishCompass.scan() ->
          harvest_blooms() -> classify -> fulfill_l2() -> verify

Usage:
    python3 scripts/compass_e2e_validation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import ShellStage
from wish_engine.compass.scanner import DialogueScanner
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    WishLevel,
    WishType,
)
from wish_engine.l2_fulfiller import fulfill_l2

FIXTURE_DIR = Path("/Users/michael/soulgraph/fixtures")

# ── Character definitions ───────────────────────────────────────────────────

CHARACTERS: list[dict[str, Any]] = [
    {
        "name": "Scarlett",
        "fixture": "scarlett_full.jsonl",
        "entities": {
            "Rhett": ["rhett", "butler", "captain butler"],
            "Ashley": ["ashley", "wilkes"],
        },
        "hidden_desire": "Rhett",
        "expected_fulfillers": ["breakup_healing", "confidence", "deep_social"],
        "description": "Hidden love for Rhett masked by denial and hostility",
    },
    {
        "name": "Darcy",
        "fixture": "darcy_full.jsonl",
        "entities": {
            "Elizabeth": ["elizabeth", "eliza", "miss bennet", "her eyes"],
            "Bingley": ["bingley"],
        },
        "hidden_desire": "Elizabeth",
        "expected_fulfillers": ["confidence", "deep_social", "breakup_healing"],
        "description": "Hidden love for Elizabeth masked by pride and class anxiety",
    },
    {
        "name": "Walter White",
        "fixture": "walter_white_full.jsonl",
        "entities": {
            "Power": ["power", "empire", "control", "respect", "king", "feared",
                       "in charge", "the one who knocks", "say my name"],
            "Chemistry": ["chemistry", "genius", "brilliance", "gray matter"],
        },
        "hidden_desire": "Power",
        "expected_fulfillers": ["career", "startup_resources", "confidence"],
        "description": "Hidden desire for power masked by 'providing for family'",
    },
    {
        "name": "Gatsby",
        "fixture": "gatsby_full.jsonl",
        "entities": {
            "Origins": ["james gatz", "north dakota", "farm", "parents", "poor",
                        "old sport", "oxford", "invented"],
            "Daisy": ["daisy"],
        },
        "hidden_desire": "Origins",
        "expected_fulfillers": ["roots_journey", "identity_exploration", "confidence"],
        "description": "Hidden shame about humble origins masked by reinvention",
    },
    {
        "name": "Don Draper",
        "fixture": "don_draper_full.jsonl",
        "entities": {
            "Identity": ["dick whitman", "real name", "who i am", "who am i",
                         "somebody else", "past", "korea", "deserter",
                         "don draper", "not my name"],
            "Success": ["success", "advertising", "pitch", "creative"],
        },
        "hidden_desire": "Identity",
        "expected_fulfillers": ["identity_exploration", "roots_journey", "confidence"],
        "description": "Hidden identity crisis masked by Don Draper persona",
    },
]


# ── Helpers ─────────────────────────────────────────────────────────────────

def load_dialogues(fixture_name: str) -> list[dict]:
    """Load JSONL dialogue fixture."""
    path = FIXTURE_DIR / fixture_name
    if not path.exists():
        print(f"  [SKIP] Fixture not found: {path}")
        return []
    lines = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(json.loads(line))
    return lines


def make_classified_wish(wish_text: str) -> ClassifiedWish:
    """Create a ClassifiedWish for L2 fulfillment from harvest output."""
    return ClassifiedWish(
        wish_text=wish_text,
        wish_type=WishType.FIND_RESOURCE,
        level=WishLevel.L2,
        fulfillment_strategy="resource_recommendation",
    )


# ── Main pipeline ───────────────────────────────────────────────────────────

def run_character(char: dict[str, Any]) -> dict[str, Any]:
    """Run the full compass -> L2 pipeline for one character."""
    name = char["name"]
    print(f"\n{'='*60}")
    print(f"  {name}: {char['description']}")
    print(f"{'='*60}")

    # 1. Load dialogues
    dialogues = load_dialogues(char["fixture"])
    if not dialogues:
        return {"name": name, "status": "skipped", "reason": "no fixture"}
    print(f"  Loaded {len(dialogues)} dialogues")

    # 2. Create scanner and compass
    scanner = DialogueScanner(entity_names=char["entities"])
    compass = WishCompass()

    # 3. Group dialogues into sessions by chapter_phase, feed through scanner -> compass
    shells_by_stage: dict[str, int] = {}
    desire_entity = char["hidden_desire"]
    desire_first_seen = None
    desire_bloom_at = None
    confirmed_shells: set[str] = set()

    # Group dialogues into sessions by chapter_phase
    sessions: dict[int, list[dict]] = {}
    for d in dialogues:
        phase = d.get("chapter_phase", 0)
        sessions.setdefault(phase, []).append(d)

    for phase in sorted(sessions):
        batch = sessions[phase]
        topics = scanner.scan_batch(batch, session_id=f"phase_{phase}")

        if not topics:
            continue

        result = compass.scan(
            topics=topics,
            detector_results=DetectorResults(),
            session_id=f"phase_{phase}",
        )

        # Simulate user confirmation on bud-stage shells (realistic:
        # in production the Compass triggers a revelation and the user
        # confirms). This pushes bud -> bloom.
        for shell in compass.vault.visible_shells:
            if (shell.stage == ShellStage.BUD
                    and shell.id not in confirmed_shells):
                compass.record_feedback(shell.id, "confirm")
                confirmed_shells.add(shell.id)
                print(f"  [{name}] User confirmed {shell.topic} "
                      f"(conf={shell.confidence:.3f})")

        # Track the hidden desire entity
        desire_shells = compass.vault.get_by_topic(desire_entity)
        if desire_shells:
            shell = desire_shells[0]
            stage = shell.stage.value
            if stage not in shells_by_stage:
                shells_by_stage[stage] = phase
                print(f"  [{name}] {desire_entity} reached {stage.upper()} "
                      f"at phase {phase} (conf={shell.confidence:.3f})")
            if desire_first_seen is None:
                desire_first_seen = phase
            if shell.stage == ShellStage.BLOOM and desire_bloom_at is None:
                desire_bloom_at = phase

    # 4. Summary of compass state
    summary = compass.summary()
    print(f"  Compass: {summary}")

    all_shells = compass.vault.all_shells
    print(f"  All shells:")
    for s in all_shells:
        print(f"    - {s.topic}: {s.pattern.value} "
              f"(conf={s.confidence:.3f}, stage={s.stage.value}, "
              f"signals={len(s.raw_signals)})")

    # 5. Harvest bloom shells
    harvested = compass.harvest_blooms()
    print(f"  Harvested {len(harvested)} bloom shell(s)")

    # 6. Feed through L2 fulfillment
    fulfillment_results = []
    for h in harvested:
        wish_text = h["wish_text"]
        print(f"  Fulfilling: '{wish_text}'")
        classified = make_classified_wish(wish_text)
        try:
            result = fulfill_l2(classified, DetectorResults())
            recs = result.recommendations
            print(f"    -> {len(recs)} recommendations:")
            for r in recs:
                print(f"       [{r.category}] {r.title} (score={r.score:.2f})")
            fulfillment_results.append({
                "wish_text": wish_text,
                "shell_topic": h["shell_topic"],
                "shell_pattern": h["shell_pattern"],
                "recommendations": [
                    {"title": r.title, "category": r.category, "score": r.score}
                    for r in recs
                ],
            })
        except Exception as e:
            print(f"    -> FULFILLMENT ERROR: {e}")
            fulfillment_results.append({
                "wish_text": wish_text,
                "shell_topic": h["shell_topic"],
                "error": str(e),
            })

    # 7. Check if hidden desire was detected
    desire_detected = desire_entity in [s.topic for s in all_shells]
    desire_bloomed = any(
        s.topic == desire_entity and s.stage == ShellStage.BLOOM
        for s in all_shells
    )
    desire_fulfilled = any(
        fr["shell_topic"] == desire_entity and "recommendations" in fr
        for fr in fulfillment_results
    )

    status = "PASS" if (desire_detected and desire_bloomed and desire_fulfilled) else "PARTIAL"
    if not desire_detected:
        status = "FAIL"

    print(f"\n  RESULT: {status}")
    print(f"    Detected: {desire_detected}")
    print(f"    Bloomed:  {desire_bloomed}")
    print(f"    Fulfilled: {desire_fulfilled}")

    return {
        "name": name,
        "status": status,
        "hidden_desire": desire_entity,
        "detected": desire_detected,
        "bloomed": desire_bloomed,
        "fulfilled": desire_fulfilled,
        "milestones": shells_by_stage,
        "total_shells": summary["total_shells"],
        "total_blooms": summary["blooms"],
        "harvested_count": len(harvested),
        "fulfillment_results": fulfillment_results,
    }


def main():
    print("Compass End-to-End Validation")
    print("Hidden desire detection -> L2 fulfillment pipeline")
    print("=" * 60)

    results = []
    for char in CHARACTERS:
        result = run_character(char)
        results.append(result)

    # ── Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in results:
        icon = {"PASS": "+", "PARTIAL": "~", "FAIL": "-", "skipped": "?"}[r["status"]]
        print(f"  [{icon}] {r['name']:15s} -> {r.get('hidden_desire', 'N/A'):12s} "
              f"| detected={r.get('detected', 'N/A')} "
              f"| bloomed={r.get('bloomed', 'N/A')} "
              f"| fulfilled={r.get('fulfilled', 'N/A')}")

    passed = sum(1 for r in results if r["status"] == "PASS")
    total = sum(1 for r in results if r["status"] != "skipped")
    print(f"\n  {passed}/{total} characters fully validated (detect + bloom + fulfill)")

    # Save results
    output_dir = Path("/Users/michael/wish-engine/experiment_results")
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "compass_e2e_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  Results saved to {output_dir / 'compass_e2e_results.json'}")


if __name__ == "__main__":
    main()
