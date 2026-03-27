"""AddictionMeetingFulfiller — anonymous recovery meeting recommendations.

10-entry curated catalog covering AA, NA, SMART Recovery, and more. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Addiction Meeting Catalog (10 entries) ───────────────────────────────────

ADDICTION_MEETING_CATALOG: list[dict] = [
    {
        "title": "AA Meeting Finder",
        "description": "Find local Alcoholics Anonymous meetings — open or closed, your choice.",
        "category": "aa_meeting",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recovery", "aa", "peer", "structured", "alcohol"],
    },
    {
        "title": "NA Meeting Finder",
        "description": "Narcotics Anonymous meetings near you — no judgment, just support.",
        "category": "na_meeting",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recovery", "na", "peer", "structured", "drugs"],
    },
    {
        "title": "SMART Recovery",
        "description": "Science-based recovery meetings — self-management and recovery training.",
        "category": "smart_recovery",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recovery", "smart", "science", "structured", "self_management"],
    },
    {
        "title": "Celebrate Recovery",
        "description": "Faith-based 12-step recovery program — healing through spiritual support.",
        "category": "celebrate_recovery",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recovery", "faith", "spiritual", "structured", "community"],
    },
    {
        "title": "Refuge Recovery",
        "description": "Buddhist-inspired recovery practice — mindfulness and meditation for sobriety.",
        "category": "refuge_recovery",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recovery", "mindfulness", "meditation", "spiritual", "gentle"],
    },
    {
        "title": "Online AA Meeting",
        "description": "Join AA from home — 24/7 online meetings for when you cannot attend in person.",
        "category": "online_aa",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["recovery", "aa", "online", "accessible", "peer"],
    },
    {
        "title": "Women's AA Group",
        "description": "Women-only AA meetings — a safe space for women in recovery.",
        "category": "womens_aa",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recovery", "women", "aa", "safe_space", "peer"],
    },
    {
        "title": "Young People's AA",
        "description": "AA meetings designed for younger adults — relate to peers your age.",
        "category": "young_peoples_aa",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recovery", "youth", "aa", "peer", "relatable"],
    },
    {
        "title": "LGBTQ+ Recovery Group",
        "description": "Recovery meetings in a welcoming LGBTQ+ affirming space.",
        "category": "lgbtq_recovery",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recovery", "lgbtq", "inclusive", "safe_space", "peer"],
    },
    {
        "title": "Faith-Based Recovery",
        "description": "Recovery programs rooted in faith traditions — Islamic, Christian, Jewish, and more.",
        "category": "faith_based_recovery",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recovery", "faith", "spiritual", "community", "structured"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_ADDICTION_MEETING_KEYWORDS: dict[str, list[str]] = {
    "戒瘾": ["recovery", "structured"],
    "addiction": ["recovery", "structured"],
    "aa": ["recovery", "aa"],
    "recovery": ["recovery", "peer"],
    "إدمان": ["recovery", "structured"],
    "sober": ["recovery", "peer"],
    "戒酒": ["recovery", "alcohol"],
    "戒毒": ["recovery", "drugs"],
    "meeting": ["recovery", "peer"],
    "na": ["recovery", "na"],
    "smart recovery": ["recovery", "smart"],
    "12 step": ["recovery", "structured"],
    "sponsor": ["recovery", "peer"],
    "anonymous": ["recovery", "aa"],
}


def _match_meeting_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _ADDICTION_MEETING_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class AddictionMeetingFulfiller(L2Fulfiller):
    """L2 fulfiller for addiction recovery meetings — anonymous, supportive.

    10 curated entries covering multiple recovery traditions. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_meeting_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in ADDICTION_MEETING_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in ADDICTION_MEETING_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in ADDICTION_MEETING_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="One day at a time. Your next meeting is always here.",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "aa" in tags:
        return "The original recovery community — proven for decades"
    if "smart" in tags:
        return "Science-based approach to self-management"
    if "spiritual" in tags:
        return "Recovery through spiritual connection"
    if "safe_space" in tags:
        return "A space where you can be fully yourself"
    if "online" in tags:
        return "Recovery support accessible from anywhere"
    return "A supportive meeting for your recovery journey"
