"""DebtCrisisFulfiller — financial emergency and debt crisis resources.

10-entry curated catalog. Practical, non-judgmental. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Debt Crisis Catalog (10 entries) ─────────────────────────────────────────

DEBT_CRISIS_CATALOG: list[dict] = [
    {
        "title": "Debt Counseling Service",
        "description": "Free or low-cost debt counseling — a professional helps you see the full picture.",
        "category": "debt_counseling",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt", "counseling", "professional", "structured", "guided"],
    },
    {
        "title": "Bankruptcy Information Guide",
        "description": "Understand your options — Chapter 7, Chapter 13, and what they mean for you.",
        "category": "bankruptcy_info",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt", "bankruptcy", "legal", "educational", "structured"],
    },
    {
        "title": "Creditor Negotiation Help",
        "description": "Learn to negotiate with creditors — reduce payments, lower interest, settle debt.",
        "category": "creditor_negotiation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt", "negotiation", "practical", "guided", "empowering"],
    },
    {
        "title": "Debt Consolidation Options",
        "description": "Combine multiple debts into one payment — simpler, often lower interest.",
        "category": "debt_consolidation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt", "consolidation", "practical", "structured", "financial"],
    },
    {
        "title": "Financial Emergency Fund Guide",
        "description": "How to start an emergency fund even in crisis — small steps, big difference.",
        "category": "financial_emergency_fund",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt", "emergency", "savings", "practical", "self_paced"],
    },
    {
        "title": "Food Assistance Programs",
        "description": "Find food banks, SNAP benefits, and community meals — basic needs first.",
        "category": "food_assistance",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt", "food", "assistance", "immediate", "basic_needs"],
    },
    {
        "title": "Utility Assistance Programs",
        "description": "Help paying utility bills — LIHEAP, local programs, payment plans.",
        "category": "utility_assistance",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt", "utility", "assistance", "immediate", "basic_needs"],
    },
    {
        "title": "Debt Legal Aid",
        "description": "Free legal help for debt issues — know your rights against collectors.",
        "category": "debt_legal_aid",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt", "legal", "rights", "professional", "guided"],
    },
    {
        "title": "Income Support & Job Search",
        "description": "Unemployment benefits, job training, and quick-start employment resources.",
        "category": "income_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt", "income", "employment", "practical", "empowering"],
    },
    {
        "title": "Financial Recovery Plan",
        "description": "Build a step-by-step plan to recover from debt — realistic, compassionate, achievable.",
        "category": "financial_recovery_plan",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["debt", "recovery", "planning", "structured", "self_paced"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_DEBT_KEYWORDS: dict[str, list[str]] = {
    "债务": ["debt", "structured"],
    "debt": ["debt", "structured"],
    "bankruptcy": ["debt", "bankruptcy"],
    "催收": ["debt", "legal"],
    "破产": ["debt", "bankruptcy"],
    "ديون": ["debt", "structured"],
    "owe": ["debt", "structured"],
    "欠钱": ["debt", "structured"],
    "creditor": ["debt", "negotiation"],
    "collector": ["debt", "legal"],
    "food bank": ["debt", "food"],
    "utility bill": ["debt", "utility"],
    "还不起": ["debt", "immediate"],
    "financial crisis": ["debt", "emergency"],
}


def _match_debt_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _DEBT_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class DebtCrisisFulfiller(L2Fulfiller):
    """L2 fulfiller for debt crisis — practical, non-judgmental financial help.

    10 curated entries. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_debt_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in DEBT_CRISIS_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in DEBT_CRISIS_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in DEBT_CRISIS_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Financial recovery is possible. One step at a time.",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "counseling" in tags:
        return "Professional guidance to see the full picture"
    if "legal" in tags:
        return "Know your rights — the law protects you"
    if "basic_needs" in tags:
        return "Basic needs come first — help is available"
    if "empowering" in tags:
        return "Take control of your financial future"
    if "bankruptcy" in tags:
        return "Understand all your options clearly"
    return "A practical step toward financial stability"
