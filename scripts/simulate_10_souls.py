#!/usr/bin/env python3.12
"""Simulate 10 literary characters through the full Wish Engine pipeline.

Each character:
1. Has a complete psychological profile (from TriSoul persistent intentions)
2. Expresses wishes through the system
3. Posts L3 needs to the Marketplace
4. Agents discover matches across characters

The ultimate integration test: who finds whom?
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.engine import WishEngine
from wish_engine.models import (
    DetectorResults, EmotionState, CrossDetectorPattern,
    WishType, WishLevel,
)
from wish_engine.marketplace import Marketplace
from wish_engine.classifier import classify
from wish_engine.match_reason import generate_match_reason


# ═══════════════════════════════════════════════════════════════════════════════
# 10 Character Profiles — mapped from TriSoul persistent intentions
# ═══════════════════════════════════════════════════════════════════════════════

CHARACTERS = {
    "scarlett": {
        "name": "Scarlett O'Hara",
        "source": "Gone with the Wind",
        "soul_type": "Frost Guard",  # armored vulnerability
        "profile": DetectorResults(
            emotion={"emotions": {"determination": 0.8, "fear": 0.5, "loneliness": 0.4}, "distress": 0.35},
            conflict={"style": "competing"},
            mbti={"type": "ESTJ"},
            attachment={"style": "dismissive-avoidant"},
            values={"top_values": ["power", "achievement", "self-direction"]},
            fragility={"pattern": "defensive"},
            eq={"overall": 0.45},
            communication_dna={"dominant_style": "direct-assertive"},
            humor={"style": "aggressive"},
            love_language={"primary": "acts_of_service"},
        ),
        # What Scarlett's soul truly needs (from P-layer)
        "deep_wishes": [
            "I need someone who can match my strength without trying to control me",
            "I want to understand why I push away everyone who truly loves me",
        ],
        "l3_seeking": ["resilience", "independence", "directness", "emotional_strength"],
        "l3_offering": ["determination", "survival_instinct", "practical_intelligence", "leadership"],
    },
    "amy": {
        "name": "Amy Dunne",
        "source": "Gone Girl",
        "soul_type": "Hidden Depths",  # still waters, dangerous undercurrents
        "profile": DetectorResults(
            emotion={"emotions": {"contempt": 0.6, "loneliness": 0.7, "anger": 0.5}, "distress": 0.55},
            conflict={"style": "competing"},
            mbti={"type": "INTJ"},
            attachment={"style": "disorganized"},
            values={"top_values": ["power", "self-direction", "achievement"]},
            fragility={"pattern": "perfectionistic"},
            eq={"overall": 0.85},  # high EQ used manipulatively
            communication_dna={"dominant_style": "strategic-controlled"},
            humor={"style": "aggressive"},
            love_language={"primary": "quality_time"},
        ),
        "deep_wishes": [
            "I want someone to love the real me, not the performance",
            "I need to understand why perfection never feels like enough",
        ],
        "l3_seeking": ["authenticity", "sees_through_masks", "unconditional_acceptance", "intellectual_equal"],
        "l3_offering": ["intelligence", "strategic_thinking", "attention_to_detail", "perception"],
    },
    "walter": {
        "name": "Walter White",
        "source": "Breaking Bad",
        "soul_type": "Quiet Storm",  # intensity beneath calm
        "profile": DetectorResults(
            emotion={"emotions": {"resentment": 0.7, "pride": 0.6, "fear": 0.4}, "distress": 0.50},
            conflict={"style": "competing"},
            mbti={"type": "INTJ"},
            attachment={"style": "dismissive-avoidant"},
            values={"top_values": ["achievement", "power", "self-direction"]},
            fragility={"pattern": "defensive"},
            eq={"overall": 0.55},
            communication_dna={"dominant_style": "analytical-direct"},
            humor={"style": "self-enhancing"},
            love_language={"primary": "acts_of_service"},
        ),
        "deep_wishes": [
            "I need someone who recognizes my brilliance without being afraid of it",
            "I want to understand why I couldn't accept being ordinary",
        ],
        "l3_seeking": ["intellectual_respect", "recognition_of_brilliance", "fearlessness", "ambition"],
        "l3_offering": ["brilliance", "strategic_thinking", "chemistry_knowledge", "determination"],
    },
    "tony": {
        "name": "Tony Soprano",
        "source": "The Sopranos",
        "soul_type": "Tension Wire",  # stretched between worlds
        "profile": DetectorResults(
            emotion={"emotions": {"anxiety": 0.7, "anger": 0.6, "sadness": 0.5}, "distress": 0.60},
            conflict={"style": "competing"},
            mbti={"type": "ESTP"},
            attachment={"style": "anxious-preoccupied"},
            values={"top_values": ["security", "power", "tradition"]},
            fragility={"pattern": "approval-seeking"},
            eq={"overall": 0.60},
            communication_dna={"dominant_style": "direct-emotional"},
            humor={"style": "affiliative"},
            love_language={"primary": "physical_touch"},
        ),
        "deep_wishes": [
            "I want someone who accepts me without trying to fix me or fear me",
            "I need to understand why my mother's rejection still controls everything",
        ],
        "l3_seeking": ["unconditional_acceptance", "patience", "non_judgmental", "emotional_warmth"],
        "l3_offering": ["loyalty", "protection", "generosity", "emotional_depth"],
    },
    "don": {
        "name": "Don Draper",
        "source": "Mad Men",
        "soul_type": "Hidden Depths",
        "profile": DetectorResults(
            emotion={"emotions": {"shame": 0.7, "loneliness": 0.6, "desire": 0.5}, "distress": 0.55},
            conflict={"style": "avoiding"},
            mbti={"type": "ENTP"},
            attachment={"style": "dismissive-avoidant"},
            values={"top_values": ["self-direction", "stimulation", "achievement"]},
            fragility={"pattern": "withdrawal"},
            eq={"overall": 0.70},
            communication_dna={"dominant_style": "charismatic-guarded"},
            humor={"style": "self-enhancing"},
            love_language={"primary": "physical_touch"},
        ),
        "deep_wishes": [
            "I want someone who can love Dick Whitman, not just Don Draper",
            "I need to understand why I destroy every good thing in my life",
        ],
        "l3_seeking": ["acceptance_of_true_self", "non_judgmental", "sees_through_masks", "patience"],
        "l3_offering": ["charisma", "creative_brilliance", "emotional_depth", "understanding_of_loneliness"],
    },
    "michael_c": {
        "name": "Michael Corleone",
        "source": "The Godfather",
        "soul_type": "Frost Guard",
        "profile": DetectorResults(
            emotion={"emotions": {"duty": 0.8, "isolation": 0.6, "grief": 0.4}, "distress": 0.45},
            conflict={"style": "competing"},
            mbti={"type": "ISTJ"},
            attachment={"style": "dismissive-avoidant"},
            values={"top_values": ["security", "tradition", "power"]},
            fragility={"pattern": "suppression"},
            eq={"overall": 0.65},
            communication_dna={"dominant_style": "measured-strategic"},
            humor={"style": "self-enhancing"},
            love_language={"primary": "acts_of_service"},
        ),
        "deep_wishes": [
            "I need someone who understands what it means to sacrifice everything for family",
            "I want to know if I was ever really different from my father",
        ],
        "l3_seeking": ["understanding_of_sacrifice", "loyalty", "acceptance_of_burden", "shared_duty"],
        "l3_offering": ["protection", "loyalty", "strategic_intelligence", "unwavering_commitment"],
    },
    "katniss": {
        "name": "Katniss Everdeen",
        "source": "The Hunger Games",
        "soul_type": "Calm Harbor",  # safe for others, turbulent inside
        "profile": DetectorResults(
            emotion={"emotions": {"hypervigilance": 0.7, "guilt": 0.6, "love": 0.5}, "distress": 0.55},
            conflict={"style": "avoiding"},
            mbti={"type": "ISTP"},
            attachment={"style": "dismissive-avoidant"},
            values={"top_values": ["security", "benevolence", "self-direction"]},
            fragility={"pattern": "hypervigilant"},
            eq={"overall": 0.50},
            communication_dna={"dominant_style": "action-oriented"},
            humor={"style": "self-deprecating"},
            love_language={"primary": "acts_of_service"},
        ),
        "deep_wishes": [
            "I want someone who doesn't need me to be strong all the time",
            "I need to understand why I feel guilty for surviving",
        ],
        "l3_seeking": ["patience", "no_expectations", "gentleness", "understanding_of_trauma"],
        "l3_offering": ["protection", "survival_skills", "fierce_loyalty", "practical_help"],
    },
    "jordan": {
        "name": "Jordan Belfort",
        "source": "Wolf of Wall Street",
        "soul_type": "Spark Seeker",  # addicted to intensity
        "profile": DetectorResults(
            emotion={"emotions": {"excitement": 0.8, "emptiness": 0.5, "contempt": 0.4}, "distress": 0.25},
            conflict={"style": "competing"},
            mbti={"type": "ESTP"},
            attachment={"style": "dismissive-avoidant"},
            values={"top_values": ["power", "stimulation", "hedonism"]},
            fragility={"pattern": "grandiose"},
            eq={"overall": 0.75},  # high EQ for manipulation
            communication_dna={"dominant_style": "charismatic-persuasive"},
            humor={"style": "affiliative"},
            love_language={"primary": "gifts"},
        ),
        "deep_wishes": [
            "I need someone who sees through the show and still stays",
            "I want to feel something real without needing the high",
        ],
        "l3_seeking": ["authenticity", "sees_through_masks", "emotional_honesty", "shared_intensity"],
        "l3_offering": ["charisma", "energy", "entertainment", "ambition"],
    },
    "celie": {
        "name": "Celie",
        "source": "The Color Purple",
        "soul_type": "Warm Current",  # quiet warmth that heals
        "profile": DetectorResults(
            emotion={"emotions": {"hope": 0.6, "sadness": 0.5, "love": 0.7}, "distress": 0.40},
            conflict={"style": "accommodating"},
            mbti={"type": "INFP"},
            attachment={"style": "anxious-preoccupied"},
            values={"top_values": ["benevolence", "universalism", "tradition"]},
            fragility={"pattern": "suppression"},
            eq={"overall": 0.70},
            communication_dna={"dominant_style": "quiet-reflective"},
            humor={"style": "self-deprecating"},
            love_language={"primary": "words_of_affirmation"},
        ),
        "deep_wishes": [
            "I want to be seen as someone worthy of love",
            "I need someone who believes I have something valuable to say",
        ],
        "l3_seeking": ["gentleness", "belief_in_worth", "patience", "creative_spirit"],
        "l3_offering": ["unconditional_love", "patience", "resilience", "creative_talent", "non_judgmental"],
    },
    "xu_sanguan": {
        "name": "Xu Sanguan (许三观)",
        "source": "Chronicle of a Blood Merchant",
        "soul_type": "Warm Current",
        "profile": DetectorResults(
            emotion={"emotions": {"duty": 0.7, "love": 0.6, "anxiety": 0.4}, "distress": 0.35},
            conflict={"style": "accommodating"},
            mbti={"type": "ISFJ"},
            attachment={"style": "secure"},
            values={"top_values": ["benevolence", "tradition", "security"]},
            fragility={"pattern": "self-sacrificing"},
            eq={"overall": 0.55},
            communication_dna={"dominant_style": "practical-warm"},
            humor={"style": "affiliative"},
            love_language={"primary": "acts_of_service"},
        ),
        "deep_wishes": [
            "I want someone to acknowledge that my sacrifice meant something",
            "I need to know I'm still useful even when my body fails me",
        ],
        "l3_seeking": ["recognition_of_sacrifice", "family_connection", "understanding_of_duty", "gratitude"],
        "l3_offering": ["unconditional_sacrifice", "practical_help", "loyalty", "quiet_strength", "non_judgmental"],
    },
}


def main():
    print("=" * 70)
    print("  10 SOULS IN THE WISH ENGINE")
    print("  — Who will the stars connect?")
    print("=" * 70)

    marketplace = Marketplace()
    engine = WishEngine(marketplace=marketplace, fulfill_l1=False, post_l3=True)

    # ── Phase 1: Each character processes their wishes ───────────────────

    print("\n" + "─" * 70)
    print("  PHASE 1: Star Map Generation")
    print("─" * 70)

    all_results = {}
    for char_id, char in CHARACTERS.items():
        agent_id = f"agent_{char_id}"
        marketplace.register_agent(agent_id, language="en")

        result = engine.process(
            raw_wishes=char["deep_wishes"],
            detector_results=char["profile"],
            emotion_state=EmotionState(
                distress=char["profile"].emotion.get("distress", 0.3),
            ),
            soul_type={"name": char["soul_type"]},
            user_id=char_id,
            session_id=f"sim_{char_id}",
            agent_id=agent_id,
        )
        all_results[char_id] = result

        # Post character-specific L3 needs with their actual seeking traits
        if char["l3_seeking"]:
            for wish in result.l3_wishes:
                try:
                    marketplace.post_need(
                        agent_id,
                        wish_type=wish.wish_type,
                        seeking=char["l3_seeking"],
                    )
                except (ValueError, Exception):
                    pass  # Already posted by engine or rate limit

        stars = "★" * len(result.classified) + "☆" * (5 - len(result.classified))
        print(f"\n  {char['name']} ({char['source']})")
        print(f"  Soul Type: {char['soul_type']}  |  Stars: {stars}")
        for w in result.classified:
            level_icon = {"L1": "🔮", "L2": "🌐", "L3": "💫"}.get(w.level.value, "?")
            print(f"    {level_icon} [{w.level.value}] {w.wish_type.value}: {w.wish_text[:60]}")

    # ── Phase 2: Agents post offerings to marketplace ────────────────────

    print("\n" + "─" * 70)
    print("  PHASE 2: Agents Post to Exchange")
    print("─" * 70)

    # Semantic capability synonyms — similar concepts should match
    SYNONYMS = {
        "unconditional_acceptance": {"unconditional_love", "non_judgmental", "acceptance_of_true_self"},
        "unconditional_love": {"unconditional_acceptance", "non_judgmental", "patience"},
        "emotional_warmth": {"empathy", "gentleness", "emotional_depth", "warmth"},
        "sees_through_masks": {"perception", "emotional_depth", "authenticity", "understanding_of_loneliness"},
        "intellectual_equal": {"strategic_thinking", "intelligence", "brilliance"},
        "recognition_of_brilliance": {"intellectual_respect", "recognition_of_sacrifice", "ambition"},
        "fearlessness": {"resilience", "emotional_strength", "determination", "survival_instinct"},
        "acceptance_of_true_self": {"non_judgmental", "unconditional_acceptance", "patience", "sees_through_masks"},
        "understanding_of_sacrifice": {"recognition_of_sacrifice", "loyalty", "shared_duty", "understanding_of_duty"},
        "understanding_of_trauma": {"patience", "gentleness", "non_judgmental", "emotional_depth"},
        "no_expectations": {"patience", "non_judgmental", "gentleness"},
        "emotional_honesty": {"authenticity", "emotional_depth", "directness"},
        "belief_in_worth": {"gentleness", "encouragement", "non_judgmental", "unconditional_love"},
        "creative_spirit": {"creative_talent", "creative_brilliance", "intelligence"},
        "shared_intensity": {"ambition", "energy", "determination", "excitement"},
        "family_connection": {"loyalty", "understanding_of_duty", "practical_help"},
        "gratitude": {"recognition_of_sacrifice", "patience", "gentleness"},
        "recognition_of_sacrifice": {"understanding_of_sacrifice", "gratitude", "loyalty"},
        "emotional_strength": {"resilience", "determination", "survival_instinct"},
    }

    def expand_capabilities(caps: list[str]) -> set[str]:
        expanded = set(caps)
        for cap in caps:
            expanded |= SYNONYMS.get(cap, set())
        return expanded

    # Each agent checks all open needs and responds if they can help
    for char_id, char in CHARACTERS.items():
        agent_id = f"agent_{char_id}"
        offering_expanded = expand_capabilities(char["l3_offering"])

        for need in marketplace.get_open_needs():
            if need.agent_id == agent_id:
                continue

            # Semantic overlap: expand both seeking and offering
            seeking_expanded = expand_capabilities(need.seeking)
            overlap = seeking_expanded & offering_expanded
            if len(overlap) >= 2:  # Need at least 2 shared capabilities
                try:
                    # Post actual offering (not expanded)
                    marketplace.post_response(
                        agent_id,
                        in_response_to=need.request_id,
                        offering=char["l3_offering"],
                    )
                except (ValueError, Exception):
                    pass

    stats = marketplace.get_stats()
    print(f"\n  Exchange Stats:")
    print(f"    Agents: {stats['agents']}")
    print(f"    Open needs: {stats['open_needs']}")
    print(f"    Open responses: {stats['open_responses']}")

    # ── Phase 3: Run matching engine ─────────────────────────────────────

    print("\n" + "─" * 70)
    print("  PHASE 3: Matching Engine Runs")
    print("─" * 70)

    matches = marketplace.create_matches()
    print(f"\n  Matches found: {len(matches)}")

    # ── Phase 4: Bilateral verification ──────────────────────────────────
    # In this simulation, agents auto-verify if compatibility is reasonable

    for match in matches:
        # Both agents verify (in real system, each checks host safety locally)
        marketplace.verify(match.match_id, match.agent_a_id, approved=True)
        marketplace.verify(match.match_id, match.agent_b_id, approved=True)

    mutual = marketplace.get_mutual_matches()

    # ── Phase 5: Reveal connections ──────────────────────────────────────

    print("\n" + "─" * 70)
    print("  PHASE 4: Stars Find Each Other")
    print("─" * 70)

    if not mutual:
        print("\n  No mutual matches found.")
    else:
        print(f"\n  {len(mutual)} connections discovered:\n")

        for m in sorted(mutual, key=lambda x: x.capability_overlap, reverse=True):
            char_a_id = m.agent_a_id.replace("agent_", "")
            char_b_id = m.agent_b_id.replace("agent_", "")
            char_a = CHARACTERS[char_a_id]
            char_b = CHARACTERS[char_b_id]

            # Find what they share
            need = marketplace._requests.get(m.need_request_id)
            resp = marketplace._requests.get(m.response_request_id)
            shared = set(need.seeking if need else []) & set(resp.offering if resp else [])

            # Generate match reason
            reason = generate_match_reason(
                m,
                need_seeking=need.seeking if need else [],
                offer_capabilities=resp.offering if resp else [],
                language="en",
            )

            print(f"  ╔══════════════════════════════════════════════════════════╗")
            print(f"  ║  {char_a['name']:20s}  ←→  {char_b['name']:20s}  ║")
            print(f"  ╠══════════════════════════════════════════════════════════╣")
            print(f"  ║  Compatibility: {m.capability_overlap:.0%}")
            print(f"  ║  Shared: {', '.join(shared) if shared else 'deep resonance'}")
            print(f"  ║")
            print(f"  ║  {char_a['name']}'s need:")
            print(f"  ║    \"{char_a['deep_wishes'][0][:55]}\"")
            print(f"  ║  {char_b['name']} offers:")
            print(f"  ║    {char_b['l3_offering'][:4]}")
            print(f"  ║")
            print(f"  ║  ✨ \"{reason}\"")
            print(f"  ╚══════════════════════════════════════════════════════════╝")
            print()

    # ── Summary ──────────────────────────────────────────────────────────

    print("─" * 70)
    print("  FINAL SCORECARD")
    print("─" * 70)

    total_wishes = sum(r.total_wishes for r in all_results.values())
    total_l1 = sum(len(r.l1_wishes) for r in all_results.values())
    total_l2 = sum(len(r.l2_wishes) for r in all_results.values())
    total_l3 = sum(len(r.l3_wishes) for r in all_results.values())

    print(f"\n  Characters: 10")
    print(f"  Total wishes detected: {total_wishes}")
    print(f"    L1 (AI fulfill): {total_l1}")
    print(f"    L2 (Internet): {total_l2}")
    print(f"    L3 (Human match): {total_l3}")
    print(f"  Marketplace: {stats['open_needs']} needs, {stats['open_responses']} responses")
    print(f"  Matches: {len(matches)} proposed, {len(mutual)} mutual")
    print(f"  Errors: {sum(len(r.errors) for r in all_results.values())}")


if __name__ == "__main__":
    main()
