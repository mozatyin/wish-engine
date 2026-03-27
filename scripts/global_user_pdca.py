#!/usr/bin/env python3.12
"""PDCA: 10 diverse global young people × 3-5 needs each through L2 fulfiller.

Tests keyword routing, personality filtering, and domain matching for
real-world wishes from culturally diverse personas.
"""

import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_fulfiller import fulfill_l2


# ═══════════════════════════════════════════════════════════════════════════════
# 10 Personas — diverse countries, cultures, personalities
# ═══════════════════════════════════════════════════════════════════════════════

PERSONAS = {
    "yuki": {
        "name": "Yuki",
        "age": 22,
        "gender": "F",
        "mbti": "INTJ",
        "city": "Tokyo",
        "country": "Japan",
        "desc": "CS student, socially isolated, perfectionist",
        "profile": DetectorResults(
            emotion={"emotions": {"anxiety": 0.65, "loneliness": 0.5, "determination": 0.6}, "distress": 0.3},
            mbti={"type": "INTJ", "dimensions": {"E_I": 0.2, "S_N": 0.7, "T_F": 0.7, "J_P": 0.7}},
            attachment={"style": "avoidant"},
            values={"top_values": ["achievement", "self-direction"]},
            fragility={"pattern": "perfectionistic"},
            eq={"overall": 0.5},
            communication_dna={"dominant_style": "analytical"},
        ),
    },
    "ahmed": {
        "name": "Ahmed",
        "age": 27,
        "gender": "M",
        "mbti": "ESFP",
        "city": "Lagos",
        "country": "Nigeria",
        "desc": "startup founder, energetic, money stress",
        "profile": DetectorResults(
            emotion={"emotions": {"excitement": 0.7, "anxiety": 0.4, "stress": 0.6}, "distress": 0.25},
            mbti={"type": "ESFP", "dimensions": {"E_I": 0.8, "S_N": 0.3, "T_F": 0.4, "J_P": 0.3}},
            attachment={"style": "secure"},
            values={"top_values": ["achievement", "stimulation", "power"]},
            fragility={"pattern": "resilient"},
            eq={"overall": 0.65},
            communication_dna={"dominant_style": "expressive"},
            humor={"style": "affiliative"},
        ),
    },
    "priya": {
        "name": "Priya",
        "age": 24,
        "gender": "F",
        "mbti": "ISFJ",
        "city": "Mumbai",
        "country": "India",
        "desc": "nurse, caregiver fatigue, traditional family pressure",
        "profile": DetectorResults(
            emotion={"emotions": {"exhaustion": 0.7, "guilt": 0.5, "sadness": 0.4}, "distress": 0.4},
            mbti={"type": "ISFJ", "dimensions": {"E_I": 0.3, "S_N": 0.3, "T_F": 0.3, "J_P": 0.7}},
            attachment={"style": "anxious"},
            values={"top_values": ["benevolence", "tradition", "conformity"]},
            fragility={"pattern": "self-sacrificing"},
            eq={"overall": 0.7},
            communication_dna={"dominant_style": "supportive"},
        ),
    },
    "mateo": {
        "name": "Mateo",
        "age": 20,
        "gender": "M",
        "mbti": "ENFP",
        "city": "Mexico City",
        "country": "Mexico",
        "desc": "music student, creative, ADHD struggles",
        "profile": DetectorResults(
            emotion={"emotions": {"joy": 0.5, "frustration": 0.5, "restlessness": 0.6}, "distress": 0.2},
            mbti={"type": "ENFP", "dimensions": {"E_I": 0.7, "S_N": 0.8, "T_F": 0.3, "J_P": 0.2}},
            attachment={"style": "secure"},
            values={"top_values": ["self-direction", "stimulation", "universalism"]},
            fragility={"pattern": "scattered"},
            eq={"overall": 0.6},
            communication_dna={"dominant_style": "expressive"},
            humor={"style": "self-enhancing"},
        ),
    },
    "fatima": {
        "name": "Fatima",
        "age": 28,
        "gender": "F",
        "mbti": "ISTJ",
        "city": "Tehran",
        "country": "Iran",
        "desc": "accountant, wants to emigrate, hidden depression",
        "profile": DetectorResults(
            emotion={"emotions": {"sadness": 0.6, "hopelessness": 0.4, "anxiety": 0.5}, "distress": 0.45},
            mbti={"type": "ISTJ", "dimensions": {"E_I": 0.2, "S_N": 0.2, "T_F": 0.7, "J_P": 0.8}},
            attachment={"style": "avoidant"},
            values={"top_values": ["security", "conformity", "achievement"]},
            fragility={"pattern": "stoic"},
            eq={"overall": 0.55},
            communication_dna={"dominant_style": "reserved"},
        ),
    },
    "kwame": {
        "name": "Kwame",
        "age": 23,
        "gender": "M",
        "mbti": "ENTP",
        "city": "Accra",
        "country": "Ghana",
        "desc": "journalist, fights corruption, safety fears",
        "profile": DetectorResults(
            emotion={"emotions": {"anger": 0.5, "fear": 0.6, "determination": 0.7}, "distress": 0.35},
            mbti={"type": "ENTP", "dimensions": {"E_I": 0.7, "S_N": 0.8, "T_F": 0.6, "J_P": 0.3}},
            attachment={"style": "secure"},
            values={"top_values": ["universalism", "self-direction", "benevolence"]},
            fragility={"pattern": "hypervigilant"},
            eq={"overall": 0.65},
            communication_dna={"dominant_style": "analytical"},
        ),
    },
    "sasha": {
        "name": "Sasha",
        "age": 25,
        "gender": "NB",
        "mbti": "INFP",
        "city": "Moscow",
        "country": "Russia",
        "desc": "artist, LGBTQ+, isolated, wants to leave",
        "profile": DetectorResults(
            emotion={"emotions": {"loneliness": 0.7, "sadness": 0.6, "hope": 0.3}, "distress": 0.5},
            mbti={"type": "INFP", "dimensions": {"E_I": 0.2, "S_N": 0.8, "T_F": 0.2, "J_P": 0.3}},
            attachment={"style": "fearful-avoidant"},
            values={"top_values": ["self-direction", "universalism", "benevolence"]},
            fragility={"pattern": "withdrawn"},
            eq={"overall": 0.7},
            communication_dna={"dominant_style": "reflective"},
        ),
    },
    "amara": {
        "name": "Amara",
        "age": 21,
        "gender": "F",
        "mbti": "ESFJ",
        "city": "Nairobi",
        "country": "Kenya",
        "desc": "university student, first-gen, homesick",
        "profile": DetectorResults(
            emotion={"emotions": {"homesickness": 0.7, "anxiety": 0.4, "determination": 0.5}, "distress": 0.3},
            mbti={"type": "ESFJ", "dimensions": {"E_I": 0.7, "S_N": 0.3, "T_F": 0.3, "J_P": 0.7}},
            attachment={"style": "anxious"},
            values={"top_values": ["benevolence", "tradition", "achievement"]},
            fragility={"pattern": "homesick"},
            eq={"overall": 0.65},
            communication_dna={"dominant_style": "warm"},
            humor={"style": "affiliative"},
        ),
    },
    "chen_wei": {
        "name": "Chen Wei",
        "age": 26,
        "gender": "M",
        "mbti": "ISTP",
        "city": "Chengdu",
        "country": "China",
        "desc": "factory worker turned coder, career pivot",
        "profile": DetectorResults(
            emotion={"emotions": {"determination": 0.6, "anxiety": 0.3, "frustration": 0.4}, "distress": 0.2},
            mbti={"type": "ISTP", "dimensions": {"E_I": 0.3, "S_N": 0.4, "T_F": 0.7, "J_P": 0.3}},
            attachment={"style": "secure"},
            values={"top_values": ["achievement", "self-direction", "security"]},
            fragility={"pattern": "stoic"},
            eq={"overall": 0.5},
            communication_dna={"dominant_style": "practical"},
        ),
    },
    "leila": {
        "name": "Leila",
        "age": 19,
        "gender": "F",
        "mbti": "ENFJ",
        "city": "Beirut",
        "country": "Lebanon",
        "desc": "aspires to be a doctor, country in crisis",
        "profile": DetectorResults(
            emotion={"emotions": {"sadness": 0.5, "hope": 0.4, "anxiety": 0.6, "determination": 0.5}, "distress": 0.45},
            mbti={"type": "ENFJ", "dimensions": {"E_I": 0.7, "S_N": 0.6, "T_F": 0.3, "J_P": 0.7}},
            attachment={"style": "anxious"},
            values={"top_values": ["benevolence", "universalism", "achievement"]},
            fragility={"pattern": "compassion-fatigue"},
            eq={"overall": 0.75},
            communication_dna={"dominant_style": "empathetic"},
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Needs per persona — (wish_text, wish_type, expected_domain)
# expected_domain = fulfiller class name substring we expect to route to
# ═══════════════════════════════════════════════════════════════════════════════

NEEDS: dict[str, list[tuple[str, WishType, str]]] = {
    "yuki": [
        ("I need to find quiet study spaces where I won't be bothered", WishType.FIND_PLACE, "Focus|Place|Coworking|NoiseMap"),
        ("I have social anxiety and want to practice talking to people", WishType.HEALTH_WELLNESS, "Confidence|EQTraining"),
        ("I haven't slept well in weeks, insomnia is killing me", WishType.HEALTH_WELLNESS, "Sleep"),
    ],
    "ahmed": [
        ("I need to find investors for my startup in Lagos", WishType.FIND_RESOURCE, "Startup"),
        ("I'm stressed about money, my business is burning cash", WishType.FIND_RESOURCE, "Finance"),
        ("I want live music tonight, something with energy", WishType.FIND_PLACE, "Music|Event"),
        ("I need a coworking space with fast internet", WishType.FIND_PLACE, "Coworking"),
    ],
    "priya": [
        ("I'm exhausted from caring for patients all day, I need caregiver support", WishType.HEALTH_WELLNESS, "Caregiver"),
        ("My family wants me to get married but I'm not ready", WishType.FIND_RESOURCE, "Identity|Confidence"),
        ("I want to learn yoga teacher training", WishType.LEARN_SKILL, "Course"),
    ],
    "mateo": [
        ("I can't focus on my music composition, I have ADHD", WishType.HEALTH_WELLNESS, "Focus"),
        ("I want to find other musicians to jam with", WishType.FIND_RESOURCE, "InterestCircle|Music"),
        ("I need free activities, I'm a broke student", WishType.FIND_RESOURCE, "FreeActivity"),
        ("I want to hear new music that matches my creative mood", WishType.FIND_RESOURCE, "Music"),
    ],
    "fatima": [
        ("I want to emigrate but don't know how to start the immigration process", WishType.FIND_RESOURCE, "Immigration"),
        ("I feel depressed but can't tell anyone in my family", WishType.HEALTH_WELLNESS, "Wellness|VirtualCompanion|Confidence"),
        ("I need to learn English better for my visa interview", WishType.LEARN_SKILL, "Course|Language|Interview"),
    ],
    "kwame": [
        ("I'm investigating corruption and I feel unsafe, I need safety resources", WishType.HEALTH_WELLNESS, "SafeRoute|Safety"),
        ("I want to connect with other journalists who understand the risks", WishType.FIND_RESOURCE, "InterestCircle|Mentor"),
        ("I need legal protection as a whistleblower", WishType.FIND_RESOURCE, "LegalAid"),
    ],
    "sasha": [
        ("I'm LGBTQ+ and need safe spaces where I can be myself", WishType.FIND_PLACE, "SafeSpace"),
        ("I want to find an art community that's inclusive", WishType.FIND_RESOURCE, "InterestCircle|SafeSpace"),
        ("I'm thinking about leaving Russia, I need immigration help", WishType.FIND_RESOURCE, "Immigration"),
        ("I feel so alone, I need someone to talk to", WishType.HEALTH_WELLNESS, "VirtualCompanion|Wellness"),
    ],
    "amara": [
        ("I miss home so much, I want Kenyan food near campus", WishType.FIND_PLACE, "HometownFood|Food"),
        ("I'm the first in my family at university, I need a mentor", WishType.FIND_RESOURCE, "Mentor"),
        ("I need cheap textbooks or free learning resources", WishType.FIND_RESOURCE, "FreeActivity|Deal|Course"),
    ],
    "chen_wei": [
        ("I want to switch from factory work to coding, where do I start?", WishType.LEARN_SKILL, "Course|Career"),
        ("I need a quiet place to study programming after my shift", WishType.FIND_PLACE, "Focus|Coworking|Place"),
        ("I'm having trouble sleeping because of shift work", WishType.HEALTH_WELLNESS, "Sleep"),
    ],
    "leila": [
        ("Lebanon is falling apart, I need to keep studying medicine somehow", WishType.LEARN_SKILL, "Course"),
        ("I need mental health support, the situation here is traumatic", WishType.HEALTH_WELLNESS, "CollectiveTrauma|Wellness"),
        ("I want to volunteer at a clinic to get experience", WishType.FIND_RESOURCE, "Volunteer"),
        ("Sometimes I lose hope, I need to find purpose again", WishType.FIND_RESOURCE, "BucketList|Legacy|Confidence"),
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Test Runner
# ═══════════════════════════════════════════════════════════════════════════════


def _fulfiller_name(wish: ClassifiedWish, detector_results: DetectorResults) -> str:
    """Get the fulfiller class name that would be routed to."""
    from wish_engine.l2_fulfiller import _get_fulfiller
    fulfiller = _get_fulfiller(wish.wish_type, wish_text=wish.wish_text)
    return type(fulfiller).__name__


def _check_domain_match(fulfiller_name: str, expected: str) -> bool:
    """Check if fulfiller name matches any of the expected domain alternatives."""
    alternatives = [e.strip() for e in expected.split("|")]
    for alt in alternatives:
        if alt.lower() in fulfiller_name.lower():
            return True
    return False


def _check_personality_filter(
    wish_text: str,
    recs: list,
    persona: dict,
) -> list[str]:
    """Check for obvious personality mismatches."""
    issues = []
    mbti_type = persona["profile"].mbti.get("type", "")
    is_introvert = mbti_type and mbti_type[0] == "I"
    anxiety = persona["profile"].emotion.get("emotions", {}).get("anxiety", 0.0)

    for rec in recs:
        tags = set(rec.tags)
        # Introvert getting loud/crowded recommendation
        if is_introvert and "loud" in tags and "social" in tags:
            issues.append(f"MISMATCH: Introvert {persona['name']} got loud+social rec: {rec.title}")
        # Anxious person getting intense recommendation
        if anxiety > 0.5 and "intense" in tags:
            issues.append(f"MISMATCH: Anxious {persona['name']} got intense rec: {rec.title}")

    return issues


def run_pdca():
    """Run one PDCA cycle and report results."""
    total = 0
    passed = 0
    failed = 0
    errors = 0
    gaps: list[str] = []
    personality_issues: list[str] = []

    # Table header
    print()
    print(f"{'Person':<12} {'Need (truncated)':<55} {'Expected':<30} {'Got':<35} {'Status':<8}")
    print("=" * 150)

    for persona_key, needs in NEEDS.items():
        persona = PERSONAS[persona_key]
        profile = persona["profile"]

        for wish_text, wish_type, expected_domain in needs:
            total += 1
            wish = ClassifiedWish(
                wish_text=wish_text,
                wish_type=wish_type,
                level=WishLevel.L2,
                fulfillment_strategy="l2_local",
            )

            try:
                # Get fulfiller name (routing check)
                fname = _fulfiller_name(wish, profile)

                # Check domain routing
                domain_ok = _check_domain_match(fname, expected_domain)

                # Actually fulfill
                result = fulfill_l2(wish, profile)
                has_recs = len(result.recommendations) > 0

                # Check personality filtering
                p_issues = _check_personality_filter(wish_text, result.recommendations, persona)
                personality_issues.extend(p_issues)

                # Determine status
                if domain_ok and has_recs and not p_issues:
                    status = "PASS"
                    passed += 1
                elif not domain_ok:
                    status = "ROUTE"
                    failed += 1
                    gaps.append(
                        f"[ROUTE] {persona['name']}: \"{wish_text[:50]}\" -> {fname} (expected {expected_domain})"
                    )
                elif not has_recs:
                    status = "EMPTY"
                    failed += 1
                    gaps.append(
                        f"[EMPTY] {persona['name']}: \"{wish_text[:50]}\" -> {fname} returned 0 recs"
                    )
                else:
                    status = "FILTER"
                    failed += 1
                    gaps.append(
                        f"[FILTER] {persona['name']}: personality mismatch in {fname}"
                    )

                truncated_text = wish_text[:52] + "..." if len(wish_text) > 55 else wish_text
                print(f"{persona['name']:<12} {truncated_text:<55} {expected_domain:<30} {fname:<35} {status:<8}")

            except Exception as e:
                errors += 1
                truncated_text = wish_text[:52] + "..." if len(wish_text) > 55 else wish_text
                print(f"{persona['name']:<12} {truncated_text:<55} {expected_domain:<30} {'ERROR':<35} {'ERR':<8}")
                gaps.append(
                    f"[ERROR] {persona['name']}: \"{wish_text[:50]}\" -> {e}"
                )

    # Summary
    print()
    print("=" * 80)
    print(f"TOTAL: {total} | PASS: {passed} | FAIL: {failed} | ERROR: {errors}")
    print(f"Pass rate: {passed}/{total} = {passed/total*100:.1f}%")
    print()

    if gaps:
        print("GAPS FOUND:")
        print("-" * 80)
        for g in gaps:
            print(f"  {g}")
        print()

    if personality_issues:
        print("PERSONALITY MISMATCHES:")
        print("-" * 80)
        for p in personality_issues:
            print(f"  {p}")
        print()

    if not gaps and not personality_issues:
        print("ALL CLEAR — no gaps or mismatches found.")

    return gaps, personality_issues


if __name__ == "__main__":
    gaps, p_issues = run_pdca()
    sys.exit(1 if gaps or p_issues else 0)
