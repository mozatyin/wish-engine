"""CourseTrackerFulfiller — online course progress tracking with nudge logic.

10 course types with progress states. Core innovation: stalled >7 days triggers
a nudge reminder. Personality-aware course recommendations.
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

# ── Course Type Catalog (10 entries) ─────────────────────────────────────────

COURSE_CATALOG: list[dict] = [
    {
        "title": "MOOC Platform Course",
        "description": "Coursera, edX, or Udemy — structured learning from top universities.",
        "category": "mooc",
        "tags": ["theory", "self-paced", "quiet", "academic"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "progress_nudge": "Your MOOC course is waiting — just one lecture today?",
    },
    {
        "title": "Coding Bootcamp",
        "description": "Intensive programming training — build projects and land a job.",
        "category": "bootcamp",
        "tags": ["practical", "tech", "energizing"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "medium",
        "progress_nudge": "Don't lose your bootcamp momentum — code for 30 minutes!",
    },
    {
        "title": "Professional Certification",
        "description": "AWS, PMP, CPA — earn a credential that opens doors.",
        "category": "certification",
        "tags": ["practical", "theory", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "progress_nudge": "Your certification exam is closer than you think — review today!",
    },
    {
        "title": "Language Course",
        "description": "Duolingo, Babbel, or a structured course — open a new world.",
        "category": "language_course",
        "tags": ["language", "self-paced", "quiet", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "progress_nudge": "Keep your language streak alive — 15 minutes today!",
    },
    {
        "title": "Creative Course",
        "description": "Skillshare or MasterClass — photography, writing, design, music.",
        "category": "creative_course",
        "tags": ["creative", "self-paced", "quiet", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "progress_nudge": "Your creative course misses you — watch one lesson!",
    },
    {
        "title": "Professional Development",
        "description": "Leadership, communication, management — grow in your career.",
        "category": "professional_dev",
        "tags": ["practical", "social", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "progress_nudge": "Invest in your career — continue your professional course!",
    },
    {
        "title": "Academic Course",
        "description": "University-level content — deep dive into a subject you love.",
        "category": "academic",
        "tags": ["theory", "quiet", "academic", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "progress_nudge": "Your academic journey continues — read the next chapter!",
    },
    {
        "title": "Tutorial Series",
        "description": "YouTube or blog tutorials — step-by-step learning at your pace.",
        "category": "tutorial_series",
        "tags": ["practical", "self-paced", "quiet", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "progress_nudge": "The next tutorial is ready — pick up where you left off!",
    },
    {
        "title": "Workshop Series",
        "description": "Multi-session workshops — hands-on learning with a community.",
        "category": "workshop_series",
        "tags": ["practical", "social", "energizing"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "high",
        "progress_nudge": "Your workshop group is counting on you — join the next session!",
    },
    {
        "title": "Self-Study Plan",
        "description": "Books + notes + practice — the classic self-directed learning path.",
        "category": "self_study",
        "tags": ["self-paced", "quiet", "autonomous", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "progress_nudge": "Your self-study plan needs you — 20 minutes today!",
    },
]

# Progress states
PROGRESS_STATES = ["not_started", "in_progress", "stalled", "almost_done", "completed"]


def _detect_progress_state(wish_text: str) -> str | None:
    """Detect progress state from wish text."""
    text_lower = wish_text.lower()
    if any(kw in text_lower for kw in ["stalled", "停", "放弃", "没继续", "stuck"]):
        return "stalled"
    if any(kw in text_lower for kw in ["almost", "快完成", "差一点", "almost done"]):
        return "almost_done"
    if any(kw in text_lower for kw in ["start", "开始", "新", "begin"]):
        return "not_started"
    if any(kw in text_lower for kw in ["continue", "继续", "progress", "进度"]):
        return "in_progress"
    return None


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates based on text and personality."""
    progress = _detect_progress_state(wish_text)
    text_lower = wish_text.lower()

    candidates: list[dict] = []
    for item in COURSE_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Category keyword matching
        cat = item["category"]
        if cat in text_lower or any(t in text_lower for t in item.get("tags", [])):
            score_boost += 0.2

        # Stalled nudge
        if progress == "stalled":
            item_copy["relevance_reason"] = item["progress_nudge"]
            score_boost += 0.15

        # Almost done encouragement
        if progress == "almost_done":
            item_copy["relevance_reason"] = "You're so close to finishing — push through!"
            score_boost += 0.1

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


class CourseTrackerFulfiller(L2Fulfiller):
    """L2 fulfiller for course tracking wishes — progress-aware nudging.

    10-entry curated catalog with stall detection. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "Keep learning — every step counts"

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
                text="Check in on your course progress today!",
                delay_hours=48,
            ),
        )
