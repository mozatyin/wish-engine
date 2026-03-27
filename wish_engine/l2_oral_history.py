"""OralHistoryFulfiller — oral history recording and preservation resources.

10-entry catalog of family story recording, cultural preservation, and archiving.
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

ORAL_HISTORY_CATALOG: list[dict] = [
    {
        "title": "Family Interview Guide",
        "description": "100+ questions to ask your family — capture stories before they are lost forever.",
        "category": "family_interview_guide",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["family", "interview", "guide", "calming", "self-paced"],
    },
    {
        "title": "Story Recording App",
        "description": "Easy-to-use audio and video recording apps designed for oral history projects.",
        "category": "story_recording_app",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["recording", "app", "technology", "calming", "self-paced"],
    },
    {
        "title": "Photo Digitization Service",
        "description": "Scan and preserve old photos — protect family memories from fading and damage.",
        "category": "photo_digitization",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["photo", "digitization", "preservation", "calming"],
    },
    {
        "title": "Ancestry Research Tools",
        "description": "Trace your family tree — genealogy databases, DNA testing, and record searches.",
        "category": "ancestry_research",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ancestry", "research", "genealogy", "calming", "self-paced"],
    },
    {
        "title": "Community Archive Project",
        "description": "Start a community oral history archive — preserve your neighborhood's collective memory.",
        "category": "community_archive",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["community", "archive", "preservation", "calming"],
    },
    {
        "title": "Immigrant Story Project",
        "description": "Record immigrant and diaspora stories — journeys, sacrifices, and new beginnings.",
        "category": "immigrant_story",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["immigrant", "story", "diaspora", "calming"],
    },
    {
        "title": "War Memory Preservation",
        "description": "Record veteran and civilian war experiences — preserve firsthand accounts of history.",
        "category": "war_memory",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["war", "memory", "history", "calming"],
    },
    {
        "title": "Cultural Tradition Recording",
        "description": "Document cultural traditions — ceremonies, customs, and practices unique to your community.",
        "category": "cultural_tradition_recording",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["cultural", "tradition", "recording", "calming"],
    },
    {
        "title": "Recipe Preservation Project",
        "description": "Record family recipes with the stories behind them — taste is memory.",
        "category": "recipe_preservation",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recipe", "food", "family", "calming", "self-paced"],
    },
    {
        "title": "Language Documentation",
        "description": "Document endangered languages and dialects — preserve linguistic heritage before it fades.",
        "category": "language_documentation",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["language", "documentation", "preservation", "calming"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_ORAL_HISTORY_KEYWORDS: dict[str, list[str]] = {
    "口述历史": [],
    "oral history": [],
    "记录": [],
    "story": [],
    "تاريخ شفوي": [],
    "family story": ["family", "interview"],
    "传承": [],
    "heritage": [],
    "recipe": ["recipe", "food"],
    "食谱": ["recipe", "food"],
    "photo": ["photo", "digitization"],
    "照片": ["photo", "digitization"],
    "ancestry": ["ancestry", "genealogy"],
    "家谱": ["ancestry", "genealogy"],
    "immigrant": ["immigrant", "diaspora"],
    "移民": ["immigrant", "diaspora"],
    "language": ["language", "documentation"],
    "方言": ["language", "documentation"],
}


def _match_oral_history_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _ORAL_HISTORY_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class OralHistoryFulfiller(L2Fulfiller):
    """L2 fulfiller for oral history — recording and preserving stories.

    10 curated entries for family and community history preservation. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_oral_history_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in ORAL_HISTORY_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in ORAL_HISTORY_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in ORAL_HISTORY_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Every story matters. Start recording before memories fade.",
                delay_hours=72,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "family" in tags:
        return "Preserve your family stories for future generations"
    if "preservation" in tags:
        return "Protect cultural heritage from being lost"
    if "community" in tags:
        return "Strengthen your community through shared history"
    if "recording" in tags:
        return "Capture stories in their own voices"
    return "Every story deserves to be remembered"
