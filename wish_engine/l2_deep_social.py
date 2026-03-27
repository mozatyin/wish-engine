"""DeepSocialFulfiller — deep connection format recommendations.

15-entry curated catalog for people who want depth not breadth.
Ideal for INFJ/INFP/INTJ types. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── MBTI → Deep Social Style Mapping ─────────────────────────────────────────

MBTI_DEEP_MAP: dict[str, list[str]] = {
    "I": ["small_group", "one_on_one", "reflective", "quiet"],
    "E": ["group", "structured_group", "facilitated"],
    "N": ["philosophical", "abstract", "symbolic", "existential"],
    "S": ["practical", "hands_on", "activity_based"],
    "T": ["debate", "analytical", "structured"],
    "F": ["vulnerability", "emotional", "storytelling", "empathic"],
    "J": ["structured", "facilitated", "scheduled"],
    "P": ["spontaneous", "organic", "exploratory"],
}

# ── Deep Social Catalog (15 entries) ─────────────────────────────────────────

DEEP_SOCIAL_CATALOG: list[dict] = [
    {
        "title": "Philosophical Cafe",
        "description": "Structured discussion on a big question — 'What is a good life?' No small talk.",
        "category": "philosophical_cafe",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["philosophical", "structured", "small_group", "debate", "existential"],
    },
    {
        "title": "Death Cafe",
        "description": "Open discussion about mortality over tea and cake. Surprisingly life-affirming.",
        "category": "death_cafe",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["existential", "vulnerability", "small_group", "emotional", "quiet"],
    },
    {
        "title": "Story Exchange",
        "description": "Two strangers, two stories, one hour. No interrupting. Deep listening.",
        "category": "story_exchange",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["storytelling", "one_on_one", "vulnerability", "emotional", "reflective"],
    },
    {
        "title": "36 Questions Dinner",
        "description": "The famous NYT 36 questions that lead to love — or at least real connection.",
        "category": "36_questions_dinner",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["structured", "one_on_one", "vulnerability", "emotional", "reflective"],
    },
    {
        "title": "Silent Retreat Group",
        "description": "Days of shared silence. Paradox: connection deepens without words.",
        "category": "silent_retreat_group",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "reflective", "small_group", "existential", "calming"],
    },
    {
        "title": "Book Deep Dive",
        "description": "One book, 4 people, 3 hours. Go deep — not a book club, a book excavation.",
        "category": "book_deep_dive",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["analytical", "small_group", "structured", "reflective", "philosophical"],
    },
    {
        "title": "Documentary Discussion Night",
        "description": "Watch together, then discuss for longer than the film lasted.",
        "category": "documentary_discussion",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["analytical", "structured_group", "debate", "small_group"],
    },
    {
        "title": "Life Story Sharing Circle",
        "description": "Each person shares a chapter of their life. No advice — just witness.",
        "category": "life_story_sharing",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["storytelling", "vulnerability", "emotional", "small_group", "empathic"],
    },
    {
        "title": "Vulnerability Circle",
        "description": "Structured sharing of fears, failures, and hopes. Brave space, not just safe space.",
        "category": "vulnerability_circle",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["vulnerability", "emotional", "facilitated", "empathic", "small_group"],
    },
    {
        "title": "Mentoring Pair",
        "description": "One-on-one mentoring relationship — depth through consistent presence.",
        "category": "mentoring_pair",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["one_on_one", "structured", "practical", "hands_on", "reflective"],
    },
    {
        "title": "Walking Dialogue",
        "description": "Side-by-side walking removes eye contact pressure. Best conversations happen in motion.",
        "category": "walking_dialogue",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["one_on_one", "organic", "quiet", "reflective", "activity_based"],
    },
    {
        "title": "Fireside Chat",
        "description": "A fire, a few people, and questions that matter. Ancient format, timeless depth.",
        "category": "fireside_chat",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["small_group", "organic", "storytelling", "quiet", "reflective"],
    },
    {
        "title": "Art Interpretation Evening",
        "description": "Stand before a painting and share what you see. No right answers — only perspectives.",
        "category": "art_interpretation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["symbolic", "philosophical", "small_group", "reflective", "abstract"],
    },
    {
        "title": "Dream Sharing Circle",
        "description": "Share last night's dream and explore symbols together. Intimate and surprising.",
        "category": "dream_sharing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["symbolic", "vulnerability", "small_group", "abstract", "exploratory"],
    },
    {
        "title": "Grief Support Circle",
        "description": "For those carrying loss. Shared grief halves its weight.",
        "category": "grief_support_circle",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["emotional", "empathic", "facilitated", "vulnerability", "small_group"],
    },
]


def _match_deep_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    kw_map = {
        "philosophy": ["philosophical", "existential"],
        "哲学": ["philosophical", "existential"],
        "story": ["storytelling", "emotional"],
        "故事": ["storytelling", "emotional"],
        "vulnerable": ["vulnerability", "emotional"],
        "脆弱": ["vulnerability", "emotional"],
        "book": ["analytical", "reflective"],
        "书": ["analytical", "reflective"],
        "one on one": ["one_on_one"],
        "一对一": ["one_on_one"],
        "grief": ["emotional", "empathic"],
        "悲伤": ["emotional", "empathic"],
        "dream": ["symbolic", "abstract"],
        "梦": ["symbolic", "abstract"],
        "silence": ["quiet", "reflective"],
        "沉默": ["quiet", "reflective"],
        "mentor": ["one_on_one", "structured"],
        "导师": ["one_on_one", "structured"],
    }
    for keyword, tags in kw_map.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


def _mbti_to_deep_tags(det: DetectorResults) -> list[str]:
    tags: list[str] = []
    mbti_type = det.mbti.get("type", "")
    if len(mbti_type) == 4:
        for letter in mbti_type:
            for t in MBTI_DEEP_MAP.get(letter, []):
                if t not in tags:
                    tags.append(t)
    return tags


class DeepSocialFulfiller(L2Fulfiller):
    """L2 fulfiller for deep social connection — MBTI-matched depth formats.

    15 deep connection formats for INFx/INTx who want depth. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_deep_tags(wish.wish_text)
        mbti_tags = _mbti_to_deep_tags(detector_results)

        all_tags = list(keyword_tags)
        for t in mbti_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in DEEP_SOCIAL_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in DEEP_SOCIAL_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in DEEP_SOCIAL_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Deep connection takes courage. Try one this week.",
                delay_hours=72,
            ),
        )


def _build_relevance_reason(item: dict, det: DetectorResults) -> str:
    tags = set(item.get("tags", []))
    mbti = det.mbti.get("type", "")

    if mbti and len(mbti) == 4:
        if mbti[0] == "I" and "one_on_one" in tags:
            return "One-on-one format perfect for introverts seeking depth"
        if mbti[1] == "N" and "philosophical" in tags:
            return "Philosophical exploration matching your intuitive mind"
        if mbti[2] == "F" and "emotional" in tags:
            return "Emotional depth that speaks to your Feeling preference"
        if mbti[2] == "T" and "analytical" in tags:
            return "Analytical deep dive matching your Thinking preference"

    if "vulnerability" in tags:
        return "Vulnerability is the birthplace of real connection"

    return f"Deep connection format: {item.get('category', '').replace('_', ' ')}"
