"""EnvironmentalActionFulfiller — environmental action and sustainability resources.

10-entry catalog of eco-friendly actions and communities. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Catalog (10 entries) ─────────────────────────────────────────────────────

ENVIRONMENTAL_CATALOG: list[dict] = [
    {
        "title": "Carbon Footprint Calculator",
        "description": "Measure your carbon footprint — personalized tips to reduce your environmental impact.",
        "category": "carbon_footprint_calculator",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["carbon", "calculator", "awareness", "calming", "self-paced"],
    },
    {
        "title": "Tree Planting Programs",
        "description": "Join local tree planting events or sponsor trees in deforested areas worldwide.",
        "category": "tree_planting",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["trees", "planting", "community", "calming", "outdoor"],
    },
    {
        "title": "Beach Cleanup Events",
        "description": "Join coastal cleanup events near you — protect marine life and keep beaches beautiful.",
        "category": "beach_cleanup",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["cleanup", "ocean", "community", "outdoor", "calming"],
    },
    {
        "title": "Community Garden (Eco)",
        "description": "Grow food locally — join or start a community garden focused on sustainability.",
        "category": "community_garden_eco",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["garden", "community", "food", "calming", "outdoor"],
    },
    {
        "title": "Sustainable Shopping Guide",
        "description": "Find ethical brands, sustainable products, and eco-friendly alternatives.",
        "category": "sustainable_shopping",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["shopping", "sustainable", "practical", "calming", "self-paced"],
    },
    {
        "title": "Zero Waste Starter Kit",
        "description": "Begin your zero-waste journey — practical swaps, tips, and community support.",
        "category": "zero_waste",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["zero_waste", "practical", "lifestyle", "calming", "self-paced"],
    },
    {
        "title": "Renewable Energy Guide",
        "description": "Switch to renewable energy — solar panels, green energy providers, and incentives.",
        "category": "renewable_energy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["renewable", "energy", "practical", "calming"],
    },
    {
        "title": "Wildlife Conservation",
        "description": "Support wildlife conservation — volunteer, donate, or adopt an endangered species.",
        "category": "wildlife_conservation",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["wildlife", "conservation", "nature", "calming"],
    },
    {
        "title": "Climate Education Resources",
        "description": "Understand climate science — accessible resources for all levels of knowledge.",
        "category": "climate_education",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["climate", "education", "awareness", "calming", "self-paced"],
    },
    {
        "title": "Eco Community Hub",
        "description": "Connect with local environmentalists — meetups, projects, and shared initiatives.",
        "category": "eco_community",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["eco", "community", "social", "calming"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_ENVIRONMENTAL_KEYWORDS: dict[str, list[str]] = {
    "环保": [],
    "environment": [],
    "climate": ["climate", "awareness"],
    "碳": ["carbon", "calculator"],
    "carbon": ["carbon", "calculator"],
    "بيئة": [],
    "green": [],
    "sustainable": ["sustainable", "practical"],
    "可持续": ["sustainable", "practical"],
    "tree": ["trees", "planting"],
    "树": ["trees", "planting"],
    "zero waste": ["zero_waste", "lifestyle"],
    "零浪费": ["zero_waste", "lifestyle"],
    "wildlife": ["wildlife", "conservation"],
    "renewable": ["renewable", "energy"],
    "solar": ["renewable", "energy"],
    "cleanup": ["cleanup", "community"],
    "garden": ["garden", "food"],
}


def _match_environmental_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _ENVIRONMENTAL_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class EnvironmentalActionFulfiller(L2Fulfiller):
    """L2 fulfiller for environmental action — eco-friendly resources and communities.

    10 curated entries for sustainability and environmental impact. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_environmental_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in ENVIRONMENTAL_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in ENVIRONMENTAL_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in ENVIRONMENTAL_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Every small action adds up. The planet thanks you.",
                delay_hours=72,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "community" in tags:
        return "Join others who care about the environment"
    if "practical" in tags:
        return "Actionable step you can start today"
    if "awareness" in tags:
        return "Knowledge powers better environmental choices"
    if "nature" in tags:
        return "Protect the natural world we all depend on"
    return "Contribute to a healthier planet"
