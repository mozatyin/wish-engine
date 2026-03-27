"""EstateItemsFulfiller — guidance for sorting and handling belongings after loss.

10-entry curated catalog. Practical yet gentle. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Estate Items Catalog (10 entries) ────────────────────────────────────────

ESTATE_ITEMS_CATALOG: list[dict] = [
    {
        "title": "Estate Planning Guide",
        "description": "Step-by-step guide to understanding and organizing estate matters.",
        "category": "estate_planning_guide",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["estate", "planning", "structured", "practical", "guided"],
    },
    {
        "title": "Sorting Belongings Checklist",
        "description": "A gentle, room-by-room checklist for going through belongings — no rush.",
        "category": "sorting_belongings",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["estate", "sorting", "structured", "practical", "self_paced"],
    },
    {
        "title": "Donation Service Finder",
        "description": "Find local charities that accept donations — give belongings a second life.",
        "category": "donation_service",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["estate", "donation", "community", "practical", "gentle"],
    },
    {
        "title": "Keepsake Selection Guide",
        "description": "How to choose meaningful keepsakes — keep what matters, release what does not.",
        "category": "keepsake_selection",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["estate", "keepsake", "memory", "gentle", "self_paced"],
    },
    {
        "title": "Digital Account Closure Guide",
        "description": "Guide to closing or memorializing online accounts — email, social media, subscriptions.",
        "category": "digital_account_closure",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["estate", "digital", "practical", "structured", "guided"],
    },
    {
        "title": "Photo Preservation Service",
        "description": "Digitize and preserve old photos, letters, and documents before they fade.",
        "category": "photo_preservation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["estate", "photos", "memory", "preservation", "gentle"],
    },
    {
        "title": "Letter Discovery — What They Left Behind",
        "description": "Guidance for handling discovered letters, diaries, and personal writings.",
        "category": "letter_discovery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["estate", "letters", "emotional", "gentle", "solo"],
    },
    {
        "title": "Clothing Repurpose Ideas",
        "description": "Transform their clothing into quilts, pillows, or keepsakes — wearable memories.",
        "category": "clothing_repurpose",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["estate", "clothing", "creative", "memory", "gentle"],
    },
    {
        "title": "Furniture Redistribution Guide",
        "description": "How to redistribute furniture to family members or donate meaningfully.",
        "category": "furniture_redistribution",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["estate", "furniture", "practical", "family", "structured"],
    },
    {
        "title": "Memory Box Creation",
        "description": "Curate a special box of their most meaningful items — a portable memorial.",
        "category": "memory_box_creation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["estate", "memory_box", "creative", "gentle", "solo"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_ESTATE_KEYWORDS: dict[str, list[str]] = {
    "遗物": ["estate", "sorting"],
    "estate": ["estate", "planning"],
    "belongings": ["estate", "sorting"],
    "整理": ["estate", "sorting"],
    "تركة": ["estate", "planning"],
    "inheritance": ["estate", "planning"],
    "遗产": ["estate", "planning"],
    "donate": ["estate", "donation"],
    "keepsake": ["estate", "keepsake"],
    "photos": ["estate", "photos"],
    "letters": ["estate", "letters"],
    "clothing": ["estate", "clothing"],
    "furniture": ["estate", "furniture"],
    "digital accounts": ["estate", "digital"],
}


def _match_estate_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _ESTATE_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class EstateItemsFulfiller(L2Fulfiller):
    """L2 fulfiller for estate items — practical yet gentle belongings guidance.

    10 curated entries. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_estate_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in ESTATE_ITEMS_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in ESTATE_ITEMS_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in ESTATE_ITEMS_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Take your time. There is no deadline for memories.",
                delay_hours=48,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "planning" in tags:
        return "Clear guidance for a difficult task"
    if "memory" in tags:
        return "Preserve what matters most"
    if "creative" in tags:
        return "Transform belongings into lasting memories"
    if "donation" in tags:
        return "Give their things a meaningful second life"
    if "digital" in tags:
        return "Handle the digital side with care"
    return "A practical, gentle guide for handling belongings"
