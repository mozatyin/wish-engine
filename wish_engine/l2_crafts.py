"""CraftsFulfiller — MBTI-aware handcraft experience recommendations.

15-type curated catalog of craft activities with MBTI introversion/extraversion
personality mapping for solo vs. group workshops. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── MBTI → Craft Style Mapping ───────────────────────────────────────────────

MBTI_CRAFT_MAP: dict[str, list[str]] = {
    "I": ["pottery", "calligraphy", "leather_craft", "embroidery", "papercraft"],
    "E": ["glass_blowing", "mosaic", "batik", "metalwork", "jewelry"],
}

# ── Crafts Catalog (15 entries) ──────────────────────────────────────────────

CRAFTS_CATALOG: list[dict] = [
    {
        "title": "Pottery & Ceramics Workshop",
        "description": "Shape clay on the wheel — meditative solo sessions or guided classes.",
        "category": "pottery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pottery", "calming", "quiet", "practical", "traditional"],
    },
    {
        "title": "Woodworking Studio",
        "description": "From spoons to shelves — learn to craft with your hands and natural wood.",
        "category": "woodworking",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["woodworking", "practical", "traditional"],
    },
    {
        "title": "Leather Craft Workshop",
        "description": "Hand-stitch wallets, belts, and bags — a satisfying solo craft.",
        "category": "leather_craft",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["leather_craft", "quiet", "practical"],
    },
    {
        "title": "Calligraphy & Lettering",
        "description": "Arabic, Chinese, or Western calligraphy — the art of beautiful writing.",
        "category": "calligraphy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calligraphy", "quiet", "traditional", "heritage", "calming"],
    },
    {
        "title": "Weaving & Textile Arts",
        "description": "From simple looms to tapestry — create fabric art with patience and rhythm.",
        "category": "weaving",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["weaving", "traditional", "calming", "quiet"],
    },
    {
        "title": "Glass Blowing Experience",
        "description": "Shape molten glass into stunning pieces — a thrilling group workshop.",
        "category": "glass_blowing",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["glass_blowing", "social"],
    },
    {
        "title": "Jewelry Making Workshop",
        "description": "Design and craft your own rings, necklaces, and bracelets.",
        "category": "jewelry",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["jewelry", "practical", "social"],
    },
    {
        "title": "Candle Making Class",
        "description": "Scented candles, beeswax, and soy — a cozy, aromatic craft.",
        "category": "candle_making",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["candle_making", "calming", "quiet", "practical"],
    },
    {
        "title": "Soap Making Workshop",
        "description": "Natural ingredients, essential oils — handmade soaps as gifts or self-care.",
        "category": "soap_making",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["soap_making", "practical", "calming"],
    },
    {
        "title": "Embroidery & Cross-Stitch",
        "description": "Thread and needle artistry — meditative stitching for beautiful patterns.",
        "category": "embroidery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["embroidery", "quiet", "calming", "traditional"],
    },
    {
        "title": "Papercraft & Origami",
        "description": "From origami cranes to pop-up cards — the art of paper folding.",
        "category": "papercraft",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["papercraft", "quiet", "practical"],
    },
    {
        "title": "Metalwork & Blacksmithing",
        "description": "Forge and hammer — create functional art from raw metal.",
        "category": "metalwork",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["metalwork", "social", "practical"],
    },
    {
        "title": "Ceramic Painting Studio",
        "description": "Paint pre-made ceramics with your own designs — relaxing and colorful.",
        "category": "ceramic_painting",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["ceramic_painting", "calming", "practical"],
    },
    {
        "title": "Batik Fabric Art",
        "description": "Wax-resist dyeing technique — vibrant patterns on fabric in a group setting.",
        "category": "batik",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["batik", "social", "traditional", "heritage"],
    },
    {
        "title": "Mosaic Art Workshop",
        "description": "Piece together colorful tiles into stunning mosaic artwork.",
        "category": "mosaic",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["mosaic", "social", "practical", "traditional"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_CRAFT_KEYWORDS: dict[str, list[str]] = {
    "手工": ["craft"],
    "craft": ["craft"],
    "陶艺": ["pottery"],
    "pottery": ["pottery"],
    "木工": ["woodworking"],
    "woodwork": ["woodworking"],
    "diy": ["craft", "practical"],
    "حرف": ["craft"],
    "calligraphy": ["calligraphy"],
    "书法": ["calligraphy"],
    "خط": ["calligraphy"],
    "leather": ["leather_craft"],
    "皮具": ["leather_craft"],
    "weaving": ["weaving"],
    "编织": ["weaving"],
    "jewelry": ["jewelry"],
    "首饰": ["jewelry"],
    "candle": ["candle_making"],
    "蜡烛": ["candle_making"],
    "embroidery": ["embroidery"],
    "刺绣": ["embroidery"],
    "origami": ["papercraft"],
    "折纸": ["papercraft"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _CRAFT_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _mbti_to_craft_tags(mbti_type: str) -> list[str]:
    """Map MBTI E/I to preferred craft styles (solo vs. group)."""
    if len(mbti_type) >= 1:
        return MBTI_CRAFT_MAP.get(mbti_type[0], [])
    return []


def _build_relevance_reason(item: dict, mbti_type: str) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")

    if mbti_type and len(mbti_type) >= 1:
        if mbti_type[0] == "I" and item.get("social") == "low":
            return "A peaceful solo craft — perfect for your reflective nature"
        if mbti_type[0] == "E" and item.get("social") in ("high", "medium"):
            return "A fun group workshop to craft and connect"

    reason_map = {
        "pottery": "Shape something beautiful with your hands",
        "calligraphy": "The meditative art of beautiful writing",
        "woodworking": "Create lasting pieces from natural wood",
        "leather_craft": "Craft something you'll carry every day",
        "glass_blowing": "An unforgettable hands-on experience",
        "jewelry": "Design your own wearable art",
        "embroidery": "Thread by thread, create something beautiful",
    }
    return reason_map.get(category, "Discover the joy of making things by hand")


class CraftsFulfiller(L2Fulfiller):
    """L2 fulfiller for craft/handwork wishes — MBTI-aware recommendations.

    Uses keyword matching + MBTI E/I→solo/group mapping to select from 15-type
    catalog, then applies PersonalityFilter. Zero LLM.
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
        mbti_tags = _mbti_to_craft_tags(mbti_type)

        all_tags = list(matched_categories)
        for t in mbti_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in CRAFTS_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in CRAFTS_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in CRAFTS_CATALOG]

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
                text="More craft workshops near you — check back soon!",
                delay_hours=48,
            ),
        )
