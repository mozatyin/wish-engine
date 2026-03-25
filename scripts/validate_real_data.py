#!/usr/bin/env python3.12
"""P0: Validate Wish Detector against real SoulMap V9 production data.

Uses:
- real_users_annotated.jsonl (100 real user messages)
- multi_turn_sessions.jsonl (30 multi-turn sessions)
- critical.jsonl (584 high-distress records)

Treats user_text as if it were a Deep Soul intention (simplified).
Measures: wish detection rate, type distribution, confidence calibration.
"""

import json
import sys
from pathlib import Path
from collections import Counter

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import Intention, EmotionState, WishType, WishLevel
from wish_engine.detector import detect_wishes
from wish_engine.classifier import classify


def load_jsonl(path: str) -> list[dict]:
    """Load JSONL file."""
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def validate_single_turn(records: list[dict]) -> dict:
    """Validate detector on single-turn user messages."""
    total = len(records)
    detected = 0
    type_dist: Counter = Counter()
    level_dist: Counter = Counter()
    conf_sum = 0.0
    wish_examples: list[dict] = []
    high_distress_wishes = 0
    high_distress_total = 0

    for rec in records:
        text = rec.get("user_text", "")
        distress = rec.get("prod_distress", 0.0)
        if not text or len(text) < 3:
            continue

        intention = Intention(id=rec.get("id", "unknown"), text=text)
        emotion = EmotionState(distress=distress) if distress else None

        results = detect_wishes([intention], emotion_state=emotion)

        if distress and distress > 0.5:
            high_distress_total += 1

        if results:
            detected += 1
            wish = results[0]
            classified = classify(wish)
            type_dist[wish.wish_type.value] += 1
            level_dist[classified.level.value] += 1
            conf_sum += wish.confidence

            if distress and distress > 0.5:
                high_distress_wishes += 1

            if len(wish_examples) < 20:
                wish_examples.append({
                    "text": text[:80],
                    "type": wish.wish_type.value,
                    "level": classified.level.value,
                    "confidence": round(wish.confidence, 2),
                    "distress": round(distress, 2) if distress else None,
                })

    return {
        "total": total,
        "detected": detected,
        "detection_rate": round(detected / total, 3) if total else 0,
        "avg_confidence": round(conf_sum / detected, 3) if detected else 0,
        "type_distribution": dict(type_dist.most_common()),
        "level_distribution": dict(level_dist.most_common()),
        "high_distress_wish_rate": round(high_distress_wishes / high_distress_total, 3) if high_distress_total else 0,
        "high_distress_total": high_distress_total,
        "examples": wish_examples,
    }


def validate_multi_turn(sessions: list[dict]) -> dict:
    """Validate detector on multi-turn sessions."""
    total_turns = 0
    wishes_found = 0
    sessions_with_wishes = 0
    wishes_per_session: list[int] = []

    for session in sessions:
        conv = session.get("conversation", [])
        session_wishes = 0

        for turn in conv:
            text = turn.get("text", "")
            distress = turn.get("prod_distress", 0.0)
            if not text or len(text) < 3:
                continue

            total_turns += 1
            intention = Intention(id=f"{session['session_id']}_{turn.get('turn', 0)}", text=text)
            emotion = EmotionState(distress=distress) if distress else None
            results = detect_wishes([intention], emotion_state=emotion)

            if results:
                wishes_found += 1
                session_wishes += 1

        wishes_per_session.append(session_wishes)
        if session_wishes > 0:
            sessions_with_wishes += 1

    return {
        "total_sessions": len(sessions),
        "total_turns": total_turns,
        "wishes_found": wishes_found,
        "sessions_with_wishes": sessions_with_wishes,
        "avg_wishes_per_session": round(sum(wishes_per_session) / len(wishes_per_session), 2) if wishes_per_session else 0,
        "wish_per_turn_rate": round(wishes_found / total_turns, 3) if total_turns else 0,
    }


