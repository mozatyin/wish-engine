"""ElderlyCareFulfiller — gentle, accessible activity recommendations for seniors.

12-type curated catalog with quiet/gentle/accessible tags. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Elderly Care Catalog (12 entries) ─────────────────────────────────────────

ELDERLY_CATALOG: list[dict] = [
    {
        "title": "Quiet Park Bench Spots",
        "description": "Peaceful park benches with shade, scenic views, and easy access.",
        "category": "quiet_park_bench",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet_park_bench", "outdoor", "quiet", "calming", "accessible", "gentle"],
    },
    {
        "title": "Gentle Exercise Class",
        "description": "Low-impact stretching, chair yoga, and balance exercises for seniors.",
        "category": "gentle_exercise",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["gentle_exercise", "indoor", "calming", "accessible", "gentle", "quiet"],
    },
    {
        "title": "Tea House Visit",
        "description": "Quiet tea houses with comfortable seating — perfect for a peaceful afternoon.",
        "category": "tea_house",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["tea_house", "indoor", "quiet", "calming", "gentle", "traditional"],
    },
    {
        "title": "Senior Community Center",
        "description": "Social activities, classes, and companionship at a nearby senior center.",
        "category": "senior_center",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["senior_center", "indoor", "social", "accessible", "gentle"],
    },
    {
        "title": "Slow Walk Trail",
        "description": "Flat, paved walking trails with benches and rest stops along the way.",
        "category": "slow_walk_trail",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["slow_walk_trail", "outdoor", "quiet", "calming", "accessible", "gentle"],
    },
    {
        "title": "Classical Concert",
        "description": "Afternoon classical music performances in comfortable, seated venues.",
        "category": "classical_concert",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["classical_concert", "indoor", "calming", "quiet", "gentle"],
    },
    {
        "title": "Museum Quiet Hours",
        "description": "Special senior-friendly museum hours with reduced crowds and guided tours.",
        "category": "museum_quiet_hours",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["museum_quiet_hours", "indoor", "quiet", "calming", "accessible", "learning"],
    },
    {
        "title": "Tai Chi in the Park",
        "description": "Gentle tai chi sessions outdoors — balance, breathing, and peace of mind.",
        "category": "tai_chi",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["tai_chi", "outdoor", "quiet", "calming", "gentle", "accessible"],
    },
    {
        "title": "Chess & Board Game Club",
        "description": "Friendly chess and board game meetups — keep the mind sharp and social.",
        "category": "chess_club",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["chess_club", "indoor", "quiet", "calming", "gentle", "practical"],
    },
    {
        "title": "Garden Club",
        "description": "Community gardening with raised beds — fresh air and gentle exercise.",
        "category": "garden_club",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["garden_club", "outdoor", "quiet", "calming", "gentle", "practical"],
    },
    {
        "title": "Senior Swimming Session",
        "description": "Warm-water pool sessions at a gentle pace — great for joints and mobility.",
        "category": "senior_swimming",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["senior_swimming", "indoor", "calming", "accessible", "gentle"],
    },
    {
        "title": "Memory Care Activities",
        "description": "Guided memory exercises, photo sharing, and storytelling sessions.",
        "category": "memory_care",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["memory_care", "indoor", "quiet", "calming", "gentle", "accessible"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_ELDERLY_KEYWORDS: dict[str, list[str]] = {
    "长辈": [],
    "elderly": [],
    "老人": [],
    "senior": [],
    "كبار السن": [],
    "parent": [],
    "爸妈": [],
    "grandparent": [],
    "奶奶": [],
    "爷爷": [],
    "park": ["quiet_park_bench", "slow_walk_trail"],
    "公园": ["quiet_park_bench", "slow_walk_trail"],
    "exercise": ["gentle_exercise"],
    "tea": ["tea_house"],
    "茶": ["tea_house"],
    "tai chi": ["tai_chi"],
    "太极": ["tai_chi"],
    "chess": ["chess_club"],
    "garden": ["garden_club"],
    "swim": ["senior_swimming"],
    "concert": ["classical_concert"],
    "museum": ["museum_quiet_hours"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _ELDERLY_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "quiet_park_bench": "A peaceful spot to sit and enjoy nature",
        "gentle_exercise": "Stay active with low-impact movement",
        "tea_house": "A quiet place to relax and savor the moment",
        "senior_center": "Community and companionship close to home",
        "slow_walk_trail": "A gentle walk at your own pace",
        "classical_concert": "Beautiful music in a comfortable setting",
        "museum_quiet_hours": "Explore art and history at a relaxed pace",
        "tai_chi": "Balance, breathing, and inner peace",
        "chess_club": "Keep the mind sharp with good company",
        "garden_club": "Nurture plants and friendships together",
        "senior_swimming": "Gentle on the body, great for the spirit",
        "memory_care": "Meaningful activities that spark joy and connection",
    }
    return reason_map.get(category, "A gentle, accessible activity for comfort and joy")


class ElderlyCareFulfiller(L2Fulfiller):
    """L2 fulfiller for elderly care wishes — gentle, accessible recommendations.

    Uses keyword matching to select from 12-type catalog. All entries are
    quiet/gentle/accessible. Applies PersonalityFilter. Zero LLM.
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
                dict(item) for item in ELDERLY_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in ELDERLY_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in ELDERLY_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More gentle activities nearby — check back soon!",
                delay_hours=24,
            ),
        )
