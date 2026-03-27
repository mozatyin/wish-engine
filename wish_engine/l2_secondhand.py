"""SecondhandFulfiller — personality-based secondhand item exchange matching.

20-entry curated catalog of item categories. Core innovation: values -> item style
mapping (universalism->eco-friendly, security->practical, aesthetics->curated).
Multilingual keyword routing (EN/ZH/AR).
Zero LLM.
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

# ── Secondhand Item Catalog (20 entries) ─────────────────────────────────────

SECONDHAND_CATALOG: list[dict] = [
    {
        "title": "Pre-loved Books Exchange",
        "description": "Trade your finished reads for new adventures — every book deserves a second life.",
        "category": "books",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["eco-friendly", "practical", "quiet", "curated"],
        "values_match": ["universalism", "self-direction"],
    },
    {
        "title": "Refurbished Electronics",
        "description": "Quality-checked phones, laptops, and gadgets at a fraction of the price.",
        "category": "electronics",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "eco-friendly"],
        "values_match": ["security", "universalism"],
    },
    {
        "title": "Vintage Clothing Swap",
        "description": "Curated secondhand fashion — unique pieces with stories to tell.",
        "category": "clothing",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["curated", "social", "eco-friendly", "creative"],
        "values_match": ["universalism", "stimulation"],
    },
    {
        "title": "Furniture Rehome",
        "description": "Give your furniture a new home or find quality pieces for yours.",
        "category": "furniture",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "eco-friendly"],
        "values_match": ["security", "universalism"],
    },
    {
        "title": "Sports Gear Exchange",
        "description": "Swap sports equipment — try new activities without the full price tag.",
        "category": "sports_gear",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "social", "eco-friendly"],
        "values_match": ["stimulation", "universalism"],
    },
    {
        "title": "Musical Instruments Marketplace",
        "description": "Pre-owned guitars, keyboards, and more — music should be accessible.",
        "category": "musical_instruments",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "curated", "eco-friendly"],
        "values_match": ["self-direction", "stimulation"],
    },
    {
        "title": "Art Supplies Swap",
        "description": "Paints, canvases, and brushes looking for their next artist.",
        "category": "art_supplies",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "eco-friendly", "curated"],
        "values_match": ["self-direction", "universalism"],
    },
    {
        "title": "Kitchen & Cookware Exchange",
        "description": "Quality pots, pans, and gadgets — upgrade your kitchen sustainably.",
        "category": "kitchen",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "eco-friendly"],
        "values_match": ["security", "benevolence"],
    },
    {
        "title": "Baby Items Circle",
        "description": "Gently used baby gear, clothes, and toys — kids grow fast, items don't have to go to waste.",
        "category": "baby_items",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "eco-friendly", "social"],
        "values_match": ["benevolence", "security"],
    },
    {
        "title": "Plant Adoption Corner",
        "description": "Give away cuttings or adopt a new green friend — grow your indoor jungle.",
        "category": "plants",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["eco-friendly", "calming", "creative"],
        "values_match": ["universalism", "benevolence"],
    },
    {
        "title": "Vinyl Records Swap",
        "description": "Trade records and discover new sounds — the analog music revival.",
        "category": "vinyl_records",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["curated", "creative", "eco-friendly"],
        "values_match": ["stimulation", "self-direction"],
    },
    {
        "title": "Camera & Photography Gear",
        "description": "Pre-owned cameras, lenses, and accessories — capture moments affordably.",
        "category": "cameras",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "curated", "practical"],
        "values_match": ["self-direction", "stimulation"],
    },
    {
        "title": "Board Games Library",
        "description": "Swap and borrow board games — game night doesn't need a big budget.",
        "category": "board_games",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "practical", "eco-friendly"],
        "values_match": ["benevolence", "stimulation"],
    },
    {
        "title": "Craft Supplies Exchange",
        "description": "Yarn, fabric, beads, and more — crafters sharing with crafters.",
        "category": "craft_supplies",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "eco-friendly", "social"],
        "values_match": ["self-direction", "universalism"],
    },
    {
        "title": "Outdoor Gear Swap",
        "description": "Tents, backpacks, and hiking boots — adventure gear at a fraction of the cost.",
        "category": "outdoor_gear",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "eco-friendly", "social"],
        "values_match": ["stimulation", "universalism"],
    },
    {
        "title": "Language Learning Materials",
        "description": "Textbooks, flashcards, and audio courses — pass on the gift of language.",
        "category": "language_materials",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "eco-friendly", "quiet"],
        "values_match": ["self-direction", "universalism"],
    },
    {
        "title": "Home Decor Exchange",
        "description": "Curated home pieces looking for new walls and shelves — refresh your space.",
        "category": "home_decor",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["curated", "eco-friendly", "creative"],
        "values_match": ["self-direction", "universalism"],
    },
    {
        "title": "Tools & Hardware Share",
        "description": "Borrow or swap power tools and hardware — no need to buy for one-time use.",
        "category": "tools",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "eco-friendly"],
        "values_match": ["security", "universalism"],
    },
    {
        "title": "Yoga Mats & Fitness Gear",
        "description": "Pre-owned yoga mats, resistance bands, and weights — wellness on a budget.",
        "category": "yoga_mats",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "eco-friendly", "calming"],
        "values_match": ["universalism", "benevolence"],
    },
    {
        "title": "Bicycle Exchange",
        "description": "Pre-owned bikes for commuting or weekend rides — pedal forward sustainably.",
        "category": "bicycles",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "eco-friendly"],
        "values_match": ["universalism", "stimulation"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

SECONDHAND_KEYWORDS: set[str] = {
    "二手", "闲置", "exchange", "swap", "旧物", "secondhand", "مستعمل",
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates based on values and text preferences."""
    text_lower = wish_text.lower()
    top_values = detector_results.values.get("top_values", [])

    candidates: list[dict] = []
    for item in SECONDHAND_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Values matching
        item_values = set(item.get("values_match", []))
        matched_values = set(top_values) & item_values
        if matched_values:
            score_boost += 0.15 * len(matched_values)
            item_copy["relevance_reason"] = _values_reason(list(matched_values)[0])

        # Text-based category hints
        category = item["category"]
        if category in text_lower or any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "books": ["book", "书", "كتاب", "读"],
    "electronics": ["电子", "手机", "laptop", "phone"],
    "clothing": ["衣服", "clothes", "fashion", "ملابس"],
    "furniture": ["家具", "desk", "chair", "أثاث"],
    "sports_gear": ["运动", "sports", "رياضة"],
    "musical_instruments": ["乐器", "guitar", "piano", "موسيقى"],
    "plants": ["植物", "plant", "نبات"],
    "bicycles": ["自行车", "bike", "دراجة"],
}


def _values_reason(value: str) -> str:
    reasons = {
        "universalism": "Sustainable and eco-friendly — aligned with your values",
        "security": "Practical and reliable — a smart choice",
        "self-direction": "Unique and curated — express your individuality",
        "stimulation": "Something new and exciting to discover",
        "benevolence": "Share and care — giving items a second life",
    }
    return reasons.get(value, "A great match for your personality")


class SecondhandFulfiller(L2Fulfiller):
    """L2 fulfiller for secondhand item exchange — values-based matching.

    20-entry curated catalog. Zero LLM.
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
                relevance_reason=c.get("relevance_reason", "A great match for your personality"),
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
                c["relevance_reason"] = "A great match for your personality"

        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=None,
            reminder_option=ReminderOption(
                text="Check out these secondhand items?",
                delay_hours=12,
            ),
        )
