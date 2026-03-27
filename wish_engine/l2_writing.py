"""WritingFulfiller — writing/journal prompts with personality matching.

15 writing prompts matched to MBTI personality types. INFP gets poetry prompts,
ESTJ gets structured reflection, etc.
Multilingual keyword routing (EN/ZH/AR).
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

# ── Writing Prompt Catalog (15 entries) ──────────────────────────────────────

WRITING_CATALOG: list[dict] = [
    {
        "title": "Letter to Yourself",
        "description": "Write a letter to your future self, one year from now. What do you hope for?",
        "category": "letter_to_self",
        "tags": ["reflective", "calming", "quiet", "self-paced", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["INFP", "INFJ", "ENFP"],
    },
    {
        "title": "What Scared Me Today",
        "description": "Name one thing that made you uncomfortable today. Why did it scare you?",
        "category": "what_scared_me_today",
        "tags": ["reflective", "calming", "quiet", "self-paced", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["INTJ", "INTP", "ISTJ"],
    },
    {
        "title": "Gratitude List",
        "description": "List 10 things you're grateful for right now — big and small.",
        "category": "gratitude_list",
        "tags": ["gratitude", "calming", "quiet", "simple", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["ESFJ", "ISFJ", "ENFJ"],
    },
    {
        "title": "The Unsent Letter",
        "description": "Write a letter you'll never send — say everything you've been holding in.",
        "category": "unsent_letter",
        "tags": ["reflective", "calming", "quiet", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["INFP", "INFJ", "ISFP"],
    },
    {
        "title": "Future Self Portrait",
        "description": "Describe your life 5 years from now in vivid detail — where, what, who.",
        "category": "future_self",
        "tags": ["reflective", "creative", "quiet", "theory", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["ENTJ", "INTJ", "ENFP"],
    },
    {
        "title": "Childhood Memory",
        "description": "Describe your happiest childhood memory — every detail you can remember.",
        "category": "childhood_memory",
        "tags": ["reflective", "calming", "quiet", "warm", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["ISFP", "ESFP", "ISFJ"],
    },
    {
        "title": "Relationship Reflection",
        "description": "Think about your most important relationship. What makes it work? What doesn't?",
        "category": "relationship_reflection",
        "tags": ["reflective", "calming", "quiet", "social"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["ENFJ", "INFJ", "ESFJ"],
    },
    {
        "title": "Values Check-In",
        "description": "List your top 5 values. Are you living by them? Where's the gap?",
        "category": "values_check",
        "tags": ["reflective", "practical", "quiet", "calming", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["ISTJ", "ESTJ", "INTJ"],
    },
    {
        "title": "Dream Journal",
        "description": "Write down last night's dream — or make one up. What does it tell you?",
        "category": "dream_journal",
        "tags": ["creative", "calming", "quiet", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["INFP", "ENFP", "INTP"],
    },
    {
        "title": "Anger Journal",
        "description": "What made you angry recently? Write it all out — raw, unfiltered.",
        "category": "anger_journal",
        "tags": ["reflective", "calming", "quiet", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["ESTP", "ENTJ", "ESTJ"],
    },
    {
        "title": "Joy Collection",
        "description": "Collect 5 moments of joy from this week — tiny ones count the most.",
        "category": "joy_collection",
        "tags": ["gratitude", "calming", "quiet", "warm", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["ESFP", "ENFP", "ISFP"],
    },
    {
        "title": "Forgiveness Letter",
        "description": "Write to someone you need to forgive — including yourself.",
        "category": "forgiveness_letter",
        "tags": ["reflective", "calming", "quiet", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["INFJ", "ENFJ", "ISFJ"],
    },
    {
        "title": "Bucket List Brain Dump",
        "description": "Write down everything you want to do before you die — no filter.",
        "category": "bucket_list",
        "tags": ["creative", "calming", "quiet", "self-paced", "energizing"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["ENTP", "ENFP", "ESTP"],
    },
    {
        "title": "Life Lesson Learned",
        "description": "What's one thing life taught you the hard way? Write the story.",
        "category": "life_lesson",
        "tags": ["reflective", "calming", "quiet", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["ISTJ", "INTJ", "ESTJ"],
    },
    {
        "title": "Wisdom for Your Younger Self",
        "description": "If you could tell 16-year-old you one thing, what would it be?",
        "category": "wisdom_for_younger_self",
        "tags": ["reflective", "calming", "quiet", "warm", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_match": ["INFP", "INFJ", "ENFJ"],
    },
]


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates with MBTI personality matching."""
    mbti = detector_results.mbti.get("type", "")

    candidates: list[dict] = []
    for item in WRITING_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # MBTI matching
        if mbti and mbti in item.get("mbti_match", []):
            score_boost += 0.25
            item_copy["relevance_reason"] = f"Matched to your {mbti} personality"

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


class WritingFulfiller(L2Fulfiller):
    """L2 fulfiller for writing/journal wishes — personality-matched prompts.

    15-entry curated catalog. MBTI-aware prompt selection. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "A writing prompt to explore your inner world"

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
                text="Ready to write? Your journal is waiting.",
                delay_hours=24,
            ),
        )
