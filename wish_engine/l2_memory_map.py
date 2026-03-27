"""MemoryMapFulfiller — personal memory place recommendations.

12 memory types for mapping meaningful places in your life.
Private/personal — star map overlay of meaningful places. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Memory Map Catalog (12 entries) ───────────────────────────────────────────

MEMORY_MAP_CATALOG: list[dict] = [
    {
        "title": "First Date Spot",
        "description": "Revisit or memorialize where your love story began.",
        "category": "first_date_spot",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["first_date_spot", "romantic", "personal", "calming", "quiet"],
    },
    {
        "title": "Childhood Place",
        "description": "The park, school, or street where you grew up — pin it to your map.",
        "category": "childhood_place",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["childhood_place", "personal", "calming", "quiet", "nostalgia"],
    },
    {
        "title": "Graduation Venue",
        "description": "Where you earned your achievement — a milestone worth marking.",
        "category": "graduation_venue",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["graduation_venue", "personal", "achievement", "calming"],
    },
    {
        "title": "Family Home",
        "description": "The house that shaped you — parents' home, grandparents' kitchen.",
        "category": "family_home",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["family_home", "personal", "calming", "quiet", "nostalgia", "traditional"],
    },
    {
        "title": "Travel Memory",
        "description": "That unforgettable trip — the view, the food, the feeling.",
        "category": "travel_memory",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["travel_memory", "personal", "calming", "adventure"],
    },
    {
        "title": "Friendship Place",
        "description": "Where you met your best friend or had that unforgettable moment together.",
        "category": "friendship_place",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["friendship_place", "personal", "social", "calming"],
    },
    {
        "title": "Achievement Location",
        "description": "Where you won, broke through, or proved yourself — mark your victory.",
        "category": "achievement_location",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["achievement_location", "personal", "achievement", "calming"],
    },
    {
        "title": "Healing Place",
        "description": "The quiet spot where you found peace during a hard time.",
        "category": "healing_place",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["healing_place", "personal", "calming", "quiet", "peaceful"],
    },
    {
        "title": "Proposal Spot",
        "description": "Where you asked or were asked — the beginning of forever.",
        "category": "proposal_spot",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["proposal_spot", "romantic", "personal", "calming"],
    },
    {
        "title": "First Job",
        "description": "Where your career began — the office, shop, or studio that started it all.",
        "category": "first_job",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["first_job", "personal", "achievement", "calming", "practical"],
    },
    {
        "title": "Mentor Meeting Place",
        "description": "Where you met someone who changed your path — a cafe, a campus, an office.",
        "category": "mentor_meeting",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["mentor_meeting", "personal", "calming", "learning"],
    },
    {
        "title": "Spiritual Moment",
        "description": "A place of prayer, meditation, or spiritual awakening.",
        "category": "spiritual_moment",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["spiritual_moment", "personal", "calming", "quiet", "peaceful", "traditional"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_MEMORY_KEYWORDS: dict[str, list[str]] = {
    "回忆": [],
    "memory": [],
    "纪念": [],
    "remember": [],
    "ذكرى": [],
    "special place": [],
    "meaningful": [],
    "first date": ["first_date_spot"],
    "初次约会": ["first_date_spot"],
    "childhood": ["childhood_place"],
    "童年": ["childhood_place"],
    "graduation": ["graduation_venue"],
    "毕业": ["graduation_venue"],
    "family home": ["family_home"],
    "老家": ["family_home"],
    "travel": ["travel_memory"],
    "旅行": ["travel_memory"],
    "friend": ["friendship_place"],
    "朋友": ["friendship_place"],
    "proposal": ["proposal_spot"],
    "求婚": ["proposal_spot"],
    "first job": ["first_job"],
    "第一份工作": ["first_job"],
    "mentor": ["mentor_meeting"],
    "spiritual": ["spiritual_moment"],
    "healing": ["healing_place"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _MEMORY_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "first_date_spot": "Where your love story began",
        "childhood_place": "The roots that made you who you are",
        "graduation_venue": "A milestone worth remembering",
        "family_home": "The place that shaped your heart",
        "travel_memory": "Adventures that changed your perspective",
        "friendship_place": "Where a bond was forged",
        "achievement_location": "Where you proved what you're capable of",
        "healing_place": "Your sanctuary when you needed it most",
        "proposal_spot": "The beginning of forever",
        "first_job": "Where your journey started",
        "mentor_meeting": "Where wisdom found you",
        "spiritual_moment": "A place of deep inner peace",
    }
    return reason_map.get(category, "A meaningful place in your story")


class MemoryMapFulfiller(L2Fulfiller):
    """L2 fulfiller for memory/nostalgia wishes — personal place mapping.

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
                dict(item) for item in MEMORY_MAP_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in MEMORY_MAP_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in MEMORY_MAP_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Add more memories to your map anytime!",
                delay_hours=72,
            ),
        )
