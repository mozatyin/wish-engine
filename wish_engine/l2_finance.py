"""FinanceFulfiller — values-based financial direction recommendations.

15-entry curated catalog of financial topics. NOT specific products.
Core innovation: values -> financial direction mapping
(security->conservative, stimulation->growth, self-direction->entrepreneurial).
Multilingual keyword routing (EN/ZH/AR).
Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    Recommendation,
    ReminderOption,
)

# ── Finance Catalog (15 entries) ─────────────────────────────────────────────

FINANCE_CATALOG: list[dict] = [
    {
        "title": "Budgeting Basics",
        "description": "Track income and expenses — the foundation of financial health.",
        "category": "budgeting_basics",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "conservative", "quiet"],
        "values_match": ["security", "conformity"],
    },
    {
        "title": "Emergency Fund Guide",
        "description": "Build a safety net for unexpected expenses — peace of mind in 3-6 months.",
        "category": "emergency_fund",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "conservative", "calming", "quiet"],
        "values_match": ["security"],
    },
    {
        "title": "Smart Saving Habits",
        "description": "Automate savings, use the 50/30/20 rule, and watch your balance grow.",
        "category": "saving_habits",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "conservative", "quiet"],
        "values_match": ["security", "conformity"],
    },
    {
        "title": "Investing 101",
        "description": "Index funds, ETFs, and compound interest — start investing with confidence.",
        "category": "investing_101",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["growth", "practical", "quiet"],
        "values_match": ["stimulation", "self-direction"],
    },
    {
        "title": "Debt Management Strategy",
        "description": "Snowball or avalanche method — a clear plan to become debt-free.",
        "category": "debt_management",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "conservative", "quiet"],
        "values_match": ["security"],
    },
    {
        "title": "Side Income Ideas",
        "description": "Freelancing, tutoring, or creating — earn extra based on your skills.",
        "category": "side_income",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["entrepreneurial", "creative", "growth"],
        "values_match": ["self-direction", "stimulation"],
    },
    {
        "title": "Frugal Living Tips",
        "description": "Live well on less — smart substitutions and mindful spending.",
        "category": "frugal_living",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "conservative", "quiet"],
        "values_match": ["security", "universalism"],
    },
    {
        "title": "Retirement Planning Basics",
        "description": "Start early, contribute consistently — your future self will thank you.",
        "category": "retirement_planning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["conservative", "practical", "quiet"],
        "values_match": ["security", "tradition"],
    },
    {
        "title": "Insurance Basics",
        "description": "Health, life, and property insurance — understand what you actually need.",
        "category": "insurance_basics",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "conservative", "quiet"],
        "values_match": ["security"],
    },
    {
        "title": "Tax Optimization",
        "description": "Legal deductions, credits, and strategies — keep more of what you earn.",
        "category": "tax_optimization",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "quiet"],
        "values_match": ["self-direction", "security"],
    },
    {
        "title": "Financial Literacy Resources",
        "description": "Books, podcasts, and courses to build your money knowledge.",
        "category": "financial_literacy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "quiet", "growth"],
        "values_match": ["self-direction", "universalism"],
    },
    {
        "title": "Crypto Awareness",
        "description": "Understand blockchain, risks, and basics — education before speculation.",
        "category": "crypto_awareness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["growth", "creative", "quiet"],
        "values_match": ["stimulation", "self-direction"],
    },
    {
        "title": "Real Estate Basics",
        "description": "Renting vs buying, mortgages, and property investment fundamentals.",
        "category": "real_estate_basics",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "growth", "quiet"],
        "values_match": ["security", "self-direction"],
    },
    {
        "title": "Scholarship Finder Guide",
        "description": "Find grants, scholarships, and funding — education without the debt.",
        "category": "scholarship_finder",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "quiet"],
        "values_match": ["universalism", "self-direction"],
    },
    {
        "title": "Financial Wellbeing",
        "description": "Money and mental health — reduce financial stress with healthy money habits.",
        "category": "financial_wellbeing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "practical", "quiet"],
        "values_match": ["benevolence", "security"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

FINANCE_KEYWORDS: set[str] = {
    "理财", "finance", "money", "省钱", "投资", "存钱", "مال", "budget",
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates based on values and text preferences."""
    text_lower = wish_text.lower()
    top_values = detector_results.values.get("top_values", [])

    candidates: list[dict] = []
    for item in FINANCE_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0
        tags = set(item.get("tags", []))

        # Values matching
        item_values = set(item.get("values_match", []))
        matched_values = set(top_values) & item_values
        if matched_values:
            score_boost += 0.15 * len(matched_values)
            item_copy["relevance_reason"] = _values_reason(list(matched_values)[0])

        # Text hints
        if any(kw in text_lower for kw in ["save", "存钱", "saving", "省"]):
            if "conservative" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["invest", "投资", "grow", "增长"]):
            if "growth" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["side", "副业", "freelance", "额外收入"]):
            if "entrepreneurial" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["debt", "贷款", "还款", "دين"]):
            if item["category"] == "debt_management":
                score_boost += 0.3

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


def _values_reason(value: str) -> str:
    reasons = {
        "security": "A solid foundation for financial peace of mind",
        "stimulation": "Growth-oriented strategies for ambitious goals",
        "self-direction": "Take control of your financial future",
        "universalism": "Sustainable and socially responsible approaches",
        "benevolence": "Financial wellness for you and your loved ones",
        "tradition": "Time-tested financial wisdom",
        "conformity": "Proven and reliable financial practices",
    }
    return reasons.get(value, "Personalized financial guidance for you")


class FinanceFulfiller(L2Fulfiller):
    """L2 fulfiller for finance wishes — values-based financial direction.

    15-entry curated catalog. NOT specific products. Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:max_results]

        return [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "Personalized financial guidance for you"),
                score=c.get("_personality_score", 0.5),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "Personalized financial guidance for you"

        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=None,
            reminder_option=ReminderOption(
                text="Start your financial journey today?",
                delay_hours=24,
            ),
        )
