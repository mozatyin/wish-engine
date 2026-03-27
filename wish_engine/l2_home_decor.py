"""HomeDecorFulfiller — personality-driven home decor style recommendations.

15-entry curated style catalog with MBTI + values mapping. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Personality → Style Mapping ──────────────────────────────────────────────

MBTI_STYLE_MAP: dict[str, list[str]] = {
    "I": ["minimalist", "japanese_wabi_sabi", "scandinavian", "cottage_core"],
    "E": ["bohemian", "tropical", "mid_century", "art_deco"],
    "N": ["art_deco", "brutalist", "bohemian", "japanese_wabi_sabi"],
    "S": ["scandinavian", "coastal", "rustic", "traditional_chinese"],
    "T": ["minimalist", "industrial", "brutalist", "modern_luxury"],
    "F": ["cottage_core", "bohemian", "coastal", "tropical"],
    "J": ["scandinavian", "minimalist", "traditional_chinese", "traditional_arabic"],
    "P": ["bohemian", "industrial", "mid_century", "tropical"],
}

VALUES_STYLE_MAP: dict[str, list[str]] = {
    "tradition": ["traditional_chinese", "traditional_arabic", "rustic", "cottage_core"],
    "stimulation": ["art_deco", "bohemian", "tropical", "industrial"],
    "self-direction": ["minimalist", "japanese_wabi_sabi", "brutalist"],
    "security": ["scandinavian", "traditional_chinese", "coastal"],
    "hedonism": ["modern_luxury", "art_deco", "tropical"],
    "universalism": ["bohemian", "japanese_wabi_sabi", "scandinavian"],
    "achievement": ["modern_luxury", "industrial", "minimalist"],
    "conformity": ["scandinavian", "traditional_chinese", "traditional_arabic"],
}

# ── Style Catalog (15 entries) ───────────────────────────────────────────────

STYLE_CATALOG: list[dict] = [
    {
        "title": "Minimalist — Less is More",
        "description": "Clean lines, neutral palette, and intentional emptiness that calms the mind.",
        "category": "minimalist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["minimalist", "quiet", "calming", "self-paced", "modern"],
    },
    {
        "title": "Scandinavian — Hygge Warmth",
        "description": "Light wood, soft textiles, candles, and the Danish art of cozy living.",
        "category": "scandinavian",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["scandinavian", "quiet", "calming", "practical", "cozy"],
    },
    {
        "title": "Japanese Wabi-Sabi — Imperfect Beauty",
        "description": "Handmade ceramics, natural wood, and finding beauty in imperfection.",
        "category": "japanese_wabi_sabi",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["japanese_wabi_sabi", "quiet", "calming", "reflective", "traditional"],
    },
    {
        "title": "Industrial — Raw and Real",
        "description": "Exposed brick, metal fixtures, and converted loft energy.",
        "category": "industrial",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["industrial", "bold", "modern", "practical"],
    },
    {
        "title": "Bohemian — Creative Chaos",
        "description": "Layered textiles, global patterns, and a home that tells stories.",
        "category": "bohemian",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["bohemian", "social", "colorful", "eclectic", "creative"],
    },
    {
        "title": "Mid-Century Modern — Retro Elegance",
        "description": "Organic curves, bold colors, and the optimism of the 1950s.",
        "category": "mid_century",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["mid_century", "modern", "bold", "practical"],
    },
    {
        "title": "Coastal — Ocean Breeze",
        "description": "White and blue palette, driftwood accents, and sea glass touches.",
        "category": "coastal",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["coastal", "quiet", "calming", "nature", "relaxed"],
    },
    {
        "title": "Rustic — Country Charm",
        "description": "Reclaimed wood, stone, and the warmth of a farmhouse hearth.",
        "category": "rustic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["rustic", "quiet", "calming", "traditional", "cozy"],
    },
    {
        "title": "Art Deco — Glamorous Geometry",
        "description": "Gold accents, geometric patterns, and the roaring twenties reborn.",
        "category": "art_deco",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["art_deco", "bold", "modern", "luxury", "social"],
    },
    {
        "title": "Traditional Chinese — Eastern Harmony",
        "description": "Rosewood furniture, silk screens, and feng shui balance.",
        "category": "traditional_chinese",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["traditional_chinese", "traditional", "quiet", "heritage", "calming"],
    },
    {
        "title": "Traditional Arabic — Desert Palace",
        "description": "Intricate mosaics, arched doorways, and warm lantern light.",
        "category": "traditional_arabic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["traditional_arabic", "traditional", "quiet", "heritage", "calming"],
    },
    {
        "title": "Modern Luxury — Refined Opulence",
        "description": "Marble surfaces, designer furniture, and curated art collections.",
        "category": "modern_luxury",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["modern_luxury", "modern", "luxury", "bold"],
    },
    {
        "title": "Tropical — Indoor Jungle",
        "description": "Lush plants, rattan furniture, and a perpetual vacation mood.",
        "category": "tropical",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["tropical", "colorful", "nature", "social", "relaxed"],
    },
    {
        "title": "Cottage Core — Pastoral Dream",
        "description": "Floral prints, handmade quilts, and a life slower than the world.",
        "category": "cottage_core",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cottage_core", "quiet", "calming", "traditional", "cozy"],
    },
    {
        "title": "Brutalist — Concrete Poetry",
        "description": "Raw concrete, bold geometry, and architectural statements as art.",
        "category": "brutalist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["brutalist", "bold", "modern", "reflective"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_DECOR_KEYWORDS: dict[str, list[str]] = {
    "minimalist": ["minimalist"],
    "极简": ["minimalist"],
    "cozy": ["cozy", "calming"],
    "温馨": ["cozy", "calming"],
    "traditional": ["traditional", "heritage"],
    "传统": ["traditional", "heritage"],
    "modern": ["modern", "bold"],
    "现代": ["modern", "bold"],
    "luxury": ["luxury", "modern"],
    "奢华": ["luxury", "modern"],
    "bohemian": ["bohemian", "eclectic"],
    "波西米亚": ["bohemian", "eclectic"],
    "natural": ["nature", "calming"],
    "自然": ["nature", "calming"],
    "chinese": ["traditional_chinese", "heritage"],
    "中式": ["traditional_chinese", "heritage"],
    "arabic": ["traditional_arabic", "heritage"],
    "阿拉伯": ["traditional_arabic", "heritage"],
    "japanese": ["japanese_wabi_sabi"],
    "日式": ["japanese_wabi_sabi"],
}


def _match_decor_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _DECOR_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


def _personality_to_style_tags(det: DetectorResults) -> list[str]:
    tags: list[str] = []
    mbti_type = det.mbti.get("type", "")
    if len(mbti_type) == 4:
        for letter in mbti_type:
            for t in MBTI_STYLE_MAP.get(letter, []):
                if t not in tags:
                    tags.append(t)
    top_values = det.values.get("top_values", [])
    for value in top_values:
        for t in VALUES_STYLE_MAP.get(value, []):
            if t not in tags:
                tags.append(t)
    return tags


class HomeDecorFulfiller(L2Fulfiller):
    """L2 fulfiller for home decor wishes — MBTI + values style matching.

    15 interior styles, personality-driven recommendations. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_decor_tags(wish.wish_text)
        personality_tags = _personality_to_style_tags(detector_results)

        all_tags = list(keyword_tags)
        for t in personality_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in STYLE_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in STYLE_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in STYLE_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Save these style ideas for your next home refresh!",
                delay_hours=168,
            ),
        )


def _build_relevance_reason(item: dict, det: DetectorResults) -> str:
    tags = set(item.get("tags", []))
    mbti_type = det.mbti.get("type", "")
    top_values = det.values.get("top_values", [])

    if mbti_type and len(mbti_type) == 4:
        if mbti_type[0] == "I" and "quiet" in tags:
            return "Calm aesthetic perfect for your introverted nature"
        if mbti_type[0] == "E" and "social" in tags:
            return "Vibrant style matching your social energy"
    if "tradition" in top_values and "traditional" in tags:
        return "Heritage-inspired style honoring your traditional values"
    if "stimulation" in top_values and "bold" in tags:
        return "Bold design matching your love of stimulation"

    return f"A {item.get('category', '').replace('_', ' ')} style recommended for you"
