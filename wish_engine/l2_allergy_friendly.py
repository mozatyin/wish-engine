"""AllergyFriendlyFulfiller — local-compute allergy-safe dining recommendation.

12-entry curated catalog of allergy-friendly and dietary-restriction places. Zero LLM.
Keyword matching (English/Chinese/Arabic) routes wish text to relevant
categories, then PersonalityFilter scores and ranks candidates.

Tags: gluten-free/nut-free/dairy-free/vegan/halal/kosher.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
)

# ── Allergy-Friendly Catalog (12 entries) ─────────────────────────────────────

ALLERGY_CATALOG: list[dict] = [
    {
        "title": "Gluten-Free Restaurant",
        "description": "Dedicated gluten-free kitchen — safe for celiac and gluten-sensitive diners.",
        "category": "gluten_free_restaurant",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["gluten-free", "dining", "celiac", "calming", "safe"],
    },
    {
        "title": "Nut-Free Bakery",
        "description": "A bakery that guarantees zero nut contamination — safe treats for all.",
        "category": "nut_free_bakery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nut-free", "bakery", "calming", "quiet", "safe"],
    },
    {
        "title": "Dairy-Free Cafe",
        "description": "All plant-based milks and dairy-free treats — no cross-contamination.",
        "category": "dairy_free_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dairy-free", "cafe", "calming", "quiet", "safe"],
    },
    {
        "title": "Vegan Restaurant",
        "description": "100% plant-based menu — naturally free of dairy, eggs, and most allergens.",
        "category": "vegan_restaurant",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["vegan", "dining", "plant-based", "calming", "safe"],
    },
    {
        "title": "Halal-Certified Restaurant",
        "description": "Certified halal kitchen — trusted and transparent preparation.",
        "category": "halal_certified",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "dining", "certified", "calming", "traditional"],
    },
    {
        "title": "Kosher Restaurant",
        "description": "Strictly kosher-certified dining with supervised preparation.",
        "category": "kosher_restaurant",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["kosher", "dining", "certified", "calming", "traditional"],
    },
    {
        "title": "Organic Market",
        "description": "Fresh organic produce with clear labeling — know exactly what you eat.",
        "category": "organic_market",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["organic", "market", "calming", "quiet", "practical"],
    },
    {
        "title": "Allergen-Aware Restaurant",
        "description": "Staff trained in allergen awareness — every dish labeled for top 14 allergens.",
        "category": "allergen_aware_restaurant",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["allergen-aware", "dining", "safe", "calming", "inclusive"],
    },
    {
        "title": "Celiac-Friendly Eatery",
        "description": "Specializing in celiac-safe cuisine with dedicated prep surfaces.",
        "category": "celiac_friendly",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["gluten-free", "celiac", "dining", "calming", "safe"],
    },
    {
        "title": "Egg-Free Bakery",
        "description": "Delicious baked goods made without eggs — perfect for egg allergy sufferers.",
        "category": "egg_free_bakery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["egg-free", "bakery", "calming", "quiet", "safe"],
    },
    {
        "title": "Soy-Free Kitchen",
        "description": "Soy-free menu options with careful ingredient sourcing.",
        "category": "soy_free",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["soy-free", "dining", "calming", "safe", "practical"],
    },
    {
        "title": "Shellfish-Free Restaurant",
        "description": "No shellfish on premises — zero risk of cross-contamination.",
        "category": "shellfish_free",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["shellfish-free", "dining", "calming", "safe", "practical"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

ALLERGY_KEYWORDS: set[str] = {
    "过敏", "allergy", "gluten free", "素食", "vegan", "حساسية",
    "nut free", "dairy free", "halal", "kosher", "celiac",
    "食物过敏", "allergen", "乳糖", "lactose", "无麸质",
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "gluten_free_restaurant": ["gluten", "gluten free", "无麸质", "غلوتين"],
    "nut_free_bakery": ["nut", "nut free", "坚果", "مكسرات"],
    "dairy_free_cafe": ["dairy", "dairy free", "乳制品", "lactose", "حليب"],
    "vegan_restaurant": ["vegan", "plant-based", "素食", "نباتي"],
    "halal_certified": ["halal", "清真", "حلال"],
    "kosher_restaurant": ["kosher", "犹太", "كوشر"],
    "organic_market": ["organic", "有机", "عضوي"],
    "allergen_aware_restaurant": ["allergen", "过敏原", "مسببات الحساسية"],
    "celiac_friendly": ["celiac", "乳糜泻", "سيلياك"],
    "egg_free_bakery": ["egg free", "无蛋", "بدون بيض"],
    "soy_free": ["soy free", "无大豆", "بدون صويا"],
    "shellfish_free": ["shellfish", "贝类", "محار"],
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    for item in ALLERGY_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.25

        # General allergy awareness boost
        if any(kw in text_lower for kw in ["allergy", "过敏", "حساسية", "allergen"]):
            if "safe" in item.get("tags", []):
                score_boost += 0.1

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict) -> str:
    """Build a relevance reason for allergy-friendly recommendations."""
    reasons = {
        "gluten_free_restaurant": "Safe dining for gluten sensitivity",
        "nut_free_bakery": "Nut-free baked goods you can trust",
        "dairy_free_cafe": "Dairy-free drinks and treats",
        "vegan_restaurant": "100% plant-based and allergen-friendly",
        "halal_certified": "Certified halal — trusted preparation",
        "kosher_restaurant": "Strictly kosher-certified dining",
        "organic_market": "Clean, clearly labeled organic produce",
        "allergen_aware_restaurant": "Top 14 allergens labeled on every dish",
        "celiac_friendly": "Celiac-safe with dedicated prep surfaces",
        "egg_free_bakery": "Egg-free baking done right",
        "soy_free": "Soy-free menu with careful sourcing",
        "shellfish_free": "Zero shellfish risk guaranteed",
    }
    return reasons.get(item["category"], "An allergy-friendly option nearby")


class AllergyFriendlyFulfiller(L2Fulfiller):
    """L2 fulfiller for allergy-friendly dining wishes.

    12-entry curated catalog. Tags: gluten-free/nut-free/dairy-free/vegan/halal/kosher.
    Zero LLM.
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
                relevance_reason=c.get("relevance_reason", "An allergy-friendly option nearby"),
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
        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="allergy_friendly", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Save this allergy-safe spot for next time!",
                delay_hours=4,
            ),
        )
