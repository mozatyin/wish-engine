"""CollectingFulfiller — personality-aware collecting hobby recommendations.

12-type curated catalog with values-based mapping: tradition→antiques/stamps,
aesthetics→art/cameras. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Values → Collecting Style Mapping ────────────────────────────────────────

VALUES_COLLECTING_MAP: dict[str, list[str]] = {
    "tradition": ["antiques", "stamps", "coins", "tea_sets", "postcards"],
    "self-direction": ["art_prints", "vintage_cameras", "rare_books"],
    "stimulation": ["sneakers", "vinyl_records", "watches"],
    "hedonism": ["watches", "sneakers", "crystals"],
    "universalism": ["postcards", "art_prints", "rare_books"],
    "achievement": ["coins", "watches", "stamps"],
}

# ── Collecting Catalog (12 entries) ──────────────────────────────────────────

COLLECTING_CATALOG: list[dict] = [
    {
        "title": "Vinyl Record Collection",
        "description": "Build your vinyl library — rare pressings, classics, and new releases on wax.",
        "category": "vinyl_records",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["vinyl_records", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Stamp Collecting Guide",
        "description": "Philately for beginners and experts — rare stamps, albums, and trading tips.",
        "category": "stamps",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["stamps", "quiet", "calming", "traditional", "self-paced"],
    },
    {
        "title": "Coin Collecting Starter Kit",
        "description": "Numismatics made approachable — historical coins, grading, and building a set.",
        "category": "coins",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["coins", "quiet", "calming", "traditional", "theory"],
    },
    {
        "title": "Vintage Camera Collection",
        "description": "Film cameras with character — Leica, Rolleiflex, Polaroid, and more.",
        "category": "vintage_cameras",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["vintage_cameras", "quiet", "calming", "practical", "self-paced"],
    },
    {
        "title": "Art Prints & Limited Editions",
        "description": "Curate your walls — gallery prints, indie artists, and signed editions.",
        "category": "art_prints",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["art_prints", "quiet", "calming", "theory"],
    },
    {
        "title": "Rare & First Edition Books",
        "description": "Build a library of treasures — signed copies, first editions, and out-of-print gems.",
        "category": "rare_books",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["rare_books", "quiet", "calming", "theory", "traditional", "self-paced"],
    },
    {
        "title": "Crystal & Mineral Collection",
        "description": "Amethyst, quartz, tourmaline — natural beauty from deep within the earth.",
        "category": "crystals",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crystals", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Antiques & Vintage Finds",
        "description": "Furniture, ceramics, and curiosities — each piece tells a story.",
        "category": "antiques",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["antiques", "calming", "traditional"],
    },
    {
        "title": "Sneaker Collection Hub",
        "description": "Limited drops, rare colorways, and sneaker culture — your next grail awaits.",
        "category": "sneakers",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["sneakers", "social", "practical"],
    },
    {
        "title": "Watch Collection Guide",
        "description": "Mechanical marvels — from affordable automatics to grail timepieces.",
        "category": "watches",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["watches", "quiet", "calming", "practical", "self-paced"],
    },
    {
        "title": "Tea Set Collection",
        "description": "Ceramic, porcelain, and clay — curate a beautiful tea ceremony set.",
        "category": "tea_sets",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["tea_sets", "quiet", "calming", "traditional"],
    },
    {
        "title": "Postcard Collection",
        "description": "Vintage postcards from around the world — miniature windows to other times and places.",
        "category": "postcards",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["postcards", "quiet", "calming", "traditional", "self-paced"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_COLLECTING_KEYWORDS: dict[str, list[str]] = {
    "收藏": ["collecting"],
    "collect": ["collecting"],
    "collection": ["collecting"],
    "hobby": ["collecting"],
    "هواية": ["collecting"],
    "vintage": ["antiques", "vintage_cameras"],
    "vinyl": ["vinyl_records"],
    "黑胶": ["vinyl_records"],
    "stamp": ["stamps"],
    "邮票": ["stamps"],
    "coin": ["coins"],
    "硬币": ["coins"],
    "camera": ["vintage_cameras"],
    "相机": ["vintage_cameras"],
    "book": ["rare_books"],
    "sneaker": ["sneakers"],
    "球鞋": ["sneakers"],
    "watch": ["watches"],
    "手表": ["watches"],
    "crystal": ["crystals"],
    "水晶": ["crystals"],
    "antique": ["antiques"],
    "古董": ["antiques"],
    "tea": ["tea_sets"],
    "茶具": ["tea_sets"],
    "postcard": ["postcards"],
    "明信片": ["postcards"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _COLLECTING_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _values_to_collecting_tags(top_values: list[str]) -> list[str]:
    """Map user's top values to preferred collecting hobbies."""
    tags: list[str] = []
    for value in top_values:
        for tag in VALUES_COLLECTING_MAP.get(value, []):
            if tag not in tags:
                tags.append(tag)
    return tags


def _build_relevance_reason(item: dict, top_values: list[str]) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")

    if "tradition" in top_values and category in ("antiques", "stamps", "coins", "tea_sets"):
        return "A timeless hobby that honors history and tradition"
    if "self-direction" in top_values and category in ("art_prints", "vintage_cameras", "rare_books"):
        return "Curate a collection that expresses your unique taste"

    reason_map = {
        "vinyl_records": "Warm analog sound — each record tells a story",
        "stamps": "Tiny artworks from around the world",
        "coins": "Hold history in the palm of your hand",
        "vintage_cameras": "Beautiful machines with character",
        "art_prints": "Curate your walls with meaningful art",
        "rare_books": "Build a library of literary treasures",
        "crystals": "Natural beauty from deep within the earth",
        "antiques": "Each piece carries a unique story",
        "sneakers": "Your next grail awaits",
        "watches": "Mechanical marvels on your wrist",
        "tea_sets": "The art of tea, beautifully crafted",
        "postcards": "Miniature windows to other times and places",
    }
    return reason_map.get(category, "Start or grow a collection you'll love")


class CollectingFulfiller(L2Fulfiller):
    """L2 fulfiller for collecting hobby wishes — values-aware recommendations.

    Uses keyword matching + values→hobby mapping to select from 12-type catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Add values-based preferences
        top_values = detector_results.values.get("top_values", [])
        values_tags = _values_to_collecting_tags(top_values)

        all_tags = list(matched_categories)
        for t in values_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in COLLECTING_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in COLLECTING_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in COLLECTING_CATALOG]

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
                text="New collecting tips and finds — check back soon!",
                delay_hours=72,
            ),
        )
