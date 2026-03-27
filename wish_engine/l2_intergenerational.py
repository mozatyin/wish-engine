"""IntergenerationalFulfiller — cross-age connection activity recommendations.

10-type curated catalog for intergenerational bonding and tradition passing. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Intergenerational Catalog (10 entries) ────────────────────────────────────

INTERGENERATIONAL_CATALOG: list[dict] = [
    {
        "title": "Oral History Project",
        "description": "Record grandparents' stories — preserve family history for future generations.",
        "category": "oral_history_project",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["oral_history_project", "personal", "calming", "quiet", "traditional", "heritage"],
    },
    {
        "title": "Tech Help: Youth to Senior",
        "description": "Young people teaching elders how to use phones, apps, and the internet.",
        "category": "tech_help_youth_to_senior",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["tech_help_youth_to_senior", "practical", "calming", "quiet", "learning"],
    },
    {
        "title": "Cooking Traditions",
        "description": "Grandma's recipes passed down hands-on — cook together, learn together.",
        "category": "cooking_traditions",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["cooking_traditions", "traditional", "calming", "heritage", "practical"],
    },
    {
        "title": "Craft Passing",
        "description": "Learn knitting, woodwork, or calligraphy from an elder who mastered it.",
        "category": "craft_passing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["craft_passing", "traditional", "calming", "quiet", "heritage", "learning"],
    },
    {
        "title": "Cross-Age Mentoring",
        "description": "Pair a senior mentor with a young mentee — wisdom meets ambition.",
        "category": "mentoring_cross_age",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["mentoring_cross_age", "social", "calming", "learning"],
    },
    {
        "title": "Reading Together",
        "description": "Grandparents and grandchildren reading aloud — sharing stories across ages.",
        "category": "reading_together",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["reading_together", "calming", "quiet", "learning"],
    },
    {
        "title": "Mixed-Age Game Night",
        "description": "Board games, card games, and puzzles — fun that bridges generations.",
        "category": "game_night_mixed_age",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["game_night_mixed_age", "social", "calming", "practical"],
    },
    {
        "title": "Garden Together",
        "description": "Plant seeds side by side — teach patience, nurture growth across ages.",
        "category": "garden_together",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["garden_together", "outdoor", "calming", "quiet", "practical"],
    },
    {
        "title": "Story Recording",
        "description": "Record family stories on audio or video — voices to keep forever.",
        "category": "story_recording",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["story_recording", "personal", "calming", "quiet", "heritage"],
    },
    {
        "title": "Wisdom Exchange Circle",
        "description": "Group sessions where elders share life lessons and youth share new perspectives.",
        "category": "wisdom_exchange",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["wisdom_exchange", "social", "calming", "learning", "heritage"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_INTERGENERATIONAL_KEYWORDS: dict[str, list[str]] = {
    "代际": [],
    "intergenerational": [],
    "跨代": [],
    "传承": [],
    "أجيال": [],
    "generations": [],
    "grandparent": [],
    "爷爷奶奶": [],
    "oral history": ["oral_history_project"],
    "口述": ["oral_history_project"],
    "tech help": ["tech_help_youth_to_senior"],
    "教手机": ["tech_help_youth_to_senior"],
    "recipe": ["cooking_traditions"],
    "传统菜": ["cooking_traditions"],
    "craft": ["craft_passing"],
    "手艺": ["craft_passing"],
    "mentor": ["mentoring_cross_age"],
    "read": ["reading_together"],
    "game night": ["game_night_mixed_age"],
    "garden": ["garden_together"],
    "story": ["story_recording", "oral_history_project"],
    "wisdom": ["wisdom_exchange"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _INTERGENERATIONAL_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "oral_history_project": "Preserve priceless family stories before they're lost",
        "tech_help_youth_to_senior": "Bridge the digital divide with patience and love",
        "cooking_traditions": "Family recipes are love letters to the future",
        "craft_passing": "Skills passed hand-to-hand last forever",
        "mentoring_cross_age": "Wisdom and ambition, learning from each other",
        "reading_together": "Stories shared aloud create bonds across ages",
        "game_night_mixed_age": "Fun that brings every generation to the table",
        "garden_together": "Grow something beautiful together — side by side",
        "story_recording": "Capture their voice before it becomes a memory",
        "wisdom_exchange": "Every generation has something valuable to teach",
    }
    return reason_map.get(category, "Strengthening bonds across generations")


class IntergenerationalFulfiller(L2Fulfiller):
    """L2 fulfiller for intergenerational bonding wishes.

    Uses keyword matching to select from 10-type catalog,
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
                dict(item) for item in INTERGENERATIONAL_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in INTERGENERATIONAL_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in INTERGENERATIONAL_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More intergenerational activities — check back soon!",
                delay_hours=48,
            ),
        )
