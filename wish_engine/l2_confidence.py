"""ConfidenceFulfiller — confidence builders with fragility awareness.

15 confidence builders. Gentle for high fragility. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    Recommendation,
    ReminderOption,
)

# ── Confidence Catalog (15 entries) ──────────────────────────────────────────

CONFIDENCE_CATALOG: list[dict] = [
    {
        "title": "Daily Affirmation Practice",
        "description": "Write 3 'I am' statements each morning — repetition rewires belief.",
        "category": "daily_affirmation",
        "tags": ["quiet", "self-paced", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Achievement Log",
        "description": "Write down 3 things you accomplished today — no matter how small. They count.",
        "category": "achievement_log",
        "tags": ["quiet", "self-paced", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Strength Finder Exercise",
        "description": "Ask 3 people: 'What do you think I'm good at?' Their answers might surprise you.",
        "category": "strength_finder",
        "tags": ["social", "warm", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
    },
    {
        "title": "Power Pose for 2 Minutes",
        "description": "Stand tall, hands on hips, chin up for 2 minutes — your body teaches your mind.",
        "category": "power_pose",
        "tags": ["quiet", "self-paced", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Comfort Zone Challenge",
        "description": "Do one thing today that makes you slightly uncomfortable — that's where growth lives.",
        "category": "comfort_zone_challenge",
        "tags": ["self-paced", "energizing", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Positive Self-Talk Swap",
        "description": "Catch one negative thought today and rewrite it — 'I can't' becomes 'I'm learning to'.",
        "category": "positive_self_talk",
        "tags": ["quiet", "self-paced", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Visualization Practice",
        "description": "Close your eyes and picture yourself succeeding — hold that image for 5 minutes.",
        "category": "visualization",
        "tags": ["quiet", "self-paced", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Past Wins Review",
        "description": "List 10 things you've overcome in your life — you've already proven you can do hard things.",
        "category": "past_wins_review",
        "tags": ["quiet", "self-paced", "calming", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Compliment Practice",
        "description": "Give 3 genuine compliments today — confidence grows when you uplift others.",
        "category": "compliment_practice",
        "tags": ["social", "warm", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "gentle",
    },
    {
        "title": "Rejection Therapy",
        "description": "Ask for something you expect to be refused — a discount, a favor, a seat upgrade. The 'no' is the lesson.",
        "category": "rejection_therapy",
        "tags": ["social", "energizing", "practical"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "bold",
    },
    {
        "title": "Skill Mastery Session",
        "description": "Spend 30 minutes improving one specific skill — competence builds confidence.",
        "category": "skill_mastery",
        "tags": ["quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Body Language Awareness",
        "description": "For one hour, notice your posture, eye contact, and gestures — adjust with intention.",
        "category": "body_language",
        "tags": ["self-paced", "practical", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Voice Training Exercise",
        "description": "Record yourself speaking for 2 minutes — listen back and notice your pace, tone, clarity.",
        "category": "voice_training",
        "tags": ["quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Mirror Exercise",
        "description": "Look into your own eyes in a mirror for 2 minutes — say 'I am enough.' Mean it.",
        "category": "mirror_exercise",
        "tags": ["quiet", "self-paced", "calming", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Success Journal",
        "description": "Before bed, write one thing that went well today and why — train your brain to find wins.",
        "category": "success_journal",
        "tags": ["quiet", "self-paced", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
]


def _select_difficulty(detector_results: DetectorResults) -> str:
    """Fragility-aware difficulty selection."""
    fragility = detector_results.fragility.get("pattern", "")
    if fragility in ("defensive", "fragile", "avoidant"):
        return "gentle"
    if fragility == "resilient":
        mbti = detector_results.mbti.get("type", "")
        if len(mbti) == 4 and mbti[0] == "E":
            return "bold"
    return "moderate"


def _match_candidates(detector_results: DetectorResults) -> list[dict]:
    """Score candidates — gentle for high fragility."""
    target_difficulty = _select_difficulty(detector_results)

    candidates: list[dict] = []
    for item in CONFIDENCE_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        if item["difficulty"] == target_difficulty:
            score_boost += 0.20
        elif target_difficulty == "gentle" and item["difficulty"] == "bold":
            score_boost -= 0.20  # Strong penalty for fragile users
        elif target_difficulty == "gentle" and item["difficulty"] == "moderate":
            score_boost -= 0.05

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_reason(item, target_difficulty)
        candidates.append(item_copy)

    return candidates


def _build_reason(item: dict, difficulty: str) -> str:
    """Build relevance reason."""
    base = f"Build confidence: {item['category'].replace('_', ' ')}"
    if difficulty == "gentle":
        return f"{base} — safe and gentle"
    if difficulty == "bold":
        return f"{base} — push your limits"
    return base


class ConfidenceFulfiller(L2Fulfiller):
    """L2 fulfiller for confidence wishes — fragility-aware builders.

    15-entry curated catalog. Gentle for high fragility. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(detector_results)

        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:3]

        recommendations = [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "Matches your profile"),
                score=c.get("_personality_score", 0.5),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Did you do your confidence exercise today?",
                delay_hours=12,
            ),
        )
