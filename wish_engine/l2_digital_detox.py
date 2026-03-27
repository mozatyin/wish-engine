"""DigitalDetoxFulfiller — screen-free activities for digital wellness.

12 detox activities with personality-based filtering. Zero LLM.
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

# ── Detox Catalog (12 entries) ───────────────────────────────────────────────

DETOX_CATALOG: list[dict] = [
    {
        "title": "Nature Walk — No Phone",
        "description": "Leave your phone at home for a 20-minute walk — notice what you see without a screen.",
        "category": "nature_walk_no_phone",
        "tags": ["quiet", "self-paced", "calming", "nature"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Analog Hobby Hour",
        "description": "Spend 1 hour on a non-digital hobby: drawing, cooking, knitting, woodwork — hands only.",
        "category": "analog_hobby",
        "tags": ["quiet", "self-paced", "calming", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Face-to-Face Meal",
        "description": "Eat one meal today with another person — phones face-down, eyes up.",
        "category": "face_to_face_meal",
        "tags": ["social", "warm", "calming"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "moderate",
    },
    {
        "title": "Paper Book Session",
        "description": "Read a physical book for 30 minutes — feel the pages, smell the paper.",
        "category": "paper_book",
        "tags": ["quiet", "self-paced", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Handwrite a Letter",
        "description": "Write a real letter to someone — pen, paper, envelope. Mail it.",
        "category": "handwrite_letter",
        "tags": ["quiet", "self-paced", "calming", "warm", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Board Game Night",
        "description": "Gather friends for a board game — real dice, real cards, real laughter.",
        "category": "board_game_night",
        "tags": ["social", "energizing", "warm"],
        "mood": "calming",
        "noise": "moderate",
        "social": "high",
        "difficulty": "moderate",
    },
    {
        "title": "Sunset Watching",
        "description": "Watch a sunset without taking a photo — just be present with the colors.",
        "category": "sunset_watching",
        "tags": ["quiet", "self-paced", "calming", "nature", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Phone-Free Morning",
        "description": "Don't touch your phone for the first hour after waking — start your day for yourself.",
        "category": "phone_free_morning",
        "tags": ["quiet", "self-paced", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Tech-Free Weekend",
        "description": "Go 48 hours without unnecessary screens — rediscover what boredom creates.",
        "category": "tech_free_weekend",
        "tags": ["self-paced", "calming", "nature"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "bold",
    },
    {
        "title": "Digital Sabbath",
        "description": "Pick one day per week as your screen-free day — make it sacred.",
        "category": "digital_sabbath",
        "tags": ["self-paced", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "bold",
    },
    {
        "title": "App Limit Challenge",
        "description": "Set 30-min daily limits on your top 3 time-wasting apps — notice the urge to check.",
        "category": "app_limit_challenge",
        "tags": ["practical", "self-paced", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Social Media Fast",
        "description": "No social media for 7 days — journal what you notice without the feed.",
        "category": "social_media_fast",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "bold",
    },
]


def _select_difficulty(detector_results: DetectorResults) -> str:
    """Select difficulty based on fragility and personality."""
    fragility = detector_results.fragility.get("pattern", "")
    if fragility in ("defensive", "fragile", "avoidant"):
        return "gentle"
    mbti = detector_results.mbti.get("type", "")
    if fragility == "resilient" and len(mbti) == 4 and mbti[0] == "E":
        return "bold"
    return "moderate"


def _match_candidates(detector_results: DetectorResults) -> list[dict]:
    """Score candidates based on personality."""
    target_difficulty = _select_difficulty(detector_results)
    mbti = detector_results.mbti.get("type", "")

    candidates: list[dict] = []
    for item in DETOX_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Difficulty matching
        if item["difficulty"] == target_difficulty:
            score_boost += 0.20
        elif target_difficulty == "gentle" and item["difficulty"] == "bold":
            score_boost -= 0.15

        # Introvert preference: solo activities
        if len(mbti) == 4 and mbti[0] == "I" and item.get("social") == "low":
            score_boost += 0.10

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_reason(item, target_difficulty)
        candidates.append(item_copy)

    return candidates


def _build_reason(item: dict, difficulty: str) -> str:
    """Build relevance reason."""
    base = f"Reclaim your attention: {item['category'].replace('_', ' ')}"
    if difficulty == "gentle":
        return f"{base} — start small"
    if difficulty == "bold":
        return f"{base} — you're ready for the full reset"
    return base


class DigitalDetoxFulfiller(L2Fulfiller):
    """L2 fulfiller for digital detox wishes — screen-free activities.

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
                text="How was your screen-free time today?",
                delay_hours=24,
            ),
        )
