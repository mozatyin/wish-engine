"""AntiDiscriminationFulfiller — anti-discrimination resources and support.

10-entry curated catalog of reporting, legal, and community resources. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Anti-Discrimination Catalog (10 entries) ─────────────────────────────────

ANTI_DISCRIMINATION_CATALOG: list[dict] = [
    {
        "title": "Discrimination Hotline",
        "description": "Confidential hotline to report discrimination and get immediate guidance.",
        "category": "discrimination_hotline",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["discrimination_hotline", "calming", "immediate", "reporting", "confidential"],
    },
    {
        "title": "Filing a Discrimination Complaint",
        "description": "Step-by-step guide to filing formal complaints with equality commissions.",
        "category": "filing_complaint",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["filing_complaint", "calming", "practical", "legal", "official"],
    },
    {
        "title": "Legal Protection Guide",
        "description": "Know what laws protect you — anti-discrimination statutes explained clearly.",
        "category": "legal_protection",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["legal_protection", "calming", "rights", "legal", "self-paced"],
    },
    {
        "title": "Support Community Network",
        "description": "Connect with others who have faced discrimination — solidarity, not isolation.",
        "category": "support_community",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["support_community", "calming", "community", "social", "gentle"],
    },
    {
        "title": "Ally Training Program",
        "description": "Learn to be an effective ally — bystander intervention and inclusive practices.",
        "category": "ally_training",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["ally_training", "calming", "learning", "community", "skills"],
    },
    {
        "title": "Bias Incident Reporting",
        "description": "Document and report bias incidents — even when they do not rise to legal thresholds.",
        "category": "bias_incident_report",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["bias_incident_report", "calming", "reporting", "practical", "documentation"],
    },
    {
        "title": "Workplace Equity Resources",
        "description": "Tools for fair hiring, pay equity analysis, and inclusive workplace policies.",
        "category": "workplace_equity",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["workplace_equity", "calming", "work", "practical", "rights"],
    },
    {
        "title": "Hate Crime Reporting",
        "description": "Report hate crimes safely — know what qualifies and how to document evidence.",
        "category": "hate_crime_report",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["hate_crime_report", "calming", "reporting", "urgent", "safety"],
    },
    {
        "title": "Cultural Sensitivity Resources",
        "description": "Educational materials on cultural awareness, implicit bias, and inclusive language.",
        "category": "cultural_sensitivity",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cultural_sensitivity", "calming", "learning", "self-paced", "gentle"],
    },
    {
        "title": "Advocacy Organization Directory",
        "description": "Connect with organizations fighting discrimination in your area and community.",
        "category": "advocacy_org",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["advocacy_org", "calming", "community", "rights", "organizing"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_ANTI_DISCRIMINATION_KEYWORDS: dict[str, list[str]] = {
    "歧视": [],
    "discrimination": [],
    "反歧视": [],
    "anti": [],
    "تمييز": [],
    "racism": ["filing_complaint", "hate_crime_report"],
    "bias": ["bias_incident_report"],
    "平等": [],
    "hate crime": ["hate_crime_report"],
    "complaint": ["filing_complaint"],
    "hotline": ["discrimination_hotline"],
    "workplace equity": ["workplace_equity"],
    "ally": ["ally_training"],
    "advocacy": ["advocacy_org"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _ANTI_DISCRIMINATION_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "discrimination_hotline": "Immediate guidance when discrimination happens",
        "filing_complaint": "Your experience deserves to be officially documented",
        "legal_protection": "The law is on your side — know your protections",
        "support_community": "You are not alone — find solidarity and strength",
        "ally_training": "Be part of the solution — learn to stand up effectively",
        "bias_incident_report": "Every incident matters — document and report",
        "workplace_equity": "Fair workplaces start with informed action",
        "hate_crime_report": "Hate crimes must be reported and prosecuted",
        "cultural_sensitivity": "Understanding builds bridges across differences",
        "advocacy_org": "Organizations fighting for equality in your community",
    }
    return reason_map.get(category, "Resources for equality and dignity")


class AntiDiscriminationFulfiller(L2Fulfiller):
    """L2 fulfiller for anti-discrimination — reporting, legal, and community resources.

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
                dict(item) for item in ANTI_DISCRIMINATION_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in ANTI_DISCRIMINATION_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in ANTI_DISCRIMINATION_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More anti-discrimination resources available — you deserve equality.",
                delay_hours=24,
            ),
        )
