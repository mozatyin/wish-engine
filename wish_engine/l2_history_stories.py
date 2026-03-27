"""HistoryStoryFulfiller — historical site stories and heritage experiences.

15-entry catalog of history story types, each with a story snippet. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

VALUES_HISTORY_MAP: dict[str, list[str]] = {
    "tradition": ["heritage", "religious", "traditional", "ancient"],
    "universalism": ["world", "migration", "natural", "humanity"],
    "self-direction": ["discovery", "exploration", "intellectual", "literary"],
    "stimulation": ["adventure", "revolution", "war", "dramatic"],
    "achievement": ["scientific", "industrial", "trade", "innovation"],
    "benevolence": ["migration", "humanity", "community"],
}

HISTORY_CATALOG: list[dict] = [
    {
        "title": "Ancient Ruins Exploration",
        "description": "Walk among pillars that stood before empires fell — every stone holds a thousand years.",
        "category": "ancient_ruins",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ancient", "heritage", "exploration", "quiet", "discovery"],
    },
    {
        "title": "War Memorial Reflection",
        "description": "Names etched in stone, stories of courage — memorials that teach us the cost of conflict.",
        "category": "war_memorial",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["war", "heritage", "humanity", "quiet", "dramatic"],
    },
    {
        "title": "Colonial Architecture Tour",
        "description": "Grand facades hiding complex histories — the beauty and burden of colonial legacy.",
        "category": "colonial_architecture",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["heritage", "traditional", "exploration", "world", "quiet"],
    },
    {
        "title": "Sacred Sites & Religious Heritage",
        "description": "From cathedral naves to mosque domes — sacred spaces that shaped civilizations.",
        "category": "religious_site",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["religious", "heritage", "ancient", "traditional", "quiet"],
    },
    {
        "title": "Royal Palace Stories",
        "description": "Behind gilded doors: intrigue, power, and the private lives of rulers.",
        "category": "royal_palace",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["heritage", "dramatic", "traditional", "world", "discovery"],
    },
    {
        "title": "Old Market Heritage",
        "description": "Bazaars and souks where silk road traders once bargained — commerce as old as civilization.",
        "category": "old_market",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["trade", "heritage", "traditional", "ancient", "community"],
    },
    {
        "title": "Literary Landmark Visit",
        "description": "The cafe where Hemingway wrote, the garden where Rumi composed — words born in places.",
        "category": "literary_landmark",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["literary", "intellectual", "quiet", "discovery", "heritage"],
    },
    {
        "title": "Scientific Discovery Site",
        "description": "Where Newton watched apples fall and Curie isolated radium — birthplaces of breakthroughs.",
        "category": "scientific_discovery_site",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["scientific", "intellectual", "innovation", "discovery", "quiet"],
    },
    {
        "title": "Revolutionary Site Tour",
        "description": "Barricades, speeches, and the turning points that changed nations overnight.",
        "category": "revolutionary_site",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["revolution", "dramatic", "heritage", "humanity", "world"],
    },
    {
        "title": "Ancient Trade Route Stop",
        "description": "Caravanserais and port towns where Silk Road merchants rested and traded stories.",
        "category": "trade_route_stop",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trade", "ancient", "world", "exploration", "heritage"],
    },
    {
        "title": "Ancient Garden Heritage",
        "description": "Persian gardens, Japanese zen gardens, Mughal pleasure gardens — paradise on earth.",
        "category": "ancient_garden",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ancient", "heritage", "traditional", "quiet", "natural"],
    },
    {
        "title": "Industrial Heritage Site",
        "description": "Factories, mines, and railways that powered the modern world — sweat and steel.",
        "category": "industrial_heritage",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["industrial", "innovation", "heritage", "trade", "discovery"],
    },
    {
        "title": "Migration Story Trail",
        "description": "Ports, borders, and neighborhoods shaped by waves of human movement and hope.",
        "category": "migration_story",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["migration", "humanity", "heritage", "world", "community"],
    },
    {
        "title": "Natural Wonder Stories",
        "description": "Grand canyons, ancient forests, volcanic islands — nature's own monuments with deep histories.",
        "category": "natural_wonder",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["natural", "ancient", "exploration", "adventure", "quiet"],
    },
    {
        "title": "Archaeological Dig Experience",
        "description": "Sift through layers of time — join a dig or visit active excavation sites.",
        "category": "archaeological_dig",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["ancient", "discovery", "exploration", "scientific", "adventure"],
    },
]

_HISTORY_KEYWORDS: dict[str, list[str]] = {
    "历史": ["heritage", "ancient"],
    "history": ["heritage", "ancient"],
    "故事": ["literary", "dramatic"],
    "story": ["literary", "dramatic"],
    "تاريخ": ["heritage", "ancient"],
    "heritage": ["heritage", "traditional"],
    "遗迹": ["ancient", "heritage"],
    "ancient": ["ancient", "heritage"],
    "ruins": ["ancient", "exploration"],
    "palace": ["heritage", "dramatic"],
    "museum": ["heritage", "intellectual"],
    "war": ["war", "dramatic"],
    "战争": ["war", "dramatic"],
    "trade route": ["trade", "ancient"],
    "silk road": ["trade", "ancient"],
    "archaeological": ["ancient", "scientific"],
    "考古": ["ancient", "scientific"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _HISTORY_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _values_to_history_tags(top_values: list[str]) -> list[str]:
    tags: list[str] = []
    for value in top_values:
        for tag in VALUES_HISTORY_MAP.get(value, []):
            if tag not in tags:
                tags.append(tag)
    return tags


def _build_relevance_reason(item: dict, top_values: list[str]) -> str:
    tags = set(item.get("tags", []))
    for value in top_values:
        if value == "tradition" and tags & {"heritage", "ancient", "traditional"}:
            return "Stories rooted in the traditions you cherish"
        if value == "universalism" and tags & {"world", "migration", "humanity"}:
            return "History that connects all of humanity"
        if value == "self-direction" and tags & {"discovery", "intellectual", "literary"}:
            return "Intellectual adventure through the past"
        if value == "stimulation" and tags & {"adventure", "revolution", "dramatic"}:
            return "Dramatic stories that still echo today"

    category = item.get("category", "")
    reason_map = {
        "ancient_ruins": "Walk where ancient civilizations stood",
        "literary_landmark": "Words were born here",
        "migration_story": "Stories of people seeking better lives",
        "archaeological_dig": "Touch history with your own hands",
    }
    return reason_map.get(category, "History comes alive in this place")


class HistoryStoryFulfiller(L2Fulfiller):
    """L2 fulfiller for history/heritage wishes — story-rich site recommendations.

    Uses keyword matching + values→history mapping to select from 15-entry catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        matched_categories = _match_categories(wish.wish_text)
        top_values = detector_results.values.get("top_values", [])
        values_tags = _values_to_history_tags(top_values)

        all_tags = list(matched_categories)
        for t in values_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in HISTORY_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in HISTORY_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in HISTORY_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, top_values)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More history stories added — check back for new discoveries!",
                delay_hours=72,
            ),
        )
