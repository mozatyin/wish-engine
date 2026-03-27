"""PetLossFulfiller — support resources for pet loss and grief.

10-entry curated catalog. Gentle, validating tone. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Pet Loss Catalog (10 entries) ────────────────────────────────────────────

PET_LOSS_CATALOG: list[dict] = [
    {
        "title": "Pet Grief Counseling",
        "description": "Professional counseling for pet loss — your grief is valid and real.",
        "category": "pet_grief_counseling",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pet_loss", "professional", "gentle", "guided", "solo"],
    },
    {
        "title": "Pet Memorial Service",
        "description": "Create a meaningful farewell for your companion — ceremony ideas and support.",
        "category": "pet_memorial",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pet_loss", "memorial", "ritual", "gentle"],
    },
    {
        "title": "Rainbow Bridge Support Group",
        "description": "Online community of pet parents who understand — share memories, find comfort.",
        "category": "rainbow_bridge_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["pet_loss", "peer", "online", "support_group", "gentle"],
    },
    {
        "title": "Pet Loss Hotline",
        "description": "Call anytime — trained volunteers who understand the bond you lost.",
        "category": "pet_loss_hotline",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pet_loss", "hotline", "immediate", "gentle", "guided"],
    },
    {
        "title": "Pet Cremation Services",
        "description": "Dignified cremation options with memorial keepsakes.",
        "category": "pet_cremation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pet_loss", "cremation", "practical", "gentle"],
    },
    {
        "title": "Pet Burial & Garden Memorial",
        "description": "Home burial guidance or memorial garden options for your beloved pet.",
        "category": "pet_burial",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pet_loss", "burial", "nature", "gentle", "memorial"],
    },
    {
        "title": "Grief Journaling for Pet Loss",
        "description": "Guided prompts to process your grief — write letters to your pet, capture memories.",
        "category": "grief_journaling_pet",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pet_loss", "journaling", "creative", "solo", "gentle"],
    },
    {
        "title": "New Pet Readiness Assessment",
        "description": "When you are ready — gentle guidance on opening your heart again, no rush.",
        "category": "new_pet_readiness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pet_loss", "readiness", "hope", "gentle", "self_paced"],
    },
    {
        "title": "Pet Memory Book Creator",
        "description": "Create a beautiful memory book of photos, stories, and moments with your pet.",
        "category": "pet_memory_book",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pet_loss", "memory", "creative", "gentle", "solo"],
    },
    {
        "title": "Volunteer at a Shelter",
        "description": "Channel your love into helping other animals — healing through giving.",
        "category": "volunteer_at_shelter",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["pet_loss", "volunteer", "healing", "community", "gentle"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_PET_LOSS_KEYWORDS: dict[str, list[str]] = {
    "宠物去世": ["pet_loss", "gentle"],
    "pet loss": ["pet_loss", "gentle"],
    "rainbow bridge": ["pet_loss", "peer"],
    "失去宠物": ["pet_loss", "gentle"],
    "فقدان حيوان": ["pet_loss", "gentle"],
    "pet died": ["pet_loss", "gentle"],
    "dog died": ["pet_loss", "gentle"],
    "cat died": ["pet_loss", "gentle"],
    "pet grief": ["pet_loss", "professional"],
    "pet memorial": ["pet_loss", "memorial"],
    "cremation": ["pet_loss", "cremation"],
}


def _match_pet_loss_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _PET_LOSS_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class PetLossFulfiller(L2Fulfiller):
    """L2 fulfiller for pet loss — validating, gentle grief support.

    10 curated entries. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_pet_loss_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in PET_LOSS_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in PET_LOSS_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in PET_LOSS_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="They were family. Take all the time you need.",
                delay_hours=48,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "professional" in tags:
        return "Your grief is real — professional support helps"
    if "support_group" in tags:
        return "Others who loved and lost a pet companion"
    if "memorial" in tags:
        return "Honor the bond you shared"
    if "volunteer" in tags:
        return "Channel your love into helping other animals"
    if "creative" in tags:
        return "Capture and preserve precious memories"
    return "A gentle resource for your pet loss journey"