def main():
    print("=" * 70)
    print("  WISH ENGINE — REAL DATA VALIDATION")
    print("=" * 70)

    # 1. Annotated real users (100)
    path1 = "/Users/mozat/detector-orchestrator/eval/real_users_annotated.jsonl"
    print(f"\n[1/3] Loading {path1}...")
    records = load_jsonl(path1)
    result1 = validate_single_turn(records)
    print(f"  Records: {result1['total']}")
    print(f"  Wishes detected: {result1['detected']} ({result1['detection_rate']:.1%})")
    print(f"  Avg confidence: {result1['avg_confidence']:.3f}")
    print(f"  High-distress wish rate: {result1['high_distress_wish_rate']:.1%} ({result1['high_distress_total']} high-distress records)")
    print(f"  Type dist: {result1['type_distribution']}")
    print(f"  Level dist: {result1['level_distribution']}")
    print(f"\n  Top wish examples:")
    for ex in result1["examples"][:10]:
        print(f"    [{ex['type']}/{ex['level']}] conf={ex['confidence']} dist={ex['distress']} | {ex['text']}")

    # 2. Multi-turn sessions (30)
    path2 = "/Users/mozat/detector-orchestrator/eval/multi_turn_sessions.jsonl"
    print(f"\n[2/3] Loading {path2}...")
    sessions = load_jsonl(path2)
    result2 = validate_multi_turn(sessions)
    print(f"  Sessions: {result2['total_sessions']}")
    print(f"  Total turns: {result2['total_turns']}")
    print(f"  Wishes found: {result2['wishes_found']}")
    print(f"  Sessions with wishes: {result2['sessions_with_wishes']}/{result2['total_sessions']}")
    print(f"  Avg wishes/session: {result2['avg_wishes_per_session']}")
    print(f"  Wish per turn rate: {result2['wish_per_turn_rate']:.1%}")

    # 3. Critical records (584)
    path3 = "/Users/mozat/emotion-detector/data/real_user/critical.jsonl"
    print(f"\n[3/3] Loading {path3}...")
    critical = load_jsonl(path3)
    result3 = validate_single_turn(critical)
    print(f"  Records: {result3['total']}")
    print(f"  Wishes detected: {result3['detected']} ({result3['detection_rate']:.1%})")
    print(f"  Avg confidence: {result3['avg_confidence']:.3f}")
    print(f"  High-distress wish rate: {result3['high_distress_wish_rate']:.1%}")
    print(f"  Type dist: {result3['type_distribution']}")
    print(f"  Level dist: {result3['level_distribution']}")
    print(f"\n  Top wish examples:")
    for ex in result3["examples"][:10]:
        print(f"    [{ex['type']}/{ex['level']}] conf={ex['confidence']} dist={ex['distress']} | {ex['text']}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY")
    print(f"{'=' * 70}")
    total_records = result1["total"] + result2["total_turns"] + result3["total"]
    total_wishes = result1["detected"] + result2["wishes_found"] + result3["detected"]
    overall_rate = total_wishes / total_records if total_records else 0
    print(f"  Total records processed: {total_records}")
    print(f"  Total wishes detected: {total_wishes} ({overall_rate:.1%})")
    print(f"  Expected range: 5-15% of messages contain wish-like expressions")

    if overall_rate > 0.20:
        print(f"  ⚠️  Detection rate HIGH ({overall_rate:.1%}) — may have false positives")
        print(f"     → Recommend raising confidence threshold to 0.85+")
    elif overall_rate < 0.03:
        print(f"  ⚠️  Detection rate LOW ({overall_rate:.1%}) — may be too restrictive")
        print(f"     → Recommend expanding desire markers")
    else:
        print(f"  ✓  Detection rate in expected range")

    # Save results
    output = {
        "annotated_100": result1,
        "multi_turn_30": result2,
        "critical_584": result3,
        "overall_rate": round(overall_rate, 3),
    }
    out_path = Path(__file__).parent / "real_data_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved to {out_path}")


if __name__ == "__main__":
    main()
