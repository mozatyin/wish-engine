"""CyberbullyingFulfiller — cyberbullying response and support resources.

10-entry catalog of actionable steps for dealing with online harassment.
Zero LLM.
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

CYBERBULLYING_CATALOG: list[dict] = [
    {
        "title": "Evidence Collection Guide",
        "description": "How to screenshot, save, and document cyberbullying — building a record that matters.",
        "category": "evidence_collection",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["evidence", "documentation", "practical", "calming", "self-paced"],
    },
    {
        "title": "Platform Reporting Toolkit",
        "description": "Step-by-step guides for reporting harassment on major platforms — Instagram, TikTok, Twitter, etc.",
        "category": "platform_reporting",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["reporting", "platform", "practical", "calming", "self-paced"],
    },
    {
        "title": "School Reporting Guide",
        "description": "How to report cyberbullying to schools — template letters, escalation paths, and rights.",
        "category": "school_reporting",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["school", "reporting", "practical", "calming"],
    },
    {
        "title": "Legal Action Resources",
        "description": "When cyberbullying crosses legal lines — understanding your rights and options.",
        "category": "legal_action",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["legal", "rights", "professional", "calming"],
    },
    {
        "title": "Blocking and Safety Guide",
        "description": "Comprehensive blocking guide across platforms — protect yourself from further contact.",
        "category": "blocking_guide",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["blocking", "safety", "practical", "calming", "self-paced"],
    },
    {
        "title": "Emotional Support Resources",
        "description": "Counseling hotlines and support for the emotional impact of cyberbullying.",
        "category": "emotional_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["emotional", "support", "counseling", "calming", "gentle"],
    },
    {
        "title": "Parent Guide to Cyberbullying",
        "description": "Help your child through cyberbullying — what to say, what to do, when to intervene.",
        "category": "parent_guide",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["parent", "family", "education", "calming"],
    },
    {
        "title": "Digital Footprint Cleanup",
        "description": "Remove harmful content, request takedowns, and clean up your online presence.",
        "category": "digital_footprint_cleanup",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cleanup", "digital", "practical", "calming", "self-paced"],
    },
    {
        "title": "Online Reputation Recovery",
        "description": "Rebuild your online presence after harassment — positive content strategies.",
        "category": "online_reputation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["reputation", "recovery", "digital", "calming"],
    },
    {
        "title": "Peer Mediation Program",
        "description": "Structured mediation for resolving online conflicts — trained mediators available.",
        "category": "peer_mediation",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["mediation", "resolution", "social", "calming"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_CYBERBULLYING_KEYWORDS: dict[str, list[str]] = {
    "网络霸凌": [],
    "cyberbullying": [],
    "网暴": [],
    "online harassment": [],
    "تنمر إلكتروني": [],
    "bully": [],
    "harassment": [],
    "骚扰": [],
    "report": ["reporting", "platform"],
    "举报": ["reporting", "platform"],
    "block": ["blocking", "safety"],
    "屏蔽": ["blocking", "safety"],
    "evidence": ["evidence", "documentation"],
    "证据": ["evidence", "documentation"],
    "legal": ["legal", "rights"],
    "法律": ["legal", "rights"],
    "parent": ["parent", "family"],
    "家长": ["parent", "family"],
}


def _match_cyberbullying_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _CYBERBULLYING_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class CyberbullyingFulfiller(L2Fulfiller):
    """L2 fulfiller for cyberbullying response — actionable protection steps.

    10 curated entries covering evidence, reporting, and support. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_cyberbullying_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in CYBERBULLYING_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in CYBERBULLYING_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in CYBERBULLYING_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="You do not deserve this. Help and support are available.",
                delay_hours=12,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "evidence" in tags:
        return "Document everything — this is your strongest tool"
    if "reporting" in tags:
        return "Take action by reporting through official channels"
    if "safety" in tags:
        return "Protect yourself from further contact"
    if "support" in tags or "counseling" in tags:
        return "Emotional support to help you through this"
    return "Practical step to address cyberbullying"
