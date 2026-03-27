"""HousingFulfiller — personality-matched housing neighborhoods and roommate compatibility.

15-entry curated catalog of neighborhood types. Core innovation: MBTI + values ->
neighborhood matching (I->quiet_residential, E->nightlife/artsy,
security->family_friendly, stimulation->nightlife, tradition->historic).
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

# ── Housing Neighborhood Catalog (15 entries) ────────────────────────────────

HOUSING_CATALOG: list[dict] = [
    {
        "title": "Quiet Residential Area",
        "description": "Tree-lined streets, low traffic, and peaceful nights — your sanctuary.",
        "category": "quiet_residential",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "calming", "practical"],
        "values_match": ["security"],
    },
    {
        "title": "Artsy District",
        "description": "Galleries, studios, and indie cafes — creativity around every corner.",
        "category": "artsy_district",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["creative", "social"],
        "values_match": ["self-direction", "stimulation"],
    },
    {
        "title": "Student Quarter",
        "description": "Affordable, lively, and close to campus — perfect for student life.",
        "category": "student_quarter",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "practical"],
        "values_match": ["stimulation", "universalism"],
    },
    {
        "title": "Tech Hub Area",
        "description": "Co-living with founders, fast wifi, and startup energy.",
        "category": "tech_hub_area",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "practical"],
        "values_match": ["self-direction", "stimulation"],
    },
    {
        "title": "Family-Friendly Neighborhood",
        "description": "Parks, schools, and safe sidewalks — ideal for families.",
        "category": "family_friendly",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["quiet", "calming", "practical", "traditional"],
        "values_match": ["security", "benevolence", "tradition"],
    },
    {
        "title": "Nightlife District",
        "description": "Bars, clubs, and late-night eats — the city that never sleeps.",
        "category": "nightlife_district",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["social"],
        "values_match": ["stimulation"],
    },
    {
        "title": "Nature-Adjacent Area",
        "description": "Trails, parks, and fresh air minutes from your door — urban meets nature.",
        "category": "nature_adjacent",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "calming", "outdoor"],
        "values_match": ["universalism", "self-direction"],
    },
    {
        "title": "Cultural District",
        "description": "Museums, theaters, and heritage sites — live among history and art.",
        "category": "cultural_district",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "traditional", "cultural"],
        "values_match": ["tradition", "universalism"],
    },
    {
        "title": "Affordable Area",
        "description": "Budget-friendly rents with good public transit — stretch your dollar further.",
        "category": "affordable_area",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical"],
        "values_match": ["security", "conformity"],
    },
    {
        "title": "Expat Community",
        "description": "International neighbors, multilingual shops, and global food — home away from home.",
        "category": "expat_community",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "practical"],
        "values_match": ["universalism", "stimulation"],
    },
    {
        "title": "Historic Center",
        "description": "Cobblestone streets, old architecture, and local charm — timeless living.",
        "category": "historic_center",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["traditional", "cultural", "creative"],
        "values_match": ["tradition", "universalism"],
    },
    {
        "title": "Modern Development",
        "description": "New buildings, smart home features, and modern amenities — fresh and efficient.",
        "category": "modern_development",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "quiet"],
        "values_match": ["self-direction", "security"],
    },
    {
        "title": "Walkable Neighborhood",
        "description": "Everything within walking distance — groceries, cafes, and parks.",
        "category": "walkable_area",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "social"],
        "values_match": ["universalism", "security"],
    },
    {
        "title": "Transit Hub Area",
        "description": "Metro, bus, and train at your doorstep — commute with ease.",
        "category": "transit_hub",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical"],
        "values_match": ["security", "conformity"],
    },
    {
        "title": "Cozy Suburban Area",
        "description": "Spacious homes, gardens, and a slower pace — suburban comfort.",
        "category": "cozy_suburban",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "calming", "practical", "traditional"],
        "values_match": ["security", "tradition", "benevolence"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

HOUSING_KEYWORDS: set[str] = {
    "租房", "housing", "合租", "roommate", "neighborhood", "搬家", "سكن",
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates based on MBTI, values, and text preferences."""
    text_lower = wish_text.lower()
    mbti = detector_results.mbti
    top_values = detector_results.values.get("top_values", [])

    candidates: list[dict] = []
    for item in HOUSING_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0
        tags = set(item.get("tags", []))

        # MBTI matching
        mbti_type = mbti.get("type", "")
        if len(mbti_type) == 4:
            if mbti_type[0] == "I" and "quiet" in tags:
                score_boost += 0.2
                item_copy["relevance_reason"] = "A peaceful space that matches your introverted nature"
            elif mbti_type[0] == "E" and "social" in tags:
                score_boost += 0.2
                item_copy["relevance_reason"] = "A vibrant area perfect for your social energy"

        # Values matching
        item_values = set(item.get("values_match", []))
        matched_values = set(top_values) & item_values
        if matched_values:
            score_boost += 0.15 * len(matched_values)
            if "relevance_reason" not in item_copy:
                item_copy["relevance_reason"] = _values_reason(list(matched_values)[0])

        # Text preference hints
        if any(kw in text_lower for kw in ["quiet", "安静", "peaceful", "هادئ"]):
            if "quiet" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["cheap", "便宜", "affordable", "رخيص"]):
            if "practical" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["family", "家庭", "عائلة", "kids"]):
            if "traditional" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["roommate", "合租", "شريك"]):
            if "social" in tags:
                score_boost += 0.1

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


def _values_reason(value: str) -> str:
    reasons = {
        "security": "A safe and stable neighborhood for peace of mind",
        "stimulation": "An exciting area full of energy and activity",
        "self-direction": "A neighborhood that supports your independent lifestyle",
        "tradition": "A place with character, history, and community roots",
        "universalism": "A diverse and inclusive neighborhood",
        "benevolence": "A caring community where neighbors look out for each other",
        "conformity": "A well-organized area with clear community standards",
    }
    return reasons.get(value, "A neighborhood that matches your lifestyle")


class HousingFulfiller(L2Fulfiller):
    """L2 fulfiller for housing wishes — personality-matched neighborhoods.

    15-entry curated catalog. Zero LLM.
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
                relevance_reason=c.get("relevance_reason", "A neighborhood that matches your lifestyle"),
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
                c["relevance_reason"] = "A neighborhood that matches your lifestyle"

        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="neighborhood", radius_km=10.0),
            reminder_option=ReminderOption(
                text="Explore this neighborhood this weekend?",
                delay_hours=48,
            ),
        )
