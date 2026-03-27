"""SeasonalWellnessFulfiller — culture-aware seasonal wellness recommendations.

12-entry curated catalog with cultural awareness for Chinese solar terms and
Islamic calendar. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Culture → Season Mapping ─────────────────────────────────────────────────

CULTURE_SEASON_MAP: dict[str, list[str]] = {
    "chinese": ["chinese_solar_terms", "spring_renewal", "autumn_harvest", "winter_warmth"],
    "mena": ["ramadan_fasting_tips", "dust_storm_care", "summer_heat_stress"],
    "south_asian": ["monsoon_mood", "summer_heat_stress", "hay_fever_season"],
}

# ── Seasonal Wellness Catalog (12 entries) ───────────────────────────────────

SEASONAL_WELLNESS_CATALOG: list[dict] = [
    {
        "title": "Spring Renewal Rituals",
        "description": "Detox, light exercise, and fresh foods — reset your body for spring.",
        "category": "spring_renewal",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["spring_renewal", "calming", "quiet", "practical"],
    },
    {
        "title": "Summer Hydration Guide",
        "description": "Stay cool and hydrated — electrolyte tips, cooling foods, and shade strategies.",
        "category": "summer_hydration",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["summer_hydration", "calming", "practical", "self-paced"],
    },
    {
        "title": "Autumn Harvest Nutrition",
        "description": "Seasonal superfoods — pumpkin, sweet potato, warming spices for immune support.",
        "category": "autumn_harvest",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["autumn_harvest", "calming", "practical", "traditional"],
    },
    {
        "title": "Winter Warmth & Comfort",
        "description": "Hot soups, warming teas, layering tips — stay cozy and healthy in winter.",
        "category": "winter_warmth",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["winter_warmth", "calming", "quiet", "practical", "traditional"],
    },
    {
        "title": "Ramadan Fasting Wellness Tips",
        "description": "Suhoor nutrition, hydration timing, and energy management during Ramadan.",
        "category": "ramadan_fasting_tips",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ramadan_fasting_tips", "calming", "traditional", "quiet"],
    },
    {
        "title": "Chinese Solar Terms Guide (二十四节气)",
        "description": "Follow the ancient 24 solar terms — seasonal foods, exercises, and lifestyle tips.",
        "category": "chinese_solar_terms",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["chinese_solar_terms", "calming", "traditional", "quiet", "theory"],
    },
    {
        "title": "Monsoon Mood Support",
        "description": "Combat humidity fatigue, mold prevention, and mood-lifting tips for rainy season.",
        "category": "monsoon_mood",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["monsoon_mood", "calming", "practical"],
    },
    {
        "title": "Dust Storm Self-Care",
        "description": "Protect your lungs and skin — indoor activities and air quality tips during dust season.",
        "category": "dust_storm_care",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dust_storm_care", "calming", "practical", "quiet"],
    },
    {
        "title": "Hay Fever Season Survival",
        "description": "Natural remedies, pollen tracking, and indoor alternatives during allergy season.",
        "category": "hay_fever_season",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["hay_fever_season", "calming", "practical", "self-paced"],
    },
    {
        "title": "Winter Blues Light Therapy",
        "description": "Beat seasonal affective disorder — light exposure, vitamin D, and cozy rituals.",
        "category": "winter_blues",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["winter_blues", "calming", "quiet", "self-paced"],
    },
    {
        "title": "Summer Heat Stress Relief",
        "description": "Cooling techniques, workout timing, and heat-safe outdoor tips.",
        "category": "summer_heat_stress",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["summer_heat_stress", "calming", "practical"],
    },
    {
        "title": "Holiday Stress Management",
        "description": "Boundaries, self-care routines, and mindful holiday planning.",
        "category": "holiday_stress",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["holiday_stress", "calming", "quiet", "self-paced"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_SEASONAL_KEYWORDS: dict[str, list[str]] = {
    "节气": ["chinese_solar_terms"],
    "二十四节气": ["chinese_solar_terms"],
    "solar term": ["chinese_solar_terms"],
    "seasonal": ["seasonal"],
    "养生": ["wellness"],
    "wellness": ["wellness"],
    "季节": ["seasonal"],
    "فصل": ["seasonal"],
    "season": ["seasonal"],
    "spring": ["spring_renewal"],
    "春": ["spring_renewal"],
    "summer": ["summer_hydration", "summer_heat_stress"],
    "夏": ["summer_hydration", "summer_heat_stress"],
    "autumn": ["autumn_harvest"],
    "秋": ["autumn_harvest"],
    "winter": ["winter_warmth", "winter_blues"],
    "冬": ["winter_warmth", "winter_blues"],
    "ramadan": ["ramadan_fasting_tips"],
    "رمضان": ["ramadan_fasting_tips"],
    "斋月": ["ramadan_fasting_tips"],
    "monsoon": ["monsoon_mood"],
    "雨季": ["monsoon_mood"],
    "dust storm": ["dust_storm_care"],
    "沙尘暴": ["dust_storm_care"],
    "allergy": ["hay_fever_season"],
    "过敏": ["hay_fever_season"],
    "holiday stress": ["holiday_stress"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _SEASONAL_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")
    reason_map = {
        "spring_renewal": "Fresh start — align your body with the season",
        "summer_hydration": "Stay cool and energized in the heat",
        "autumn_harvest": "Nourish yourself with seasonal superfoods",
        "winter_warmth": "Stay warm, healthy, and cozy",
        "ramadan_fasting_tips": "Healthy fasting guidance for Ramadan",
        "chinese_solar_terms": "Ancient wisdom for modern wellness",
        "monsoon_mood": "Stay upbeat despite the rain",
        "dust_storm_care": "Protect yourself during dust season",
        "hay_fever_season": "Breathe easier this allergy season",
        "winter_blues": "Light and warmth to beat the winter blues",
        "summer_heat_stress": "Cool strategies for hot days",
        "holiday_stress": "Keep your peace during the holidays",
    }
    return reason_map.get(category, "Seasonal wellness tailored for you")


class SeasonalWellnessFulfiller(L2Fulfiller):
    """L2 fulfiller for seasonal wellness wishes — culture-aware recommendations.

    Uses keyword matching + cultural context to select from 12-entry catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Filter catalog
        if matched_categories:
            tag_set = set(matched_categories)
            candidates = [
                dict(item) for item in SEASONAL_WELLNESS_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in SEASONAL_WELLNESS_CATALOG]

        # 3. Fallback
        if not candidates:
            candidates = [dict(item) for item in SEASONAL_WELLNESS_CATALOG]

        # 4. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        # 5. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New seasonal tips available — check back next week!",
                delay_hours=168,
            ),
        )
