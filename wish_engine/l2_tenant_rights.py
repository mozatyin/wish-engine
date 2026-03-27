"""TenantRightsFulfiller — tenant rights and rental protection resources.

10-entry curated catalog of renter protections and housing resources. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Tenant Rights Catalog (10 entries) ───────────────────────────────────────

TENANT_RIGHTS_CATALOG: list[dict] = [
    {
        "title": "Rent Increase Limits Guide",
        "description": "Know the legal cap on rent increases in your area — fight illegal hikes.",
        "category": "rent_increase_limits",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["rent_increase_limits", "rights", "calming", "financial", "practical"],
    },
    {
        "title": "Eviction Defense Resources",
        "description": "Facing eviction? Know your rights, timelines, and legal defenses.",
        "category": "eviction_defense",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["eviction_defense", "rights", "calming", "urgent", "legal"],
    },
    {
        "title": "Security Deposit Recovery",
        "description": "Get your deposit back — know deadlines, document damage, and file claims.",
        "category": "deposit_recovery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["deposit_recovery", "rights", "calming", "financial", "practical"],
    },
    {
        "title": "Repair Demand Templates",
        "description": "Landlord ignoring repairs? Use legal demand letters to force action.",
        "category": "repair_demands",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["repair_demands", "rights", "calming", "practical", "housing"],
    },
    {
        "title": "Habitability Standards Guide",
        "description": "Your landlord must provide safe, livable conditions — know the minimum standards.",
        "category": "habitability_standards",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["habitability_standards", "rights", "calming", "safety", "housing"],
    },
    {
        "title": "Lease Review Checklist",
        "description": "Before you sign a lease — red flags, illegal clauses, and what to negotiate.",
        "category": "lease_review",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["lease_review", "practical", "calming", "rights", "self-paced"],
    },
    {
        "title": "Tenant Union Directory",
        "description": "Find and join a tenant union in your area — collective power for renters.",
        "category": "tenant_union",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["tenant_union", "community", "calming", "rights", "organizing"],
    },
    {
        "title": "Housing Authority Contact",
        "description": "File complaints with your local housing authority for code violations.",
        "category": "housing_authority",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["housing_authority", "reporting", "calming", "rights", "official"],
    },
    {
        "title": "Rental Scam Alert Guide",
        "description": "Spot fake listings, advance fee scams, and identity theft in rental markets.",
        "category": "rental_scam_alert",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["rental_scam_alert", "safety", "calming", "practical", "prevention"],
    },
    {
        "title": "Subletting Rights Guide",
        "description": "Can you sublet? Know your rights, landlord obligations, and legal procedures.",
        "category": "subletting_rights",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["subletting_rights", "rights", "calming", "practical", "housing"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_TENANT_KEYWORDS: dict[str, list[str]] = {
    "租客": [],
    "tenant": [],
    "房东": [],
    "landlord": [],
    "إيجار": [],
    "rent": ["rent_increase_limits"],
    "eviction": ["eviction_defense"],
    "deposit": ["deposit_recovery"],
    "repair": ["repair_demands"],
    "lease": ["lease_review"],
    "sublet": ["subletting_rights"],
    "scam": ["rental_scam_alert"],
    "housing authority": ["housing_authority"],
    "tenant union": ["tenant_union"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _TENANT_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "rent_increase_limits": "Know the legal cap — do not overpay",
        "eviction_defense": "You have rights even when facing eviction",
        "deposit_recovery": "That deposit is yours — get it back",
        "repair_demands": "Landlords must fix what is broken",
        "habitability_standards": "Your home must meet minimum safety standards",
        "lease_review": "Understand before you commit",
        "tenant_union": "Stronger together — join fellow renters",
        "housing_authority": "Official channels to report violations",
        "rental_scam_alert": "Protect yourself from rental fraud",
        "subletting_rights": "Know what you can and cannot do with your lease",
    }
    return reason_map.get(category, "Know your rights as a tenant")


class TenantRightsFulfiller(L2Fulfiller):
    """L2 fulfiller for tenant rights — renter protections and housing resources.

    Uses keyword matching to select from 10-entry catalog.
    Applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        matched_categories = _match_categories(wish.wish_text)

        if matched_categories:
            tag_set = set(matched_categories)
            candidates = [
                dict(item) for item in TENANT_RIGHTS_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in TENANT_RIGHTS_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in TENANT_RIGHTS_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Tenant rights resources updated — check back for more.",
                delay_hours=24,
            ),
        )
