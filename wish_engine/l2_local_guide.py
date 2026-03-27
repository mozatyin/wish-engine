"""LocalGuideFulfiller — curated local secrets and hidden gems, not tourist traps.

15-entry catalog of local experience types with personality mapping. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Values → Local Experience Mapping ────────────────────────────────────────

VALUES_LOCAL_MAP: dict[str, list[str]] = {
    "stimulation": ["adventurous", "discovery", "underground", "secret"],
    "self-direction": ["solo", "autonomous", "hidden", "exploration"],
    "tradition": ["heritage", "traditional", "historical", "artisan"],
    "hedonism": ["foodie", "indulgence", "rooftop", "scenic"],
    "universalism": ["nature", "community", "inclusive", "cultural"],
    "achievement": ["photography", "challenge", "exploration"],
}

# ── Local Guide Catalog (15 entries) ─────────────────────────────────────────

LOCAL_CATALOG: list[dict] = [
    {
        "title": "Hidden Cafe Discovery",
        "description": "Tucked-away cafes that locals love — no queues, real character, perfect coffee.",
        "category": "hidden_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["hidden", "foodie", "solo", "quiet", "indulgence"],
    },
    {
        "title": "Street Art Walking Tour",
        "description": "Follow the murals, graffiti, and installations that tell the city's underground story.",
        "category": "street_art_walk",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["discovery", "cultural", "autonomous", "exploration", "creative"],
    },
    {
        "title": "Local Market Morning",
        "description": "Wake up early for the real market — where chefs shop, before tourists arrive.",
        "category": "local_market",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["traditional", "foodie", "community", "heritage", "authentic"],
    },
    {
        "title": "Neighborhood History Walk",
        "description": "Every block has a story — discover the layers of history in your own neighborhood.",
        "category": "neighborhood_history",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["historical", "heritage", "solo", "quiet", "exploration"],
    },
    {
        "title": "Artisan Workshop Visit",
        "description": "Watch master craftspeople at work — blacksmiths, potters, weavers in their studios.",
        "category": "artisan_workshop",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["artisan", "traditional", "hidden", "heritage", "cultural"],
    },
    {
        "title": "Secret Rooftop Spots",
        "description": "Rooftop bars, gardens, and viewpoints that only locals know about.",
        "category": "rooftop_secret",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["rooftop", "scenic", "secret", "indulgence", "hidden"],
    },
    {
        "title": "Underground Music Scene",
        "description": "Basement jazz clubs, garage punk shows, and vinyl-only DJ sets.",
        "category": "underground_music",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["underground", "adventurous", "discovery", "social", "creative"],
    },
    {
        "title": "Food Alley Explorer",
        "description": "The narrow alleys where the best street food hides — follow the smoke and the queue.",
        "category": "food_alley",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["foodie", "discovery", "adventurous", "authentic", "hidden"],
    },
    {
        "title": "Vintage Shop Tour",
        "description": "Curated route through the best vintage, thrift, and antique shops in the area.",
        "category": "vintage_shop_tour",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["discovery", "autonomous", "hidden", "solo", "exploration"],
    },
    {
        "title": "Temple & Shrine Walk",
        "description": "Peaceful walks through lesser-known temples, shrines, and spiritual spaces.",
        "category": "temple_walk",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["heritage", "traditional", "quiet", "solo", "nature"],
    },
    {
        "title": "Secret Garden Path",
        "description": "Hidden parks, community gardens, and green spaces the guidebooks missed.",
        "category": "garden_path",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nature", "hidden", "quiet", "solo", "scenic"],
    },
    {
        "title": "Waterfront Discovery",
        "description": "Quiet harbors, hidden piers, and waterfront walks away from the tourist promenades.",
        "category": "waterfront_discovery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["scenic", "nature", "discovery", "quiet", "exploration"],
    },
    {
        "title": "Architectural Walk",
        "description": "Art Deco facades, brutalist gems, and forgotten architectural treasures.",
        "category": "architectural_walk",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["heritage", "cultural", "exploration", "autonomous", "historical"],
    },
    {
        "title": "Night Photography Spots",
        "description": "The best low-light locations for moody cityscapes and long-exposure magic.",
        "category": "night_photography_spot",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["photography", "solo", "secret", "adventurous", "exploration"],
    },
    {
        "title": "Sunrise Viewpoint",
        "description": "Wake before the city — hilltops, towers, and bridges with golden-hour views.",
        "category": "sunrise_viewpoint",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["scenic", "nature", "solo", "quiet", "challenge"],
    },
]


# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_LOCAL_KEYWORDS: dict[str, list[str]] = {
    "本地": ["authentic", "community"],
    "local": ["authentic", "community"],
    "隐藏": ["hidden", "secret"],
    "hidden": ["hidden", "secret"],
    "secret": ["hidden", "secret"],
    "秘密": ["hidden", "secret"],
    "探索": ["discovery", "exploration"],
    "discover": ["discovery", "exploration"],
    "explore": ["discovery", "exploration"],
    "محلي": ["authentic", "community"],
    "street art": ["creative", "cultural"],
    "rooftop": ["rooftop", "scenic"],
    "vintage": ["discovery", "hidden"],
    "alley": ["foodie", "hidden"],
    "小巷": ["foodie", "hidden"],
    "photography": ["photography", "solo"],
    "sunrise": ["scenic", "nature"],
    "日出": ["scenic", "nature"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _LOCAL_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _values_to_local_tags(top_values: list[str]) -> list[str]:
    tags: list[str] = []
    for value in top_values:
        for tag in VALUES_LOCAL_MAP.get(value, []):
            if tag not in tags:
                tags.append(tag)
    return tags


def _build_relevance_reason(item: dict, top_values: list[str]) -> str:
    tags = set(item.get("tags", []))

    for value in top_values:
        if value == "stimulation" and tags & {"adventurous", "discovery", "underground"}:
            return "An adventure only locals know about"
        if value == "self-direction" and tags & {"solo", "autonomous", "hidden"}:
            return "Your kind of solo discovery — off the beaten path"
        if value == "tradition" and tags & {"heritage", "traditional", "artisan"}:
            return "Authentic local heritage worth preserving"
        if value == "hedonism" and tags & {"foodie", "indulgence", "scenic"}:
            return "A hidden pleasure most visitors never find"

    category = item.get("category", "")
    reason_map = {
        "hidden_cafe": "Your next favorite quiet spot",
        "street_art_walk": "The city speaks through its walls",
        "food_alley": "Follow your nose to the best bites",
        "sunrise_viewpoint": "The city belongs to early risers",
    }
    return reason_map.get(category, "A local secret worth discovering")


class LocalGuideFulfiller(L2Fulfiller):
    """L2 fulfiller for local discovery wishes — curated hidden gems, not tourist traps.

    Uses keyword matching + values→local mapping to select from 15-entry catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        matched_categories = _match_categories(wish.wish_text)
        top_values = detector_results.values.get("top_values", [])
        values_tags = _values_to_local_tags(top_values)

        all_tags = list(matched_categories)
        for t in values_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in LOCAL_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in LOCAL_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in LOCAL_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, top_values)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New local secrets uncovered — check back soon!",
                delay_hours=72,
            ),
        )
