"""CaregiverSupportFulfiller — support groups and resources for caregivers.

10-entry curated catalog of peer support, training, and planning resources. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Caregiver Support Catalog (10 entries) ───────────────────────────────────

CAREGIVER_SUPPORT_CATALOG: list[dict] = [
    {
        "title": "Local Caregiver Support Group",
        "description": "Weekly in-person meetups with fellow caregivers — share, listen, and feel understood.",
        "category": "caregiver_support_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["caregiver_support_group", "social", "calming", "community", "weekly"],
    },
    {
        "title": "Online Caregiver Forum",
        "description": "24/7 online community of caregivers — ask questions, share stories, find solidarity.",
        "category": "online_caregiver_forum",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["online_caregiver_forum", "digital", "social", "calming", "self-paced"],
    },
    {
        "title": "Caregiver Therapy Sessions",
        "description": "Professional counseling tailored to caregiver stress, guilt, and grief.",
        "category": "caregiver_therapy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["caregiver_therapy", "professional", "calming", "mental_health", "private"],
    },
    {
        "title": "Caregiver Retreat Weekend",
        "description": "Structured retreat with workshops, rest, and peer connection — just for caregivers.",
        "category": "caregiver_retreat",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["caregiver_retreat", "residential", "calming", "restorative", "community"],
    },
    {
        "title": "Caregiver Training Program",
        "description": "Learn practical skills — lifting, medication management, communication with dementia.",
        "category": "caregiver_training",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["caregiver_training", "learning", "calming", "practical", "skills"],
    },
    {
        "title": "Burnout Recovery Program",
        "description": "Step-by-step recovery from caregiver burnout — boundaries, rest, and renewal.",
        "category": "burnout_recovery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["burnout_recovery", "calming", "mental_health", "self-paced", "gentle"],
    },
    {
        "title": "Anticipatory Grief Support",
        "description": "Processing grief before loss — understanding, validating, and coping together.",
        "category": "grief_anticipation",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["grief_anticipation", "calming", "mental_health", "social", "gentle"],
    },
    {
        "title": "Self-Care for Caregivers Guide",
        "description": "Practical self-care strategies that fit into a caregiver's impossible schedule.",
        "category": "self_care_for_caregivers",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["self_care_for_caregivers", "calming", "self-paced", "practical", "gentle"],
    },
    {
        "title": "Financial Planning for Care",
        "description": "Navigate insurance, benefits, and costs — financial guidance for care families.",
        "category": "financial_planning_care",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["financial_planning_care", "practical", "calming", "planning", "financial"],
    },
    {
        "title": "Legal Care Planning",
        "description": "Power of attorney, advance directives, and guardianship — legal prep made clear.",
        "category": "legal_care_planning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["legal_care_planning", "practical", "calming", "planning", "legal"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_CAREGIVER_SUPPORT_KEYWORDS: dict[str, list[str]] = {
    "照护者支持": [],
    "caregiver support": [],
    "互助": [],
    "support group": ["caregiver_support_group"],
    "دعم مقدمي الرعاية": [],
    "burnout": ["burnout_recovery"],
    "therapy": ["caregiver_therapy"],
    "training": ["caregiver_training"],
    "grief": ["grief_anticipation"],
    "forum": ["online_caregiver_forum"],
    "financial": ["financial_planning_care"],
    "legal planning": ["legal_care_planning"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _CAREGIVER_SUPPORT_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "caregiver_support_group": "You are not alone — find your people",
        "online_caregiver_forum": "Connect with caregivers anytime, anywhere",
        "caregiver_therapy": "Professional support for the weight you carry",
        "caregiver_retreat": "A weekend to just be yourself again",
        "caregiver_training": "Practical skills build confidence and reduce stress",
        "burnout_recovery": "Recovery starts with permission to rest",
        "grief_anticipation": "It is okay to grieve before goodbye",
        "self_care_for_caregivers": "Small acts of care for the caregiver too",
        "financial_planning_care": "Financial clarity reduces caregiving anxiety",
        "legal_care_planning": "Peace of mind through proper planning",
    }
    return reason_map.get(category, "Support for those who care for others")


class CaregiverSupportFulfiller(L2Fulfiller):
    """L2 fulfiller for caregiver support — peer groups, training, planning.

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
                dict(item) for item in CAREGIVER_SUPPORT_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in CAREGIVER_SUPPORT_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in CAREGIVER_SUPPORT_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More caregiver resources available — you are not alone!",
                delay_hours=24,
            ),
        )
