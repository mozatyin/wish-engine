"""LegalAidFulfiller — legal aid navigation and resource recommendations.

15-entry curated catalog of legal services and rights resources. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Legal Aid Catalog (15 entries) ───────────────────────────────────────────

LEGAL_AID_CATALOG: list[dict] = [
    {
        "title": "Free Legal Clinic",
        "description": "Walk-in legal clinics with pro bono lawyers — get free advice on your situation.",
        "category": "free_legal_clinic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["free_legal_clinic", "free", "calming", "professional", "general"],
    },
    {
        "title": "Tenant Rights Lawyer",
        "description": "Legal help for renters — evictions, deposits, landlord disputes, lease issues.",
        "category": "tenant_lawyer",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["tenant_lawyer", "housing", "calming", "professional", "rights"],
    },
    {
        "title": "Employment Lawyer",
        "description": "Legal support for workplace issues — wrongful termination, harassment, wage theft.",
        "category": "employment_lawyer",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["employment_lawyer", "work", "calming", "professional", "rights"],
    },
    {
        "title": "Family Lawyer",
        "description": "Divorce, custody, domestic violence protection orders — compassionate legal help.",
        "category": "family_lawyer",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["family_lawyer", "family", "calming", "professional", "sensitive"],
    },
    {
        "title": "Immigration Lawyer",
        "description": "Visa, asylum, deportation defense, and residency applications — expert guidance.",
        "category": "immigration_lawyer",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["immigration_lawyer", "immigration", "calming", "professional", "rights"],
    },
    {
        "title": "Consumer Rights Service",
        "description": "Fight scams, unfair contracts, and defective products — know your consumer rights.",
        "category": "consumer_rights",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["consumer_rights", "consumer", "calming", "practical", "rights"],
    },
    {
        "title": "Criminal Defense Referral",
        "description": "Connect with criminal defense attorneys — from minor charges to serious cases.",
        "category": "criminal_defense",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["criminal_defense", "criminal", "calming", "professional", "urgent"],
    },
    {
        "title": "Disability Rights Advocate",
        "description": "Legal advocacy for disability accommodations, benefits, and discrimination cases.",
        "category": "disability_rights",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["disability_rights", "disability", "calming", "professional", "rights"],
    },
    {
        "title": "Domestic Violence Legal Aid",
        "description": "Confidential legal help for abuse survivors — protection orders and safe planning.",
        "category": "domestic_violence_legal",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["domestic_violence_legal", "safety", "calming", "professional", "sensitive"],
    },
    {
        "title": "Debt Counselor",
        "description": "Free debt counseling — negotiate with creditors, understand bankruptcy options.",
        "category": "debt_counselor",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt_counselor", "financial", "calming", "practical", "free"],
    },
    {
        "title": "Human Rights Organization",
        "description": "Report human rights violations and get connected with advocacy organizations.",
        "category": "human_rights_org",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["human_rights_org", "rights", "calming", "advocacy", "community"],
    },
    {
        "title": "Legal Hotline",
        "description": "Call a legal hotline for immediate guidance — no appointment needed.",
        "category": "legal_hotline",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["legal_hotline", "calming", "immediate", "free", "general"],
    },
    {
        "title": "Court Navigator Program",
        "description": "Volunteer court navigators help you understand forms, procedures, and next steps.",
        "category": "court_navigator",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["court_navigator", "calming", "practical", "free", "guidance"],
    },
    {
        "title": "Mediation Service",
        "description": "Resolve disputes without court — trained mediators for neighbor, family, or work conflicts.",
        "category": "mediation_service",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["mediation_service", "calming", "practical", "resolution", "community"],
    },
    {
        "title": "Legal Document Help",
        "description": "Free help filling out legal forms — contracts, complaints, applications.",
        "category": "legal_document_help",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["legal_document_help", "calming", "practical", "free", "general"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_LEGAL_KEYWORDS: dict[str, list[str]] = {
    "法律": [],
    "legal": [],
    "律师": [],
    "lawyer": [],
    "محامي": [],
    "rights": ["human_rights_org"],
    "权益": [],
    "法援": ["free_legal_clinic"],
    "tenant": ["tenant_lawyer"],
    "employment": ["employment_lawyer"],
    "family law": ["family_lawyer"],
    "immigration": ["immigration_lawyer"],
    "consumer": ["consumer_rights"],
    "criminal": ["criminal_defense"],
    "disability": ["disability_rights"],
    "domestic violence": ["domestic_violence_legal"],
    "debt": ["debt_counselor"],
    "hotline": ["legal_hotline"],
    "mediation": ["mediation_service"],
    "court": ["court_navigator"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _LEGAL_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "free_legal_clinic": "Free professional legal advice — no cost barrier",
        "tenant_lawyer": "Know your rights as a renter",
        "employment_lawyer": "Workplace injustice deserves a legal response",
        "family_lawyer": "Compassionate legal help for family matters",
        "immigration_lawyer": "Expert guidance through complex immigration law",
        "consumer_rights": "Fight back against unfair business practices",
        "criminal_defense": "Everyone deserves proper legal defense",
        "disability_rights": "Legal protection for disability accommodations",
        "domestic_violence_legal": "Confidential legal help for your safety",
        "debt_counselor": "Financial clarity and a path forward",
        "human_rights_org": "Connect with organizations fighting for your rights",
        "legal_hotline": "Immediate legal guidance — just one call away",
        "court_navigator": "Navigate the court system with confidence",
        "mediation_service": "Resolve conflicts without the stress of court",
        "legal_document_help": "Get your legal paperwork right — for free",
    }
    return reason_map.get(category, "Legal help when you need it most")


class LegalAidFulfiller(L2Fulfiller):
    """L2 fulfiller for legal aid — rights-based resource navigation.

    Uses keyword matching to select from 15-entry catalog.
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
                dict(item) for item in LEGAL_AID_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in LEGAL_AID_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in LEGAL_AID_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Legal resources updated regularly — check back for more options.",
                delay_hours=24,
            ),
        )
