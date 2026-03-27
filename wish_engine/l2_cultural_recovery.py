"""CulturalRecoveryFulfiller — cultural recovery and tradition revival resources.

10-entry catalog for reconnecting with traditional practices and cultural heritage.
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

CULTURAL_RECOVERY_CATALOG: list[dict] = [
    {
        "title": "Traditional Ceremony Guide",
        "description": "Learn about and participate in traditional ceremonies from your cultural heritage.",
        "category": "traditional_ceremony",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["ceremony", "tradition", "spiritual", "calming"],
    },
    {
        "title": "Indigenous Practice Revival",
        "description": "Reconnect with indigenous practices — land-based learning, ceremonies, and community.",
        "category": "indigenous_practice",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["indigenous", "practice", "community", "calming"],
    },
    {
        "title": "Cultural Celebration Planning",
        "description": "Plan cultural celebrations — traditional holidays, harvest festivals, and coming-of-age rites.",
        "category": "cultural_celebration",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["celebration", "festival", "community", "social", "calming"],
    },
    {
        "title": "Traditional Medicine Knowledge",
        "description": "Explore traditional medicine practices — herbal knowledge, healing traditions, and wellness.",
        "category": "traditional_medicine_knowledge",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["medicine", "traditional", "healing", "calming", "self-paced"],
    },
    {
        "title": "Traditional Music Learning",
        "description": "Learn traditional instruments and songs — preserve musical heritage through practice.",
        "category": "traditional_music",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["music", "traditional", "learning", "calming"],
    },
    {
        "title": "Traditional Dance Classes",
        "description": "Learn traditional dances from your culture — folk dance, ceremonial dance, and social dance.",
        "category": "traditional_dance",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["dance", "traditional", "movement", "calming"],
    },
    {
        "title": "Traditional Clothing Guide",
        "description": "Learn about and find traditional clothing — textile arts, cultural dress, and occasion wear.",
        "category": "traditional_clothing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["clothing", "textile", "traditional", "calming", "self-paced"],
    },
    {
        "title": "Sacred Site Visits",
        "description": "Visit sacred and culturally significant sites — pilgrimages, temples, and ancestral lands.",
        "category": "sacred_site_visit",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sacred", "travel", "spiritual", "calming"],
    },
    {
        "title": "Elder Wisdom Circle",
        "description": "Learn from cultural elders — wisdom keepers, storytellers, and tradition bearers.",
        "category": "elder_wisdom",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["elder", "wisdom", "oral", "community", "calming"],
    },
    {
        "title": "Cultural Revival Movement",
        "description": "Join movements reviving endangered cultures — language, art, food, and spiritual practices.",
        "category": "cultural_revival_movement",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["revival", "movement", "community", "activism", "calming"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_CULTURAL_RECOVERY_KEYWORDS: dict[str, list[str]] = {
    "文化恢复": [],
    "cultural recovery": [],
    "传统": [],
    "tradition": ["tradition"],
    "تراث": [],
    "indigenous": ["indigenous", "practice"],
    "复兴": ["revival", "movement"],
    "revival": ["revival", "movement"],
    "ceremony": ["ceremony", "spiritual"],
    "仪式": ["ceremony", "spiritual"],
    "elder": ["elder", "wisdom"],
    "长老": ["elder", "wisdom"],
    "sacred": ["sacred", "spiritual"],
    "圣地": ["sacred", "spiritual"],
    "dance": ["dance", "movement"],
    "舞蹈": ["dance", "movement"],
    "music": ["music", "traditional"],
    "medicine": ["medicine", "healing"],
}


def _match_cultural_recovery_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _CULTURAL_RECOVERY_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class CulturalRecoveryFulfiller(L2Fulfiller):
    """L2 fulfiller for cultural recovery — tradition revival and heritage reconnection.

    10 curated entries for cultural preservation and practice. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_cultural_recovery_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in CULTURAL_RECOVERY_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in CULTURAL_RECOVERY_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in CULTURAL_RECOVERY_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Culture lives through practice. Every step toward revival matters.",
                delay_hours=72,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "tradition" in tags:
        return "Reconnect with the traditions that define your culture"
    if "community" in tags:
        return "Join others in keeping your culture alive"
    if "spiritual" in tags:
        return "Deepen your connection to spiritual heritage"
    if "learning" in tags:
        return "Learn traditional arts and practices firsthand"
    return "Revive and celebrate your cultural heritage"
