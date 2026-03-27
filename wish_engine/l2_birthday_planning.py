"""BirthdayPlannerFulfiller — MBTI-aware birthday celebration recommendations.

12-type curated catalog with personality mapping: I→intimate/solo, E→big party/bar crawl.
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

# ── MBTI → Birthday Style Mapping ────────────────────────────────────────────

MBTI_BIRTHDAY_MAP: dict[str, list[str]] = {
    "I": ["intimate_dinner", "solo_treat", "cooking_party", "cultural_outing"],
    "E": ["surprise_party", "bar_crawl", "adventure_birthday", "game_night"],
}

# ── Birthday Plan Catalog (12 entries) ───────────────────────────────────────

BIRTHDAY_CATALOG: list[dict] = [
    {
        "title": "Surprise Birthday Party",
        "description": "Coordinate a surprise with friends — decorations, cake, and unforgettable reactions.",
        "category": "surprise_party",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["surprise_party", "social", "adventure"],
    },
    {
        "title": "Intimate Birthday Dinner",
        "description": "A special dinner with your closest people — quality over quantity.",
        "category": "intimate_dinner",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["intimate_dinner", "quiet", "calming"],
    },
    {
        "title": "Adventure Birthday Experience",
        "description": "Skydiving, bungee jumping, or hot air balloon — an adrenaline-fueled celebration.",
        "category": "adventure_birthday",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["adventure_birthday", "social", "adventure"],
    },
    {
        "title": "Spa Birthday Retreat",
        "description": "A full day of pampering — massage, facial, and relaxation for your birthday.",
        "category": "spa_birthday",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["spa_birthday", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Cooking Party Celebration",
        "description": "Cook together with friends — a fun, hands-on birthday with delicious results.",
        "category": "cooking_party",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["cooking_party", "social", "practical", "calming"],
    },
    {
        "title": "Birthday Game Night",
        "description": "Board games, video games, and party games — competitive fun all night.",
        "category": "game_night",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["game_night", "social", "practical"],
    },
    {
        "title": "Outdoor Birthday Picnic",
        "description": "Balloons, blankets, and birthday cake in the park — a relaxed celebration.",
        "category": "outdoor_picnic",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["outdoor_picnic", "calming", "social"],
    },
    {
        "title": "Birthday Bar Crawl",
        "description": "Dress up and hit the town — a progressive bar tour with your squad.",
        "category": "bar_crawl",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["bar_crawl", "social", "adventure"],
    },
    {
        "title": "Cultural Birthday Outing",
        "description": "Art exhibition, theater, or live music — a cultured birthday experience.",
        "category": "cultural_outing",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["cultural_outing", "calming", "traditional", "theory"],
    },
    {
        "title": "Volunteer Birthday",
        "description": "Celebrate by giving back — volunteer at a shelter or organize a charity event.",
        "category": "volunteer_birthday",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["volunteer_birthday", "social", "helping", "calming"],
    },
    {
        "title": "Solo Birthday Treat",
        "description": "Treat yourself — fancy dinner, shopping spree, or a full day doing what YOU love.",
        "category": "solo_treat",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solo_treat", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Virtual Birthday Party",
        "description": "Celebrate across distances — video call with games, cake, and virtual toasts.",
        "category": "virtual_party",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["virtual_party", "social", "practical"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_BIRTHDAY_KEYWORDS: dict[str, list[str]] = {
    "生日": ["birthday"],
    "birthday": ["birthday"],
    "عيد ميلاد": ["birthday"],
    "party": ["surprise_party", "game_night"],
    "派对": ["surprise_party", "game_night"],
    "celebrate": ["birthday"],
    "庆祝": ["birthday"],
    "surprise": ["surprise_party"],
    "惊喜": ["surprise_party"],
    "dinner": ["intimate_dinner"],
    "spa": ["spa_birthday"],
    "adventure": ["adventure_birthday"],
    "game": ["game_night"],
    "picnic": ["outdoor_picnic"],
    "bar": ["bar_crawl"],
    "volunteer": ["volunteer_birthday"],
    "solo": ["solo_treat"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _BIRTHDAY_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _mbti_to_birthday_tags(mbti_type: str) -> list[str]:
    """Map MBTI E/I to preferred birthday celebration styles."""
    if len(mbti_type) >= 1:
        return MBTI_BIRTHDAY_MAP.get(mbti_type[0], [])
    return []


def _build_relevance_reason(item: dict, mbti_type: str) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")

    if mbti_type and len(mbti_type) >= 1:
        if mbti_type[0] == "I" and item.get("social") == "low":
            return "A meaningful celebration — intimate and personal"
        if mbti_type[0] == "E" and item.get("social") in ("high", "medium"):
            return "A big, social celebration to match your energy"

    reason_map = {
        "surprise_party": "Nothing beats the look of genuine surprise",
        "intimate_dinner": "Quality time with your closest people",
        "adventure_birthday": "An adrenaline rush you'll never forget",
        "spa_birthday": "You deserve a day of complete pampering",
        "cooking_party": "Cook, laugh, and eat together",
        "game_night": "Competitive fun and birthday cake",
        "outdoor_picnic": "A relaxed celebration under the sky",
        "bar_crawl": "A progressive party across the city",
        "cultural_outing": "A birthday that feeds the mind",
        "volunteer_birthday": "Give back on your special day",
        "solo_treat": "Treat yourself — it's YOUR day",
        "virtual_party": "Celebrate together, even apart",
    }
    return reason_map.get(category, "A perfect way to celebrate your birthday")


class BirthdayPlannerFulfiller(L2Fulfiller):
    """L2 fulfiller for birthday planning wishes — MBTI-aware recommendations.

    Uses keyword matching + MBTI E/I→intimate/social mapping to select from
    12-type catalog, then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Add MBTI-based preferences
        mbti_type = detector_results.mbti.get("type", "")
        mbti_tags = _mbti_to_birthday_tags(mbti_type)

        all_tags = list(matched_categories)
        for t in mbti_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in BIRTHDAY_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in BIRTHDAY_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in BIRTHDAY_CATALOG]

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, mbti_type)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Birthday coming up? Start planning early!",
                delay_hours=168,
            ),
        )
