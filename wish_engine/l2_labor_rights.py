"""LaborRightsFulfiller — labor rights information and workplace protection resources.

12-entry curated catalog of worker rights tools and reporting channels. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Labor Rights Catalog (12 entries) ────────────────────────────────────────

LABOR_RIGHTS_CATALOG: list[dict] = [
    {
        "title": "Overtime Pay Calculator",
        "description": "Calculate what you are owed — input your hours and rate to see unpaid overtime.",
        "category": "overtime_calculator",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["overtime_calculator", "practical", "calming", "financial", "self-paced"],
    },
    {
        "title": "Wage Theft Report",
        "description": "Report unpaid wages, stolen tips, or illegal deductions to labor authorities.",
        "category": "wage_theft_report",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wage_theft_report", "reporting", "calming", "rights", "financial"],
    },
    {
        "title": "Workplace Safety Guide",
        "description": "Know your safety rights — report hazards, understand OSHA protections.",
        "category": "workplace_safety",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["workplace_safety", "safety", "calming", "rights", "practical"],
    },
    {
        "title": "Union Information Center",
        "description": "Learn about unions — how to join, organize, or find your industry's union.",
        "category": "union_info",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["union_info", "community", "calming", "rights", "organizing"],
    },
    {
        "title": "Harassment Reporting Guide",
        "description": "Step-by-step guide to document and report workplace harassment safely.",
        "category": "harassment_report",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["harassment_report", "safety", "calming", "reporting", "sensitive"],
    },
    {
        "title": "Wrongful Termination Help",
        "description": "Were you fired illegally? Understand your rights and next steps.",
        "category": "wrongful_termination",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wrongful_termination", "rights", "calming", "urgent", "legal"],
    },
    {
        "title": "Contract Review Checklist",
        "description": "Before you sign — key clauses to watch for in employment contracts.",
        "category": "contract_review",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["contract_review", "practical", "calming", "rights", "self-paced"],
    },
    {
        "title": "Workers Compensation Guide",
        "description": "Injured at work? Navigate the workers comp process step by step.",
        "category": "workers_comp",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["workers_comp", "safety", "calming", "rights", "medical"],
    },
    {
        "title": "Whistleblower Protection Info",
        "description": "Know your protections before reporting — anti-retaliation laws explained.",
        "category": "whistleblower_protection",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["whistleblower_protection", "rights", "calming", "reporting", "legal"],
    },
    {
        "title": "Maternity & Parental Rights",
        "description": "Your rights to parental leave, pumping breaks, and job protection.",
        "category": "maternity_rights",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["maternity_rights", "rights", "calming", "family", "practical"],
    },
    {
        "title": "Disability Accommodation Guide",
        "description": "Request workplace accommodations — know what employers must provide by law.",
        "category": "disability_accommodation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["disability_accommodation", "rights", "calming", "accessibility", "practical"],
    },
    {
        "title": "Gig Worker Rights",
        "description": "Rights for freelancers and gig workers — pay protections, insurance, classification.",
        "category": "gig_worker_rights",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["gig_worker_rights", "rights", "calming", "practical", "financial"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_LABOR_KEYWORDS: dict[str, list[str]] = {
    "劳动": [],
    "labor": [],
    "加班": ["overtime_calculator"],
    "overtime": ["overtime_calculator"],
    "欠薪": ["wage_theft_report"],
    "wage": ["wage_theft_report", "overtime_calculator"],
    "عمال": [],
    "worker rights": [],
    "harassment": ["harassment_report"],
    "fired": ["wrongful_termination"],
    "union": ["union_info"],
    "contract": ["contract_review"],
    "injury": ["workers_comp"],
    "whistleblower": ["whistleblower_protection"],
    "maternity": ["maternity_rights"],
    "gig": ["gig_worker_rights"],
    "safety": ["workplace_safety"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _LABOR_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "overtime_calculator": "Know exactly what you are owed",
        "wage_theft_report": "Your wages belong to you — report theft",
        "workplace_safety": "A safe workplace is your legal right",
        "union_info": "Collective power protects individual workers",
        "harassment_report": "Document and report safely — you are protected",
        "wrongful_termination": "Illegal firing has legal consequences",
        "contract_review": "Understand before you sign",
        "workers_comp": "Injured workers deserve support and compensation",
        "whistleblower_protection": "Truth-telling is legally protected",
        "maternity_rights": "Parental leave is a right, not a favor",
        "disability_accommodation": "Employers must accommodate — know your rights",
        "gig_worker_rights": "Gig workers have rights too",
    }
    return reason_map.get(category, "Know your rights as a worker")


class LaborRightsFulfiller(L2Fulfiller):
    """L2 fulfiller for labor rights — workplace protection and worker resources.

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
                dict(item) for item in LABOR_RIGHTS_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in LABOR_RIGHTS_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in LABOR_RIGHTS_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Workers rights resources updated — check back for more.",
                delay_hours=24,
            ),
        )
