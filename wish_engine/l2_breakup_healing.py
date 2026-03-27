"""BreakupHealingFulfiller — attachment-aware healing activity recommendations.

15-entry curated healing catalog. Avoids places associated with ex
(conceptual — tags 'new_area'). Attachment-aware: anxious→structure,
avoidant→space. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Attachment → Healing Mapping ─────────────────────────────────────────────

ATTACHMENT_HEALING_MAP: dict[str, list[str]] = {
    "anxious": ["structured", "social_support", "routine", "guided", "body"],
    "avoidant": ["solo", "space", "creative", "self_paced", "nature"],
    "secure": ["balanced", "social_support", "creative", "nature", "body"],
    "fearful": ["gentle", "guided", "solo", "nature", "structured"],
}

EMOTION_HEALING_MAP: dict[str, list[str]] = {
    "sadness": ["gentle", "nature", "creative", "social_support"],
    "anger": ["body", "nature", "solo", "creative"],
    "anxiety": ["structured", "guided", "body", "routine"],
}

# ── Healing Catalog (15 entries) ─────────────────────────────────────────────

HEALING_CATALOG: list[dict] = [
    {
        "title": "Solo Cafe in a New Area",
        "description": "Discover a cafe you have never been to — new space, new start, no old memories.",
        "category": "solo_cafe_new_area",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solo", "new_area", "gentle", "self_paced", "space"],
    },
    {
        "title": "Nature Walk on a New Trail",
        "description": "Fresh air, unfamiliar trees — let a trail you have never walked reset your mind.",
        "category": "nature_walk_new_trail",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solo", "nature", "new_area", "gentle", "body", "space"],
    },
    {
        "title": "Journaling Prompt Session",
        "description": "Guided prompts to process your feelings — write what you cannot say yet.",
        "category": "journaling_prompt",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solo", "structured", "guided", "creative", "self_paced"],
    },
    {
        "title": "Group Fitness Class",
        "description": "Sweat it out together with strangers — endorphins and silent solidarity.",
        "category": "group_fitness",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["social_support", "body", "routine", "structured"],
    },
    {
        "title": "Cooking for One — New Recipes",
        "description": "Learn dishes you never cooked before. Nourish yourself, literally.",
        "category": "cooking_for_one",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solo", "creative", "self_paced", "new_area", "routine"],
    },
    {
        "title": "Solo Travel — Weekend Escape",
        "description": "A short trip alone to remind yourself you are whole on your own.",
        "category": "travel_solo",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solo", "space", "new_area", "nature", "self_paced"],
    },
    {
        "title": "New Hobby Class",
        "description": "Pottery, dance, photography — build a new identity piece by piece.",
        "category": "new_hobby_class",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "social_support", "structured", "new_area", "guided"],
    },
    {
        "title": "Volunteer Work",
        "description": "Help others to heal yourself — purpose fills the void faster than distraction.",
        "category": "volunteer_work",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["social_support", "balanced", "gentle", "routine"],
    },
    {
        "title": "Therapy Session",
        "description": "Professional support to untangle the knots. Not weakness — wisdom.",
        "category": "therapy_session",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["guided", "structured", "solo", "gentle", "self_paced"],
    },
    {
        "title": "Meditation Retreat",
        "description": "Silence, stillness, and space to just be — no explaining needed.",
        "category": "meditation_retreat",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solo", "space", "gentle", "nature", "guided", "calming"],
    },
    {
        "title": "Art Therapy Workshop",
        "description": "Paint, sculpt, or collage your emotions when words fail.",
        "category": "art_therapy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "guided", "gentle", "solo", "self_paced"],
    },
    {
        "title": "Dance Class — Move Through It",
        "description": "Let your body express what your heart cannot articulate.",
        "category": "dance_class",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["body", "creative", "social_support", "structured"],
    },
    {
        "title": "Pet Cafe Visit",
        "description": "Unconditional love from cats or dogs — no questions asked.",
        "category": "pet_cafe_visit",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["gentle", "calming", "solo", "new_area", "space"],
    },
    {
        "title": "Sunrise Challenge — 7 Days",
        "description": "Wake up early, watch sunrise for 7 days. New rhythm, new perspective.",
        "category": "sunrise_challenge",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["routine", "structured", "solo", "nature", "body", "self_paced"],
    },
    {
        "title": "Gratitude Practice — Daily 3",
        "description": "Write 3 things you are grateful for each day. Small, but scientifically proven.",
        "category": "gratitude_practice",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["routine", "structured", "solo", "guided", "gentle", "self_paced"],
    },
]


def _match_healing_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    kw_map = {
        "journal": ["structured", "creative"],
        "日记": ["structured", "creative"],
        "exercise": ["body", "routine"],
        "运动": ["body", "routine"],
        "alone": ["solo", "space"],
        "一个人": ["solo", "space"],
        "friends": ["social_support"],
        "朋友": ["social_support"],
        "therapy": ["guided", "structured"],
        "治疗": ["guided", "structured"],
        "nature": ["nature", "space"],
        "自然": ["nature", "space"],
        "art": ["creative", "gentle"],
        "creative": ["creative"],
        "meditate": ["guided", "gentle"],
        "冥想": ["guided", "gentle"],
    }
    for keyword, tags in kw_map.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


def _attachment_to_tags(det: DetectorResults) -> list[str]:
    style = det.attachment.get("style", "")
    return list(ATTACHMENT_HEALING_MAP.get(style, []))


def _emotion_to_tags(det: DetectorResults) -> list[str]:
    tags: list[str] = []
    emotions = det.emotion.get("emotions", {})
    for emotion, threshold in [("sadness", 0.3), ("anger", 0.3), ("anxiety", 0.3)]:
        if emotions.get(emotion, 0) > threshold:
            for t in EMOTION_HEALING_MAP.get(emotion, []):
                if t not in tags:
                    tags.append(t)
    return tags


class BreakupHealingFulfiller(L2Fulfiller):
    """L2 fulfiller for breakup healing — attachment-aware activity recommendations.

    15 healing activities, avoids 'old' places (new_area tagged). Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_healing_tags(wish.wish_text)
        attachment_tags = _attachment_to_tags(detector_results)
        emotion_tags = _emotion_to_tags(detector_results)

        all_tags = list(keyword_tags)
        for t in attachment_tags + emotion_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in HEALING_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in HEALING_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in HEALING_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Healing takes time. Check in with yourself tomorrow.",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict, det: DetectorResults) -> str:
    tags = set(item.get("tags", []))
    attachment = det.attachment.get("style", "")

    if attachment == "anxious" and "structured" in tags:
        return "Structured activity to ground your anxious attachment pattern"
    if attachment == "avoidant" and "space" in tags:
        return "Gives you the space your avoidant side needs right now"
    if "new_area" in tags:
        return "New place, no old memories — a fresh start"
    if "gentle" in tags:
        return "A gentle step forward on your healing journey"

    return f"A healing activity recommended for you: {item.get('category', '').replace('_', ' ')}"
