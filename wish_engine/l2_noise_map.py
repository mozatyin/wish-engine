"""NoiseMapFulfiller — local-compute noise-level zone recommendation.

10-entry curated catalog of noise-mapped zones. Zero LLM.
Introvert gold: know the noise level before you go.
Keyword matching (English/Chinese/Arabic) routes wish text to relevant
categories, then PersonalityFilter scores and ranks candidates.

Tags: silent/whisper/conversation/lively/nature.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
)

# ── Noise Map Catalog (10 entries) ────────────────────────────────────────────

NOISE_CATALOG: list[dict] = [
    {
        "title": "Silent Zone",
        "description": "Near-zero ambient noise — libraries, meditation halls, silent reading rooms.",
        "category": "silent_zone",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["silent", "quiet", "calming", "indoor", "self-paced"],
    },
    {
        "title": "Whisper Zone",
        "description": "Soft ambient sounds — tea houses, quiet cafes, art galleries.",
        "category": "whisper_zone",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["whisper", "quiet", "calming", "indoor", "self-paced"],
    },
    {
        "title": "Conversation Zone",
        "description": "Comfortable for talking — well-designed cafes and coworking spaces.",
        "category": "conversation_zone",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["conversation", "moderate", "calming", "social", "indoor"],
    },
    {
        "title": "Lively Zone",
        "description": "Energetic buzz — bustling markets, food courts, social hubs.",
        "category": "lively_zone",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["lively", "loud", "social", "energetic", "outdoor"],
    },
    {
        "title": "Loud Zone",
        "description": "High energy — clubs, concert venues, sports bars.",
        "category": "loud_zone",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["loud", "social", "energetic", "intense", "indoor"],
    },
    {
        "title": "Nature Sounds",
        "description": "Birdsong, rustling leaves, flowing streams — natural white noise.",
        "category": "nature_sounds",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nature", "quiet", "calming", "outdoor", "self-paced"],
    },
    {
        "title": "Water Sounds",
        "description": "Fountains, rivers, ocean waves — naturally soothing soundscapes.",
        "category": "water_sounds",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["water", "quiet", "calming", "outdoor", "nature"],
    },
    {
        "title": "Library Quiet",
        "description": "The classic hush — dedicated study spaces with enforced silence.",
        "category": "library_quiet",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["silent", "quiet", "calming", "indoor", "self-paced"],
    },
    {
        "title": "Park Quiet",
        "description": "Open green spaces away from traffic — peaceful outdoor reading spots.",
        "category": "park_quiet",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "calming", "outdoor", "nature", "self-paced"],
    },
    {
        "title": "Rooftop Quiet",
        "description": "Above the city noise — rooftop gardens and terraces with calm views.",
        "category": "rooftop_quiet",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "calming", "outdoor", "scenic", "self-paced"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

NOISE_KEYWORDS: set[str] = {
    "噪音", "noise", "quiet", "安静", "هدوء", "sound", "loud",
    "吵", "silent", "peaceful", "宁静", "白噪音", "white noise",
    "noise level", "嘈杂", "صوت",
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "silent_zone": ["silent", "无声", "صامت", "zero noise"],
    "whisper_zone": ["whisper", "轻声", "低语", "همس"],
    "conversation_zone": ["conversation", "聊天", "talk", "محادثة"],
    "lively_zone": ["lively", "热闹", "bustling", "حيوي"],
    "loud_zone": ["loud", "吵", "noisy", "صاخب"],
    "nature_sounds": ["nature", "自然", "birds", "طبيعة"],
    "water_sounds": ["water", "fountain", "river", "水", "ماء"],
    "library_quiet": ["library", "图书馆", "مكتبة", "study"],
    "park_quiet": ["park", "公园", "حديقة"],
    "rooftop_quiet": ["rooftop", "天台", "سطح", "terrace"],
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    # Detect noise preference
    wants_quiet = any(kw in text_lower for kw in [
        "quiet", "安静", "هدوء", "silent", "peaceful", "宁静", "calm",
    ])
    wants_loud = any(kw in text_lower for kw in [
        "loud", "吵", "lively", "热闹", "energetic", "حيوي",
    ])

    for item in NOISE_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        # Preference-based boost
        if wants_quiet and "quiet" in item.get("tags", []):
            score_boost += 0.15
        if wants_loud and "loud" in item.get("tags", []):
            score_boost += 0.15

        # Introvert personality boost for quiet zones
        mbti = detector_results.mbti
        if mbti.get("type", "") and len(mbti.get("type", "")) == 4:
            if mbti["type"][0] == "I" and "quiet" in item.get("tags", []):
                score_boost += 0.1

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict) -> str:
    """Build a relevance reason for noise map recommendations."""
    reasons = {
        "silent_zone": "Near-zero noise — perfect for deep focus",
        "whisper_zone": "Soft ambient sounds for gentle concentration",
        "conversation_zone": "Comfortable noise level for chatting",
        "lively_zone": "Energetic atmosphere when you want buzz",
        "loud_zone": "High-energy spot for when you want excitement",
        "nature_sounds": "Natural white noise for peaceful moments",
        "water_sounds": "Soothing water sounds to calm the mind",
        "library_quiet": "Classic quiet for focused study",
        "park_quiet": "Peaceful outdoor escape from city noise",
        "rooftop_quiet": "Above the noise with a view",
    }
    return reasons.get(item["category"], "A noise-mapped zone nearby")


class NoiseMapFulfiller(L2Fulfiller):
    """L2 fulfiller for noise-level preference wishes.

    10-entry curated catalog. Introvert gold: know noise before you go.
    Tags: silent/whisper/conversation/lively/nature. Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:max_results]

        return [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "A noise-mapped zone nearby"),
                score=c.get("_personality_score", 0.5),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)
        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="noise_zone", radius_km=3.0),
            reminder_option=ReminderOption(
                text="Found your ideal noise level?",
                delay_hours=4,
            ),
        )
