"""LegacyPlanningFulfiller — legacy and purpose-driven planning resources.

10-entry catalog of ways to create lasting meaning and impact. Zero LLM.
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

LEGACY_CATALOG: list[dict] = [
    {
        "title": "Ethical Will Writing",
        "description": "Write a letter of values, wishes, and life lessons for future generations — not money, meaning.",
        "category": "ethical_will",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ethical_will", "values", "writing", "calming", "self-paced"],
    },
    {
        "title": "Life Story Recording",
        "description": "Record your life story — guided prompts, audio/video recording tools, and memoir templates.",
        "category": "life_story_recording",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["story", "recording", "memoir", "calming", "self-paced"],
    },
    {
        "title": "Mentoring Next Generation",
        "description": "Become a mentor — share your expertise with young people who need guidance.",
        "category": "mentoring_next_gen",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["mentoring", "youth", "community", "calming"],
    },
    {
        "title": "Community Project Starter",
        "description": "Launch a community project that outlives you — parks, libraries, programs, gardens.",
        "category": "community_project",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["community", "project", "impact", "calming"],
    },
    {
        "title": "Scholarship Creation Guide",
        "description": "Create a scholarship fund — help future students pursue their dreams.",
        "category": "scholarship_creation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["scholarship", "education", "giving", "calming"],
    },
    {
        "title": "Tree Planting Legacy",
        "description": "Plant trees that will grow for generations — memorial forests and community orchards.",
        "category": "tree_planting_legacy",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["trees", "nature", "environmental", "calming"],
    },
    {
        "title": "Art Collection Curation",
        "description": "Build a meaningful art collection — supporting artists and preserving culture.",
        "category": "art_collection",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["art", "culture", "curation", "calming", "self-paced"],
    },
    {
        "title": "Family Archive Project",
        "description": "Digitize and organize family photos, documents, and heirlooms for future generations.",
        "category": "family_archive",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["family", "archive", "preservation", "calming", "self-paced"],
    },
    {
        "title": "Wisdom Letter Writing",
        "description": "Write letters of wisdom to be opened at future milestones — graduations, weddings, births.",
        "category": "wisdom_letter",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wisdom", "writing", "values", "calming", "self-paced"],
    },
    {
        "title": "Charitable Trust Setup",
        "description": "Create a charitable trust — structured giving that continues beyond your lifetime.",
        "category": "charitable_trust",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["charitable", "trust", "giving", "calming"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_LEGACY_KEYWORDS: dict[str, list[str]] = {
    "遗产": [],
    "legacy": [],
    "留给": [],
    "leave behind": [],
    "إرث": [],
    "purpose": [],
    "意义": [],
    "mentor": ["mentoring", "youth"],
    "导师": ["mentoring", "youth"],
    "story": ["story", "recording"],
    "故事": ["story", "recording"],
    "scholarship": ["scholarship", "education"],
    "奖学金": ["scholarship", "education"],
    "family": ["family", "archive"],
    "wisdom": ["wisdom", "writing"],
    "charitable": ["charitable", "giving"],
    "慈善": ["charitable", "giving"],
}


def _match_legacy_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _LEGACY_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class LegacyPlanningFulfiller(L2Fulfiller):
    """L2 fulfiller for legacy planning — creating lasting meaning and impact.

    10 curated entries for purpose-driven legacy creation. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_legacy_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in LEGACY_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in LEGACY_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in LEGACY_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="The best time to plant a tree was 20 years ago. The second best time is now.",
                delay_hours=168,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "values" in tags:
        return "Pass on what matters most — your values and wisdom"
    if "community" in tags:
        return "Create something that uplifts your community"
    if "giving" in tags:
        return "Generosity that continues beyond your lifetime"
    if "preservation" in tags:
        return "Preserve your family story for future generations"
    return "Create a legacy of meaning and purpose"
