"""SobrietyTrackerFulfiller — sobriety milestone tracking and daily check-in.

10-entry curated catalog. Encouraging, milestone-based. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Sobriety Tracker Catalog (10 entries) ────────────────────────────────────

SOBRIETY_CATALOG: list[dict] = [
    {
        "title": "Daily Sobriety Check-In",
        "description": "A 2-minute daily reflection — how are you feeling today in your recovery?",
        "category": "daily_check_in",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sobriety", "daily", "check_in", "structured", "self_paced"],
    },
    {
        "title": "Milestone Celebration Guide",
        "description": "Celebrate 24 hours, 1 week, 30 days, 90 days — every milestone matters.",
        "category": "milestone_celebration",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sobriety", "milestone", "celebration", "motivation", "structured"],
    },
    {
        "title": "Sobriety Journal",
        "description": "Track your recovery journey — wins, struggles, and everything between.",
        "category": "sobriety_journal",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sobriety", "journal", "reflection", "solo", "self_paced"],
    },
    {
        "title": "Daily Recovery Quote",
        "description": "A curated recovery quote each day — words from those who walked before you.",
        "category": "recovery_quote",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sobriety", "inspiration", "daily", "gentle", "motivation"],
    },
    {
        "title": "Connect with Your Sponsor",
        "description": "A reminder and easy way to reach out to your sponsor today.",
        "category": "sponsor_connect",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sobriety", "sponsor", "connection", "support", "guided"],
    },
    {
        "title": "Gratitude in Recovery",
        "description": "Write 3 things you are grateful for today — gratitude rewires the brain.",
        "category": "gratitude_in_recovery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sobriety", "gratitude", "daily", "reflection", "gentle"],
    },
    {
        "title": "Trigger Log",
        "description": "Log triggers when they happen — patterns become visible, prevention becomes possible.",
        "category": "trigger_log",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sobriety", "trigger", "tracking", "awareness", "structured"],
    },
    {
        "title": "Mood in Recovery Tracker",
        "description": "Track your emotional state daily — see how sobriety changes your mood over time.",
        "category": "mood_in_recovery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sobriety", "mood", "tracking", "awareness", "self_paced"],
    },
    {
        "title": "Sleep in Recovery",
        "description": "Track sleep quality as you recover — watch your rest improve week by week.",
        "category": "sleep_in_recovery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sobriety", "sleep", "health", "tracking", "self_paced"],
    },
    {
        "title": "Health Improvements Timeline",
        "description": "See how your body heals over time — 24 hours, 1 week, 1 month milestones.",
        "category": "health_improvements",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sobriety", "health", "milestone", "motivation", "educational"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_SOBRIETY_KEYWORDS: dict[str, list[str]] = {
    "清醒": ["sobriety", "daily"],
    "sober": ["sobriety", "daily"],
    "sobriety": ["sobriety", "milestone"],
    "clean days": ["sobriety", "milestone"],
    "نظافة": ["sobriety", "daily"],
    "recovery track": ["sobriety", "tracking"],
    "milestone": ["sobriety", "milestone"],
    "check in": ["sobriety", "check_in"],
    "打卡": ["sobriety", "check_in"],
    "days clean": ["sobriety", "milestone"],
    "days sober": ["sobriety", "milestone"],
    "sponsor": ["sobriety", "sponsor"],
    "gratitude": ["sobriety", "gratitude"],
}


def _match_sobriety_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _SOBRIETY_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class SobrietyTrackerFulfiller(L2Fulfiller):
    """L2 fulfiller for sobriety tracking — milestones, check-ins, motivation.

    10 curated entries. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_sobriety_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in SOBRIETY_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in SOBRIETY_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in SOBRIETY_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Another day, another victory. Check in tomorrow.",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "milestone" in tags:
        return "Every day sober is a milestone worth celebrating"
    if "check_in" in tags:
        return "A daily moment of honest self-reflection"
    if "sponsor" in tags:
        return "Stay connected to your support system"
    if "gratitude" in tags:
        return "Gratitude rewires the brain toward recovery"
    if "tracking" in tags:
        return "See your progress — data proves you are healing"
    return "A tool to support your sobriety journey"
