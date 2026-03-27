"""MicroChallengeFulfiller — daily micro-challenges by personality dimension.

25 challenges across 5 dimensions: social anxiety, conflict avoidance,
introvert stretch, creativity, values. MBTI/fragility-aware difficulty.
Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Challenge Catalog (25 entries) ───────────────────────────────────────────

CHALLENGE_CATALOG: list[dict] = [
    # ── Social Anxiety ──────────────────────────────────────────────────────
    {
        "title": "Smile at a Stranger",
        "description": "Just one genuine smile to someone you pass today — notice how it feels.",
        "category": "social_anxiety",
        "tags": ["social", "gentle", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Ask a Barista Their Name",
        "description": "A tiny act of connection — learn the name of someone who serves you daily.",
        "category": "social_anxiety",
        "tags": ["social", "gentle", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Say Hello to a Neighbor",
        "description": "Break the invisible wall — a simple greeting can change a day.",
        "category": "social_anxiety",
        "tags": ["social", "gentle", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Make Eye Contact & Nod",
        "description": "Hold eye contact for 2 seconds with a stranger and nod — you survived!",
        "category": "social_anxiety",
        "tags": ["social", "gentle", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Order Something New",
        "description": "Try a menu item you've never had — practice being slightly uncomfortable.",
        "category": "social_anxiety",
        "tags": ["social", "gentle", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    # ── Conflict Avoidance ──────────────────────────────────────────────────
    {
        "title": "Disagree Politely Once Today",
        "description": "When you disagree with something, say 'I see it differently' — just once.",
        "category": "conflict_avoidance",
        "tags": ["assertive", "social", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
    },
    {
        "title": "Set One Boundary",
        "description": "Say no to one thing today that you'd normally say yes to reluctantly.",
        "category": "conflict_avoidance",
        "tags": ["assertive", "practical", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Express a Preference",
        "description": "When asked 'where should we eat?' — actually choose instead of saying 'anywhere'.",
        "category": "conflict_avoidance",
        "tags": ["assertive", "social", "practical", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "gentle",
    },
    {
        "title": "Ask for What You Need",
        "description": "Make one specific request today — 'Could you please...' is enough.",
        "category": "conflict_avoidance",
        "tags": ["assertive", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
    },
    {
        "title": "Share Your Real Opinion",
        "description": "When someone asks what you think, give your honest answer — kindly but clearly.",
        "category": "conflict_avoidance",
        "tags": ["assertive", "social", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
    },
    # ── Introvert Stretch ───────────────────────────────────────────────────
    {
        "title": "Start a Conversation",
        "description": "Initiate one conversation today — even about the weather. You can do this.",
        "category": "introvert_stretch",
        "tags": ["social", "energizing"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "bold",
    },
    {
        "title": "Eat Lunch with a Colleague",
        "description": "Invite someone to join you for lunch — shared meals build unexpected bonds.",
        "category": "introvert_stretch",
        "tags": ["social", "warm", "energizing"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "bold",
    },
    {
        "title": "Join a Group Chat",
        "description": "Post in a group you've been lurking in — your voice matters.",
        "category": "introvert_stretch",
        "tags": ["social", "quiet", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Attend a Meetup",
        "description": "Go to one social event — you can leave after 30 minutes if you want.",
        "category": "introvert_stretch",
        "tags": ["social", "energizing"],
        "mood": "calming",
        "noise": "loud",
        "social": "high",
        "difficulty": "bold",
    },
    {
        "title": "Give a Compliment",
        "description": "Tell someone one specific thing you appreciate about them.",
        "category": "introvert_stretch",
        "tags": ["social", "gentle", "warm", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    # ── Creativity ──────────────────────────────────────────────────────────
    {
        "title": "Draw Something in 5 Minutes",
        "description": "Grab a pen, set a timer, draw anything — perfection not required.",
        "category": "creativity",
        "tags": ["creative", "quiet", "self-paced", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Write a Haiku",
        "description": "5-7-5 syllables about this exact moment — capture it in words.",
        "category": "creativity",
        "tags": ["creative", "quiet", "self-paced", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Take 3 Creative Photos",
        "description": "Find beauty in ordinary things — shoot 3 photos with intention.",
        "category": "creativity",
        "tags": ["creative", "quiet", "self-paced", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Rearrange One Space",
        "description": "Move 3 things in your room — small changes shift perspective.",
        "category": "creativity",
        "tags": ["creative", "practical", "quiet", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Make Up a Song",
        "description": "Hum or sing a melody that doesn't exist yet — it's yours.",
        "category": "creativity",
        "tags": ["creative", "quiet", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    # ── Values ──────────────────────────────────────────────────────────────
    {
        "title": "Donate a Small Amount",
        "description": "Give ¥1 / $1 to a cause you believe in — generosity starts small.",
        "category": "values",
        "tags": ["helping", "simple", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Compliment Someone Genuinely",
        "description": "Find something real to praise — not flattery, but honest recognition.",
        "category": "values",
        "tags": ["social", "helping", "warm", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Pick Up Litter",
        "description": "Pick up 3 pieces of trash that aren't yours — silent kindness.",
        "category": "values",
        "tags": ["helping", "nature", "simple", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Write a Thank You Note",
        "description": "Send a message to someone who helped you — gratitude is powerful.",
        "category": "values",
        "tags": ["helping", "quiet", "calming", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Listen Without Interrupting",
        "description": "In your next conversation, just listen — no advice, no fix, just presence.",
        "category": "values",
        "tags": ["social", "calming", "helping", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
    },
]


def _get_fragility_pattern(detector_results: DetectorResults) -> str:
    """Get fragility pattern from detector results."""
    return detector_results.fragility.get("pattern", "")


def _get_mbti_type(detector_results: DetectorResults) -> str:
    """Get MBTI type from detector results."""
    return detector_results.mbti.get("type", "")


def _select_difficulty(detector_results: DetectorResults) -> str:
    """Select appropriate difficulty based on fragility and MBTI."""
    fragility = _get_fragility_pattern(detector_results)
    mbti = _get_mbti_type(detector_results)

    # Fragile users get gentle challenges
    if fragility in ("defensive", "fragile", "avoidant"):
        return "gentle"

    # Resilient extraverts get bolder challenges
    if fragility == "resilient" and len(mbti) == 4 and mbti[0] == "E":
        return "bold"

    return "moderate"


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select and score candidates based on personality."""
    target_difficulty = _select_difficulty(detector_results)

    candidates: list[dict] = []
    for item in CHALLENGE_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Difficulty matching
        if item["difficulty"] == target_difficulty:
            score_boost += 0.2
        elif target_difficulty == "gentle" and item["difficulty"] == "bold":
            score_boost -= 0.15  # Penalize bold for fragile
        elif target_difficulty == "bold" and item["difficulty"] == "gentle":
            score_boost -= 0.05  # Slight penalize gentle for resilient

        item_copy["_emotion_boost"] = score_boost
        if "relevance_reason" not in item_copy:
            item_copy["relevance_reason"] = _build_reason(item, target_difficulty)
        candidates.append(item_copy)

    return candidates


def _build_reason(item: dict, difficulty: str) -> str:
    """Build relevance reason based on category and difficulty."""
    category_reasons = {
        "social_anxiety": "A gentle step toward social confidence",
        "conflict_avoidance": "Practice speaking your truth",
        "introvert_stretch": "Stretch your comfort zone, at your pace",
        "creativity": "Unlock your creative side in just minutes",
        "values": "Live your values through small actions",
    }
    base = category_reasons.get(item["category"], "A small challenge with big impact")
    if difficulty == "gentle":
        return f"{base} — no pressure, just try"
    if difficulty == "bold":
        return f"{base} — you're ready for this"
    return base


class MicroChallengeFulfiller(L2Fulfiller):
    """L2 fulfiller for micro-challenge wishes — MBTI/fragility-aware difficulty.

    25-entry curated catalog across 5 personality dimensions. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:3]

        from wish_engine.models import Recommendation

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
                text="Did you complete today's micro-challenge?",
                delay_hours=12,
            ),
        )
