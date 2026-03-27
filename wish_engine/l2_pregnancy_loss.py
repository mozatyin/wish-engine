"""PregnancyLossFulfiller — extremely gentle support for pregnancy and child loss.

10-entry curated catalog. Highest sensitivity. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Pregnancy Loss Catalog (10 entries) ──────────────────────────────────────

PREGNANCY_LOSS_CATALOG: list[dict] = [
    {
        "title": "Miscarriage Support Group",
        "description": "A safe circle of people who understand — no platitudes, just presence.",
        "category": "miscarriage_support",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["loss", "miscarriage", "peer", "gentle", "support_group"],
    },
    {
        "title": "Stillbirth Counseling",
        "description": "Specialized counseling for stillbirth — professional, compassionate, unhurried.",
        "category": "stillbirth_counseling",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["loss", "stillbirth", "professional", "gentle", "guided"],
    },
    {
        "title": "NICU Family Support",
        "description": "Resources and peer support for families navigating NICU experiences.",
        "category": "nicu_family_support",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["loss", "nicu", "family", "peer", "gentle"],
    },
    {
        "title": "Pregnancy Loss Support Group",
        "description": "Weekly group for all forms of pregnancy loss — held with care.",
        "category": "pregnancy_loss_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["loss", "pregnancy", "peer", "support_group", "gentle"],
    },
    {
        "title": "Memorial Garden Visit",
        "description": "Quiet memorial gardens for babies — a place to remember and be still.",
        "category": "memorial_garden",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["loss", "memorial", "nature", "solo", "gentle", "space"],
    },
    {
        "title": "Fertility Grief Counseling",
        "description": "Support for the grief that comes with fertility struggles and loss.",
        "category": "fertility_grief",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["loss", "fertility", "professional", "gentle", "guided"],
    },
    {
        "title": "Rainbow Pregnancy Support",
        "description": "Guidance and emotional support for pregnancy after loss — hope held gently.",
        "category": "rainbow_pregnancy_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["loss", "rainbow", "hope", "gentle", "guided"],
    },
    {
        "title": "Partner Grief Support",
        "description": "Support specifically for partners — your grief matters too.",
        "category": "partner_grief",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["loss", "partner", "peer", "gentle", "solo"],
    },
    {
        "title": "Sibling Grief — Child Loss",
        "description": "Helping surviving siblings process the loss of a brother or sister.",
        "category": "sibling_grief_child_loss",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["loss", "sibling", "children", "family", "gentle"],
    },
    {
        "title": "Holiday Grief Support",
        "description": "Navigating holidays and milestones after pregnancy or child loss.",
        "category": "holiday_grief_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["loss", "holiday", "anniversary", "gentle", "structured"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_PREGNANCY_LOSS_KEYWORDS: dict[str, list[str]] = {
    "流产": ["loss", "miscarriage"],
    "miscarriage": ["loss", "miscarriage"],
    "loss of child": ["loss", "family"],
    "失去孩子": ["loss", "children"],
    "إجهاض": ["loss", "miscarriage"],
    "stillbirth": ["loss", "stillbirth"],
    "死产": ["loss", "stillbirth"],
    "nicu": ["loss", "nicu"],
    "fertility": ["loss", "fertility"],
    "rainbow baby": ["loss", "rainbow"],
    "pregnancy loss": ["loss", "pregnancy"],
    "baby loss": ["loss", "gentle"],
    "partner grief": ["loss", "partner"],
}


def _match_pregnancy_loss_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _PREGNANCY_LOSS_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class PregnancyLossFulfiller(L2Fulfiller):
    """L2 fulfiller for pregnancy/child loss — extremely gentle support resources.

    10 curated entries. Highest sensitivity tone. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_pregnancy_loss_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in PREGNANCY_LOSS_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in PREGNANCY_LOSS_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in PREGNANCY_LOSS_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="There is no right way to grieve. We are here when you need us.",
                delay_hours=72,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "professional" in tags:
        return "Compassionate professional support for your loss"
    if "support_group" in tags:
        return "Others who understand this particular grief"
    if "memorial" in tags:
        return "A quiet place to remember"
    if "rainbow" in tags:
        return "Hope held gently for your journey ahead"
    if "partner" in tags:
        return "Your grief as a partner matters deeply"
    return "A gentle resource for this tender time"
