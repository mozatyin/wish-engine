"""WeekendPlannerFulfiller — MBTI + emotion-aware weekend plan recommendations.

15-type curated catalog of weekend activities. Auto-selects based on MBTI
energy (I→solo/quiet, E→social/active) and recent emotion state. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── MBTI → Weekend Style Mapping ─────────────────────────────────────────────

MBTI_WEEKEND_MAP: dict[str, list[str]] = {
    "I": ["lazy_morning", "reading_marathon", "solo_exploration", "home_project", "creative_workshop"],
    "E": ["food_crawl", "night_out", "social_brunch", "active_outdoor", "couple_day"],
}

# ── Weekend Plan Catalog (15 entries) ────────────────────────────────────────

WEEKEND_CATALOG: list[dict] = [
    {
        "title": "Lazy Morning Routine",
        "description": "Sleep in, slow breakfast, journaling — a gentle start to your weekend.",
        "category": "lazy_morning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["lazy_morning", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Active Outdoor Adventure",
        "description": "Hiking, cycling, or beach run — fresh air and endorphins for an energizing day.",
        "category": "active_outdoor",
        "noise": "moderate",
        "social": "medium",
        "mood": "intense",
        "tags": ["active_outdoor", "social", "adventure", "practical"],
    },
    {
        "title": "Cultural Day Out",
        "description": "Museum, gallery, or heritage site — feed your mind with art and history.",
        "category": "cultural_day",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["cultural_day", "calming", "traditional", "theory"],
    },
    {
        "title": "Food Crawl Adventure",
        "description": "Hop between the best local eateries — taste your way through the city.",
        "category": "food_crawl",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["food_crawl", "social", "adventure"],
    },
    {
        "title": "Spa & Self-Care Day",
        "description": "Massage, facial, hot springs — a full day of pampering and relaxation.",
        "category": "spa_day",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["spa_day", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Creative Workshop Day",
        "description": "Pottery, painting, or cooking class — learn something new with your hands.",
        "category": "creative_workshop",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative_workshop", "calming", "practical"],
    },
    {
        "title": "Volunteering Saturday",
        "description": "Give back — community garden, animal shelter, or charity event.",
        "category": "volunteering_day",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["volunteering_day", "social", "helping", "calming"],
    },
    {
        "title": "Reading Marathon",
        "description": "Stack of books, cozy corner, tea — uninterrupted reading all day.",
        "category": "reading_marathon",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["reading_marathon", "quiet", "calming", "self-paced", "theory"],
    },
    {
        "title": "Weekend Road Trip",
        "description": "Pick a direction and drive — small towns, scenic routes, and spontaneous stops.",
        "category": "road_trip",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["road_trip", "adventure", "social"],
    },
    {
        "title": "Night Out Plan",
        "description": "Dinner, live music, rooftop bar — a curated evening of fun and connection.",
        "category": "night_out",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["night_out", "social", "adventure"],
    },
    {
        "title": "Home Project Day",
        "description": "Organize a room, build something, or start a DIY project — productive and satisfying.",
        "category": "home_project",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["home_project", "quiet", "practical", "self-paced"],
    },
    {
        "title": "Social Brunch",
        "description": "Gather friends for brunch — good food, good coffee, great conversation.",
        "category": "social_brunch",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["social_brunch", "social", "calming"],
    },
    {
        "title": "Solo Exploration Walk",
        "description": "Wander a new neighborhood, discover hidden gems, and take your time.",
        "category": "solo_exploration",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solo_exploration", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Couple's Day Plan",
        "description": "Cooking together, sunset walk, movie night — quality time for two.",
        "category": "couple_day",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["couple_day", "calming", "social"],
    },
    {
        "title": "Family Outing",
        "description": "Park, zoo, or family-friendly restaurant — fun for all ages.",
        "category": "family_outing",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["family_outing", "social", "practical", "calming"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_WEEKEND_KEYWORDS: dict[str, list[str]] = {
    "周末": ["weekend"],
    "weekend": ["weekend"],
    "计划": ["plan"],
    "plan": ["plan"],
    "عطلة": ["weekend"],
    "what to do": ["weekend"],
    "lazy": ["lazy_morning"],
    "赖床": ["lazy_morning"],
    "hiking": ["active_outdoor"],
    "户外": ["active_outdoor"],
    "museum": ["cultural_day"],
    "博物馆": ["cultural_day"],
    "food crawl": ["food_crawl"],
    "吃遍": ["food_crawl"],
    "spa": ["spa_day"],
    "road trip": ["road_trip"],
    "自驾": ["road_trip"],
    "brunch": ["social_brunch"],
    "早午餐": ["social_brunch"],
    "solo": ["solo_exploration"],
    "couple": ["couple_day"],
    "family": ["family_outing"],
    "家庭": ["family_outing"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _WEEKEND_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _mbti_to_weekend_tags(mbti_type: str) -> list[str]:
    """Map MBTI E/I to preferred weekend styles."""
    if len(mbti_type) >= 1:
        return MBTI_WEEKEND_MAP.get(mbti_type[0], [])
    return []


def _build_relevance_reason(item: dict, mbti_type: str) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")

    if mbti_type and len(mbti_type) >= 1:
        if mbti_type[0] == "I" and item.get("social") == "low":
            return "A peaceful weekend plan — recharge at your own pace"
        if mbti_type[0] == "E" and item.get("social") in ("high", "medium"):
            return "An energizing social plan for your weekend"

    reason_map = {
        "lazy_morning": "Sometimes doing less is the best plan",
        "active_outdoor": "Fresh air and movement to reset your mind",
        "cultural_day": "Feed your curiosity with art and culture",
        "food_crawl": "Taste your way through the best local spots",
        "spa_day": "You deserve a day of complete relaxation",
        "creative_workshop": "Learn something new while having fun",
        "reading_marathon": "Get lost in a good book all day",
        "road_trip": "Adventure awaits just a drive away",
        "night_out": "A curated evening of fun and connection",
        "home_project": "Productive and satisfying — a DIY weekend",
        "solo_exploration": "Discover hidden gems at your own pace",
        "family_outing": "Quality time for the whole family",
    }
    return reason_map.get(category, "A great way to spend your weekend")


class WeekendPlannerFulfiller(L2Fulfiller):
    """L2 fulfiller for weekend planning wishes — MBTI + emotion-aware.

    Uses keyword matching + MBTI E/I→solo/social mapping to select from 15-type
    catalog, then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Add MBTI-based preferences
        mbti_type = detector_results.mbti.get("type", "")
        mbti_tags = _mbti_to_weekend_tags(mbti_type)

        all_tags = list(matched_categories)
        for t in mbti_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in WEEKEND_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in WEEKEND_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in WEEKEND_CATALOG]

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, mbti_type)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Weekend plans refresh every Thursday — check back!",
                delay_hours=72,
            ),
        )
