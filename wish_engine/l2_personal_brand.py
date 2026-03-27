"""PersonalBrandFulfiller — personal brand building by MBTI type.

12 brand building types. Introvert→written/visual, Extravert→speaking/video. Zero LLM.
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

# ── Brand Catalog (12 entries) ───────────────────────────────────────────────

BRAND_CATALOG: list[dict] = [
    {
        "title": "Build a Portfolio Website",
        "description": "Create a simple portfolio to showcase your best work — your digital handshake.",
        "category": "portfolio_creation",
        "tags": ["quiet", "self-paced", "practical", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "personality_fit": "introvert",
    },
    {
        "title": "Optimize Your LinkedIn",
        "description": "Rewrite your headline and summary — make people stop scrolling and read yours.",
        "category": "linkedin_optimization",
        "tags": ["quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "personality_fit": "any",
    },
    {
        "title": "Start a Blog",
        "description": "Write your first blog post about something only you know — your unique perspective matters.",
        "category": "blog_start",
        "tags": ["quiet", "self-paced", "creative", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "personality_fit": "introvert",
    },
    {
        "title": "Launch a YouTube Channel",
        "description": "Record your first video — 3 minutes on a topic you care about. Just press record.",
        "category": "youtube_channel",
        "tags": ["creative", "energizing", "social"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "bold",
        "personality_fit": "extravert",
    },
    {
        "title": "Start a Podcast",
        "description": "Record episode one — just you and your thoughts. Edit later, start now.",
        "category": "podcast_launch",
        "tags": ["creative", "social", "energizing"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "difficulty": "bold",
        "personality_fit": "extravert",
    },
    {
        "title": "Create a Speaking Profile",
        "description": "Build a speaker bio and topic list — be ready when opportunities knock.",
        "category": "speaking_profile",
        "tags": ["social", "energizing", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "personality_fit": "extravert",
    },
    {
        "title": "Set Up a Freelance Profile",
        "description": "Create your profile on Upwork/Fiverr — package your skills as services.",
        "category": "freelance_profile",
        "tags": ["quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
        "personality_fit": "any",
    },
    {
        "title": "Curate a Design Portfolio",
        "description": "Select your 5 best design pieces and present them beautifully — less is more.",
        "category": "design_portfolio",
        "tags": ["quiet", "self-paced", "creative", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "personality_fit": "introvert",
    },
    {
        "title": "Polish Your GitHub Profile",
        "description": "Pin your best repos, write clear READMEs, add a profile README — let your code speak.",
        "category": "github_profile",
        "tags": ["quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "personality_fit": "introvert",
    },
    {
        "title": "Compile Writing Samples",
        "description": "Gather your 5 best pieces of writing — create a reading experience for editors.",
        "category": "writing_samples",
        "tags": ["quiet", "self-paced", "creative", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "personality_fit": "introvert",
    },
    {
        "title": "Build a Photography Portfolio",
        "description": "Select 10-15 photos that tell your visual story — curate with intention.",
        "category": "photography_portfolio",
        "tags": ["quiet", "self-paced", "creative", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
        "personality_fit": "introvert",
    },
    {
        "title": "Record a Music Demo",
        "description": "Record a 3-track demo of your best songs — share your sound with the world.",
        "category": "music_demo",
        "tags": ["creative", "self-paced", "energizing"],
        "mood": "calming",
        "noise": "moderate",
        "social": "low",
        "difficulty": "moderate",
        "personality_fit": "any",
    },
]


def _match_candidates(detector_results: DetectorResults) -> list[dict]:
    """Score candidates based on MBTI introversion/extraversion."""
    mbti = detector_results.mbti.get("type", "")
    is_introvert = len(mbti) == 4 and mbti[0] == "I"
    is_extravert = len(mbti) == 4 and mbti[0] == "E"

    fragility = detector_results.fragility.get("pattern", "")
    target_difficulty = "gentle" if fragility in ("defensive", "fragile", "avoidant") else "moderate"

    candidates: list[dict] = []
    for item in BRAND_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        fit = item.get("personality_fit", "any")
        if is_introvert and fit == "introvert":
            score_boost += 0.25
        elif is_extravert and fit == "extravert":
            score_boost += 0.25
        elif fit == "any":
            score_boost += 0.10
        # Mismatch penalty
        elif is_introvert and fit == "extravert":
            score_boost -= 0.10
        elif is_extravert and fit == "introvert":
            score_boost -= 0.05

        # Difficulty matching
        if item["difficulty"] == target_difficulty:
            score_boost += 0.10

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_reason(item, is_introvert)
        candidates.append(item_copy)

    return candidates


def _build_reason(item: dict, is_introvert: bool) -> str:
    """Build relevance reason."""
    fit = item.get("personality_fit", "any")
    if is_introvert and fit == "introvert":
        return f"Perfect for introverts — {item['category'].replace('_', ' ')}"
    if not is_introvert and fit == "extravert":
        return f"Great for extraverts — {item['category'].replace('_', ' ')}"
    return f"Build your brand: {item['category'].replace('_', ' ')}"


class PersonalBrandFulfiller(L2Fulfiller):
    """L2 fulfiller for personal brand wishes — MBTI-matched brand building.

    12-entry curated catalog. I→written/visual, E→speaking/video. Zero LLM.
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
                text="Have you taken a step on your personal brand today?",
                delay_hours=48,
            ),
        )
