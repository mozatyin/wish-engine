"""SuicidePreventionFulfiller — HIGHEST sensitivity crisis resource routing.

10-entry curated catalog. Always uses question style for gentle engagement.
Crisis hotlines always presented first. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Suicide Prevention Catalog (10 entries) ──────────────────────────────────

SUICIDE_PREVENTION_CATALOG: list[dict] = [
    {
        "title": "Crisis Hotline — Call Now",
        "description": "988 Suicide & Crisis Lifeline (US) or your local crisis line. Someone is waiting.",
        "category": "crisis_hotline",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "hotline", "immediate", "professional", "priority"],
    },
    {
        "title": "Crisis Text Line",
        "description": "Text HOME to 741741 — if calling feels too hard, text instead.",
        "category": "text_crisis_line",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "text", "immediate", "accessible", "priority"],
    },
    {
        "title": "Crisis Chat Support",
        "description": "Online chat with a crisis counselor — type when you cannot speak.",
        "category": "crisis_chat",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "chat", "immediate", "accessible", "online"],
    },
    {
        "title": "Safety Planning Guide",
        "description": "Create a personal safety plan — warning signs, coping strategies, emergency contacts.",
        "category": "safety_planning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "safety_plan", "structured", "professional", "guided"],
    },
    {
        "title": "Means Restriction Guide",
        "description": "Reduce access to harmful means — practical steps that save lives.",
        "category": "means_restriction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "means_restriction", "practical", "safety", "guided"],
    },
    {
        "title": "Peer Support Connection",
        "description": "Talk to someone who has been through it — lived experience peer support.",
        "category": "peer_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "peer", "connection", "gentle", "support"],
    },
    {
        "title": "Crisis Walk-In Center",
        "description": "Find a walk-in crisis center near you — no appointment needed.",
        "category": "crisis_walk_in",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "walk_in", "immediate", "professional", "local"],
    },
    {
        "title": "Hospital Emergency Department",
        "description": "If you are in immediate danger — go to your nearest emergency room.",
        "category": "hospital_emergency",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "emergency", "immediate", "hospital", "priority"],
    },
    {
        "title": "Follow-Up Care After Crisis",
        "description": "Continued support after a crisis — therapy referrals, check-ins, recovery planning.",
        "category": "follow_up_care",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "follow_up", "professional", "ongoing", "structured"],
    },
    {
        "title": "Family Support After Crisis",
        "description": "Resources for family members — how to support a loved one through crisis.",
        "category": "family_support_after",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "family", "support", "education", "gentle"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_SUICIDE_KEYWORDS: dict[str, list[str]] = {
    "自杀": ["crisis", "immediate"],
    "suicide": ["crisis", "immediate"],
    "不想活": ["crisis", "immediate"],
    "kill myself": ["crisis", "immediate"],
    "انتحار": ["crisis", "immediate"],
    "crisis": ["crisis", "immediate"],
    "想死": ["crisis", "immediate"],
    "end my life": ["crisis", "immediate"],
    "结束生命": ["crisis", "immediate"],
    "活不下去": ["crisis", "immediate"],
    "no reason to live": ["crisis", "immediate"],
    "self harm": ["crisis", "immediate"],
    "自残": ["crisis", "immediate"],
    "overdose": ["crisis", "immediate"],
}


def _match_crisis_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _SUICIDE_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class SuicidePreventionFulfiller(L2Fulfiller):
    """L2 fulfiller for suicide prevention — HIGHEST sensitivity crisis routing.

    Always prioritizes crisis hotline. Question-style engagement. Zero LLM.
    """

    safety_critical = True

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # Always include crisis hotline as first recommendation
        candidates = [dict(item) for item in SUICIDE_PREVENTION_CATALOG]

        # Prioritize immediate-access resources
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
                text="You matter. Would you like to check in again tomorrow?",
                delay_hours=12,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "hotline" in tags:
        return "Someone is ready to listen right now"
    if "text" in tags:
        return "If calling is too hard, texting works too"
    if "chat" in tags:
        return "Type when you cannot speak"
    if "emergency" in tags:
        return "Immediate safety is the priority"
    if "safety_plan" in tags:
        return "A plan you can hold onto in dark moments"
    if "peer" in tags:
        return "Someone who has been through it and made it"
    return "You are not alone — help is available"
