#!/usr/bin/env python3.12
"""P0: Validate L1 Fulfiller quality by calling real Sonnet API.

Tests 12 healing cases with realistic detector profiles.
Evaluates: personalization, warmth, clinical-term avoidance, length.
"""

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from wish_engine.models import (
    CardType, ClassifiedWish, CrossDetectorPattern, DetectorResults,
    L1FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l1_fulfiller import fulfill


# ── 12 Healing Cases with realistic profiles ─────────────────────────────────

CASES = [
    {
        "name": "Conflict Avoidance Insight",
        "wish": ClassifiedWish(
            wish_text="想理解为什么我总是回避冲突",
            wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"anxiety": 0.6, "frustration": 0.4}, "distress": 0.45},
            conflict={"style": "avoiding"},
            mbti={"type": "INFJ"},
            attachment={"style": "anxious-preoccupied"},
            values={"top_values": ["belonging", "benevolence"]},
            fragility={"pattern": "approval-seeking"},
        ),
        "soul_type": {"name": "Hidden Depths"},
        "patterns": [CrossDetectorPattern(pattern_name="safe_silence", confidence=0.82)],
    },
    {
        "name": "Relationship Fight Analysis",
        "wish": ClassifiedWish(
            wish_text="想知道我和他为什么总吵架",
            wish_type=WishType.RELATIONSHIP_INSIGHT,
            level=WishLevel.L1,
            fulfillment_strategy="bond_analysis",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"frustration": 0.7, "sadness": 0.4}, "distress": 0.55},
            conflict={"style": "competing"},
            attachment={"style": "anxious-preoccupied"},
            love_language={"primary": "quality_time"},
            communication_dna={"dominant_style": "direct-emotional"},
        ),
        "soul_type": {"name": "Tension Wire"},
        "patterns": [],
    },
    {
        "name": "Letter to Self",
        "wish": ClassifiedWish(
            wish_text="想给自己写一封信",
            wish_type=WishType.SELF_EXPRESSION,
            level=WishLevel.L1,
            fulfillment_strategy="assisted_writing",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"hope": 0.5, "sadness": 0.3}, "distress": 0.25},
            mbti={"type": "INFP"},
            fragility={"pattern": "open"},
            values={"top_values": ["self-direction", "universalism"]},
        ),
        "soul_type": {"name": "Quiet Storm"},
        "patterns": [],
    },
    {
        "name": "Soul Portrait",
        "wish": ClassifiedWish(
            wish_text="想做一个关于自己的总结",
            wish_type=WishType.LIFE_REFLECTION,
            level=WishLevel.L1,
            fulfillment_strategy="soul_portrait",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"curiosity": 0.6, "hope": 0.4}, "distress": 0.15},
            conflict={"style": "collaborating"},
            mbti={"type": "ENFP"},
            attachment={"style": "secure"},
            values={"top_values": ["self-direction", "stimulation", "achievement"]},
            eq={"overall": 0.78},
            communication_dna={"dominant_style": "expressive-warm"},
            humor={"style": "affiliative"},
        ),
        "soul_type": {"name": "Spark Seeker"},
        "patterns": [],
    },
    {
        "name": "Anger Origin Trace",
        "wish": ClassifiedWish(
            wish_text="想理解我的愤怒从哪来",
            wish_type=WishType.EMOTIONAL_PROCESSING,
            level=WishLevel.L1,
            fulfillment_strategy="emotion_trace",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"anger": 0.8, "frustration": 0.6, "hurt": 0.4}, "distress": 0.62},
            conflict={"style": "competing"},
            attachment={"style": "dismissive-avoidant"},
            values={"top_values": ["power", "achievement", "self-direction"]},
            fragility={"pattern": "defensive"},
        ),
        "soul_type": {"name": "Frost Guard"},
        "patterns": [CrossDetectorPattern(pattern_name="frozen_distance", confidence=0.75)],
    },
    {
        "name": "EN: Why I Push People Away",
        "wish": ClassifiedWish(
            wish_text="I want to understand why I push people away",
            wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"loneliness": 0.6, "fear": 0.5}, "distress": 0.50},
            conflict={"style": "avoiding"},
            attachment={"style": "dismissive-avoidant"},
            values={"top_values": ["security", "self-direction"]},
            fragility={"pattern": "withdrawal"},
            eq={"overall": 0.55},
        ),
        "soul_type": {"name": "Frost Guard"},
        "patterns": [CrossDetectorPattern(pattern_name="frozen_distance", confidence=0.80)],
    },
    {
        "name": "EN: Process Grief",
        "wish": ClassifiedWish(
            wish_text="I want to process the grief I've been carrying since dad passed",
            wish_type=WishType.EMOTIONAL_PROCESSING,
            level=WishLevel.L1,
            fulfillment_strategy="emotion_trace",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"grief": 0.8, "sadness": 0.7, "guilt": 0.4}, "distress": 0.72},
            conflict={"style": "accommodating"},
            attachment={"style": "secure"},
            values={"top_values": ["tradition", "benevolence", "security"]},
        ),
        "soul_type": {"name": "Warm Current"},
        "patterns": [],
    },
    {
        "name": "EN: Express Feelings",
        "wish": ClassifiedWish(
            wish_text="I want to express what I've been holding inside for so long",
            wish_type=WishType.SELF_EXPRESSION,
            level=WishLevel.L1,
            fulfillment_strategy="assisted_writing",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"sadness": 0.5, "hope": 0.3}, "distress": 0.35},
            mbti={"type": "ISFJ"},
            attachment={"style": "anxious-preoccupied"},
            fragility={"pattern": "suppression"},
        ),
        "soul_type": {"name": "Calm Harbor"},
        "patterns": [],
    },
    {
        "name": "EN: Understand Relationship",
        "wish": ClassifiedWish(
            wish_text="I wish I could understand why we keep having the same fight",
            wish_type=WishType.RELATIONSHIP_INSIGHT,
            level=WishLevel.L1,
            fulfillment_strategy="bond_analysis",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"frustration": 0.6, "love": 0.4}, "distress": 0.40},
            conflict={"style": "compromising"},
            love_language={"primary": "words_of_affirmation"},
            attachment={"style": "anxious-preoccupied"},
        ),
        "soul_type": {"name": "Hidden Depths"},
        "patterns": [],
    },
    {
        "name": "ZH: Let Go of Ex",
        "wish": ClassifiedWish(
            wish_text="希望可以放下对前任的执念",
            wish_type=WishType.EMOTIONAL_PROCESSING,
            level=WishLevel.L1,
            fulfillment_strategy="emotion_trace",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"longing": 0.7, "sadness": 0.5, "regret": 0.4}, "distress": 0.50},
            attachment={"style": "anxious-preoccupied"},
            values={"top_values": ["belonging", "security"]},
            fragility={"pattern": "rumination"},
        ),
        "soul_type": {"name": "Hidden Depths"},
        "patterns": [],
    },
    {
        "name": "ZH: People Pleasing",
        "wish": ClassifiedWish(
            wish_text="想弄清楚为什么自己总是讨好别人",
            wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"anxiety": 0.5, "shame": 0.4}, "distress": 0.42},
            conflict={"style": "accommodating"},
            attachment={"style": "anxious-preoccupied"},
            values={"top_values": ["conformity", "benevolence"]},
            fragility={"pattern": "approval-seeking"},
            eq={"overall": 0.60},
        ),
        "soul_type": {"name": "Warm Current"},
        "patterns": [CrossDetectorPattern(pattern_name="honest_anchor", confidence=0.70)],
    },
    {
        "name": "AR: Understand Self",
        "wish": ClassifiedWish(
            wish_text="أريد أن أفهم نفسي بشكل أفضل",
            wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        ),
        "profile": DetectorResults(
            emotion={"emotions": {"curiosity": 0.5, "confusion": 0.4}, "distress": 0.30},
            mbti={"type": "INTJ"},
            values={"top_values": ["self-direction", "universalism"]},
        ),
        "soul_type": {"name": "Quiet Storm"},
        "patterns": [],
    },
]


