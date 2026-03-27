"""GiftFulfiller — love language + personality matched gift recommendations.

15-entry curated gift catalog. Matches love language for the recipient
and MBTI for personality fit. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Love Language → Gift Category Mapping ────────────────────────────────────

LOVE_LANG_GIFT_MAP: dict[str, list[str]] = {
    "words_of_affirmation": ["letter", "poem", "card"],
    "acts_of_service": ["service", "practical_help"],
    "receiving_gifts": ["thoughtful_object", "curated_set", "personalized"],
    "quality_time": ["experience", "shared_activity"],
    "physical_touch": ["comfort_item", "wearable", "sensory"],
}

# ── MBTI → Gift Style Mapping ────────────────────────────────────────────────

MBTI_GIFT_MAP: dict[str, list[str]] = {
    "I": ["solo_enjoyment", "quiet", "personal", "calming"],
    "E": ["shared_activity", "social", "experience"],
    "N": ["creative", "meaningful", "symbolic"],
    "S": ["practical", "tangible", "useful"],
    "T": ["useful", "tool", "efficient"],
    "F": ["sentimental", "personal", "meaningful"],
    "J": ["organized", "practical", "useful"],
    "P": ["surprise", "creative", "experience"],
}

# ── Gift Catalog (15 entries) ────────────────────────────────────────────────

GIFT_CATALOG: list[dict] = [
    {
        "title": "Handwritten Letter",
        "description": "Words from the heart, penned by hand — the most personal gift there is.",
        "category": "letter",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["letter", "personal", "sentimental", "meaningful", "quiet", "calming"],
    },
    {
        "title": "Custom Poem or Song",
        "description": "Commission or write a poem/song capturing your shared memories.",
        "category": "poem",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["poem", "creative", "meaningful", "sentimental", "personal"],
    },
    {
        "title": "Illustrated Greeting Card",
        "description": "A beautifully illustrated card with a personal message inside.",
        "category": "card",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["card", "personal", "sentimental", "creative", "calming"],
    },
    {
        "title": "Do Something For Them Day",
        "description": "Cook their meals, handle their errands, clean their space — a full day of service.",
        "category": "service",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["service", "practical_help", "practical", "useful", "calming"],
    },
    {
        "title": "Pre-Organized Life Upgrade",
        "description": "Set up their meal prep, organize their closet, or automate a chore they hate.",
        "category": "practical_help",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical_help", "practical", "organized", "useful", "efficient"],
    },
    {
        "title": "Thoughtful Object They Mentioned Once",
        "description": "That book they talked about months ago, that tool they need — you remembered.",
        "category": "thoughtful_object",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["thoughtful_object", "personal", "meaningful", "tangible", "sentimental"],
    },
    {
        "title": "Curated Gift Set",
        "description": "A themed box: their favorite tea + candle + book, or tech accessories.",
        "category": "curated_set",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["curated_set", "personalized", "tangible", "creative", "calming"],
    },
    {
        "title": "Personalized Engraved Item",
        "description": "Keychain, pen, or jewelry with their name, a date, or coordinates.",
        "category": "personalized",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["personalized", "tangible", "sentimental", "meaningful"],
    },
    {
        "title": "Experience Together — Concert/Class/Trip",
        "description": "Two tickets to something you will both remember forever.",
        "category": "experience",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["experience", "shared_activity", "social", "surprise"],
    },
    {
        "title": "Shared Activity Day",
        "description": "Plan a full day around something they love — hiking, museum, cooking, gaming.",
        "category": "shared_activity",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["shared_activity", "experience", "social", "meaningful"],
    },
    {
        "title": "Ultra-Soft Comfort Blanket",
        "description": "Weighted or cashmere — a warm hug they can wrap themselves in.",
        "category": "comfort_item",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["comfort_item", "sensory", "calming", "wearable", "solo_enjoyment"],
    },
    {
        "title": "Premium Quality Tool",
        "description": "Best-in-class version of a tool they use daily — pen, knife, headphones.",
        "category": "tool",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["tool", "useful", "practical", "efficient", "tangible"],
    },
    {
        "title": "Wearable Keepsake",
        "description": "Bracelet, ring, or watch with personal significance.",
        "category": "wearable",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wearable", "personal", "sentimental", "tangible", "sensory"],
    },
    {
        "title": "Subscription Gift",
        "description": "Monthly delivery of their passion — books, coffee, art supplies, snacks.",
        "category": "subscription",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["surprise", "solo_enjoyment", "creative", "calming", "self-paced"],
    },
    {
        "title": "Photo Book of Memories",
        "description": "Curated collection of your best photos together, printed beautifully.",
        "category": "photo_book",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sentimental", "personal", "meaningful", "creative", "calming"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_GIFT_KEYWORDS: dict[str, list[str]] = {
    "letter": ["letter", "personal"],
    "信": ["letter", "personal"],
    "experience": ["experience", "shared_activity"],
    "体验": ["experience", "shared_activity"],
    "practical": ["practical", "useful"],
    "实用": ["practical", "useful"],
    "sentimental": ["sentimental", "meaningful"],
    "纪念": ["sentimental", "meaningful"],
    "creative": ["creative", "surprise"],
    "创意": ["creative", "surprise"],
    "comfort": ["comfort_item", "sensory"],
    "friend": ["personal", "meaningful"],
    "朋友": ["personal", "meaningful"],
    "partner": ["sentimental", "personal"],
    "伴侣": ["sentimental", "personal"],
    "tool": ["tool", "useful"],
    "工具": ["tool", "useful"],
}


def _match_gift_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _GIFT_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


def _personality_to_gift_tags(det: DetectorResults) -> list[str]:
    tags: list[str] = []
    # Love language
    ll = det.love_language.get("primary", "")
    for t in LOVE_LANG_GIFT_MAP.get(ll, []):
        if t not in tags:
            tags.append(t)
    # MBTI
    mbti_type = det.mbti.get("type", "")
    if len(mbti_type) == 4:
        for letter in mbti_type:
            for t in MBTI_GIFT_MAP.get(letter, []):
                if t not in tags:
                    tags.append(t)
    return tags


class GiftFulfiller(L2Fulfiller):
    """L2 fulfiller for gift wishes — love language + MBTI matched recommendations.

    15 gift categories, personality-driven. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_gift_tags(wish.wish_text)
        personality_tags = _personality_to_gift_tags(detector_results)

        all_tags = list(keyword_tags)
        for t in personality_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in GIFT_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in GIFT_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in GIFT_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Set a reminder before the special date!",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict, det: DetectorResults) -> str:
    tags = set(item.get("tags", []))
    ll = det.love_language.get("primary", "")
    mbti = det.mbti.get("type", "")

    if ll == "words_of_affirmation" and tags & {"letter", "poem", "card"}:
        return "Perfect for someone whose love language is words of affirmation"
    if ll == "quality_time" and tags & {"experience", "shared_activity"}:
        return "Quality time together — their favorite way to feel loved"
    if ll == "receiving_gifts" and tags & {"thoughtful_object", "personalized"}:
        return "A thoughtful object shows you truly see them"
    if ll == "acts_of_service" and tags & {"service", "practical_help"}:
        return "Acts of service speak louder than any wrapped gift"
    if ll == "physical_touch" and tags & {"comfort_item", "wearable"}:
        return "Something they can hold or wear — closeness even apart"

    if mbti and len(mbti) == 4:
        if mbti[2] == "T" and "useful" in tags:
            return "Practical and useful — the way a Thinker likes it"
        if mbti[2] == "F" and "sentimental" in tags:
            return "Sentimental touch that speaks to a Feeler's heart"

    return f"Gift idea: {item.get('category', '').replace('_', ' ')}"
