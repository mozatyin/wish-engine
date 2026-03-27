"""CollectiveTraumaFulfiller — post-disaster and collective trauma support.

10-entry curated catalog. Community-oriented healing. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Collective Trauma Catalog (10 entries) ───────────────────────────────────

COLLECTIVE_TRAUMA_CATALOG: list[dict] = [
    {
        "title": "Disaster Counseling Services",
        "description": "Free crisis counseling after disasters — FEMA Crisis Counseling Program and local services.",
        "category": "disaster_counseling",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trauma", "disaster", "professional", "free", "immediate"],
    },
    {
        "title": "Community Healing Circle",
        "description": "Facilitated community gathering to process shared grief and trauma together.",
        "category": "community_healing_circle",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["trauma", "community", "peer", "healing", "structured"],
    },
    {
        "title": "PTSD Group Therapy",
        "description": "Group therapy specifically for PTSD — evidence-based, professionally facilitated.",
        "category": "ptsd_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["trauma", "ptsd", "professional", "group", "structured"],
    },
    {
        "title": "War Trauma Support",
        "description": "Support for those affected by war and conflict — veterans, civilians, refugees.",
        "category": "war_trauma_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trauma", "war", "conflict", "professional", "gentle"],
    },
    {
        "title": "Pandemic Grief Support",
        "description": "Processing collective grief from pandemic losses — isolation, loss, changed world.",
        "category": "pandemic_grief",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["trauma", "pandemic", "grief", "peer", "gentle"],
    },
    {
        "title": "Mass Violence Support",
        "description": "Resources for survivors and communities affected by mass shootings and violence.",
        "category": "mass_shooting_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trauma", "violence", "professional", "immediate", "crisis"],
    },
    {
        "title": "Refugee Trauma Services",
        "description": "Culturally sensitive trauma support for refugees and displaced people.",
        "category": "refugee_trauma",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trauma", "refugee", "cultural", "professional", "gentle"],
    },
    {
        "title": "Collective Remembrance Ritual",
        "description": "Community rituals for collective mourning — vigils, memorials, shared silence.",
        "category": "collective_ritual",
        "noise": "quiet",
        "social": "high",
        "mood": "calming",
        "tags": ["trauma", "ritual", "community", "memorial", "healing"],
    },
    {
        "title": "Resilience Workshop",
        "description": "Build community resilience — practical tools for recovering from shared trauma.",
        "category": "resilience_workshop",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["trauma", "resilience", "community", "structured", "empowering"],
    },
    {
        "title": "Children's Trauma Support",
        "description": "Age-appropriate trauma processing for children after collective events.",
        "category": "children_trauma_support",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["trauma", "children", "family", "gentle", "guided"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_COLLECTIVE_TRAUMA_KEYWORDS: dict[str, list[str]] = {
    "灾后": ["trauma", "disaster"],
    "trauma": ["trauma", "professional"],
    "ptsd": ["trauma", "ptsd"],
    "创伤": ["trauma", "professional"],
    "صدمة": ["trauma", "professional"],
    "disaster": ["trauma", "disaster"],
    "战争": ["trauma", "war"],
    "war": ["trauma", "war"],
    "refugee": ["trauma", "refugee"],
    "难民": ["trauma", "refugee"],
    "pandemic": ["trauma", "pandemic"],
    "shooting": ["trauma", "violence"],
    "枪击": ["trauma", "violence"],
    "terrorism": ["trauma", "violence"],
    "earthquake": ["trauma", "disaster"],
    "地震": ["trauma", "disaster"],
    "flood": ["trauma", "disaster"],
    "洪水": ["trauma", "disaster"],
}


def _match_trauma_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _COLLECTIVE_TRAUMA_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class CollectiveTraumaFulfiller(L2Fulfiller):
    """L2 fulfiller for collective trauma — community-oriented healing support.

    10 curated entries. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_trauma_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in COLLECTIVE_TRAUMA_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in COLLECTIVE_TRAUMA_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in COLLECTIVE_TRAUMA_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Healing from collective trauma takes a community. You are not alone.",
                delay_hours=48,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "disaster" in tags:
        return "Immediate support after disaster"
    if "community" in tags and "healing" in tags:
        return "Heal together as a community"
    if "ptsd" in tags:
        return "Evidence-based PTSD treatment"
    if "war" in tags or "conflict" in tags:
        return "Support for those affected by conflict"
    if "refugee" in tags:
        return "Culturally sensitive support for displacement"
    if "children" in tags:
        return "Protecting young hearts from trauma"
    return "Support for processing collective trauma"
