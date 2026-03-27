"""SeasonalActivityFulfiller — location + season-aware activity recommendations.

15-type curated catalog of seasonal activities with season-based routing. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Season → Activity Mapping ────────────────────────────────────────────────

SEASON_ACTIVITY_MAP: dict[str, list[str]] = {
    "spring": ["spring_picnic", "cherry_blossom_viewing", "spring_gardening", "spring_cleaning"],
    "summer": ["summer_swimming", "beach_day", "summer_camping", "summer_road_trip"],
    "autumn": ["autumn_hiking", "leaf_peeping", "autumn_harvest_festival", "autumn_photography"],
    "winter": ["winter_hot_chocolate", "ice_skating", "winter_market"],
}

# ── Seasonal Activity Catalog (15 entries) ───────────────────────────────────

SEASONAL_ACTIVITY_CATALOG: list[dict] = [
    {
        "title": "Spring Picnic in the Park",
        "description": "Pack a basket and enjoy the first warm days — flowers, sunshine, and fresh air.",
        "category": "spring_picnic",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["spring_picnic", "calming", "social", "outdoor"],
    },
    {
        "title": "Cherry Blossom Viewing",
        "description": "Hanami-style blossom viewing — bring a blanket and enjoy the pink canopy.",
        "category": "cherry_blossom_viewing",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["cherry_blossom_viewing", "calming", "traditional", "outdoor"],
    },
    {
        "title": "Summer Swimming Spots",
        "description": "Natural pools, lakes, and ocean beaches — the best places to cool off.",
        "category": "summer_swimming",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["summer_swimming", "social", "adventure", "outdoor"],
    },
    {
        "title": "Beach Day Essentials",
        "description": "Sun, sand, and waves — a curated beach day with all the tips you need.",
        "category": "beach_day",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["beach_day", "social", "adventure", "outdoor"],
    },
    {
        "title": "Autumn Hiking Trails",
        "description": "Golden trails through colorful forests — the best season for hiking.",
        "category": "autumn_hiking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["autumn_hiking", "quiet", "calming", "outdoor", "self-paced"],
    },
    {
        "title": "Leaf Peeping Road Trip",
        "description": "Chase the fall colors — scenic drives through peak foliage areas.",
        "category": "leaf_peeping",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["leaf_peeping", "calming", "outdoor", "adventure"],
    },
    {
        "title": "Winter Hot Chocolate Crawl",
        "description": "The best hot chocolate spots in town — cozy up with cocoa and marshmallows.",
        "category": "winter_hot_chocolate",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["winter_hot_chocolate", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Ice Skating Rink",
        "description": "Outdoor or indoor ice skating — a classic winter activity for everyone.",
        "category": "ice_skating",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["ice_skating", "social", "adventure"],
    },
    {
        "title": "Spring Gardening Tips",
        "description": "Start your garden — seeds, soil, and sunshine for beautiful spring blooms.",
        "category": "spring_gardening",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["spring_gardening", "quiet", "calming", "practical", "self-paced"],
    },
    {
        "title": "Summer Camping Guide",
        "description": "Best campsites, gear tips, and stargazing spots — a summer under the stars.",
        "category": "summer_camping",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["summer_camping", "calming", "adventure", "outdoor"],
    },
    {
        "title": "Autumn Harvest Festival",
        "description": "Apple picking, corn mazes, and pumpkin patches — fall family fun.",
        "category": "autumn_harvest_festival",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["autumn_harvest_festival", "social", "traditional", "outdoor"],
    },
    {
        "title": "Winter Holiday Market",
        "description": "Handmade gifts, mulled wine, and festive lights — magical winter markets.",
        "category": "winter_market",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["winter_market", "social", "traditional"],
    },
    {
        "title": "Spring Cleaning Refresh",
        "description": "Declutter, reorganize, and refresh your space — a clean start for the season.",
        "category": "spring_cleaning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["spring_cleaning", "quiet", "practical", "self-paced"],
    },
    {
        "title": "Summer Road Trip Planner",
        "description": "Map the perfect route — scenic stops, roadside diners, and hidden gems.",
        "category": "summer_road_trip",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["summer_road_trip", "adventure", "social", "outdoor"],
    },
    {
        "title": "Autumn Photography Walk",
        "description": "Capture the season — golden light, colorful leaves, and misty mornings.",
        "category": "autumn_photography",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["autumn_photography", "quiet", "calming", "self-paced", "outdoor"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_SEASONAL_ACT_KEYWORDS: dict[str, list[str]] = {
    "当季": ["seasonal"],
    "seasonal": ["seasonal"],
    "spring": ["spring_picnic", "spring_gardening"],
    "春": ["spring_picnic", "spring_gardening"],
    "summer": ["summer_swimming", "beach_day"],
    "夏": ["summer_swimming", "beach_day"],
    "autumn": ["autumn_hiking", "leaf_peeping"],
    "fall": ["autumn_hiking", "leaf_peeping"],
    "秋": ["autumn_hiking", "leaf_peeping"],
    "winter": ["winter_hot_chocolate", "ice_skating"],
    "冬": ["winter_hot_chocolate", "ice_skating"],
    "cherry blossom": ["cherry_blossom_viewing"],
    "樱花": ["cherry_blossom_viewing"],
    "picnic": ["spring_picnic"],
    "野餐": ["spring_picnic"],
    "swimming": ["summer_swimming"],
    "游泳": ["summer_swimming"],
    "beach": ["beach_day"],
    "海滩": ["beach_day"],
    "hiking": ["autumn_hiking"],
    "远足": ["autumn_hiking"],
    "skating": ["ice_skating"],
    "溜冰": ["ice_skating"],
    "camping": ["summer_camping"],
    "露营": ["summer_camping"],
    "garden": ["spring_gardening"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _SEASONAL_ACT_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")
    reason_map = {
        "spring_picnic": "Enjoy the first warm days of spring",
        "cherry_blossom_viewing": "Don't miss the fleeting cherry blossoms",
        "summer_swimming": "The best way to cool off this summer",
        "beach_day": "Sun, sand, and waves await",
        "autumn_hiking": "The most beautiful season for trails",
        "leaf_peeping": "Chase the fall colors before they fade",
        "winter_hot_chocolate": "Warm up with the coziest cocoa spots",
        "ice_skating": "A classic winter activity for everyone",
        "spring_gardening": "Plant something beautiful this spring",
        "summer_camping": "Sleep under the stars this summer",
        "autumn_harvest_festival": "Fall fun with apples, corn, and pumpkins",
        "winter_market": "Festive lights and handmade treasures",
        "spring_cleaning": "A fresh start for the new season",
        "summer_road_trip": "Adventure is just a drive away",
        "autumn_photography": "Capture the golden season",
    }
    return reason_map.get(category, "Perfect activity for this season")


class SeasonalActivityFulfiller(L2Fulfiller):
    """L2 fulfiller for seasonal activity wishes — season + location-aware.

    Uses keyword matching + season routing to select from 15-type catalog,
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
                dict(item) for item in SEASONAL_ACTIVITY_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in SEASONAL_ACTIVITY_CATALOG]

        # 3. Fallback
        if not candidates:
            candidates = [dict(item) for item in SEASONAL_ACTIVITY_CATALOG]

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
                text="Seasonal activities update with the weather — check back soon!",
                delay_hours=72,
            ),
        )
