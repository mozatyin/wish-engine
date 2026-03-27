"""BehavioralAddictionFulfiller — support for non-substance behavioral addictions.

10-entry curated catalog covering gaming, gambling, shopping, social media, etc. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Behavioral Addiction Catalog (10 entries) ────────────────────────────────

BEHAVIORAL_ADDICTION_CATALOG: list[dict] = [
    {
        "title": "Gaming Addiction Help",
        "description": "Resources for gaming addiction — screen time limits, community support, therapy.",
        "category": "gaming_addiction_help",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["behavioral", "gaming", "digital", "support", "structured"],
    },
    {
        "title": "Gambling Hotline",
        "description": "24/7 gambling addiction hotline — confidential, immediate, no judgment.",
        "category": "gambling_hotline",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["behavioral", "gambling", "hotline", "immediate", "confidential"],
    },
    {
        "title": "Shopping Addiction Support",
        "description": "Compulsive buying resources — budgeting tools, therapy options, peer support.",
        "category": "shopping_addiction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["behavioral", "shopping", "financial", "support", "structured"],
    },
    {
        "title": "Social Media Addiction",
        "description": "Break the scroll — screen time tools, dopamine detox plans, and mindful use guides.",
        "category": "social_media_addiction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["behavioral", "social_media", "digital", "detox", "self_paced"],
    },
    {
        "title": "Porn Addiction Support",
        "description": "Confidential recovery resources — therapy, accountability tools, peer groups.",
        "category": "porn_addiction_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["behavioral", "porn", "confidential", "support", "guided"],
    },
    {
        "title": "Work Addiction (Workaholism)",
        "description": "When work becomes compulsive — boundary setting, burnout prevention, therapy.",
        "category": "work_addiction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["behavioral", "work", "burnout", "boundaries", "structured"],
    },
    {
        "title": "Food Addiction Resources",
        "description": "Compulsive eating support — OA meetings, therapy, intuitive eating guidance.",
        "category": "food_addiction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["behavioral", "food", "eating", "support", "gentle"],
    },
    {
        "title": "Phone Addiction Tools",
        "description": "Reduce screen time — app blockers, grayscale mode, mindful usage trackers.",
        "category": "phone_addiction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["behavioral", "phone", "digital", "tools", "self_paced"],
    },
    {
        "title": "Exercise Addiction Awareness",
        "description": "When fitness becomes compulsive — rest days, body image, healthy relationship with movement.",
        "category": "exercise_addiction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["behavioral", "exercise", "body", "awareness", "gentle"],
    },
    {
        "title": "Relationship Addiction Support",
        "description": "Codependency and love addiction resources — CODA meetings, therapy, boundaries.",
        "category": "relationship_addiction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["behavioral", "relationship", "codependency", "support", "guided"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_BEHAVIORAL_KEYWORDS: dict[str, list[str]] = {
    "行为成瘾": ["behavioral", "support"],
    "gaming addiction": ["behavioral", "gaming"],
    "赌博": ["behavioral", "gambling"],
    "gambling": ["behavioral", "gambling"],
    "قمار": ["behavioral", "gambling"],
    "shopping addiction": ["behavioral", "shopping"],
    "购物成瘾": ["behavioral", "shopping"],
    "social media addiction": ["behavioral", "social_media"],
    "手机成瘾": ["behavioral", "phone"],
    "phone addiction": ["behavioral", "phone"],
    "work addiction": ["behavioral", "work"],
    "food addiction": ["behavioral", "food"],
    "porn": ["behavioral", "porn"],
    "exercise addiction": ["behavioral", "exercise"],
    "codependency": ["behavioral", "codependency"],
}


def _match_behavioral_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _BEHAVIORAL_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class BehavioralAddictionFulfiller(L2Fulfiller):
    """L2 fulfiller for behavioral addictions — non-substance compulsive behaviors.

    10 curated entries. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_behavioral_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in BEHAVIORAL_ADDICTION_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in BEHAVIORAL_ADDICTION_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in BEHAVIORAL_ADDICTION_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Recognizing a behavioral pattern is the first step to freedom.",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "hotline" in tags:
        return "Immediate help is available right now"
    if "digital" in tags:
        return "Tools to reclaim your relationship with technology"
    if "financial" in tags:
        return "Financial well-being starts with awareness"
    if "confidential" in tags:
        return "Private, judgment-free support"
    if "boundaries" in tags:
        return "Learn to set healthy boundaries"
    return "Support for breaking compulsive patterns"
