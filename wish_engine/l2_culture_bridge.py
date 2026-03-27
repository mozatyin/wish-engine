"""CultureBridgeFulfiller — cross-cultural activity recommendations for diaspora users.

15-entry curated catalog of cross-cultural experiences with personality mapping. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Values → Culture Bridge Mapping ──────────────────────────────────────────

VALUES_BRIDGE_MAP: dict[str, list[str]] = {
    "universalism": ["multicultural", "interfaith", "diplomatic", "inclusive"],
    "benevolence": ["mentoring", "support", "community", "helping"],
    "tradition": ["heritage", "traditional", "cultural", "craft"],
    "stimulation": ["immersive", "experiential", "social", "lively"],
    "self-direction": ["exchange", "learning", "creative", "autonomous"],
    "conformity": ["community", "structured", "social"],
}

# ── Culture Bridge Catalog (15 entries) ──────────────────────────────────────

BRIDGE_CATALOG: list[dict] = [
    {
        "title": "Language Exchange Meetup",
        "description": "Practice languages with native speakers in a relaxed cafe setting — all levels welcome.",
        "category": "language_exchange",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["exchange", "learning", "social", "multicultural", "community"],
    },
    {
        "title": "Cultural Cooking Workshop",
        "description": "Cook traditional dishes from different cultures — learn recipes and stories behind the food.",
        "category": "cultural_cooking",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["cultural", "immersive", "experiential", "traditional", "community"],
    },
    {
        "title": "Interfaith Dialogue Circle",
        "description": "Open conversations between faiths — understanding, not converting. Safe space for questions.",
        "category": "interfaith_dialogue",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["interfaith", "inclusive", "community", "spiritual", "heritage"],
    },
    {
        "title": "International Film Screening",
        "description": "Watch award-winning films from around the world with post-screening discussion.",
        "category": "international_film",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["multicultural", "creative", "learning", "quiet", "autonomous"],
    },
    {
        "title": "World Music Night",
        "description": "Live performances featuring traditional instruments and fusion genres from across continents.",
        "category": "world_music",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["multicultural", "lively", "social", "experiential", "immersive"],
    },
    {
        "title": "Cultural Awareness Workshop",
        "description": "Interactive sessions on cultural norms, communication styles, and cross-cultural empathy.",
        "category": "culture_workshop",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["learning", "inclusive", "structured", "community", "multicultural"],
    },
    {
        "title": "Expat Community Meetup",
        "description": "Connect with fellow expats — share tips, stories, and support for life abroad.",
        "category": "expat_meetup",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["community", "social", "support", "helping", "multicultural"],
    },
    {
        "title": "Cultural Festival Volunteering",
        "description": "Help organize and participate in multicultural festivals — food stalls, art, and performances.",
        "category": "cultural_festival",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["multicultural", "community", "lively", "social", "experiential"],
    },
    {
        "title": "Heritage Walking Tour",
        "description": "Guided walks through historic neighborhoods — discover the stories of immigrant communities.",
        "category": "heritage_tour",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["heritage", "learning", "cultural", "traditional", "quiet"],
    },
    {
        "title": "Multicultural Dinner Party",
        "description": "Potluck-style dinners where each guest brings a dish from their home culture.",
        "category": "multicultural_dinner",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["multicultural", "social", "community", "immersive", "traditional"],
    },
    {
        "title": "International Pen Pal Matching",
        "description": "Get matched with a pen pal from another culture — letters, not just texts.",
        "category": "pen_pal_matching",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["exchange", "autonomous", "creative", "quiet", "learning"],
    },
    {
        "title": "Cultural Mentoring Program",
        "description": "Pair newcomers with local mentors for cultural adaptation and career guidance.",
        "category": "cultural_mentoring",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["mentoring", "support", "helping", "community", "structured"],
    },
    {
        "title": "Diplomatic & Cultural Events",
        "description": "Embassy open days, cultural attache events, and international cooperation forums.",
        "category": "diplomatic_events",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["diplomatic", "multicultural", "structured", "learning", "inclusive"],
    },
    {
        "title": "Art Across Borders Exhibition",
        "description": "Art exhibitions featuring works that explore migration, identity, and cultural fusion.",
        "category": "art_across_borders",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "multicultural", "quiet", "autonomous", "heritage"],
    },
    {
        "title": "Traditional Craft Exchange",
        "description": "Learn calligraphy, origami, henna, or pottery from artisans of different cultures.",
        "category": "traditional_craft_exchange",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["craft", "traditional", "exchange", "cultural", "immersive"],
    },
]


# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_BRIDGE_KEYWORDS: dict[str, list[str]] = {
    "文化": ["cultural", "multicultural"],
    "culture": ["cultural", "multicultural"],
    "跨文化": ["multicultural", "exchange"],
    "cross-cultural": ["multicultural", "exchange"],
    "ثقافة": ["cultural", "multicultural"],
    "exchange": ["exchange", "learning"],
    "bridge": ["multicultural", "inclusive"],
    "diaspora": ["community", "support"],
    "expat": ["community", "support"],
    "interfaith": ["interfaith", "inclusive"],
    "多元": ["multicultural", "inclusive"],
    "immigrant": ["community", "support"],
    "移民": ["community", "support"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _BRIDGE_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _values_to_bridge_tags(top_values: list[str]) -> list[str]:
    tags: list[str] = []
    for value in top_values:
        for tag in VALUES_BRIDGE_MAP.get(value, []):
            if tag not in tags:
                tags.append(tag)
    return tags


def _build_relevance_reason(item: dict, top_values: list[str]) -> str:
    tags = set(item.get("tags", []))

    for value in top_values:
        if value == "universalism" and tags & {"multicultural", "interfaith", "inclusive"}:
            return "Bridges cultures — aligned with your openness to the world"
        if value == "benevolence" and tags & {"mentoring", "support", "helping"}:
            return "Help others navigate cross-cultural challenges"
        if value == "tradition" and tags & {"heritage", "traditional", "cultural"}:
            return "Preserve and share your cultural heritage"
        if value == "self-direction" and tags & {"exchange", "learning", "autonomous"}:
            return "Expand your worldview through independent exploration"

    category = item.get("category", "")
    reason_map = {
        "language_exchange": "Practice languages with real people",
        "cultural_cooking": "Taste the world without traveling",
        "expat_meetup": "Connect with fellow travelers in life",
        "heritage_tour": "Walk through living history",
    }
    return reason_map.get(category, "Bridge cultures and broaden your world")


class CultureBridgeFulfiller(L2Fulfiller):
    """L2 fulfiller for cross-cultural activity wishes — diaspora-friendly.

    Uses keyword matching + values→bridge mapping to select from 15-entry catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        matched_categories = _match_categories(wish.wish_text)
        top_values = detector_results.values.get("top_values", [])
        values_tags = _values_to_bridge_tags(top_values)

        all_tags = list(matched_categories)
        for t in values_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in BRIDGE_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in BRIDGE_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in BRIDGE_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, top_values)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New cross-cultural events added weekly — check back!",
                delay_hours=48,
            ),
        )
