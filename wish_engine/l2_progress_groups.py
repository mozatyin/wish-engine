"""ProgressGroupFulfiller — local-compute accountability group matching.

20-entry curated catalog of goal-based groups (3-5 person).
MBTI filtering: I->smaller (3), E->larger (5).
Multilingual keyword routing (EN/ZH/AR). Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Progress Group Catalog (20 entries) ──────────────────────────────────────

PROGRESS_CATALOG: list[dict] = [
    {
        "title": "Fitness Accountability Group",
        "description": "Daily check-ins on workouts, nutrition, and progress photos — stay consistent together.",
        "category": "progress_group",
        "group_size": "medium",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["physical", "practical", "social"],
    },
    {
        "title": "Reading Club Challenge",
        "description": "Read one book per month together — share highlights, discuss ideas, keep each other on track.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["intellectual", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Study Group",
        "description": "Focused study sessions with shared goals — exam prep, certifications, or skill building.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["intellectual", "quiet", "practical", "self-paced"],
    },
    {
        "title": "Meditation Circle",
        "description": "Daily guided meditation check-ins — build a consistent mindfulness practice together.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "quiet", "self-paced", "traditional"],
    },
    {
        "title": "Writing Group",
        "description": "Weekly writing sprints and feedback sessions — finish that novel, blog, or journal.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Coding Bootcamp Squad",
        "description": "Pair programming, code reviews, and daily standups — level up your coding skills.",
        "category": "progress_group",
        "group_size": "medium",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "modern", "intellectual", "quiet"],
    },
    {
        "title": "Language Exchange Partners",
        "description": "Practice a new language daily with native speakers — conversation, vocab, culture.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["social", "practical", "calming"],
    },
    {
        "title": "Art Challenge Group",
        "description": "Daily drawing/painting prompts — share your work, get feedback, grow as an artist.",
        "category": "progress_group",
        "group_size": "medium",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "quiet", "self-paced"],
    },
    {
        "title": "Cooking Adventure Group",
        "description": "Weekly new recipes — cook together virtually, share photos, rate each other's dishes.",
        "category": "progress_group",
        "group_size": "medium",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "practical", "social"],
    },
    {
        "title": "Early Riser Challenge",
        "description": "Wake up at 5am together — morning accountability with shared routines and wins.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "quiet", "self-paced"],
    },
    {
        "title": "Digital Detox Group",
        "description": "Reduce screen time together — daily no-phone hours with check-ins and support.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "quiet", "practical", "self-paced"],
    },
    {
        "title": "Journaling Circle",
        "description": "Daily journaling prompts and reflections — build self-awareness together.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "quiet", "creative", "self-paced"],
    },
    {
        "title": "Running Club",
        "description": "Train for a race together — shared routes, pacing, and race-day motivation.",
        "category": "progress_group",
        "group_size": "large",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["physical", "outdoor", "social"],
    },
    {
        "title": "Yoga Practice Group",
        "description": "Daily yoga sessions — build flexibility and inner peace with your practice partners.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["physical", "calming", "quiet", "self-paced"],
    },
    {
        "title": "Gratitude Practice Circle",
        "description": "Share three things you're grateful for every day — rewire your brain for positivity.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "quiet", "helping", "self-paced"],
    },
    {
        "title": "Career Change Support Group",
        "description": "Navigating career transitions together — resume reviews, interview prep, moral support.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "calming", "social", "helping"],
    },
    {
        "title": "Sobriety Support Circle",
        "description": "Daily check-ins for those on a sobriety journey — judgment-free accountability.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "quiet", "helping", "self-paced"],
    },
    {
        "title": "Budgeting & Savings Group",
        "description": "Track expenses, share tips, and reach financial goals together.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "quiet", "calming"],
    },
    {
        "title": "Creativity Challenge Group",
        "description": "30-day creative challenges — photography, music, writing, crafts. One new creation daily.",
        "category": "progress_group",
        "group_size": "medium",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "self-paced", "modern"],
    },
    {
        "title": "Declutter Challenge Group",
        "description": "Minimize together — daily decluttering tasks, before/after photos, KonMari support.",
        "category": "progress_group",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "quiet", "calming", "self-paced"],
    },
]

# ── Keywords ──────────────────────────────────────────────────────────────────

_PROGRESS_KEYWORDS: set[str] = {
    "打卡", "小组", "accountability", "group", "一起", "challenge", "互助",
    "check-in", "目标", "goal", "تحدي",
}


def _mbti_group_size_filter(
    candidates: list[dict],
    detector_results: DetectorResults,
) -> list[dict]:
    """MBTI-based group size: I->small(3), E->large(5)."""
    mbti = detector_results.mbti
    if not mbti.get("type"):
        return candidates

    ei = mbti.get("dimensions", {}).get("E_I", 0.5)
    is_introvert = ei < 0.4

    if is_introvert:
        return [c for c in candidates if c.get("group_size") in ("small",)]
    else:
        return [c for c in candidates if c.get("group_size") in ("medium", "large")]


class ProgressGroupFulfiller(L2Fulfiller):
    """L2 fulfiller for accountability group wishes — goal-based matching.

    20-entry curated catalog with MBTI group size filtering. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Start with full catalog
        candidates = [dict(item) for item in PROGRESS_CATALOG]

        # 2. Apply MBTI group size filter
        filtered = _mbti_group_size_filter(candidates, detector_results)
        if not filtered:
            filtered = candidates

        # 3. Add relevance reasons
        for c in filtered:
            tags = c.get("tags", [])
            if "physical" in tags:
                c["relevance_reason"] = "Stay active with your accountability partners"
            elif "creative" in tags:
                c["relevance_reason"] = "Create daily with like-minded people"
            elif "intellectual" in tags:
                c["relevance_reason"] = "Learn and grow with focused study partners"
            elif "helping" in tags:
                c["relevance_reason"] = "Support each other on your journey"
            else:
                c["relevance_reason"] = "Achieve your goals with accountability partners"

        # 4. Personality filter and rank
        recommendations = self._build_recommendations(
            filtered, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Check in with your progress group today?",
                delay_hours=12,
            ),
        )
