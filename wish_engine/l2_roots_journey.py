"""RootsJourneyFulfiller — heritage and ancestry exploration resources.

10-entry catalog for reconnecting with roots, homeland, and cultural origins.
Zero LLM.
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

ROOTS_CATALOG: list[dict] = [
    {
        "title": "Ancestry DNA Testing",
        "description": "Discover your genetic heritage — DNA testing services with cultural context.",
        "category": "ancestry_dna",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dna", "ancestry", "discovery", "calming", "self-paced"],
    },
    {
        "title": "Homeland Visit Planning",
        "description": "Plan a meaningful trip to your ancestral homeland — guides, contacts, and cultural prep.",
        "category": "homeland_visit",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["homeland", "travel", "planning", "calming"],
    },
    {
        "title": "Cultural Heritage Sites",
        "description": "Visit UNESCO sites and cultural landmarks connected to your heritage.",
        "category": "cultural_heritage_site",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["heritage", "culture", "travel", "calming"],
    },
    {
        "title": "Diaspora Community Connection",
        "description": "Find your diaspora community locally — people who share your cultural background.",
        "category": "diaspora_community",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["diaspora", "community", "social", "calming"],
    },
    {
        "title": "Family Reunion Planner",
        "description": "Organize a family reunion — reconnect with extended family across distances.",
        "category": "family_reunion",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["family", "reunion", "planning", "social", "calming"],
    },
    {
        "title": "Genealogy Research Guide",
        "description": "Deep genealogy research — archives, public records, and oral history techniques.",
        "category": "genealogy_research",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["genealogy", "research", "ancestry", "calming", "self-paced"],
    },
    {
        "title": "Cultural Festival of Origin",
        "description": "Attend festivals celebrating your cultural heritage — music, food, and tradition.",
        "category": "cultural_festival_origin",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["festival", "culture", "celebration", "social"],
    },
    {
        "title": "Traditional Craft Learning",
        "description": "Learn traditional crafts from your culture — weaving, pottery, calligraphy, and more.",
        "category": "traditional_craft_learning",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["craft", "traditional", "learning", "calming"],
    },
    {
        "title": "Indigenous Connection Program",
        "description": "Reconnect with indigenous heritage — cultural programs, language, and community.",
        "category": "indigenous_connection",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["indigenous", "heritage", "community", "calming"],
    },
    {
        "title": "Adoption Search Support",
        "description": "Resources for adoptees searching for biological roots — registries, support groups, and guidance.",
        "category": "adoption_search",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["adoption", "search", "support", "calming", "gentle"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_ROOTS_KEYWORDS: dict[str, list[str]] = {
    "寻根": [],
    "roots": [],
    "heritage": ["heritage"],
    "ancestry": ["ancestry", "dna"],
    "جذور": [],
    "homeland": ["homeland", "travel"],
    "故乡": ["homeland", "travel"],
    "diaspora": ["diaspora", "community"],
    "genealogy": ["genealogy", "research"],
    "族谱": ["genealogy", "research"],
    "family reunion": ["family", "reunion"],
    "indigenous": ["indigenous", "heritage"],
    "原住民": ["indigenous", "heritage"],
    "adoption": ["adoption", "search"],
    "领养": ["adoption", "search"],
    "dna": ["dna", "ancestry"],
}


def _match_roots_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _ROOTS_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class RootsJourneyFulfiller(L2Fulfiller):
    """L2 fulfiller for roots journey — heritage and ancestry exploration.

    10 curated entries for reconnecting with cultural origins. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_roots_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in ROOTS_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in ROOTS_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in ROOTS_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Knowing where you come from helps you know where you are going.",
                delay_hours=168,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "ancestry" in tags or "dna" in tags:
        return "Discover the story written in your DNA"
    if "community" in tags:
        return "Connect with people who share your heritage"
    if "heritage" in tags:
        return "Reconnect with the culture that shaped you"
    if "travel" in tags:
        return "Walk the land your ancestors knew"
    return "Explore the roots that ground your identity"