# ── Quality checks ───────────────────────────────────────────────────────────

CLINICAL_TERMS = [
    "disorder", "syndrome", "diagnosis", "patholog", "narcissi",
    "borderline", "schizo", "bipolar", "clinical", "DSM",
    "障碍", "诊断", "病理", "临床", "症候群",
]


def check_quality(case_name: str, result: L1FulfillmentResult, wish: ClassifiedWish) -> dict:
    """Evaluate fulfillment quality."""
    text = result.fulfillment_text
    issues = []

    # Length check
    words = len(text.split())
    if words < 50:
        issues.append(f"TOO SHORT: {words} words")
    if words > 400:
        issues.append(f"TOO LONG: {words} words")

    # Clinical terms
    lower = text.lower()
    for term in CLINICAL_TERMS:
        if term.lower() in lower:
            issues.append(f"CLINICAL TERM: '{term}'")

    # Personalization check — should reference specific profile details
    has_specific = False
    specifics = ["avoiding", "anxious", "INFJ", "ENFP", "belonging", "approval",
                 "回避", "焦虑", "讨好", "执念", "grief", "anger", "loneliness"]
    for s in specifics:
        if s.lower() in lower:
            has_specific = True
            break
    if not has_specific:
        issues.append("LOW PERSONALIZATION: no profile-specific references found")

    # Warm tone check
    warm_markers = ["you", "your", "你", "أنت", "gentle", "normal", "okay",
                    "natural", "makes sense", "understandable"]
    has_warmth = any(m.lower() in lower for m in warm_markers)
    if not has_warmth:
        issues.append("LOW WARMTH: no warm/validating language")

    return {
        "case": case_name,
        "card_type": result.card_type.value,
        "word_count": words,
        "related_stars": result.related_stars,
        "issues": issues,
        "quality": "GOOD" if not issues else "NEEDS_REVIEW",
        "text_preview": text[:200] + "..." if len(text) > 200 else text,
    }


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set. Add it to .env file.")
        sys.exit(1)

    print("=" * 70)
    print("  L1 FULFILLER — QUALITY VALIDATION (12 Healing Cases)")
    print("=" * 70)

    results = []
    total_cost = 0.0
    good_count = 0

    for i, case in enumerate(CASES):
        print(f"\n[{i+1}/12] {case['name']}...")
        try:
            start = time.time()
            result = fulfill(
                wish=case["wish"],
                detector_results=case["profile"],
                cross_detector_patterns=case.get("patterns"),
                soul_type=case.get("soul_type"),
                life_chapter=case.get("life_chapter"),
                api_key=api_key,
            )
            elapsed = time.time() - start

            quality = check_quality(case["name"], result, case["wish"])
            quality["latency_ms"] = round(elapsed * 1000)
            results.append(quality)

            status = "✓" if quality["quality"] == "GOOD" else "⚠"
            print(f"  {status} {quality['card_type']} | {quality['word_count']}w | {quality['latency_ms']}ms")
            if quality["issues"]:
                for issue in quality["issues"]:
                    print(f"    ⚠ {issue}")
            print(f"  Preview: {quality['text_preview'][:120]}")

            if quality["quality"] == "GOOD":
                good_count += 1

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({"case": case["name"], "quality": "ERROR", "error": str(e)})

        time.sleep(0.5)  # Rate limit

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  FULFILLER QUALITY SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Good: {good_count}/12")
    print(f"  Needs review: {12 - good_count}/12")

    issue_types = Counter()
    for r in results:
        for issue in r.get("issues", []):
            issue_types[issue.split(":")[0]] += 1
    if issue_types:
        print(f"  Issue breakdown:")
        for issue, count in issue_types.most_common():
            print(f"    {issue}: {count}")

    # Save
    out_path = Path(__file__).parent / "fulfiller_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved to {out_path}")


if __name__ == "__main__":
    main()
