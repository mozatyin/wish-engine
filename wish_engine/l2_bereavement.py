"""BereavementFulfiller — grief support resource recommendations.

12-entry curated catalog for bereavement support. Personality-filtered,
all calming/gentle tone. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Bereavement Catalog (12 entries) ─────────────────────────────────────────

BEREAVEMENT_CATALOG: list[dict] = [
    {
        "title": "Grief Support Group",
        "description": "Weekly peer support circle — share your loss with others who understand.",
        "category": "grief_support_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["grief", "support_group", "peer", "gentle", "structured"],
    },
    {
        "title": "Bereavement Counselor",
        "description": "One-on-one professional grief counseling — process loss at your own pace.",
        "category": "bereavement_counselor",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["grief", "professional", "solo", "gentle", "guided"],
    },
    {
        "title": "Memorial Service Planning",
        "description": "Guidance on creating a meaningful memorial — honoring a life well lived.",
        "category": "memorial_service",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["grief", "memorial", "ritual", "structured", "community"],
    },
    {
        "title": "Grief Retreat",
        "description": "Multi-day retreat in nature for deep grief processing — silence, journaling, healing.",
        "category": "grief_retreat",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["grief", "retreat", "nature", "solo", "gentle", "space"],
    },
    {
        "title": "Online Grief Forum",
        "description": "24/7 online community for grief support — share anonymously when you are ready.",
        "category": "online_grief_forum",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["grief", "online", "peer", "anonymous", "gentle"],
    },
    {
        "title": "Anniversary Support Guide",
        "description": "Tools for navigating grief on anniversaries and special dates.",
        "category": "anniversary_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["grief", "anniversary", "gentle", "structured", "self_paced"],
    },
    {
        "title": "Complicated Grief Therapy",
        "description": "Specialized therapy for prolonged grief — when loss feels impossible to move through.",
        "category": "complicated_grief_therapy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["grief", "professional", "therapy", "guided", "intensive"],
    },
    {
        "title": "Children's Grief Support",
        "description": "Age-appropriate grief resources and groups for children who have lost a loved one.",
        "category": "children_grief_support",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["grief", "children", "family", "gentle", "guided"],
    },
    {
        "title": "Spousal Loss Group",
        "description": "Support group specifically for those who have lost a spouse or partner.",
        "category": "spousal_loss_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["grief", "spouse", "peer", "support_group", "gentle"],
    },
    {
        "title": "Parent Loss Group",
        "description": "Peer support for adults who have lost a parent — shared understanding in grief.",
        "category": "parent_loss_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["grief", "parent", "peer", "support_group", "gentle"],
    },
    {
        "title": "Sibling Loss Group",
        "description": "Support for the often-overlooked grief of losing a brother or sister.",
        "category": "sibling_loss_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["grief", "sibling", "peer", "support_group", "gentle"],
    },
    {
        "title": "Sudden Loss Support",
        "description": "Specialized resources for coping with unexpected, sudden loss — shock and trauma processing.",
        "category": "sudden_loss_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["grief", "sudden", "trauma", "professional", "gentle", "guided"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_BEREAVEMENT_KEYWORDS: dict[str, list[str]] = {
    "丧亲": ["grief", "support_group"],
    "bereavement": ["grief", "professional"],
    "grief": ["grief", "gentle"],
    "loss": ["grief", "gentle"],
    "失去": ["grief", "gentle"],
    "فقدان": ["grief", "gentle"],
    "mourning": ["grief", "ritual"],
    "spouse": ["spouse", "peer"],
    "parent": ["parent", "peer"],
    "sibling": ["sibling", "peer"],
    "child": ["children", "family"],
    "sudden": ["sudden", "trauma"],
    "anniversary": ["anniversary", "structured"],
    "memorial": ["memorial", "ritual"],
    "counselor": ["professional", "guided"],
    "support group": ["support_group", "peer"],
}


def _match_bereavement_tags(wish_text: str) -> list[str]:
    """Extract matching tags from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _BEREAVEMENT_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class BereavementFulfiller(L2Fulfiller):
    """L2 fulfiller for bereavement support — gentle grief resource recommendations.

    12 curated entries covering different types of loss. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_bereavement_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in BEREAVEMENT_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in BEREAVEMENT_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in BEREAVEMENT_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Grief has no timeline. We are here whenever you need us.",
                delay_hours=48,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "professional" in tags:
        return "Professional support to help you process your grief"
    if "support_group" in tags:
        return "You are not alone — others share this journey"
    if "retreat" in tags:
        return "A safe space to grieve in peace"
    if "memorial" in tags:
        return "Honor their memory in a meaningful way"
    if "children" in tags:
        return "Age-appropriate support for young hearts"
    return "A gentle resource for your grief journey"
