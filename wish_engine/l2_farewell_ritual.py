"""FarewellRitualFulfiller — culture-aware mourning ritual and ceremony design.

10-entry curated catalog. Covers Islamic janazah, Chinese traditions,
Western memorial, and universal practices. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Farewell Ritual Catalog (10 entries) ─────────────────────────────────────

FAREWELL_RITUAL_CATALOG: list[dict] = [
    {
        "title": "Traditional Funeral Planning",
        "description": "Step-by-step guidance for organizing a traditional funeral ceremony.",
        "category": "traditional_funeral",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["ritual", "traditional", "structured", "community", "formal"],
    },
    {
        "title": "Celebration of Life",
        "description": "Plan a joyful gathering that honors the person's life — stories, laughter, love.",
        "category": "celebration_of_life",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["ritual", "celebration", "community", "joyful", "memorial"],
    },
    {
        "title": "Scattering Ceremony",
        "description": "Plan an ash-scattering ceremony at a meaningful location — sea, mountain, garden.",
        "category": "scattering_ceremony",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ritual", "nature", "intimate", "gentle", "memorial"],
    },
    {
        "title": "Memory Tree Planting",
        "description": "Plant a living memorial — a tree that grows as their legacy lives on.",
        "category": "memory_tree_planting",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ritual", "nature", "living_memorial", "gentle", "hope"],
    },
    {
        "title": "Lantern Release Ceremony",
        "description": "Release lanterns into the sky or onto water — light carrying love upward.",
        "category": "lantern_release",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["ritual", "lantern", "symbolic", "community", "gentle"],
    },
    {
        "title": "Ocean Farewell",
        "description": "A sea-based farewell ceremony — flowers on waves, words to the horizon.",
        "category": "ocean_farewell",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ritual", "ocean", "nature", "intimate", "gentle"],
    },
    {
        "title": "Sky Burial Information",
        "description": "Learn about Tibetan sky burial traditions and their spiritual significance.",
        "category": "sky_burial_info",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ritual", "cultural", "tibetan", "spiritual", "educational"],
    },
    {
        "title": "Digital Memorial Creation",
        "description": "Create an online memorial page — photos, stories, and a place to visit anytime.",
        "category": "digital_memorial",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ritual", "digital", "memorial", "creative", "self_paced"],
    },
    {
        "title": "Anniversary Remembrance Ritual",
        "description": "Design a yearly ritual to honor their memory — candles, letters, shared meals.",
        "category": "anniversary_ritual",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ritual", "anniversary", "structured", "gentle", "recurring"],
    },
    {
        "title": "Personal Goodbye Letter",
        "description": "Write a letter to the person you lost — say what was left unsaid.",
        "category": "personal_goodbye",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ritual", "letter", "solo", "creative", "gentle", "closure"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_FAREWELL_KEYWORDS: dict[str, list[str]] = {
    "告别": ["ritual", "gentle"],
    "farewell": ["ritual", "gentle"],
    "仪式": ["ritual", "structured"],
    "ritual": ["ritual", "structured"],
    "وداع": ["ritual", "gentle"],
    "memorial": ["ritual", "memorial"],
    "纪念": ["ritual", "memorial"],
    "funeral": ["ritual", "traditional"],
    "葬礼": ["ritual", "traditional"],
    "جنازة": ["ritual", "traditional"],
    "janazah": ["ritual", "traditional"],
    "头七": ["ritual", "cultural"],
    "lantern": ["ritual", "lantern"],
    "cremation": ["ritual", "nature"],
    "scattering": ["ritual", "nature"],
    "goodbye": ["ritual", "closure"],
}


def _match_farewell_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _FAREWELL_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class FarewellRitualFulfiller(L2Fulfiller):
    """L2 fulfiller for farewell rituals — culture-aware ceremony design.

    10 curated entries spanning multiple cultural traditions. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_farewell_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in FAREWELL_RITUAL_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in FAREWELL_RITUAL_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in FAREWELL_RITUAL_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="A meaningful farewell is an act of love.",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "traditional" in tags:
        return "A time-honored way to say goodbye"
    if "nature" in tags:
        return "Return to nature — a peaceful farewell"
    if "community" in tags:
        return "Shared remembrance with those who care"
    if "creative" in tags:
        return "Express your goodbye in your own way"
    if "closure" in tags:
        return "Say what needs to be said"
    return "A meaningful farewell ritual"
