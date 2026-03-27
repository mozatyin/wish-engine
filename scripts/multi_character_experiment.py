#!/usr/bin/env python3
"""Multi-character Compass experiment — validates across Darcy, Gatsby, Walter White."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import DetectorResults
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.scanner import DialogueScanner

FIXTURES = Path("/Users/michael/soulgraph/fixtures")

CHARACTERS = {
    "Darcy": {
        "file": "darcy_full.jsonl",
        "entities": {
            "Elizabeth": ["elizabeth", "miss bennet", "eliza", "her eyes", "her wit"],
            "Bingley": ["bingley"],
            "Wickham": ["wickham"],
        },
        "expected_shell": "Elizabeth",
        "hidden_desire": "Love for Elizabeth behind pride and coldness",
    },
    "Gatsby": {
        "file": "gatsby_full.jsonl",
        "entities": {
            "Daisy": ["daisy", "her voice", "she said", "her eyes", "her hand"],
            "Past": ["james gatz", "north dakota", "parents", "origins", "farm", "poverty", "nothing"],
            "Nick": ["nick", "old sport"],
        },
        "expected_shell": "Daisy",
        "hidden_desire": "Daisy as proxy for class transcendence / self-hatred about origins",
    },
    "Walter White": {
        "file": "walter_white_full.jsonl",
        "entities": {
            "Family": ["family", "skyler", "junior", "holly", "son", "wife"],
            "Power": ["empire", "heisenberg", "respect", "control", "king", "genius", "brilliant", "power"],
            "Gray_Matter": ["gray matter", "elliott", "gretchen"],
        },
        "expected_shell": "Power",
        "hidden_desire": "Enjoyment of power/empire, not 'doing it for family'",
    },
}


def run_character(name: str, config: dict) -> dict:
    path = FIXTURES / config["file"]
    compass = WishCompass()
    scanner = DialogueScanner(config["entities"])

    dialogues = []
    with open(path) as f:
        for line in f:
            dialogues.append(json.loads(line.strip()))

    milestones = {}
    for i, d in enumerate(dialogues):
        topics = scanner.scan_dialogue(d["text"])
        if topics:
            compass.scan(topics=topics, detector_results=DetectorResults(), session_id=f"s_{i}")

        expected = config["expected_shell"]
        shells = compass.vault.get_by_topic(expected)
        if shells:
            stage = shells[0].stage.value
            if stage not in milestones:
                milestones[stage] = i

    summary = compass.summary()
    all_shells = [(s.topic, s.confidence, s.stage.value) for s in compass.vault.all_shells]

    return {
        "character": name,
        "dialogues": len(dialogues),
        "expected_shell": config["expected_shell"],
        "hidden_desire": config["hidden_desire"],
        "milestones": milestones,
        "summary": summary,
        "all_shells": all_shells,
    }


def main():
    print("=" * 70)
    print("MULTI-CHARACTER COMPASS EXPERIMENT")
    print("=" * 70)

    results = []
    for name, config in CHARACTERS.items():
        print(f"\n--- {name} ---")
        print(f"Hidden desire: {config['hidden_desire']}")
        r = run_character(name, config)
        results.append(r)

        if r["milestones"]:
            for stage, dial_num in sorted(r["milestones"].items(), key=lambda x: x[1]):
                pct = dial_num / r["dialogues"] * 100
                print(f"  {config['expected_shell']:12s} -> {stage:8s} at dialogue #{dial_num:3d} ({pct:.0f}%)")
        else:
            print(f"  [MISS] {config['expected_shell']} shell never emerged")

        print(f"  All shells: {r['all_shells']}")
        print(f"  Summary: {r['summary']}")

    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT")
    print("=" * 70)
    for r in results:
        detected = bool(r["milestones"])
        status = "PASS" if detected else "FAIL"
        print(f"  [{status}] {r['character']}: {r['expected_shell']} {'detected' if detected else 'NOT detected'}")

    # Save
    out_dir = Path("/Users/michael/wish-engine/experiment_results")
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "multi_character_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {out_dir}/multi_character_results.json")


if __name__ == "__main__":
    main()
