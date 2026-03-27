"""KidsActivityFulfiller — age-aware family activity recommendations.

15-type curated catalog of kids activities with age-group personality mapping.
Toddler/preschool/school_age tags for developmental appropriateness. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Kids Activity Catalog (15 entries) ────────────────────────────────────────

KIDS_CATALOG: list[dict] = [
    {
        "title": "Playground Adventure",
        "description": "Nearby playgrounds with slides, swings, and climbing frames for active play.",
        "category": "playground",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["playground", "outdoor", "toddler", "preschool", "school_age", "active"],
    },
    {
        "title": "Children's Museum Visit",
        "description": "Interactive exhibits designed for curious young minds — touch, build, and explore.",
        "category": "children_museum",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["children_museum", "indoor", "preschool", "school_age", "learning"],
    },
    {
        "title": "Kids Cooking Class",
        "description": "Hands-on cooking for little chefs — simple recipes, big smiles.",
        "category": "kids_cooking",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["kids_cooking", "indoor", "preschool", "school_age", "practical"],
    },
    {
        "title": "Kids Art Studio",
        "description": "Painting, drawing, and sculpting — creative expression for all ages.",
        "category": "kids_art",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["kids_art", "indoor", "toddler", "preschool", "school_age", "calming"],
    },
    {
        "title": "Family Hiking Trail",
        "description": "Easy nature trails perfect for families — fresh air and discovery.",
        "category": "family_hike",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["family_hike", "outdoor", "preschool", "school_age", "calming", "quiet"],
    },
    {
        "title": "Zoo Day Out",
        "description": "Meet animals from around the world — educational and fun for all ages.",
        "category": "zoo",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["zoo", "outdoor", "toddler", "preschool", "school_age", "learning"],
    },
    {
        "title": "Aquarium Visit",
        "description": "Underwater wonders — jellyfish, sharks, and interactive touch pools.",
        "category": "aquarium",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["aquarium", "indoor", "toddler", "preschool", "school_age", "calming"],
    },
    {
        "title": "Kids Sports Program",
        "description": "Soccer, basketball, swimming — structured sports for growing bodies.",
        "category": "kids_sports",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["kids_sports", "outdoor", "school_age", "active", "social"],
    },
    {
        "title": "Story Time at the Library",
        "description": "Read-aloud sessions with puppets and songs — perfect for little listeners.",
        "category": "story_time",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["story_time", "indoor", "toddler", "preschool", "quiet", "calming"],
    },
    {
        "title": "Puppet Show",
        "description": "Live puppet theater — captivating stories that spark imagination.",
        "category": "puppet_show",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["puppet_show", "indoor", "toddler", "preschool", "calming"],
    },
    {
        "title": "Science Museum Exploration",
        "description": "Hands-on experiments and exhibits — future scientists start here.",
        "category": "science_museum",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["science_museum", "indoor", "school_age", "learning", "practical"],
    },
    {
        "title": "Water Park Fun",
        "description": "Splash pads, slides, and lazy rivers — the ultimate summer adventure.",
        "category": "water_park",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["water_park", "outdoor", "preschool", "school_age", "active", "social"],
    },
    {
        "title": "Indoor Playground",
        "description": "Soft play areas, ball pits, and climbing walls — rain-proof fun.",
        "category": "indoor_playground",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["indoor_playground", "indoor", "toddler", "preschool", "active"],
    },
    {
        "title": "Kids Yoga Class",
        "description": "Gentle stretching and mindfulness — helping kids find calm and focus.",
        "category": "kids_yoga",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["kids_yoga", "indoor", "preschool", "school_age", "calming", "quiet"],
    },
    {
        "title": "Nature & Outdoor Camp",
        "description": "Day camps with nature crafts, bug hunts, and campfire stories.",
        "category": "nature_camp",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["nature_camp", "outdoor", "school_age", "learning", "active"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_KIDS_KEYWORDS: dict[str, list[str]] = {
    "孩子": [],
    "kids": [],
    "children": [],
    "亲子": [],
    "أطفال": [],
    "family": [],
    "带娃": [],
    "playground": ["playground"],
    "游乐场": ["playground"],
    "museum": ["children_museum", "science_museum"],
    "博物馆": ["children_museum", "science_museum"],
    "cooking": ["kids_cooking"],
    "art": ["kids_art"],
    "画画": ["kids_art"],
    "hike": ["family_hike"],
    "zoo": ["zoo"],
    "动物园": ["zoo"],
    "aquarium": ["aquarium"],
    "水族馆": ["aquarium"],
    "sports": ["kids_sports"],
    "运动": ["kids_sports"],
    "story": ["story_time"],
    "puppet": ["puppet_show"],
    "water park": ["water_park"],
    "yoga": ["kids_yoga"],
    "camp": ["nature_camp"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _KIDS_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    """Build a relevance reason for the activity."""
    category = item.get("category", "")
    reason_map = {
        "playground": "Active outdoor play for happy, healthy kids",
        "children_museum": "Hands-on learning that feels like play",
        "kids_cooking": "Build life skills while having fun together",
        "kids_art": "Creative expression for growing minds",
        "family_hike": "Fresh air and quality family time",
        "zoo": "Meet amazing animals — unforgettable for kids",
        "aquarium": "Underwater wonders the whole family will love",
        "kids_sports": "Build confidence and teamwork through sports",
        "story_time": "Spark a lifelong love of reading",
        "puppet_show": "Imagination comes alive on stage",
        "science_museum": "Where curiosity meets discovery",
        "water_park": "Splash into the best day ever",
        "indoor_playground": "Rain or shine — the fun never stops",
        "kids_yoga": "Calm, focus, and fun for little ones",
        "nature_camp": "Outdoor adventures that build character",
    }
    return reason_map.get(category, "A wonderful activity for the whole family")


class KidsActivityFulfiller(L2Fulfiller):
    """L2 fulfiller for kids/family activity wishes — age-aware recommendations.

    Uses keyword matching + age-group tags to select from 15-type catalog,
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
                dict(item) for item in KIDS_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in KIDS_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in KIDS_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More kids activities near you — check back soon!",
                delay_hours=24,
            ),
        )
