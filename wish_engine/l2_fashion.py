"""FashionFulfiller — MBTI + values-aware fashion style recommendations.

12-style curated catalog with personality mapping: MBTI I→minimalist/classic,
E→streetwear/bold. Values tradition→modest, self-direction→avant_garde. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── MBTI → Fashion Style Mapping ─────────────────────────────────────────────

MBTI_FASHION_MAP: dict[str, list[str]] = {
    "I": ["minimalist", "classic", "vintage", "smart_casual"],
    "E": ["streetwear", "bohemian", "athleisure", "luxury"],
}

# ── Values → Fashion Style Mapping ───────────────────────────────────────────

VALUES_FASHION_MAP: dict[str, list[str]] = {
    "tradition": ["modest_fashion", "classic", "vintage"],
    "self-direction": ["avant_garde", "bohemian", "streetwear"],
    "universalism": ["sustainable", "vintage"],
    "hedonism": ["luxury", "streetwear", "bohemian"],
    "conformity": ["classic", "smart_casual", "preppy"],
    "achievement": ["smart_casual", "preppy", "luxury"],
}

# ── Fashion Catalog (12 entries) ─────────────────────────────────────────────

FASHION_CATALOG: list[dict] = [
    {
        "title": "Minimalist Capsule Wardrobe",
        "description": "Fewer pieces, more style — build a capsule wardrobe with timeless basics.",
        "category": "minimalist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["minimalist", "quiet", "calming", "practical", "self-paced"],
    },
    {
        "title": "Classic Elegant Style Guide",
        "description": "Tailored fits, neutral tones, quality fabrics — timeless elegance.",
        "category": "classic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["classic", "quiet", "calming", "traditional", "practical"],
    },
    {
        "title": "Streetwear Trends & Drops",
        "description": "Latest drops, sneaker culture, and urban style — stay ahead of the curve.",
        "category": "streetwear",
        "noise": "moderate",
        "social": "high",
        "mood": "intense",
        "tags": ["streetwear", "social", "adventure"],
    },
    {
        "title": "Bohemian Free Spirit Style",
        "description": "Flowy fabrics, earthy tones, layered accessories — express your free spirit.",
        "category": "bohemian",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["bohemian", "calming", "practical"],
    },
    {
        "title": "Preppy Classic Look",
        "description": "Polo shirts, chinos, blazers — polished and put-together every day.",
        "category": "preppy",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["preppy", "traditional", "practical", "calming"],
    },
    {
        "title": "Athleisure Style Guide",
        "description": "Sport meets street — comfortable, stylish activewear for everyday life.",
        "category": "athleisure",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["athleisure", "practical", "social"],
    },
    {
        "title": "Vintage & Thrift Finds",
        "description": "One-of-a-kind pieces from past decades — sustainable and unique style.",
        "category": "vintage",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["vintage", "quiet", "calming", "traditional", "self-paced"],
    },
    {
        "title": "Smart Casual Essentials",
        "description": "The perfect balance of relaxed and refined — ideal for work and weekends.",
        "category": "smart_casual",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["smart_casual", "practical", "calming"],
    },
    {
        "title": "Modest Fashion Lookbook",
        "description": "Stylish modest outfits — coverage meets creativity with modern designs.",
        "category": "modest_fashion",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["modest_fashion", "quiet", "calming", "traditional"],
    },
    {
        "title": "Sustainable Fashion Brands",
        "description": "Eco-friendly materials, ethical production — look good, feel good about it.",
        "category": "sustainable",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sustainable", "quiet", "calming", "practical"],
    },
    {
        "title": "Luxury Fashion Highlights",
        "description": "Designer pieces, runway trends, and investment fashion — elevate your look.",
        "category": "luxury",
        "noise": "moderate",
        "social": "high",
        "mood": "intense",
        "tags": ["luxury", "social"],
    },
    {
        "title": "Avant-Garde & Experimental",
        "description": "Push boundaries — deconstructed silhouettes, bold colors, wearable art.",
        "category": "avant_garde",
        "noise": "moderate",
        "social": "medium",
        "mood": "intense",
        "tags": ["avant_garde", "theory", "adventure"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_FASHION_KEYWORDS: dict[str, list[str]] = {
    "穿搭": ["fashion"],
    "fashion": ["fashion"],
    "style": ["fashion"],
    "衣服": ["fashion"],
    "clothing": ["fashion"],
    "أزياء": ["fashion"],
    "outfit": ["fashion"],
    "minimalist": ["minimalist"],
    "极简": ["minimalist"],
    "streetwear": ["streetwear"],
    "街头": ["streetwear"],
    "vintage": ["vintage"],
    "复古": ["vintage"],
    "modest": ["modest_fashion"],
    "محتشم": ["modest_fashion"],
    "sustainable": ["sustainable"],
    "环保": ["sustainable"],
    "luxury": ["luxury"],
    "奢侈": ["luxury"],
    "classic": ["classic"],
    "经典": ["classic"],
    "bohemian": ["bohemian"],
    "波西米亚": ["bohemian"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _FASHION_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _personality_to_fashion_tags(mbti_type: str, top_values: list[str]) -> list[str]:
    """Map MBTI E/I + values to preferred fashion styles."""
    tags: list[str] = []
    if len(mbti_type) >= 1:
        for tag in MBTI_FASHION_MAP.get(mbti_type[0], []):
            if tag not in tags:
                tags.append(tag)
    for value in top_values:
        for tag in VALUES_FASHION_MAP.get(value, []):
            if tag not in tags:
                tags.append(tag)
    return tags


def _build_relevance_reason(item: dict, mbti_type: str, top_values: list[str]) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")

    if mbti_type and len(mbti_type) >= 1:
        if mbti_type[0] == "I" and category in ("minimalist", "classic", "vintage"):
            return "Clean, understated style that matches your personality"
        if mbti_type[0] == "E" and category in ("streetwear", "luxury", "bohemian"):
            return "Bold, expressive style to match your outgoing energy"

    if "tradition" in top_values and category == "modest_fashion":
        return "Stylish and modest — honoring your values beautifully"
    if "self-direction" in top_values and category == "avant_garde":
        return "For the creative rule-breaker in you"
    if "universalism" in top_values and category == "sustainable":
        return "Fashion that cares for the planet"

    reason_map = {
        "minimalist": "Less is more — timeless simplicity",
        "classic": "Elegance that never goes out of style",
        "streetwear": "Stay ahead of the latest trends",
        "bohemian": "Free-spirited style for the adventurous",
        "preppy": "Polished and put-together every day",
        "athleisure": "Comfortable style that moves with you",
        "vintage": "Unique finds with character and history",
        "smart_casual": "The perfect balance of relaxed and refined",
        "modest_fashion": "Coverage meets creativity",
        "sustainable": "Look good, do good for the planet",
        "luxury": "Invest in pieces that elevate your look",
        "avant_garde": "Push boundaries with experimental style",
    }
    return reason_map.get(category, "Style recommendations tailored for you")


class FashionFulfiller(L2Fulfiller):
    """L2 fulfiller for fashion/style wishes — MBTI + values-aware recommendations.

    Uses keyword matching + MBTI E/I + values→style mapping to select from
    12-style catalog, then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Add personality-based preferences
        mbti_type = detector_results.mbti.get("type", "")
        top_values = detector_results.values.get("top_values", [])
        personality_tags = _personality_to_fashion_tags(mbti_type, top_values)

        all_tags = list(matched_categories)
        for t in personality_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in FASHION_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in FASHION_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in FASHION_CATALOG]

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, mbti_type, top_values)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New style inspiration dropping soon — check back!",
                delay_hours=72,
            ),
        )
