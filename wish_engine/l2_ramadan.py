"""FestivalFulfiller — culture-aware festival/holiday activity recommendations.

15-entry curated catalog covering multiple world festivals with culture-based
personality mapping. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Culture → Festival Mapping ───────────────────────────────────────────────

CULTURE_FESTIVAL_MAP: dict[str, list[str]] = {
    "arab": ["ramadan", "eid", "islamic"],
    "chinese": ["chinese_new_year", "mid_autumn", "lunar"],
    "indian": ["diwali", "holi", "hindu"],
    "western": ["christmas", "easter", "thanksgiving"],
    "jewish": ["hanukkah", "jewish"],
    "universal": ["valentines", "mothers_day", "national_day"],
}

# ── Values → Festival Preference ─────────────────────────────────────────────

VALUES_FESTIVAL_MAP: dict[str, list[str]] = {
    "tradition": ["spiritual", "religious", "heritage", "traditional"],
    "benevolence": ["charity", "family", "giving", "community"],
    "stimulation": ["celebration", "festive", "social", "lively"],
    "universalism": ["interfaith", "multicultural", "inclusive"],
    "hedonism": ["feast", "celebration", "indulgence", "festive"],
    "conformity": ["family", "traditional", "community"],
    "security": ["family", "home", "traditional"],
}

# ── Festival Catalog (15 entries) ────────────────────────────────────────────

FESTIVAL_CATALOG: list[dict] = [
    # ── Ramadan / Islamic (3) ──────────────────────────────────────────────
    {
        "title": "Ramadan Iftar Restaurant Guide",
        "description": "Curated iftar dining experiences — from lavish hotel buffets to authentic home-style spots.",
        "category": "ramadan_iftar_restaurant",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["ramadan", "islamic", "feast", "family", "spiritual", "community"],
    },
    {
        "title": "Ramadan Night Activities",
        "description": "Night markets, taraweeh gatherings, and late-night cultural walks during the holy month.",
        "category": "ramadan_night_activity",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["ramadan", "islamic", "spiritual", "community", "traditional"],
    },
    {
        "title": "Ramadan Spiritual Lectures",
        "description": "Daily spiritual talks and Quran study circles at mosques and cultural centers.",
        "category": "ramadan_spiritual_lecture",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["ramadan", "islamic", "spiritual", "religious", "heritage"],
    },
    # ── Eid / Celebration (1) ──────────────────────────────────────────────
    {
        "title": "Eid Celebration Events",
        "description": "Eid prayers, family feasts, gift exchanges, and community celebrations.",
        "category": "eid_celebration",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["eid", "islamic", "celebration", "family", "festive", "giving"],
    },
    # ── Chinese Festivals (2) ─────────────────────────────────────────────
    {
        "title": "Chinese New Year Festivities",
        "description": "Lion dances, temple fairs, red envelope traditions, and reunion dinners.",
        "category": "chinese_new_year",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["chinese_new_year", "lunar", "celebration", "family", "festive", "traditional"],
    },
    {
        "title": "Mid-Autumn Festival Guide",
        "description": "Mooncake tasting, lantern walks, and moon-gazing gatherings under the full moon.",
        "category": "mid_autumn",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["mid_autumn", "lunar", "family", "traditional", "heritage"],
    },
    # ── Indian Festival (1) ───────────────────────────────────────────────
    {
        "title": "Diwali Festival of Lights",
        "description": "Rangoli workshops, diya lighting, fireworks viewing, and sweet-sharing celebrations.",
        "category": "diwali",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["diwali", "hindu", "celebration", "festive", "family", "traditional"],
    },
    # ── Western Festivals (3) ─────────────────────────────────────────────
    {
        "title": "Christmas Market Experience",
        "description": "Mulled wine, handcrafted gifts, carol singing, and festive light displays.",
        "category": "christmas_market",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["christmas", "celebration", "festive", "family", "community"],
    },
    {
        "title": "Thanksgiving Gatherings",
        "description": "Community potlucks, gratitude circles, and volunteer-served meals for all.",
        "category": "thanksgiving",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["thanksgiving", "family", "community", "giving", "charity"],
    },
    {
        "title": "Easter Celebration Activities",
        "description": "Egg hunts, spring festivals, church services, and family brunches.",
        "category": "easter",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["easter", "religious", "family", "celebration", "community"],
    },
    # ── Jewish Festival (1) ───────────────────────────────────────────────
    {
        "title": "Hanukkah Festival of Lights",
        "description": "Menorah lighting, dreidel games, latke feasts, and community gatherings.",
        "category": "hanukkah",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["hanukkah", "jewish", "religious", "family", "traditional", "heritage"],
    },
    # ── National / Universal (4) ──────────────────────────────────────────
    {
        "title": "National Day Celebrations",
        "description": "Parades, fireworks, cultural performances, and patriotic gatherings.",
        "category": "national_day",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["national_day", "celebration", "festive", "community", "lively"],
    },
    {
        "title": "Valentine's Day Experiences",
        "description": "Romantic dinners, couples workshops, and heartfelt gift ideas.",
        "category": "valentines",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["valentines", "celebration", "indulgence", "family"],
    },
    {
        "title": "Mother's Day Celebration Guide",
        "description": "Spa packages, family brunches, handmade gift workshops, and tribute events.",
        "category": "mothers_day",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["mothers_day", "family", "giving", "celebration", "community"],
    },
    {
        "title": "Harvest Festival & Thanksgiving of Earth",
        "description": "Farm visits, harvest markets, traditional food fairs, and gratitude ceremonies.",
        "category": "harvest_festival",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["harvest_festival", "traditional", "community", "heritage", "multicultural"],
    },
]


# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_FESTIVAL_KEYWORDS: dict[str, list[str]] = {
    "斋月": ["ramadan", "islamic"],
    "ramadan": ["ramadan", "islamic"],
    "رمضان": ["ramadan", "islamic"],
    "iftar": ["ramadan", "feast"],
    "عيد": ["eid", "islamic", "celebration"],
    "eid": ["eid", "islamic", "celebration"],
    "节日": ["celebration", "festive"],
    "festival": ["celebration", "festive"],
    "春节": ["chinese_new_year", "lunar"],
    "new year": ["chinese_new_year", "celebration"],
    "中秋": ["mid_autumn", "lunar"],
    "圣诞": ["christmas", "festive"],
    "christmas": ["christmas", "festive"],
    "diwali": ["diwali", "hindu"],
    "排灯": ["diwali", "hindu"],
    "easter": ["easter", "religious"],
    "hanukkah": ["hanukkah", "jewish"],
    "thanksgiving": ["thanksgiving", "family"],
    "感恩": ["thanksgiving", "family"],
    "valentines": ["valentines", "celebration"],
    "情人节": ["valentines", "celebration"],
    "母亲节": ["mothers_day", "family"],
    "mothers day": ["mothers_day", "family"],
    "国庆": ["national_day", "celebration"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _FESTIVAL_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _culture_to_festival_tags(top_values: list[str]) -> list[str]:
    """Map user's top values to preferred festival tag categories."""
    tags: list[str] = []
    for value in top_values:
        for tag in VALUES_FESTIVAL_MAP.get(value, []):
            if tag not in tags:
                tags.append(tag)
    return tags


