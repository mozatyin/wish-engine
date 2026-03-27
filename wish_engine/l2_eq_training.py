"""EQTrainingFulfiller — EQ exercises targeting user's weak dimensions.

12 EQ exercises based on user's EQ detector weak dimensions. Zero LLM.
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

# ── EQ Training Catalog (12 entries) ─────────────────────────────────────────

EQ_CATALOG: list[dict] = [
    {
        "title": "Emotion Labeling Practice",
        "description": "3 times today, pause and name your exact emotion — not 'fine', but 'frustrated' or 'hopeful'.",
        "category": "emotion_labeling",
        "tags": ["quiet", "self-paced", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "eq_dimension": "self_awareness",
    },
    {
        "title": "Perspective Taking Exercise",
        "description": "Pick a disagreement from today — write 3 sentences from the other person's point of view.",
        "category": "perspective_taking",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "eq_dimension": "empathy",
    },
    {
        "title": "Active Listening Drill",
        "description": "In your next conversation, repeat back what you heard before responding — 'So you're saying...'",
        "category": "active_listening_drill",
        "tags": ["social", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
        "eq_dimension": "empathy",
    },
    {
        "title": "Empathy Mapping",
        "description": "Think of someone close — write what they might be Thinking, Feeling, Saying, and Doing right now.",
        "category": "empathy_mapping",
        "tags": ["quiet", "self-paced", "calming", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "eq_dimension": "empathy",
    },
    {
        "title": "Emotional Regulation Timer",
        "description": "When a strong emotion hits, set a 90-second timer before reacting — the wave will pass.",
        "category": "emotional_regulation",
        "tags": ["self-paced", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "eq_dimension": "self_regulation",
    },
    {
        "title": "Social Awareness Scan",
        "description": "In a group setting, observe: who's quiet? Who's tense? Who needs to be heard? — just notice.",
        "category": "social_awareness",
        "tags": ["social", "calming", "quiet"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "moderate",
        "eq_dimension": "social_awareness",
    },
    {
        "title": "Conflict Role-Play",
        "description": "Replay a recent conflict in your head — but this time, respond with curiosity instead of defense.",
        "category": "conflict_practice",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "eq_dimension": "social_skills",
    },
    {
        "title": "Feedback Giving Practice",
        "description": "Give one piece of feedback today using: 'When you X, I felt Y, and I'd prefer Z.'",
        "category": "feedback_giving",
        "tags": ["social", "assertive", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
        "eq_dimension": "social_skills",
    },
    {
        "title": "Receive Feedback Gracefully",
        "description": "Ask someone for honest feedback — listen fully before responding. Just say 'thank you.'",
        "category": "feedback_receiving",
        "tags": ["social", "calming", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
        "eq_dimension": "self_regulation",
    },
    {
        "title": "Emotion Vocabulary Builder",
        "description": "Learn 5 new emotion words today (e.g., wistful, exasperated, serene) — precision is power.",
        "category": "emotional_vocabulary",
        "tags": ["quiet", "self-paced", "calming", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "eq_dimension": "self_awareness",
    },
    {
        "title": "Nonverbal Reading Practice",
        "description": "Watch a conversation (muted TV works) — guess emotions from body language alone.",
        "category": "nonverbal_reading",
        "tags": ["quiet", "self-paced", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "eq_dimension": "social_awareness",
    },
    {
        "title": "Stress Response Journal",
        "description": "When stressed, write: trigger → body sensation → emotion → thought → action. Map your pattern.",
        "category": "stress_response",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "eq_dimension": "self_regulation",
    },
]


# ── EQ Weakness Detection ────────────────────────────────────────────────────

_EQ_DIM_MAP: dict[str, list[str]] = {
    "self_awareness": ["emotion_labeling", "emotional_vocabulary"],
    "empathy": ["perspective_taking", "active_listening_drill", "empathy_mapping"],
    "self_regulation": ["emotional_regulation", "feedback_receiving", "stress_response"],
    "social_awareness": ["social_awareness", "nonverbal_reading"],
    "social_skills": ["conflict_practice", "feedback_giving"],
}


def _detect_weak_eq_dims(detector_results: DetectorResults) -> list[str]:
    """Identify weak EQ dimensions from detector results."""
    weak: list[str] = []
    eq_data = detector_results.eq

    # Check overall EQ score
    eq_score = eq_data.get("score", 0.5)
    if eq_score < 0.4:
        # Low overall EQ — recommend all areas
        weak.extend(["self_awareness", "empathy", "self_regulation", "social_awareness", "social_skills"])
        return weak

    # Check individual dimensions if available
    dims = eq_data.get("dimensions", {})
    for dim_name, dim_score in dims.items():
        if isinstance(dim_score, (int, float)) and dim_score < 0.4:
            weak.append(dim_name)

    return weak


def _get_target_categories(weak_dims: list[str]) -> list[str]:
    """Map weak EQ dimensions to target exercise categories."""
    targets: list[str] = []
    for dim in weak_dims:
        targets.extend(_EQ_DIM_MAP.get(dim, []))
    return list(dict.fromkeys(targets))


def _match_candidates(detector_results: DetectorResults) -> list[dict]:
    """Score candidates based on EQ weakness alignment."""
    weak_dims = _detect_weak_eq_dims(detector_results)
    target_cats = _get_target_categories(weak_dims)

    fragility = detector_results.fragility.get("pattern", "")
    is_fragile = fragility in ("defensive", "fragile", "avoidant")

    candidates: list[dict] = []
    for item in EQ_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Weakness alignment
        if item["category"] in target_cats:
            score_boost += 0.25

        # Fragility-aware
        if is_fragile and item["difficulty"] == "gentle":
            score_boost += 0.10
        elif is_fragile and item["difficulty"] == "moderate":
            score_boost -= 0.05

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_reason(item, target_cats)
        candidates.append(item_copy)

    return candidates


def _build_reason(item: dict, target_cats: list[str]) -> str:
    """Build relevance reason."""
    dim = item.get("eq_dimension", "")
    if item["category"] in target_cats:
        return f"Targets your EQ growth area: {dim.replace('_', ' ')}"
    return f"Build your {dim.replace('_', ' ')}"


class EQTrainingFulfiller(L2Fulfiller):
    """L2 fulfiller for EQ training wishes — targets weak EQ dimensions.

    12-entry curated catalog. Zero LLM.
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
                text="Did you practice your EQ exercise today?",
                delay_hours=12,
            ),
        )
