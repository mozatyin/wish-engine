"""PersonalityGrowthFulfiller — growth exercises by weakest detector dimensions.

15 growth dimensions mapped to detector signals. Targets user's weakest areas.
Zero LLM.
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

# ── Growth Catalog (15 entries) ──────────────────────────────────────────────

GROWTH_CATALOG: list[dict] = [
    {
        "title": "Emotion Mirror Exercise",
        "description": "Name 3 emotions you felt today without judgment — awareness is the first step.",
        "category": "emotional_awareness",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Repair a Small Conflict",
        "description": "Revisit a recent disagreement and say 'I understand your point' — watch what shifts.",
        "category": "conflict_resolution",
        "tags": ["social", "assertive", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
    },
    {
        "title": "Share One Vulnerable Truth",
        "description": "Tell someone one thing you usually hide — 'I felt hurt when...' is enough.",
        "category": "vulnerability_practice",
        "tags": ["social", "warm", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "bold",
    },
    {
        "title": "Say No Without Apologizing",
        "description": "Decline one request today with a simple 'No, I can't' — no explanation needed.",
        "category": "boundary_setting",
        "tags": ["assertive", "practical", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Walk in Someone's Shoes",
        "description": "Pick someone who annoyed you today — imagine their day from morning to now.",
        "category": "empathy_building",
        "tags": ["quiet", "introspective", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Make a Clear Request",
        "description": "Ask for something specific today: 'I need X by Y' — clarity is kindness.",
        "category": "assertiveness",
        "tags": ["assertive", "social", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
    },
    {
        "title": "Listen Without Planning Your Reply",
        "description": "In one conversation, focus only on understanding — not on what you'll say next.",
        "category": "active_listening",
        "tags": ["social", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "gentle",
    },
    {
        "title": "Write Yourself a Kind Letter",
        "description": "Write 3 sentences to yourself as if you were your own best friend.",
        "category": "self_compassion",
        "tags": ["quiet", "self-paced", "calming", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Pause Before Reacting",
        "description": "Next time you feel anger rise, count to 10 before speaking — notice the gap.",
        "category": "anger_management",
        "tags": ["self-paced", "practical", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Ground Yourself in 5-4-3-2-1",
        "description": "Name 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste.",
        "category": "anxiety_coping",
        "tags": ["quiet", "self-paced", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Write a Letter to Your Younger Self",
        "description": "Tell the child version of you what you wish they'd known — healing starts here.",
        "category": "attachment_healing",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Share a Small Secret",
        "description": "Tell someone one small thing you've never mentioned — trust grows in tiny steps.",
        "category": "trust_building",
        "tags": ["social", "warm", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
    },
    {
        "title": "Release One Grudge",
        "description": "Think of someone you resent — write 'I'm letting this go' and mean it, even a little.",
        "category": "forgiveness_practice",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Recall a Time You Bounced Back",
        "description": "Write down one moment you thought you couldn't survive — but did. You're stronger.",
        "category": "resilience_building",
        "tags": ["quiet", "self-paced", "calming", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Use 'I Feel' Statements for a Day",
        "description": "Replace 'you always' with 'I feel X when Y' — watch how conversations transform.",
        "category": "communication_skills",
        "tags": ["social", "practical", "assertive"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
    },
]


# ── Weakness Detection ───────────────────────────────────────────────────────

# Map detector signals to growth dimensions
_WEAKNESS_MAP: dict[str, list[str]] = {
    "low_eq": ["emotional_awareness", "empathy_building", "active_listening"],
    "low_assertiveness": ["assertiveness", "boundary_setting", "communication_skills"],
    "high_anxiety": ["anxiety_coping", "self_compassion", "resilience_building"],
    "avoidant_attachment": ["attachment_healing", "trust_building", "vulnerability_practice"],
    "defensive_fragility": ["anger_management", "conflict_resolution", "forgiveness_practice"],
}


def _detect_weak_dimensions(detector_results: DetectorResults) -> list[str]:
    """Identify growth dimensions based on detector weaknesses."""
    weak: list[str] = []

    # EQ-based
    eq_score = detector_results.eq.get("score", 0.5)
    if eq_score < 0.4:
        weak.extend(_WEAKNESS_MAP["low_eq"])

    # Conflict style
    conflict_style = detector_results.conflict.get("style", "")
    if conflict_style in ("avoiding", "accommodating"):
        weak.extend(_WEAKNESS_MAP["low_assertiveness"])

    # Emotion-based anxiety
    anxiety = detector_results.emotion.get("emotions", {}).get("anxiety", 0.0)
    if anxiety > 0.5:
        weak.extend(_WEAKNESS_MAP["high_anxiety"])

    # Attachment
    attachment = detector_results.attachment.get("style", "")
    if attachment in ("avoidant", "fearful"):
        weak.extend(_WEAKNESS_MAP["avoidant_attachment"])

    # Fragility
    fragility = detector_results.fragility.get("pattern", "")
    if fragility in ("defensive", "fragile"):
        weak.extend(_WEAKNESS_MAP["defensive_fragility"])

    return list(dict.fromkeys(weak))  # deduplicate, preserve order


def _select_difficulty(detector_results: DetectorResults) -> str:
    """Select difficulty based on fragility."""
    fragility = detector_results.fragility.get("pattern", "")
    if fragility in ("defensive", "fragile", "avoidant"):
        return "gentle"
    if fragility == "resilient":
        return "bold"
    return "moderate"


def _match_candidates(
    detector_results: DetectorResults,
) -> list[dict]:
    """Score candidates based on weakness alignment."""
    weak_dims = _detect_weak_dimensions(detector_results)
    target_difficulty = _select_difficulty(detector_results)

    candidates: list[dict] = []
    for item in GROWTH_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Weakness alignment boost
        if item["category"] in weak_dims:
            score_boost += 0.25

        # Difficulty matching
        if item["difficulty"] == target_difficulty:
            score_boost += 0.15
        elif target_difficulty == "gentle" and item["difficulty"] == "bold":
            score_boost -= 0.15

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_reason(item, weak_dims, target_difficulty)
        candidates.append(item_copy)

    return candidates


def _build_reason(item: dict, weak_dims: list[str], difficulty: str) -> str:
    """Build relevance reason."""
    if item["category"] in weak_dims:
        base = f"Targets your growth area: {item['category'].replace('_', ' ')}"
    else:
        base = f"Build your {item['category'].replace('_', ' ')}"
    if difficulty == "gentle":
        return f"{base} — at your own pace"
    if difficulty == "bold":
        return f"{base} — you're ready to stretch"
    return base


class PersonalityGrowthFulfiller(L2Fulfiller):
    """L2 fulfiller for personality growth wishes — targets weakest dimensions.

    15-entry curated catalog across growth dimensions. Zero LLM.
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
                text="How did your growth exercise go today?",
                delay_hours=24,
            ),
        )
