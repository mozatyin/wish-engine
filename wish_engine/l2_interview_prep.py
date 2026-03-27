"""InterviewPrepFulfiller — interview preparation by MBTI-matched strategies.

12 prep types. I→preparation-heavy, E→improvisation. Zero LLM.
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

# ── Interview Prep Catalog (12 entries) ──────────────────────────────────────

INTERVIEW_CATALOG: list[dict] = [
    {
        "title": "STAR Method Practice",
        "description": "Prepare 5 stories using Situation-Task-Action-Result — your experiences are your proof.",
        "category": "behavioral_interview",
        "tags": ["quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "personality_fit": "introvert",
    },
    {
        "title": "Technical Interview Drills",
        "description": "Solve 3 coding problems daily — consistency beats intensity for technical prep.",
        "category": "technical_interview",
        "tags": ["quiet", "self-paced", "practical", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "personality_fit": "introvert",
    },
    {
        "title": "Case Study Framework",
        "description": "Learn one consulting framework today (MECE, Porter's 5, etc.) and apply it to a practice case.",
        "category": "case_study",
        "tags": ["quiet", "self-paced", "theory", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "personality_fit": "introvert",
    },
    {
        "title": "Presentation Dry Run",
        "description": "Practice your presentation 3 times — first alone, then to a friend, then to a mirror.",
        "category": "presentation_prep",
        "tags": ["self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "personality_fit": "introvert",
    },
    {
        "title": "Salary Negotiation Script",
        "description": "Write your negotiation script with 3 anchors: ideal, acceptable, walk-away. Practice saying it.",
        "category": "salary_negotiation",
        "tags": ["quiet", "self-paced", "practical", "assertive"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "bold",
        "personality_fit": "any",
    },
    {
        "title": "Cultural Fit Conversation",
        "description": "Research the company values and prepare stories that show alignment — authenticity wins.",
        "category": "cultural_fit",
        "tags": ["quiet", "self-paced", "practical", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "personality_fit": "any",
    },
    {
        "title": "Portfolio Walk-Through",
        "description": "Rehearse presenting your portfolio — explain not just what you made but why it matters.",
        "category": "portfolio_review",
        "tags": ["quiet", "self-paced", "practical", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "personality_fit": "introvert",
    },
    {
        "title": "Mock Interview with a Friend",
        "description": "Ask someone to grill you for 30 minutes — real pressure builds real confidence.",
        "category": "mock_interview",
        "tags": ["social", "energizing", "practical"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "moderate",
        "personality_fit": "extravert",
    },
    {
        "title": "Craft Your Elevator Pitch",
        "description": "60 seconds: who you are, what you do, why it matters. Write it, memorize it, own it.",
        "category": "elevator_pitch",
        "tags": ["quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "personality_fit": "any",
    },
    {
        "title": "LinkedIn Profile Audit",
        "description": "Review your LinkedIn as if you were a recruiter — would you call yourself?",
        "category": "linkedin_review",
        "tags": ["quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "personality_fit": "any",
    },
    {
        "title": "Resume Workshop",
        "description": "Rewrite each bullet point with impact: 'Increased X by Y% through Z' — numbers speak.",
        "category": "resume_workshop",
        "tags": ["quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "personality_fit": "introvert",
    },
    {
        "title": "Networking Strategy Session",
        "description": "Identify 5 people to reach out to this week — prepare a warm opener for each.",
        "category": "networking_strategy",
        "tags": ["social", "practical", "energizing"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "difficulty": "moderate",
        "personality_fit": "extravert",
    },
]


def _match_candidates(detector_results: DetectorResults) -> list[dict]:
    """Score candidates based on MBTI-matched strategies."""
    mbti = detector_results.mbti.get("type", "")
    is_introvert = len(mbti) == 4 and mbti[0] == "I"
    is_extravert = len(mbti) == 4 and mbti[0] == "E"

    fragility = detector_results.fragility.get("pattern", "")
    is_fragile = fragility in ("defensive", "fragile", "avoidant")

    candidates: list[dict] = []
    for item in INTERVIEW_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        fit = item.get("personality_fit", "any")
        if is_introvert and fit == "introvert":
            score_boost += 0.20
        elif is_extravert and fit == "extravert":
            score_boost += 0.20
        elif fit == "any":
            score_boost += 0.10

        # Fragile users prefer gentle prep
        if is_fragile and item["difficulty"] == "gentle":
            score_boost += 0.15
        elif is_fragile and item["difficulty"] == "bold":
            score_boost -= 0.10

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_reason(item, is_introvert)
        candidates.append(item_copy)

    return candidates


def _build_reason(item: dict, is_introvert: bool) -> str:
    """Build relevance reason."""
    fit = item.get("personality_fit", "any")
    if is_introvert and fit == "introvert":
        return f"Preparation-focused: {item['category'].replace('_', ' ')}"
    return f"Interview ready: {item['category'].replace('_', ' ')}"


class InterviewPrepFulfiller(L2Fulfiller):
    """L2 fulfiller for interview prep wishes — MBTI-matched strategies.

    12-entry curated catalog. I→preparation-heavy, E→improvisation. Zero LLM.
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
                text="Did you practice your interview skills today?",
                delay_hours=24,
            ),
        )
