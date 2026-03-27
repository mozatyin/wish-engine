"""ChildSafetyOnlineFulfiller — online safety resources for children.

10-entry catalog of child safety tools and parent guides. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Catalog (10 entries) ─────────────────────────────────────────────────────

CHILD_SAFETY_CATALOG: list[dict] = [
    {
        "title": "Parental Controls Setup",
        "description": "Step-by-step guides for parental controls on iOS, Android, Windows, and gaming consoles.",
        "category": "parental_controls",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["controls", "setup", "practical", "calming", "self-paced"],
    },
    {
        "title": "Age-Appropriate Apps Guide",
        "description": "Curated list of safe, educational apps for different age groups — vetted by child safety experts.",
        "category": "age_appropriate_apps",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["apps", "age_appropriate", "education", "calming"],
    },
    {
        "title": "Screen Time Management",
        "description": "Healthy screen time guidelines by age — tools and strategies for balanced digital life.",
        "category": "screen_time_guide",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["screen_time", "management", "practical", "calming"],
    },
    {
        "title": "Online Predator Awareness",
        "description": "Warning signs, prevention strategies, and what to do if you suspect grooming.",
        "category": "online_predator_awareness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["predator", "awareness", "safety", "calming", "education"],
    },
    {
        "title": "Cyberbullying Guide for Parents",
        "description": "Recognize, respond to, and prevent cyberbullying — practical steps for parents.",
        "category": "cyberbullying_parent",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cyberbullying", "parent", "education", "calming"],
    },
    {
        "title": "Social Media Age Guide",
        "description": "When is your child ready for social media? Age guidelines and readiness checklist.",
        "category": "social_media_age",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["social_media", "age", "education", "calming"],
    },
    {
        "title": "Gaming Safety Guide",
        "description": "Online gaming safety — chat monitoring, in-game purchases, and stranger danger.",
        "category": "gaming_safety",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["gaming", "safety", "practical", "calming"],
    },
    {
        "title": "Digital Literacy for Kids",
        "description": "Teach children to think critically about online content — age-appropriate lessons.",
        "category": "digital_literacy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["literacy", "education", "practical", "calming", "self-paced"],
    },
    {
        "title": "Family Media Plan",
        "description": "Create a family media agreement — screen-free zones, time limits, and shared rules.",
        "category": "family_media_plan",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["family", "planning", "practical", "calming"],
    },
    {
        "title": "Reporting Exploitation",
        "description": "How and where to report child exploitation content — immediate action steps.",
        "category": "reporting_exploitation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["reporting", "exploitation", "safety", "calming", "immediate"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_CHILD_SAFETY_KEYWORDS: dict[str, list[str]] = {
    "儿童安全": [],
    "child safety": [],
    "kids online": [],
    "أمان الأطفال": [],
    "parental control": ["controls", "setup"],
    "家长控制": ["controls", "setup"],
    "screen time": ["screen_time", "management"],
    "屏幕时间": ["screen_time", "management"],
    "predator": ["predator", "safety"],
    "cyberbullying": ["cyberbullying", "parent"],
    "gaming": ["gaming", "safety"],
    "游戏安全": ["gaming", "safety"],
    "exploitation": ["reporting", "exploitation"],
    "digital literacy": ["literacy", "education"],
}


def _match_child_safety_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _CHILD_SAFETY_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class ChildSafetyOnlineFulfiller(L2Fulfiller):
    """L2 fulfiller for child online safety — parent tools and guides.

    10 curated entries for keeping children safe online. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_child_safety_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in CHILD_SAFETY_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in CHILD_SAFETY_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in CHILD_SAFETY_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Online safety is an ongoing conversation with your child.",
                delay_hours=168,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "safety" in tags:
        return "Essential safety measure to protect your child"
    if "education" in tags:
        return "Knowledge is the best protection"
    if "practical" in tags:
        return "Actionable step you can take right now"
    return "Keeping children safe in the digital world"
