"""MotherTongueFulfiller — heritage language learning and preservation resources.

10-entry catalog for reconnecting with mother tongue and heritage languages.
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

MOTHER_TONGUE_CATALOG: list[dict] = [
    {
        "title": "Heritage Language Class",
        "description": "Find classes for your heritage language — designed for heritage speakers, not beginners.",
        "category": "language_class_heritage",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["class", "heritage", "learning", "calming"],
    },
    {
        "title": "Bilingual School Finder",
        "description": "Find bilingual and dual-language schools for your children — raise bilingual kids.",
        "category": "bilingual_school",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["bilingual", "school", "children", "calming"],
    },
    {
        "title": "Heritage Language Exchange",
        "description": "Language exchange partners who speak your heritage language — practice conversation.",
        "category": "language_exchange_heritage",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["exchange", "conversation", "social", "calming"],
    },
    {
        "title": "Cultural Media in Mother Tongue",
        "description": "Movies, music, podcasts, and books in your heritage language — immerse yourself.",
        "category": "cultural_media",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["media", "immersion", "culture", "calming", "self-paced"],
    },
    {
        "title": "Heritage Language App",
        "description": "Apps designed for heritage speakers — vocabulary recovery, reading, and writing practice.",
        "category": "heritage_language_app",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["app", "technology", "learning", "calming", "self-paced"],
    },
    {
        "title": "Immersion Program",
        "description": "Short-term immersion programs — live and learn in a heritage language environment.",
        "category": "immersion_program",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["immersion", "travel", "intensive", "calming"],
    },
    {
        "title": "Heritage Language Camp",
        "description": "Summer camps and retreats for heritage language speakers — fun and language combined.",
        "category": "language_camp",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["camp", "social", "fun", "calming"],
    },
    {
        "title": "Storytelling in Mother Tongue",
        "description": "Storytelling circles in your heritage language — oral tradition meets community.",
        "category": "storytelling_in_mother_tongue",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["storytelling", "oral", "tradition", "calming"],
    },
    {
        "title": "Heritage Language Tutor",
        "description": "One-on-one tutoring for your heritage language — personalized to your level.",
        "category": "heritage_language_tutor",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["tutor", "personal", "learning", "calming"],
    },
    {
        "title": "Language Community Group",
        "description": "Join a community of heritage language speakers — weekly meetups and cultural events.",
        "category": "language_community",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["community", "social", "heritage", "calming"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_MOTHER_TONGUE_KEYWORDS: dict[str, list[str]] = {
    "母语": [],
    "mother tongue": [],
    "heritage language": ["heritage"],
    "لغة أم": [],
    "native language": [],
    "bilingual": ["bilingual", "children"],
    "双语": ["bilingual", "children"],
    "immersion": ["immersion", "intensive"],
    "沉浸": ["immersion", "intensive"],
    "tutor": ["tutor", "personal"],
    "家教": ["tutor", "personal"],
    "storytelling": ["storytelling", "oral"],
    "故事": ["storytelling", "oral"],
    "language exchange": ["exchange", "conversation"],
}


def _match_mother_tongue_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _MOTHER_TONGUE_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class MotherTongueFulfiller(L2Fulfiller):
    """L2 fulfiller for mother tongue — heritage language learning and preservation.

    10 curated entries for reconnecting with heritage languages. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_mother_tongue_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in MOTHER_TONGUE_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in MOTHER_TONGUE_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in MOTHER_TONGUE_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Your language carries the soul of your culture. Keep it alive.",
                delay_hours=72,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "heritage" in tags:
        return "Reconnect with the language of your heritage"
    if "community" in tags or "social" in tags:
        return "Practice with others who share your language roots"
    if "learning" in tags:
        return "Structured learning path for heritage speakers"
    if "immersion" in tags:
        return "Full immersion for rapid language recovery"
    return "Strengthen your connection to your mother tongue"
