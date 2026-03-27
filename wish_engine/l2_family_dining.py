"""FamilyDiningFulfiller — large-group and kids-friendly dining recommendations.

12-type curated catalog for family meals with large group + kids friendly focus. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Family Dining Catalog (12 entries) ────────────────────────────────────────

FAMILY_DINING_CATALOG: list[dict] = [
    {
        "title": "Family-Friendly Restaurant",
        "description": "Spacious restaurants with kids menus, high chairs, and a welcoming atmosphere.",
        "category": "family_restaurant",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["family_restaurant", "kids_friendly", "large_group", "social"],
    },
    {
        "title": "Private Dining Room",
        "description": "Reserve a private room for family celebrations — quiet, spacious, and intimate.",
        "category": "private_room",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["private_room", "large_group", "quiet", "calming", "celebration"],
    },
    {
        "title": "Family Buffet",
        "description": "All-you-can-eat buffets — something for every taste, even the pickiest eater.",
        "category": "buffet",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["buffet", "kids_friendly", "large_group", "practical", "social"],
    },
    {
        "title": "Hot Pot Family Dinner",
        "description": "Gather around a shared hot pot — interactive, social, and delicious.",
        "category": "hotpot_family",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["hotpot_family", "large_group", "social", "traditional"],
    },
    {
        "title": "BBQ Family Gathering",
        "description": "Tabletop or outdoor BBQ — cook together and bond over grilled favorites.",
        "category": "bbq_family",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["bbq_family", "large_group", "social", "outdoor"],
    },
    {
        "title": "Dim Sum Brunch",
        "description": "Share baskets of dumplings, buns, and tarts — a family tradition.",
        "category": "dim_sum",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["dim_sum", "large_group", "social", "traditional", "kids_friendly"],
    },
    {
        "title": "Family Brunch Spot",
        "description": "Weekend brunch with pancakes, eggs, and fresh juice — fun for all ages.",
        "category": "brunch_family",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["brunch_family", "kids_friendly", "social", "calming"],
    },
    {
        "title": "Outdoor Terrace Dining",
        "description": "Al fresco dining with space for kids to play — fresh air and great food.",
        "category": "outdoor_terrace",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["outdoor_terrace", "kids_friendly", "outdoor", "calming"],
    },
    {
        "title": "Restaurant with Kids Menu",
        "description": "Restaurants with dedicated kids menus, coloring sheets, and play areas.",
        "category": "kids_menu",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["kids_menu", "kids_friendly", "practical", "social"],
    },
    {
        "title": "Halal Family Restaurant",
        "description": "Halal-certified restaurants with family-friendly atmosphere and large tables.",
        "category": "halal_family",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["halal_family", "large_group", "kids_friendly", "traditional"],
    },
    {
        "title": "Vegetarian Family Restaurant",
        "description": "Plant-based menus the whole family can enjoy — healthy and delicious.",
        "category": "vegetarian_family",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["vegetarian_family", "kids_friendly", "calming", "quiet"],
    },
    {
        "title": "Birthday Party Venue",
        "description": "Restaurants that host birthday parties — cake, decorations, and fun for kids.",
        "category": "birthday_venue",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["birthday_venue", "kids_friendly", "large_group", "celebration", "social"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_DINING_KEYWORDS: dict[str, list[str]] = {
    "聚餐": [],
    "family dinner": [],
    "家庭": [],
    "大桌": ["large_group"],
    "包间": ["private_room"],
    "عائلة": [],
    "private room": ["private_room"],
    "buffet": ["buffet"],
    "自助餐": ["buffet"],
    "火锅": ["hotpot_family"],
    "hotpot": ["hotpot_family"],
    "bbq": ["bbq_family"],
    "烧烤": ["bbq_family"],
    "dim sum": ["dim_sum"],
    "早茶": ["dim_sum"],
    "brunch": ["brunch_family"],
    "halal": ["halal_family"],
    "حلال": ["halal_family"],
    "vegetarian": ["vegetarian_family"],
    "素食": ["vegetarian_family"],
    "birthday": ["birthday_venue"],
    "生日": ["birthday_venue"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _DINING_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "family_restaurant": "A welcoming space for the whole family",
        "private_room": "Privacy and comfort for family gatherings",
        "buffet": "Something for everyone — even the pickiest eaters",
        "hotpot_family": "Cook together, eat together, bond together",
        "bbq_family": "Grill and gather — family fun at its best",
        "dim_sum": "A delicious family tradition worth sharing",
        "brunch_family": "Start the weekend with a family feast",
        "outdoor_terrace": "Fresh air, great food, and room for kids to play",
        "kids_menu": "Menus designed with kids in mind",
        "halal_family": "Halal dining the whole family will enjoy",
        "vegetarian_family": "Healthy, plant-based meals for everyone",
        "birthday_venue": "Celebrate with cake, fun, and family",
    }
    return reason_map.get(category, "A great place for family dining")


class FamilyDiningFulfiller(L2Fulfiller):
    """L2 fulfiller for family dining wishes — large group + kids friendly.

    Uses keyword matching to select from 12-type catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        matched_categories = _match_categories(wish.wish_text)

        if matched_categories:
            tag_set = set(matched_categories)
            candidates = [
                dict(item) for item in FAMILY_DINING_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in FAMILY_DINING_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in FAMILY_DINING_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More family dining spots — check back soon!",
                delay_hours=24,
            ),
        )
