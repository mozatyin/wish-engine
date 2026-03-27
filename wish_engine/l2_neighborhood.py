"""NeighborhoodFulfiller — local community connection recommendations.

12-type curated catalog for neighborhood engagement and community building. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Neighborhood Catalog (12 entries) ─────────────────────────────────────────

NEIGHBORHOOD_CATALOG: list[dict] = [
    {
        "title": "Community Bulletin Board",
        "description": "Post and browse local announcements, events, and services.",
        "category": "community_board",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["community_board", "local", "practical", "quiet", "calming"],
    },
    {
        "title": "Neighborhood Watch Group",
        "description": "Join your local safety network — neighbors looking out for each other.",
        "category": "neighborhood_watch",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["neighborhood_watch", "local", "practical", "social"],
    },
    {
        "title": "Block Party Organizer",
        "description": "Plan a street party — food, music, and meeting your neighbors.",
        "category": "block_party",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["block_party", "local", "social", "celebration"],
    },
    {
        "title": "Community Garden",
        "description": "Shared garden plots — grow vegetables, flowers, and friendships.",
        "category": "community_garden",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["community_garden", "local", "outdoor", "calming", "quiet", "practical"],
    },
    {
        "title": "Local Newsletter",
        "description": "Stay informed with neighborhood news, events, and local business spotlights.",
        "category": "local_newsletter",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["local_newsletter", "local", "practical", "quiet", "calming"],
    },
    {
        "title": "Welcome Committee",
        "description": "Help new neighbors feel at home — welcome baskets and introductions.",
        "category": "welcome_committee",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["welcome_committee", "local", "social", "calming", "helping"],
    },
    {
        "title": "Carpool Group",
        "description": "Share rides with neighbors — save money and reduce your carbon footprint.",
        "category": "carpool_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["carpool_group", "local", "practical", "calming"],
    },
    {
        "title": "Tool Library",
        "description": "Borrow tools from the community — drills, ladders, lawnmowers, and more.",
        "category": "tool_library",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["tool_library", "local", "practical", "quiet", "calming"],
    },
    {
        "title": "Community Kitchen",
        "description": "Shared cooking spaces for meal prep, potlucks, and cooking classes.",
        "category": "community_kitchen",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["community_kitchen", "local", "social", "practical"],
    },
    {
        "title": "Local Skill Share",
        "description": "Teach and learn from neighbors — languages, crafts, tech, and more.",
        "category": "skill_share_local",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["skill_share_local", "local", "learning", "social", "calming"],
    },
    {
        "title": "Emergency Contact Network",
        "description": "Build a local emergency contact list — be prepared, stay connected.",
        "category": "emergency_contacts",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["emergency_contacts", "local", "practical", "quiet"],
    },
    {
        "title": "Community Cleanup Day",
        "description": "Organize a neighborhood cleanup — cleaner streets, stronger bonds.",
        "category": "community_cleanup",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["community_cleanup", "local", "outdoor", "social", "helping"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_NEIGHBORHOOD_KEYWORDS: dict[str, list[str]] = {
    "邻里": [],
    "neighborhood": [],
    "社区": [],
    "community": [],
    "جيران": [],
    "local": [],
    "neighbour": [],
    "block party": ["block_party"],
    "garden": ["community_garden"],
    "花园": ["community_garden"],
    "carpool": ["carpool_group"],
    "拼车": ["carpool_group"],
    "tool": ["tool_library"],
    "工具": ["tool_library"],
    "kitchen": ["community_kitchen"],
    "cleanup": ["community_cleanup"],
    "清洁": ["community_cleanup"],
    "newsletter": ["local_newsletter"],
    "watch": ["neighborhood_watch"],
    "welcome": ["welcome_committee"],
    "emergency": ["emergency_contacts"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _NEIGHBORHOOD_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "community_board": "Stay connected with what's happening nearby",
        "neighborhood_watch": "Safety starts with neighbors who care",
        "block_party": "Meet your neighbors and build real connections",
        "community_garden": "Grow food and friendships in your own backyard",
        "local_newsletter": "Know your neighborhood inside and out",
        "welcome_committee": "Help newcomers feel they belong",
        "carpool_group": "Save money and make a commute buddy",
        "tool_library": "Why buy when you can borrow from neighbors?",
        "community_kitchen": "Cook together, eat together, thrive together",
        "skill_share_local": "Learn something new from a neighbor",
        "emergency_contacts": "Be prepared — know who to call nearby",
        "community_cleanup": "A cleaner neighborhood starts with you",
    }
    return reason_map.get(category, "Build a stronger community together")


class NeighborhoodFulfiller(L2Fulfiller):
    """L2 fulfiller for neighborhood/community wishes.

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
                dict(item) for item in NEIGHBORHOOD_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in NEIGHBORHOOD_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in NEIGHBORHOOD_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More community activities — check back soon!",
                delay_hours=48,
            ),
        )
