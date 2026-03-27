"""AccessibilityFulfiller — local-compute accessible place recommendation.

12-entry curated catalog of accessibility-focused locations. Zero LLM.
Keyword matching (English/Chinese/Arabic) routes wish text to relevant
categories, then PersonalityFilter scores and ranks candidates.

Tags: wheelchair/sensory/hearing/visual/inclusive.
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

# ── Accessibility Catalog (12 entries) ────────────────────────────────────────

ACCESSIBILITY_CATALOG: list[dict] = [
    {
        "title": "Wheelchair-Accessible Restaurant",
        "description": "Fully accessible dining with ramps, wide aisles, and adapted restrooms.",
        "category": "wheelchair_restaurant",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["wheelchair", "dining", "inclusive", "calming", "practical"],
    },
    {
        "title": "Wheelchair-Accessible Park",
        "description": "Paved paths, accessible play areas, and barrier-free green spaces.",
        "category": "wheelchair_park",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wheelchair", "outdoor", "quiet", "calming", "nature"],
    },
    {
        "title": "Elevator-Access Building",
        "description": "Buildings with reliable elevators and step-free access throughout.",
        "category": "elevator_access",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wheelchair", "indoor", "practical", "calming", "quiet"],
    },
    {
        "title": "Braille Menu Restaurant",
        "description": "Restaurants offering braille menus for visually impaired guests.",
        "category": "braille_menu",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["visual", "dining", "inclusive", "calming", "practical"],
    },
    {
        "title": "Hearing Loop Venue",
        "description": "Venues equipped with hearing induction loops for hearing aid users.",
        "category": "hearing_loop",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["hearing", "indoor", "inclusive", "calming", "quiet"],
    },
    {
        "title": "Sensory-Friendly Space",
        "description": "Low-stimulation environments with dimmed lights and reduced noise.",
        "category": "sensory_friendly",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sensory", "quiet", "calming", "inclusive", "safe"],
    },
    {
        "title": "Autism-Friendly Venue",
        "description": "Spaces designed with autism-friendly hours, quiet zones, and visual guides.",
        "category": "autism_friendly",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sensory", "quiet", "calming", "inclusive", "structured"],
    },
    {
        "title": "Guide Dog Welcome Spot",
        "description": "Businesses that warmly welcome guide dogs and service animals.",
        "category": "guide_dog_welcome",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["visual", "inclusive", "calming", "quiet", "practical"],
    },
    {
        "title": "Accessible Beach",
        "description": "Beaches with boardwalks, beach wheelchairs, and accessible changing rooms.",
        "category": "accessible_beach",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["wheelchair", "outdoor", "calming", "nature", "inclusive"],
    },
    {
        "title": "Accessible Hiking Trail",
        "description": "Well-graded, paved trails suitable for wheelchairs and mobility aids.",
        "category": "accessible_trail",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wheelchair", "outdoor", "quiet", "calming", "nature"],
    },
    {
        "title": "Accessible Public Transport",
        "description": "Transit stations with elevators, ramps, tactile paving, and audio announcements.",
        "category": "accessible_transport",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["wheelchair", "practical", "inclusive", "transit", "calming"],
    },
    {
        "title": "Accessible Hotel",
        "description": "Hotels with adapted rooms, roll-in showers, and full barrier-free access.",
        "category": "accessible_hotel",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wheelchair", "indoor", "calming", "quiet", "inclusive"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

ACCESSIBILITY_KEYWORDS: set[str] = {
    "无障碍", "accessible", "wheelchair", "disability", "إعاقة",
    "barrier-free", "残疾", "轮椅", "كرسي متحرك", "ramp",
    "braille", "hearing loop", "sensory", "guide dog", "导盲犬",
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "wheelchair_restaurant": ["restaurant", "dining", "餐厅", "مطعم"],
    "wheelchair_park": ["park", "公园", "حديقة"],
    "elevator_access": ["elevator", "电梯", "مصعد"],
    "braille_menu": ["braille", "盲文", "بريل"],
    "hearing_loop": ["hearing", "听力", "سمع", "hearing aid"],
    "sensory_friendly": ["sensory", "感官", "حسي"],
    "autism_friendly": ["autism", "自闭", "توحد"],
    "guide_dog_welcome": ["guide dog", "导盲犬", "كلب مرشد", "service animal"],
    "accessible_beach": ["beach", "海滩", "شاطئ"],
    "accessible_trail": ["trail", "hiking", "步道", "ممشى"],
    "accessible_transport": ["transport", "transit", "交通", "نقل"],
    "accessible_hotel": ["hotel", "酒店", "فندق"],
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    for item in ACCESSIBILITY_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        # Wheelchair-specific boost
        if any(kw in text_lower for kw in ["wheelchair", "轮椅", "كرسي متحرك", "ramp"]):
            if "wheelchair" in item.get("tags", []):
                score_boost += 0.15

        # Sensory-specific boost
        if any(kw in text_lower for kw in ["sensory", "autism", "感官", "自闭"]):
            if "sensory" in item.get("tags", []):
                score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict) -> str:
    """Build a relevance reason for accessibility recommendations."""
    reasons = {
        "wheelchair_restaurant": "Fully accessible dining experience",
        "wheelchair_park": "Barrier-free green space for everyone",
        "elevator_access": "Step-free access guaranteed",
        "braille_menu": "Dining with braille menu available",
        "hearing_loop": "Hearing-loop equipped for comfortable listening",
        "sensory_friendly": "Low-stimulation safe environment",
        "autism_friendly": "Designed with neurodiversity in mind",
        "guide_dog_welcome": "Service animals warmly welcomed",
        "accessible_beach": "Beach fun without barriers",
        "accessible_trail": "Nature trails accessible for all",
        "accessible_transport": "Barrier-free public transit nearby",
        "accessible_hotel": "Comfortable stay with full accessibility",
    }
    return reasons.get(item["category"], "An accessible place nearby")


class AccessibilityFulfiller(L2Fulfiller):
    """L2 fulfiller for accessibility-focused wishes.

    12-entry curated catalog. Tags: wheelchair/sensory/hearing/visual/inclusive.
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
                relevance_reason=c.get("relevance_reason", "An accessible place nearby"),
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
            map_data=MapData(place_type="accessible_place", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Found an accessible spot? Save it for later!",
                delay_hours=4,
            ),
        )
