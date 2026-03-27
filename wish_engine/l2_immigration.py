"""ImmigrationFulfiller — immigration services and integration resources.

12-entry curated catalog of visa, residency, and integration resources. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Immigration Catalog (12 entries) ─────────────────────────────────────────

IMMIGRATION_CATALOG: list[dict] = [
    {
        "title": "Visa Information Center",
        "description": "Comprehensive visa type guide — tourist, work, student, family reunification.",
        "category": "visa_info",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["visa_info", "calming", "practical", "official", "general"],
    },
    {
        "title": "Residency Permit Guide",
        "description": "Step-by-step guide to obtaining and renewing residency permits.",
        "category": "residency_permit",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["residency_permit", "calming", "practical", "official", "legal"],
    },
    {
        "title": "Citizenship Pathway",
        "description": "Requirements, timelines, and preparation for citizenship applications.",
        "category": "citizenship_path",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["citizenship_path", "calming", "practical", "official", "milestone"],
    },
    {
        "title": "Work Permit Assistance",
        "description": "Navigate work permit applications, renewals, and employer sponsorship.",
        "category": "work_permit",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["work_permit", "calming", "practical", "work", "official"],
    },
    {
        "title": "Asylum Support Services",
        "description": "Legal aid, housing support, and counseling for asylum seekers.",
        "category": "asylum_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["asylum_support", "calming", "sensitive", "urgent", "rights"],
    },
    {
        "title": "Family Reunification Guide",
        "description": "Bring your family together — sponsorship, documentation, and timelines.",
        "category": "family_reunification",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["family_reunification", "calming", "family", "official", "sensitive"],
    },
    {
        "title": "Language Integration Classes",
        "description": "Free or subsidized language courses for newcomers — build confidence and connection.",
        "category": "language_integration",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["language_integration", "calming", "learning", "community", "integration"],
    },
    {
        "title": "Credential Recognition Service",
        "description": "Get your foreign degrees and certifications recognized in your new country.",
        "category": "credential_recognition",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["credential_recognition", "calming", "practical", "work", "official"],
    },
    {
        "title": "Healthcare Access for Immigrants",
        "description": "Understand your healthcare rights and register for services as a newcomer.",
        "category": "healthcare_access",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["healthcare_access", "calming", "practical", "medical", "rights"],
    },
    {
        "title": "Banking Setup for Newcomers",
        "description": "Open a bank account, build credit, and access financial services as a newcomer.",
        "category": "banking_setup",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["banking_setup", "calming", "practical", "financial", "integration"],
    },
    {
        "title": "Cultural Orientation Program",
        "description": "Understand local customs, social norms, and practical tips for daily life.",
        "category": "cultural_orientation",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["cultural_orientation", "calming", "learning", "community", "integration"],
    },
    {
        "title": "Refugee Services Directory",
        "description": "Comprehensive support for refugees — housing, legal, education, and employment.",
        "category": "refugee_services",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["refugee_services", "calming", "sensitive", "urgent", "comprehensive"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_IMMIGRATION_KEYWORDS: dict[str, list[str]] = {
    "移民": [],
    "immigration": [],
    "签证": ["visa_info"],
    "visa": ["visa_info"],
    "هجرة": [],
    "refugee": ["refugee_services"],
    "难民": ["refugee_services"],
    "居留": ["residency_permit"],
    "residency": ["residency_permit"],
    "citizenship": ["citizenship_path"],
    "asylum": ["asylum_support"],
    "work permit": ["work_permit"],
    "family reunification": ["family_reunification"],
    "credential": ["credential_recognition"],
    "banking": ["banking_setup"],
    "language class": ["language_integration"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _IMMIGRATION_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "visa_info": "Clear guidance on visa types and requirements",
        "residency_permit": "Your path to legal residency — step by step",
        "citizenship_path": "The road to belonging starts here",
        "work_permit": "Work legally and with confidence",
        "asylum_support": "Safety and support for those seeking asylum",
        "family_reunification": "Bringing your family together",
        "language_integration": "Language is the bridge to belonging",
        "credential_recognition": "Your skills and education matter here too",
        "healthcare_access": "Healthcare is a right — know how to access it",
        "banking_setup": "Financial independence in your new home",
        "cultural_orientation": "Understand your new home — thrive, not just survive",
        "refugee_services": "Comprehensive support for a fresh start",
    }
    return reason_map.get(category, "Support for your immigration journey")


class ImmigrationFulfiller(L2Fulfiller):
    """L2 fulfiller for immigration — visa, residency, and integration resources.

    Uses keyword matching to select from 12-entry catalog.
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
                dict(item) for item in IMMIGRATION_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in IMMIGRATION_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in IMMIGRATION_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Immigration resources updated — check back for new services.",
                delay_hours=24,
            ),
        )
