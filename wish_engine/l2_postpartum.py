"""PostpartumFulfiller — postpartum support resources for new mothers.

10-entry catalog covering postpartum depression, new mom support, and recovery.
Sensitive, supportive tone. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Catalog (10 entries) ─────────────────────────────────────────────────────

POSTPARTUM_CATALOG: list[dict] = [
    {
        "title": "Postpartum Depression Screening",
        "description": "Free, confidential screening tools and guidance on when to seek professional help.",
        "category": "postpartum_depression_screening",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["depression", "screening", "professional", "calming", "gentle"],
    },
    {
        "title": "New Mom Support Group",
        "description": "Connect with other new moms — shared experiences, no judgment, real support.",
        "category": "new_mom_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["support", "community", "moms", "calming", "gentle"],
    },
    {
        "title": "Lactation Support",
        "description": "Expert breastfeeding guidance — lactation consultants, tips, and troubleshooting.",
        "category": "lactation_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["lactation", "breastfeeding", "professional", "calming"],
    },
    {
        "title": "Sleep Deprivation Help",
        "description": "Sleep strategies for new parents — safe co-sleeping, shift schedules, and recovery naps.",
        "category": "sleep_deprivation_help",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sleep", "rest", "practical", "calming", "gentle"],
    },
    {
        "title": "Partner Adjustment Guide",
        "description": "Resources for navigating relationship changes after baby — communication tools and support.",
        "category": "partner_adjustment",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["partner", "relationship", "calming", "gentle"],
    },
    {
        "title": "Postpartum Body Recovery",
        "description": "Gentle body recovery guidance — pelvic floor, diastasis recti, and timeline expectations.",
        "category": "body_recovery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["body", "recovery", "gentle", "calming", "self-paced"],
    },
    {
        "title": "Return-to-Work Planning",
        "description": "Navigating the transition back to work — childcare, pumping, and emotional preparation.",
        "category": "return_to_work",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["work", "planning", "practical", "calming"],
    },
    {
        "title": "Childcare Options Guide",
        "description": "Compare childcare options — daycare, nanny, family care, and what to look for.",
        "category": "childcare_options",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["childcare", "practical", "planning", "calming"],
    },
    {
        "title": "Postpartum Exercise",
        "description": "Safe, gentle exercises for postpartum recovery — approved by OB-GYNs and physiotherapists.",
        "category": "postpartum_exercise",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["exercise", "gentle", "recovery", "calming", "self-paced"],
    },
    {
        "title": "Postpartum Therapy",
        "description": "Find therapists specializing in postpartum mood disorders — you deserve support.",
        "category": "postpartum_therapy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["therapy", "professional", "depression", "calming", "gentle"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_POSTPARTUM_KEYWORDS: dict[str, list[str]] = {
    "产后": [],
    "postpartum": [],
    "新妈妈": ["moms", "community"],
    "new mom": ["moms", "community"],
    "ما بعد الولادة": [],
    "baby blues": ["depression", "calming"],
    "breastfeeding": ["lactation", "breastfeeding"],
    "母乳": ["lactation", "breastfeeding"],
    "sleep": ["sleep", "rest"],
    "睡眠": ["sleep", "rest"],
    "depression": ["depression", "professional"],
    "抑郁": ["depression", "professional"],
    "body": ["body", "recovery"],
    "恢复": ["body", "recovery"],
    "childcare": ["childcare", "practical"],
    "work": ["work", "planning"],
}


def _match_postpartum_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _POSTPARTUM_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class PostpartumFulfiller(L2Fulfiller):
    """L2 fulfiller for postpartum support — sensitive, supportive resources.

    10 curated entries for new mothers. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_postpartum_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in POSTPARTUM_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in POSTPARTUM_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in POSTPARTUM_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="You are doing an amazing job. Support is here whenever you need it.",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "professional" in tags:
        return "Expert support from specialists who understand postpartum needs"
    if "community" in tags:
        return "Connect with other new moms who get it"
    if "gentle" in tags:
        return "Gentle, no-pressure approach at your own pace"
    if "practical" in tags:
        return "Practical help for the challenges of new parenthood"
    return "Supportive resource for your postpartum journey"
