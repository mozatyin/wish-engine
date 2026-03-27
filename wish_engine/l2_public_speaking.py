"""PublicSpeakingFulfiller — speaking opportunities with introvert-aware options.

10 speaking opportunities. Gentle start for introverts. Zero LLM.
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

# ── Speaking Catalog (10 entries) ────────────────────────────────────────────

SPEAKING_CATALOG: list[dict] = [
    {
        "title": "Join Toastmasters",
        "description": "A structured, supportive environment to practice speaking — start with a 1-minute intro.",
        "category": "toastmasters",
        "tags": ["social", "practical", "calming"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "moderate",
    },
    {
        "title": "Try an Open Mic Night",
        "description": "Share a story, a poem, or just introduce yourself — 3 minutes of your truth.",
        "category": "open_mic",
        "tags": ["social", "creative", "energizing"],
        "mood": "calming",
        "noise": "moderate",
        "social": "high",
        "difficulty": "bold",
    },
    {
        "title": "Join a Debate Club",
        "description": "Sharpen your arguments and learn to think on your feet — ideas are your weapon.",
        "category": "debate_club",
        "tags": ["social", "energizing", "theory"],
        "mood": "calming",
        "noise": "moderate",
        "social": "high",
        "difficulty": "bold",
    },
    {
        "title": "Attend a Storytelling Night",
        "description": "Listen first, then share — storytelling is speaking from the heart, not the head.",
        "category": "storytelling_night",
        "tags": ["social", "warm", "creative", "calming"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "moderate",
    },
    {
        "title": "Apply for a Local TEDx Talk",
        "description": "You have an idea worth spreading — start drafting your 12-minute talk today.",
        "category": "ted_talk_local",
        "tags": ["social", "energizing", "creative"],
        "mood": "calming",
        "noise": "loud",
        "social": "high",
        "difficulty": "bold",
    },
    {
        "title": "Practice Your Pitch",
        "description": "Rehearse a 60-second pitch about your project — record yourself, watch, improve.",
        "category": "pitch_practice",
        "tags": ["quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Try Poetry Slam",
        "description": "Write a poem and perform it — vulnerability on stage is pure courage.",
        "category": "poetry_slam",
        "tags": ["creative", "social", "energizing"],
        "mood": "calming",
        "noise": "moderate",
        "social": "high",
        "difficulty": "bold",
    },
    {
        "title": "Try Standup Comedy",
        "description": "Write 3 jokes about your life and test them at an open mic — laughter is connection.",
        "category": "standup_comedy",
        "tags": ["creative", "social", "energizing"],
        "mood": "calming",
        "noise": "loud",
        "social": "high",
        "difficulty": "bold",
    },
    {
        "title": "Join a Panel Discussion",
        "description": "Volunteer as a panelist on a topic you know — you don't need to be the expert, just honest.",
        "category": "panel_discussion",
        "tags": ["social", "practical"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "moderate",
    },
    {
        "title": "Facilitate a Workshop",
        "description": "Teach something you know to a small group — teaching is the deepest form of learning.",
        "category": "workshop_facilitating",
        "tags": ["social", "practical", "warm"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "moderate",
    },
]


def _match_candidates(detector_results: DetectorResults) -> list[dict]:
    """Score candidates — introvert-aware gentle start."""
    mbti = detector_results.mbti.get("type", "")
    is_introvert = len(mbti) == 4 and mbti[0] == "I"
    fragility = detector_results.fragility.get("pattern", "")
    is_fragile = fragility in ("defensive", "fragile", "avoidant")

    candidates: list[dict] = []
    for item in SPEAKING_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Introverts and fragile users: boost gentle options
        if (is_introvert or is_fragile) and item["difficulty"] == "gentle":
            score_boost += 0.25
        elif (is_introvert or is_fragile) and item["difficulty"] == "bold":
            score_boost -= 0.15

        # Extraverts: boost bold
        if not is_introvert and len(mbti) == 4 and mbti[0] == "E" and item["difficulty"] == "bold":
            score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        if is_introvert or is_fragile:
            item_copy["relevance_reason"] = _build_reason_gentle(item)
        else:
            item_copy["relevance_reason"] = _build_reason_default(item)
        candidates.append(item_copy)

    return candidates


def _build_reason_gentle(item: dict) -> str:
    """Build reason for introverts/fragile users."""
    if item["difficulty"] == "gentle":
        return f"{item['category'].replace('_', ' ').title()} — a safe way to start"
    return f"{item['category'].replace('_', ' ').title()} — when you're ready"


def _build_reason_default(item: dict) -> str:
    """Build default reason."""
    return f"Grow your voice: {item['category'].replace('_', ' ')}"


class PublicSpeakingFulfiller(L2Fulfiller):
    """L2 fulfiller for public speaking wishes — introvert-aware opportunities.

    10-entry curated catalog. Zero LLM.
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
                text="Did you practice speaking today?",
                delay_hours=48,
            ),
        )
