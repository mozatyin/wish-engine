"""EmergencyShelterFulfiller — emergency housing and shelter resources.

10-entry curated catalog. Immediate, practical. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Emergency Shelter Catalog (10 entries) ───────────────────────────────────

SHELTER_CATALOG: list[dict] = [
    {
        "title": "Women's Shelter",
        "description": "Safe shelter for women and children — confidential location, immediate intake.",
        "category": "womens_shelter",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["shelter", "women", "safe_place", "immediate", "confidential"],
    },
    {
        "title": "Youth Shelter",
        "description": "Emergency shelter for youth under 25 — safe, supportive, no questions asked.",
        "category": "youth_shelter",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["shelter", "youth", "safe_place", "immediate", "supportive"],
    },
    {
        "title": "Family Shelter",
        "description": "Emergency housing for families with children — keep your family together.",
        "category": "family_shelter",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["shelter", "family", "children", "immediate", "safe_place"],
    },
    {
        "title": "Veterans Shelter",
        "description": "Dedicated shelter and services for veterans — you served, now let us serve you.",
        "category": "veterans_shelter",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["shelter", "veterans", "dedicated", "supportive", "immediate"],
    },
    {
        "title": "LGBTQ+ Shelter",
        "description": "Affirming emergency shelter for LGBTQ+ individuals — safe and welcoming.",
        "category": "lgbtq_shelter",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["shelter", "lgbtq", "inclusive", "safe_place", "immediate"],
    },
    {
        "title": "Warming Center",
        "description": "Emergency warming centers during cold weather — heat, food, safety.",
        "category": "warming_center",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["shelter", "warming", "weather", "immediate", "seasonal"],
    },
    {
        "title": "Cooling Center",
        "description": "Emergency cooling centers during heatwaves — AC, water, rest.",
        "category": "cooling_center",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["shelter", "cooling", "weather", "immediate", "seasonal"],
    },
    {
        "title": "Disaster Shelter",
        "description": "Emergency shelter during natural disasters — Red Cross and community centers.",
        "category": "disaster_shelter",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["shelter", "disaster", "emergency", "immediate", "community"],
    },
    {
        "title": "Transitional Housing",
        "description": "Bridge housing for up to 2 years — stability while you rebuild.",
        "category": "transitional_housing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["shelter", "transitional", "long_term", "structured", "supportive"],
    },
    {
        "title": "Hotel Voucher Program",
        "description": "Emergency hotel vouchers for immediate shelter — available through local agencies.",
        "category": "hotel_voucher",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["shelter", "hotel", "voucher", "immediate", "temporary"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_SHELTER_KEYWORDS: dict[str, list[str]] = {
    "庇护": ["shelter", "immediate"],
    "shelter": ["shelter", "immediate"],
    "emergency housing": ["shelter", "immediate"],
    "无家": ["shelter", "immediate"],
    "homeless": ["shelter", "immediate"],
    "مأوى": ["shelter", "immediate"],
    "safe place": ["shelter", "safe_place"],
    "nowhere to go": ["shelter", "immediate"],
    "没地方住": ["shelter", "immediate"],
    "流浪": ["shelter", "immediate"],
    "warming center": ["shelter", "warming"],
    "cooling center": ["shelter", "cooling"],
    "disaster": ["shelter", "disaster"],
    "transitional": ["shelter", "transitional"],
}


def _match_shelter_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _SHELTER_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class EmergencyShelterFulfiller(L2Fulfiller):
    """L2 fulfiller for emergency shelter — immediate housing resources.

    10 curated entries. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_shelter_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in SHELTER_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in SHELTER_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in SHELTER_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="A safe place exists for you. Reach out when ready.",
                delay_hours=12,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "immediate" in tags and "safe_place" in tags:
        return "A safe place available right now"
    if "weather" in tags:
        return "Protection from dangerous weather"
    if "disaster" in tags:
        return "Emergency shelter during disaster"
    if "transitional" in tags:
        return "Stability while you rebuild your life"
    if "veterans" in tags:
        return "Dedicated support for those who served"
    return "Emergency shelter when you need it most"
