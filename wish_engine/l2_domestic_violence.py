"""DomesticViolenceFulfiller — discreet, safety-first DV resource routing.

10-entry curated catalog. MUST be discreet — hidden interface consideration.
Safety planning always prioritized. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Domestic Violence Catalog (10 entries) ───────────────────────────────────

DV_CATALOG: list[dict] = [
    {
        "title": "DV Hotline — Confidential",
        "description": "National DV Hotline: 1-800-799-7233. Confidential, 24/7, multilingual.",
        "category": "dv_hotline",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dv", "hotline", "immediate", "confidential", "priority"],
    },
    {
        "title": "Shelter Locator",
        "description": "Find a safe shelter near you — confidential locations, immediate intake.",
        "category": "shelter_locator",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dv", "shelter", "immediate", "safe_place", "priority"],
    },
    {
        "title": "Safety Planning",
        "description": "Create a personalized safety plan — escape route, go-bag, code words, trusted contacts.",
        "category": "safety_planning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dv", "safety_plan", "structured", "practical", "priority"],
    },
    {
        "title": "Legal Protection Order",
        "description": "How to file a restraining order — step-by-step legal guidance, free legal aid.",
        "category": "legal_protection_order",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dv", "legal", "protection", "structured", "guided"],
    },
    {
        "title": "Children Witness Support",
        "description": "Resources for children who witness domestic violence — therapy, safe spaces.",
        "category": "children_witness_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dv", "children", "therapy", "gentle", "family"],
    },
    {
        "title": "Financial Independence Guide",
        "description": "Hidden bank accounts, job resources, financial aid — breaking economic control.",
        "category": "financial_independence",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dv", "financial", "independence", "practical", "structured"],
    },
    {
        "title": "Escape Plan Builder",
        "description": "Step-by-step escape planning — documents, safe location, timing, communication.",
        "category": "escape_plan",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dv", "escape", "practical", "structured", "priority"],
    },
    {
        "title": "Evidence Collection Guide",
        "description": "How to safely document abuse — photos, recordings, journal entries, witnesses.",
        "category": "evidence_collection",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dv", "evidence", "legal", "practical", "discreet"],
    },
    {
        "title": "DV Support Group",
        "description": "Peer support group for survivors — you are not alone, and it is not your fault.",
        "category": "support_group_dv",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["dv", "peer", "support_group", "gentle", "community"],
    },
    {
        "title": "DV Counseling",
        "description": "Trauma-informed counseling for domestic violence survivors — rebuild safely.",
        "category": "counseling_dv",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dv", "counseling", "professional", "trauma", "gentle"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_DV_KEYWORDS: dict[str, list[str]] = {
    "家暴": ["dv", "immediate"],
    "domestic violence": ["dv", "immediate"],
    "abuse": ["dv", "immediate"],
    "عنف أسري": ["dv", "immediate"],
    "被打": ["dv", "immediate"],
    "hurt me": ["dv", "immediate"],
    "hitting": ["dv", "immediate"],
    "beating": ["dv", "immediate"],
    "restraining order": ["dv", "legal"],
    "shelter": ["dv", "shelter"],
    "escape": ["dv", "escape"],
    "safety plan": ["dv", "safety_plan"],
    "他打我": ["dv", "immediate"],
    "她打我": ["dv", "immediate"],
}


def _match_dv_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _DV_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class DomesticViolenceFulfiller(L2Fulfiller):
    """L2 fulfiller for domestic violence — discreet, safety-first resources.

    10 curated entries. Safety plan and hotline always prioritized. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_dv_tags(wish.wish_text)

        candidates = [dict(item) for item in DV_CATALOG]

        # Always prioritize safety resources
        candidates.sort(key=lambda x: (
            0 if "priority" in x.get("tags", []) else
            1 if "immediate" in x.get("tags", []) else 2
        ))

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Your safety matters. This information will be here when you need it.",
                delay_hours=12,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "hotline" in tags:
        return "Confidential help available right now"
    if "shelter" in tags:
        return "A safe place is waiting for you"
    if "safety_plan" in tags:
        return "A plan can be the difference — be prepared"
    if "escape" in tags:
        return "When you are ready, know the steps"
    if "legal" in tags:
        return "The law is on your side"
    if "children" in tags:
        return "Protecting the children too"
    return "You deserve to be safe"
