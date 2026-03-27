"""ExtremeWeatherFulfiller — local-compute extreme weather preparedness recommendation.

10-entry curated catalog of extreme weather shelters and safety tips. Zero LLM.
Emergency preparedness focus. Keyword matching (English/Chinese/Arabic) routes
wish text to relevant categories, then PersonalityFilter scores and ranks candidates.

Tags: shelter/cooling/heating/storm/safety.
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

# ── Extreme Weather Catalog (10 entries) ──────────────────────────────────────

EXTREME_WEATHER_CATALOG: list[dict] = [
    {
        "title": "Cooling Center",
        "description": "Public cooling centers during heatwaves — air-conditioned, free, and safe.",
        "category": "cooling_center",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["cooling", "shelter", "calming", "practical", "safe"],
    },
    {
        "title": "Heated Mall / Shelter",
        "description": "Warm indoor spaces during extreme cold — heated malls and public buildings.",
        "category": "heated_mall",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["heating", "shelter", "calming", "practical", "indoor"],
    },
    {
        "title": "Dust Storm Shelter",
        "description": "Enclosed spaces with filtered air during sandstorms and dust events.",
        "category": "dust_storm_shelter",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["storm", "shelter", "calming", "quiet", "safe"],
    },
    {
        "title": "Flood Safe Area",
        "description": "Elevated zones and emergency shelters during flooding — stay above water.",
        "category": "flood_safe_area",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["storm", "shelter", "calming", "practical", "safe"],
    },
    {
        "title": "Snowstorm Essentials",
        "description": "Emergency supplies, warm shelter, and road condition updates during blizzards.",
        "category": "snowstorm_essentials",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["storm", "shelter", "calming", "practical", "quiet"],
    },
    {
        "title": "Heatwave Swimming Spot",
        "description": "Pools, lakes, and splash pads open during extreme heat events.",
        "category": "heatwave_swimming",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["cooling", "outdoor", "calming", "exercise", "practical"],
    },
    {
        "title": "Sandstorm Indoor Venue",
        "description": "Sealed, air-conditioned venues to wait out sandstorms safely.",
        "category": "sandstorm_indoor",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["storm", "shelter", "calming", "quiet", "indoor"],
    },
    {
        "title": "Typhoon Preparation",
        "description": "Emergency supplies, evacuation routes, and safe shelter during typhoon season.",
        "category": "typhoon_prep",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["storm", "safety", "calming", "practical", "quiet"],
    },
    {
        "title": "Earthquake Safety Guide",
        "description": "Drop-cover-hold locations, structural safety, and aftershock prep.",
        "category": "earthquake_safety",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safety", "shelter", "calming", "practical", "quiet"],
    },
    {
        "title": "Extreme Cold Shelter",
        "description": "Heated emergency shelters and warming stations during polar vortex events.",
        "category": "extreme_cold_shelter",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["heating", "shelter", "calming", "practical", "safe"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

EXTREME_WEATHER_KEYWORDS: set[str] = {
    "极端天气", "extreme weather", "storm", "暴风", "عاصفة",
    "heat", "cold", "沙尘暴", "heatwave", "blizzard",
    "flood", "洪水", "台风", "typhoon", "إعصار",
    "earthquake", "地震", "زلزال", "sandstorm", "freezing",
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "cooling_center": ["heat", "heatwave", "hot", "热", "حر", "cooling"],
    "heated_mall": ["cold", "freezing", "冷", "بارد", "warm"],
    "dust_storm_shelter": ["dust", "sandstorm", "沙尘", "غبار"],
    "flood_safe_area": ["flood", "洪水", "فيضان", "water level"],
    "snowstorm_essentials": ["snow", "blizzard", "暴雪", "ثلج"],
    "heatwave_swimming": ["swim", "pool", "游泳", "سباحة", "heatwave"],
    "sandstorm_indoor": ["sandstorm", "沙尘暴", "عاصفة رملية"],
    "typhoon_prep": ["typhoon", "hurricane", "台风", "إعصار"],
    "earthquake_safety": ["earthquake", "地震", "زلزال", "tremor"],
    "extreme_cold_shelter": ["extreme cold", "polar", "极寒", "صقيع"],
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    for item in EXTREME_WEATHER_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.25

        # Emergency/urgency boost
        if any(kw in text_lower for kw in ["emergency", "urgent", "紧急", "طوارئ"]):
            if "safe" in item.get("tags", []) or "shelter" in item.get("tags", []):
                score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict) -> str:
    """Build a relevance reason for extreme weather recommendations."""
    reasons = {
        "cooling_center": "Cool, safe shelter during extreme heat",
        "heated_mall": "Warm shelter from the extreme cold",
        "dust_storm_shelter": "Protected space during dust storms",
        "flood_safe_area": "Elevated safe zone during flooding",
        "snowstorm_essentials": "Emergency supplies for blizzard conditions",
        "heatwave_swimming": "Cool down in the water during heatwaves",
        "sandstorm_indoor": "Sealed indoor space during sandstorms",
        "typhoon_prep": "Prepared and safe for typhoon conditions",
        "earthquake_safety": "Know where to shelter during tremors",
        "extreme_cold_shelter": "Warm emergency shelter in extreme cold",
    }
    return reasons.get(item["category"], "Weather safety recommendation")


class ExtremeWeatherFulfiller(L2Fulfiller):
    """L2 fulfiller for extreme weather preparedness wishes.

    10-entry curated catalog. Emergency preparedness focus.
    Tags: shelter/cooling/heating/storm/safety. Zero LLM.
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
                relevance_reason=c.get("relevance_reason", "Weather safety recommendation"),
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
            map_data=MapData(place_type="weather_shelter", radius_km=10.0),
            reminder_option=ReminderOption(
                text="Stay safe — check weather updates regularly!",
                delay_hours=2,
            ),
        )
