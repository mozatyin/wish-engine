"""LanguageEnvFulfiller — language practice immersion environments.

15-entry catalog of language immersion spots matched to target language. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

VALUES_LANG_MAP: dict[str, list[str]] = {
    "self-direction": ["immersion", "autonomous", "practice", "learning"],
    "stimulation": ["social", "lively", "experiential", "cultural"],
    "tradition": ["traditional", "cultural", "heritage"],
    "universalism": ["multilingual", "inclusive", "cultural"],
    "benevolence": ["community", "helping", "social"],
}

LANGUAGE_CATALOG: list[dict] = [
    {
        "title": "English Corner Meetup",
        "description": "Free-flowing English conversation in a relaxed cafe — all levels, no judgment.",
        "category": "english_corner",
        "language": "english",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practice", "social", "community", "learning", "multilingual"],
    },
    {
        "title": "Arabic Conversation Cafe",
        "description": "Sip qahwa while practicing Arabic — from Gulf dialect to Levantine and Egyptian.",
        "category": "arabic_cafe",
        "language": "arabic",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practice", "cultural", "traditional", "social", "immersion"],
    },
    {
        "title": "Japanese Anime & Manga Shop",
        "description": "Browse manga in Japanese, chat with fans, pick up slang you won't find in textbooks.",
        "category": "japanese_anime_shop",
        "language": "japanese",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["immersion", "cultural", "autonomous", "learning", "experiential"],
    },
    {
        "title": "French Bakery & Conversation",
        "description": "Order your croissant in French — staff happy to chat and correct your grammar.",
        "category": "french_bakery",
        "language": "french",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["immersion", "cultural", "practice", "autonomous", "traditional"],
    },
    {
        "title": "Spanish Tapas & Language Night",
        "description": "Tapas, sangria, and Spanish-only conversation — themed nights from travel to football.",
        "category": "spanish_tapas",
        "language": "spanish",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practice", "social", "lively", "cultural", "experiential"],
    },
    {
        "title": "Korean BBQ Language Exchange",
        "description": "Grill, eat, and practice Korean — K-drama fans and language learners welcome.",
        "category": "korean_bbq",
        "language": "korean",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practice", "social", "cultural", "experiential", "lively"],
    },
    {
        "title": "German Beer Hall Stammtisch",
        "description": "The Stammtisch tradition — regular table, regular conversation, in German only.",
        "category": "german_beer_hall",
        "language": "german",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["traditional", "social", "practice", "cultural", "community"],
    },
    {
        "title": "Italian Gelato & Chat",
        "description": "Learn to describe 50 gelato flavors in Italian — tastiest language lesson ever.",
        "category": "italian_gelato",
        "language": "italian",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["immersion", "cultural", "autonomous", "practice", "experiential"],
    },
    {
        "title": "Indian Restaurant Language Table",
        "description": "Hindi, Tamil, or Urdu over thali — staff and diners love to teach their mother tongue.",
        "category": "indian_restaurant",
        "language": "hindi",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practice", "cultural", "social", "community", "multilingual"],
    },
    {
        "title": "Turkish Tea House Sohbet",
        "description": "Sohbet means conversation — and over Turkish tea, it flows naturally. Practice welcomed.",
        "category": "turkish_tea_house",
        "language": "turkish",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["traditional", "cultural", "practice", "immersion", "heritage"],
    },
    {
        "title": "Russian Bookshop & Reading Circle",
        "description": "Browse Russian literature, join the reading circle, discuss Dostoevsky over tea.",
        "category": "russian_bookshop",
        "language": "russian",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["learning", "autonomous", "cultural", "quiet", "immersion"],
    },
    {
        "title": "Portuguese Cafe & Fado Night",
        "description": "Learn Portuguese through music — fado lyrics are poetry, and the cafe serves pasteis.",
        "category": "portuguese_cafe",
        "language": "portuguese",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["cultural", "immersion", "experiential", "practice", "heritage"],
    },
    {
        "title": "Mandarin Study School",
        "description": "Structured Mandarin classes with native teachers — from pinyin to business Chinese.",
        "category": "mandarin_school",
        "language": "mandarin",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["learning", "practice", "community", "multilingual", "inclusive"],
    },
    {
        "title": "Swahili Market Immersion",
        "description": "Haggle, greet, and count in Swahili at East African markets — real-world practice.",
        "category": "swahili_market",
        "language": "swahili",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["immersion", "experiential", "cultural", "lively", "practice"],
    },
    {
        "title": "Sign Language Cafe",
        "description": "Staff communicate in sign language — order, chat, and learn in a silent-friendly space.",
        "category": "sign_language_cafe",
        "language": "sign",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["inclusive", "learning", "community", "immersion", "quiet"],
    },
]

_LANG_KEYWORDS: dict[str, list[str]] = {
    "语言": ["practice", "learning"],
    "language": ["practice", "learning"],
    "练习": ["practice", "immersion"],
    "practice": ["practice", "immersion"],
    "لغة": ["practice", "learning"],
    "conversation": ["practice", "social"],
    "口语": ["practice", "social"],
    "english": ["multilingual"],
    "arabic": ["cultural", "traditional"],
    "العربية": ["cultural", "traditional"],
    "japanese": ["cultural", "immersion"],
    "日语": ["cultural", "immersion"],
    "french": ["cultural", "immersion"],
    "法语": ["cultural", "immersion"],
    "spanish": ["cultural", "lively"],
    "korean": ["cultural", "experiential"],
    "韩语": ["cultural", "experiential"],
    "chinese": ["multilingual", "learning"],
    "中文": ["multilingual", "learning"],
    "sign language": ["inclusive", "community"],
    "手语": ["inclusive", "community"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _LANG_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _values_to_lang_tags(top_values: list[str]) -> list[str]:
    tags: list[str] = []
    for value in top_values:
        for tag in VALUES_LANG_MAP.get(value, []):
            if tag not in tags:
                tags.append(tag)
    return tags


def _build_relevance_reason(item: dict, top_values: list[str]) -> str:
    tags = set(item.get("tags", []))
    for value in top_values:
        if value == "self-direction" and tags & {"immersion", "autonomous"}:
            return "Immerse yourself at your own pace"
        if value == "stimulation" and tags & {"lively", "experiential", "social"}:
            return "Language learning that feels like an adventure"
        if value == "tradition" and tags & {"traditional", "heritage"}:
            return "Learn through cultural traditions"

    lang = item.get("language", "")
    reason_map = {
        "english": "The world's lingua franca — practice here",
        "arabic": "Beautiful language, best learned over coffee",
        "japanese": "Immerse in Japanese pop culture",
        "french": "The language of love and pastry",
        "spanish": "World's second most spoken — dive in",
        "sign": "A whole language in your hands",
    }
    return reason_map.get(lang, "Practice makes fluent")


class LanguageEnvFulfiller(L2Fulfiller):
    """L2 fulfiller for language learning wishes — immersion environment matching.

    Uses keyword matching + values→language mapping to select from 15-entry catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        matched_categories = _match_categories(wish.wish_text)
        top_values = detector_results.values.get("top_values", [])
        values_tags = _values_to_lang_tags(top_values)

        all_tags = list(matched_categories)
        for t in values_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in LANGUAGE_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in LANGUAGE_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in LANGUAGE_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, top_values)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New language meetups posted weekly — check back!",
                delay_hours=48,
            ),
        )
