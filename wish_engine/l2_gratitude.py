"""GratitudeFulfiller — love-language-matched gratitude expression recommendations.

12 gratitude expression types with love language personality matching. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Love Language → Gratitude Mapping ─────────────────────────────────────────

LOVE_LANGUAGE_MAP: dict[str, list[str]] = {
    "words_of_affirmation": ["handwritten_letter", "public_appreciation", "video_message"],
    "acts_of_service": ["cook_for_them", "acts_of_service", "surprise_visit"],
    "receiving_gifts": ["gift_based_on_personality", "plant_a_tree", "memory_book"],
    "quality_time": ["shared_experience", "surprise_visit", "cook_for_them"],
    "physical_touch": ["surprise_visit", "shared_experience"],
}

# ── Gratitude Catalog (12 entries) ────────────────────────────────────────────

GRATITUDE_CATALOG: list[dict] = [
    {
        "title": "Handwritten Letter",
        "description": "Write a heartfelt letter by hand — words they'll keep forever.",
        "category": "handwritten_letter",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["handwritten_letter", "personal", "calming", "quiet", "words"],
    },
    {
        "title": "Surprise Visit",
        "description": "Show up unexpectedly — sometimes presence is the best present.",
        "category": "surprise_visit",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["surprise_visit", "personal", "social", "calming"],
    },
    {
        "title": "Cook a Special Meal",
        "description": "Prepare their favorite dish — love served on a plate.",
        "category": "cook_for_them",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cook_for_them", "practical", "calming", "quiet", "service"],
    },
    {
        "title": "Personality-Matched Gift",
        "description": "A gift chosen based on who they truly are — not just what's popular.",
        "category": "gift_based_on_personality",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["gift_based_on_personality", "personal", "calming", "practical"],
    },
    {
        "title": "Photo Album or Scrapbook",
        "description": "Collect your best moments together in a beautiful album.",
        "category": "photo_album",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["photo_album", "personal", "calming", "quiet", "nostalgia"],
    },
    {
        "title": "Video Message",
        "description": "Record a heartfelt video — your voice, your face, your gratitude.",
        "category": "video_message",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["video_message", "personal", "calming", "words"],
    },
    {
        "title": "Public Appreciation",
        "description": "Acknowledge them in front of others — a toast, a post, a shout-out.",
        "category": "public_appreciation",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["public_appreciation", "social", "words", "celebration"],
    },
    {
        "title": "Shared Experience",
        "description": "Do something together they've always wanted — a concert, a trip, a class.",
        "category": "shared_experience",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["shared_experience", "social", "calming"],
    },
    {
        "title": "Acts of Service",
        "description": "Do something they've been putting off — fix, clean, organize, or run errands.",
        "category": "acts_of_service",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["acts_of_service", "practical", "calming", "quiet", "service", "helping"],
    },
    {
        "title": "Plant a Tree in Their Name",
        "description": "A living, growing tribute — a tree planted in their honor.",
        "category": "plant_a_tree",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["plant_a_tree", "calming", "quiet", "meaningful"],
    },
    {
        "title": "Donate to a Cause They Care About",
        "description": "Make a charitable donation in their name — gratitude that gives back.",
        "category": "charity_in_their_name",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["charity_in_their_name", "calming", "quiet", "helping", "meaningful"],
    },
    {
        "title": "Memory Book",
        "description": "Collect notes from friends and family — a book of love and appreciation.",
        "category": "memory_book",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["memory_book", "personal", "calming", "quiet", "nostalgia"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_GRATITUDE_KEYWORDS: dict[str, list[str]] = {
    "感恩": [],
    "gratitude": [],
    "thank": [],
    "感谢": [],
    "شكر": [],
    "appreciate": [],
    "谢谢": [],
    "letter": ["handwritten_letter"],
    "信": ["handwritten_letter"],
    "cook": ["cook_for_them"],
    "做饭": ["cook_for_them"],
    "gift": ["gift_based_on_personality"],
    "礼物": ["gift_based_on_personality"],
    "photo": ["photo_album"],
    "照片": ["photo_album"],
    "video": ["video_message"],
    "视频": ["video_message"],
    "donate": ["charity_in_their_name"],
    "捐": ["charity_in_their_name"],
    "tree": ["plant_a_tree"],
    "plant": ["plant_a_tree"],
    "visit": ["surprise_visit"],
    "experience": ["shared_experience"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _GRATITUDE_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _love_language_to_tags(love_language: str) -> list[str]:
    """Map user's love language to preferred gratitude expression types."""
    return LOVE_LANGUAGE_MAP.get(love_language, [])


def _build_relevance_reason(item: dict, love_language: str) -> str:
    category = item.get("category", "")

    if love_language == "words_of_affirmation" and category in ("handwritten_letter", "video_message", "public_appreciation"):
        return "Words mean the world — and yours will be treasured"
    if love_language == "acts_of_service" and category in ("cook_for_them", "acts_of_service"):
        return "Actions speak louder — show your gratitude through service"
    if love_language == "quality_time" and category in ("shared_experience", "surprise_visit"):
        return "Your time is the greatest gift you can give"

    reason_map = {
        "handwritten_letter": "A letter from the heart lasts forever",
        "surprise_visit": "Sometimes showing up is everything",
        "cook_for_them": "A homemade meal says 'I care' in every bite",
        "gift_based_on_personality": "A gift that shows you truly know them",
        "photo_album": "Moments captured, memories preserved",
        "video_message": "Your voice and face — the most personal thank-you",
        "public_appreciation": "Let the world know how grateful you are",
        "shared_experience": "Create new memories as your way of saying thanks",
        "acts_of_service": "Help them with something they need — gratitude in action",
        "plant_a_tree": "A living symbol of your appreciation",
        "charity_in_their_name": "Gratitude that gives back to the world",
        "memory_book": "A collection of love from everyone who cares",
    }
    return reason_map.get(category, "A beautiful way to express your gratitude")


class GratitudeFulfiller(L2Fulfiller):
    """L2 fulfiller for gratitude expression wishes — love-language matched.

    Uses keyword matching + love language mapping to select from 12-type catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        matched_categories = _match_categories(wish.wish_text)

        # Get love language preference
        love_language = detector_results.love_language.get("primary", "")
        ll_tags = _love_language_to_tags(love_language)

        all_tags = list(matched_categories)
        for t in ll_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in GRATITUDE_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in GRATITUDE_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in GRATITUDE_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, love_language)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Gratitude grows when shared — come back anytime!",
                delay_hours=72,
            ),
        )
