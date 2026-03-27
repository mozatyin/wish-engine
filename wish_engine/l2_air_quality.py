"""AirQualityFulfiller — local-compute air quality recommendation.

10-entry curated catalog of air-quality-aware locations and tips. Zero LLM.
Keyword matching (English/Chinese/Arabic) routes wish text to relevant
categories, then PersonalityFilter scores and ranks candidates.

Tags: clean-air/indoor/outdoor/exercise/alert.
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

# ── Air Quality Catalog (10 entries) ──────────────────────────────────────────

AIR_QUALITY_CATALOG: list[dict] = [
    {
        "title": "Clean Air Park",
        "description": "Parks with verified low PM2.5 levels — breathe easy outdoors.",
        "category": "clean_air_park",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["clean-air", "outdoor", "quiet", "calming", "nature"],
    },
    {
        "title": "Indoor Air-Purified Space",
        "description": "HEPA-filtered indoor venues — cafes, libraries, malls with clean air.",
        "category": "indoor_air_purified",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["clean-air", "indoor", "quiet", "calming", "practical"],
    },
    {
        "title": "Mountain Air Retreat",
        "description": "High-altitude destinations with crisp, pure mountain air.",
        "category": "mountain_air",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["clean-air", "outdoor", "quiet", "calming", "nature"],
    },
    {
        "title": "Seaside Air Spot",
        "description": "Coastal locations with fresh sea breezes and clean ocean air.",
        "category": "seaside_air",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["clean-air", "outdoor", "calming", "nature", "water"],
    },
    {
        "title": "Forest Air Bath",
        "description": "Forest bathing spots with phytoncide-rich air — nature's air purifier.",
        "category": "forest_air",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["clean-air", "outdoor", "quiet", "calming", "nature"],
    },
    {
        "title": "Air Quality Alert",
        "description": "Real-time AQI monitoring — know when to stay indoors or go out.",
        "category": "air_quality_alert",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["alert", "practical", "calming", "quiet", "digital"],
    },
    {
        "title": "Pollution Avoidance Route",
        "description": "Low-pollution walking and cycling routes that avoid busy roads.",
        "category": "pollution_avoidance",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["clean-air", "outdoor", "exercise", "calming", "practical"],
    },
    {
        "title": "Indoor Exercise Alternative",
        "description": "Gyms and indoor sports when outdoor air quality is poor.",
        "category": "indoor_exercise_alt",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["indoor", "exercise", "practical", "calming", "clean-air"],
    },
    {
        "title": "Mask Reminder",
        "description": "Smart mask reminders based on AQI levels — protect your lungs.",
        "category": "mask_reminder",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["alert", "practical", "calming", "quiet", "digital"],
    },
    {
        "title": "Air Purifier Cafe",
        "description": "Cafes with professional-grade air purifiers — coffee with clean air.",
        "category": "air_purifier_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["clean-air", "indoor", "quiet", "calming", "cafe"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

AIR_QUALITY_KEYWORDS: set[str] = {
    "空气", "air quality", "PM2.5", "pollution", "雾霾", "جودة الهواء",
    "pm2.5", "aqi", "空气质量", "تلوث", "clean air", "smog",
    "dust", "灰尘", "غبار",
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "clean_air_park": ["park", "公园", "حديقة", "outdoor"],
    "indoor_air_purified": ["indoor", "purifier", "室内", "净化"],
    "mountain_air": ["mountain", "山", "جبل", "altitude"],
    "seaside_air": ["sea", "ocean", "海", "بحر", "coast"],
    "forest_air": ["forest", "森林", "غابة", "树林"],
    "air_quality_alert": ["alert", "aqi", "预警", "تنبيه", "monitor"],
    "pollution_avoidance": ["route", "walk", "cycle", "路线", "طريق"],
    "indoor_exercise_alt": ["exercise", "gym", "运动", "رياضة"],
    "mask_reminder": ["mask", "口罩", "كمامة", "protect"],
    "air_purifier_cafe": ["cafe", "coffee", "咖啡", "قهوة"],
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    for item in AIR_QUALITY_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        # PM2.5 / pollution concern boost
        if any(kw in text_lower for kw in ["pm2.5", "pollution", "雾霾", "smog", "تلوث"]):
            if "clean-air" in item.get("tags", []) or "alert" in item.get("tags", []):
                score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict) -> str:
    """Build a relevance reason for air quality recommendations."""
    reasons = {
        "clean_air_park": "Verified clean air for outdoor enjoyment",
        "indoor_air_purified": "HEPA-filtered indoor space for bad air days",
        "mountain_air": "Crisp mountain air far from pollution",
        "seaside_air": "Fresh ocean breeze and clean coastal air",
        "forest_air": "Nature's own air purifier — forest bathing",
        "air_quality_alert": "Stay informed about current air quality",
        "pollution_avoidance": "Low-pollution route for healthier walks",
        "indoor_exercise_alt": "Stay active indoors when air is poor",
        "mask_reminder": "Protect your lungs on high-AQI days",
        "air_purifier_cafe": "Clean air and coffee in one spot",
    }
    return reasons.get(item["category"], "Air quality aware recommendation")


class AirQualityFulfiller(L2Fulfiller):
    """L2 fulfiller for air quality wishes.

    10-entry curated catalog. Tags: clean-air/indoor/outdoor/exercise/alert.
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
                relevance_reason=c.get("relevance_reason", "Air quality aware recommendation"),
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
            map_data=MapData(place_type="air_quality", radius_km=10.0),
            reminder_option=ReminderOption(
                text="Check air quality again tomorrow?",
                delay_hours=12,
            ),
        )
