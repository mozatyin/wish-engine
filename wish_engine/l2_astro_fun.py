"""AstroFunFulfiller — fun/entertainment personality quiz and astrology recommendations.

12-type curated catalog of fun personality and astrology content. Entertainment only,
NOT serious psychology. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Astro Fun Catalog (12 entries) ───────────────────────────────────────────

ASTRO_FUN_CATALOG: list[dict] = [
    {
        "title": "Daily Zodiac Horoscope",
        "description": "Your daily star sign reading — love, career, and lucky numbers.",
        "category": "zodiac_daily",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["zodiac_daily", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Zodiac Compatibility Check",
        "description": "How well do your signs match? Fun compatibility analysis for couples and friends.",
        "category": "zodiac_compatibility",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["zodiac_compatibility", "calming", "social"],
    },
    {
        "title": "Tarot Card Reading",
        "description": "Draw your cards — past, present, and future in a fun interactive reading.",
        "category": "tarot_reading",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["tarot_reading", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Numerology Profile",
        "description": "What do your numbers say? Life path, destiny, and personal year numbers.",
        "category": "numerology",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["numerology", "quiet", "calming", "theory", "self-paced"],
    },
    {
        "title": "Chinese Zodiac Year Guide",
        "description": "Year of the Dragon, Rabbit, or Tiger? Your Chinese zodiac personality and forecast.",
        "category": "chinese_zodiac",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["chinese_zodiac", "quiet", "calming", "traditional"],
    },
    {
        "title": "Fun Personality Quiz",
        "description": "What type of pizza are you? Which Disney character? Quick fun quizzes for laughs.",
        "category": "personality_quiz",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["personality_quiz", "calming", "social", "self-paced"],
    },
    {
        "title": "Soul Type Discovery",
        "description": "Are you an old soul, free spirit, or warrior? A fun soul archetype quiz.",
        "category": "soul_type_fun",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["soul_type_fun", "quiet", "calming", "theory"],
    },
    {
        "title": "MBTI Memes & Fun Facts",
        "description": "Relatable MBTI memes, funny stereotypes, and type-specific humor.",
        "category": "mbti_memes",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["mbti_memes", "calming", "social", "self-paced"],
    },
    {
        "title": "Attachment Style Quiz",
        "description": "Secure, anxious, or avoidant? A fun quiz about your relationship patterns.",
        "category": "attachment_style_quiz",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["attachment_style_quiz", "quiet", "calming", "theory"],
    },
    {
        "title": "Love Language Test",
        "description": "Words, touch, gifts, time, or acts? Discover how you give and receive love.",
        "category": "love_language_test",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["love_language_test", "calming", "social"],
    },
    {
        "title": "Color Personality Test",
        "description": "What color is your personality? A visual quiz linking colors to traits.",
        "category": "color_personality",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["color_personality", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Spirit Animal Quiz",
        "description": "Wolf, owl, dolphin, or fox? Discover your spirit animal in a fun quiz.",
        "category": "spirit_animal",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["spirit_animal", "quiet", "calming", "self-paced"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_ASTRO_KEYWORDS: dict[str, list[str]] = {
    "星座": ["zodiac_daily", "zodiac_compatibility"],
    "astrology": ["zodiac_daily", "zodiac_compatibility"],
    "zodiac": ["zodiac_daily", "zodiac_compatibility"],
    "塔罗": ["tarot_reading"],
    "tarot": ["tarot_reading"],
    "أبراج": ["zodiac_daily", "zodiac_compatibility"],
    "fun": ["personality_quiz", "spirit_animal"],
    "趣味": ["personality_quiz", "spirit_animal"],
    "quiz": ["personality_quiz", "love_language_test"],
    "测试": ["personality_quiz", "love_language_test"],
    "horoscope": ["zodiac_daily"],
    "运势": ["zodiac_daily"],
    "compatibility": ["zodiac_compatibility"],
    "numerology": ["numerology"],
    "数字": ["numerology"],
    "chinese zodiac": ["chinese_zodiac"],
    "生肖": ["chinese_zodiac"],
    "mbti": ["mbti_memes"],
    "personality": ["personality_quiz"],
    "love language": ["love_language_test"],
    "爱的语言": ["love_language_test"],
    "spirit animal": ["spirit_animal"],
    "灵魂动物": ["spirit_animal"],
    "color": ["color_personality"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _ASTRO_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")
    reason_map = {
        "zodiac_daily": "See what the stars have in store for you today",
        "zodiac_compatibility": "Fun compatibility check — are you a match?",
        "tarot_reading": "Draw your cards and see what the universe says",
        "numerology": "Your numbers hold secrets about your path",
        "chinese_zodiac": "Ancient wisdom meets modern fun",
        "personality_quiz": "Quick, fun, and surprisingly accurate",
        "soul_type_fun": "Discover your soul archetype",
        "mbti_memes": "Relatable memes for your personality type",
        "attachment_style_quiz": "Understand your relationship style — for fun",
        "love_language_test": "How do you give and receive love?",
        "color_personality": "Your personality in colors",
        "spirit_animal": "Find your spirit animal guide",
    }
    return reason_map.get(category, "Fun personality exploration awaits")


class AstroFunFulfiller(L2Fulfiller):
    """L2 fulfiller for astrology/fun quiz wishes — entertainment recommendations.

    Uses keyword matching to select from 12-type catalog of fun personality and
    astrology content. Entertainment only. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Filter catalog
        if matched_categories:
            tag_set = set(matched_categories)
            candidates = [
                dict(item) for item in ASTRO_FUN_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in ASTRO_FUN_CATALOG]

        # 3. Fallback
        if not candidates:
            candidates = [dict(item) for item in ASTRO_FUN_CATALOG]

        # 4. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        # 5. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New horoscopes and fun quizzes daily — check back!",
                delay_hours=24,
            ),
        )