def _build_relevance_reason(item: dict, top_values: list[str]) -> str:
    """Build a personalized relevance reason based on values."""
    tags = set(item.get("tags", []))

    for value in top_values:
        if value == "tradition" and tags & {"traditional", "heritage", "spiritual"}:
            return "Celebrates your cultural traditions and heritage"
        if value == "benevolence" and tags & {"giving", "charity", "community"}:
            return "A beautiful way to give back to your community"
        if value == "stimulation" and tags & {"festive", "celebration", "lively"}:
            return "Exciting celebration to energize your spirit"
        if value == "universalism" and tags & {"multicultural", "interfaith", "inclusive"}:
            return "Explore diverse cultures and traditions"

    category = item.get("category", "")
    reason_map = {
        "ramadan_iftar_restaurant": "Discover the best iftar experiences nearby",
        "ramadan_night_activity": "Make the most of Ramadan nights",
        "ramadan_spiritual_lecture": "Deepen your spiritual journey",
        "eid_celebration": "Celebrate Eid with joy and community",
        "chinese_new_year": "Ring in the Lunar New Year with tradition",
        "diwali": "Light up your Diwali celebration",
        "christmas_market": "Festive holiday cheer awaits",
        "mid_autumn": "Enjoy the beauty of the Mid-Autumn Festival",
    }
    return reason_map.get(category, "Celebrate this special occasion")


class FestivalFulfiller(L2Fulfiller):
    """L2 fulfiller for festival/holiday wishes — culture-aware recommendations.

    Uses keyword matching + values→festival mapping to select from 15-entry catalog,
    then applies PersonalityFilter. Culture-aware filtering. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Add values-based categories
        top_values = detector_results.values.get("top_values", [])
        values_tags = _culture_to_festival_tags(top_values)

        all_tags = list(matched_categories)
        for t in values_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in FESTIVAL_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in FESTIVAL_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in FESTIVAL_CATALOG]

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, top_values)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Festival season continues — check back for more events!",
                delay_hours=24,
            ),
        )
