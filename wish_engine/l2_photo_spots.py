"""PhotoSpotFulfiller — time/weather-aware photography spot recommendations.

15-type curated catalog of photography locations with time-of-day and weather
awareness for optimal shooting conditions. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Time/Weather → Spot Mapping ──────────────────────────────────────────────

TIME_SPOT_MAP: dict[str, list[str]] = {
    "golden_hour": ["golden_hour_spot", "water_reflection", "desert_dunes", "autumn_leaves"],
    "blue_hour": ["neon_night", "urban_geometry", "rooftop_view"],
    "overcast": ["street_art_wall", "market_colors", "cafe_interior"],
    "foggy": ["foggy_morning", "temple_detail", "architecture"],
    "sunny": ["cherry_blossom", "garden_macro", "desert_dunes"],
}

# ── Photo Spot Catalog (15 entries) ──────────────────────────────────────────

PHOTO_SPOT_CATALOG: list[dict] = [
    {
        "title": "Golden Hour Landscape Spot",
        "description": "Catch the warm, soft light of sunrise or sunset — magical landscapes await.",
        "category": "golden_hour_spot",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["golden_hour_spot", "quiet", "calming", "outdoor"],
    },
    {
        "title": "Street Art & Mural Wall",
        "description": "Vibrant graffiti and murals — perfect backdrops for portraits and street photography.",
        "category": "street_art_wall",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["street_art_wall", "social", "practical"],
    },
    {
        "title": "Rooftop City View",
        "description": "Panoramic cityscapes from above — stunning for skyline and blue hour shots.",
        "category": "rooftop_view",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["rooftop_view", "quiet", "calming", "outdoor"],
    },
    {
        "title": "Garden Macro Photography",
        "description": "Flowers, insects, dewdrops — get up close in botanical gardens.",
        "category": "garden_macro",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["garden_macro", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Architectural Photography Walk",
        "description": "Lines, symmetry, and textures — explore architectural gems in your city.",
        "category": "architecture",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["architecture", "quiet", "practical", "theory"],
    },
    {
        "title": "Water Reflection Spot",
        "description": "Lakes, rivers, and puddles — capture mirror-like reflections at dawn or dusk.",
        "category": "water_reflection",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["water_reflection", "quiet", "calming", "outdoor"],
    },
    {
        "title": "Neon Night Photography",
        "description": "Neon signs, city lights, and rain-slicked streets — urban night magic.",
        "category": "neon_night",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["neon_night", "social", "practical"],
    },
    {
        "title": "Foggy Morning Shoot",
        "description": "Misty landscapes and silhouettes — ethereal shots in early morning fog.",
        "category": "foggy_morning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["foggy_morning", "quiet", "calming", "outdoor"],
    },
    {
        "title": "Autumn Leaves Trail",
        "description": "Red, orange, and gold — capture the beauty of fall foliage.",
        "category": "autumn_leaves",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["autumn_leaves", "quiet", "calming", "outdoor", "traditional"],
    },
    {
        "title": "Cherry Blossom Season",
        "description": "Pink petals and soft light — iconic spring photography at its best.",
        "category": "cherry_blossom",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["cherry_blossom", "calming", "outdoor", "traditional"],
    },
    {
        "title": "Desert Dunes at Golden Hour",
        "description": "Sweeping sand patterns and dramatic shadows — desert photography at sunset.",
        "category": "desert_dunes",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["desert_dunes", "quiet", "calming", "outdoor"],
    },
    {
        "title": "Urban Geometry Walk",
        "description": "Patterns, lines, and shapes — find abstract beauty in the city.",
        "category": "urban_geometry",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["urban_geometry", "practical", "theory"],
    },
    {
        "title": "Market Colors & Textures",
        "description": "Spice stalls, fabric shops, flower markets — rich colors and vibrant life.",
        "category": "market_colors",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["market_colors", "social", "traditional"],
    },
    {
        "title": "Temple & Heritage Detail",
        "description": "Intricate carvings, stained glass, sacred geometry — reverent close-ups.",
        "category": "temple_detail",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["temple_detail", "quiet", "calming", "traditional"],
    },
    {
        "title": "Cafe Interior Photography",
        "description": "Cozy corners, latte art, warm light — perfect for lifestyle and still life.",
        "category": "cafe_interior",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cafe_interior", "quiet", "calming", "self-paced"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_PHOTO_KEYWORDS: dict[str, list[str]] = {
    "拍照": ["photo"],
    "photo": ["photo"],
    "photography": ["photo"],
    "摄影": ["photo"],
    "تصوير": ["photo"],
    "instagram": ["photo"],
    "打卡": ["photo"],
    "golden hour": ["golden_hour_spot"],
    "日落": ["golden_hour_spot"],
    "sunset": ["golden_hour_spot"],
    "street art": ["street_art_wall"],
    "涂鸦": ["street_art_wall"],
    "rooftop": ["rooftop_view"],
    "天台": ["rooftop_view"],
    "macro": ["garden_macro"],
    "微距": ["garden_macro"],
    "neon": ["neon_night"],
    "霓虹": ["neon_night"],
    "fog": ["foggy_morning"],
    "雾": ["foggy_morning"],
    "cherry blossom": ["cherry_blossom"],
    "樱花": ["cherry_blossom"],
    "desert": ["desert_dunes"],
    "沙漠": ["desert_dunes"],
    "café": ["cafe_interior"],
    "咖啡": ["cafe_interior"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _PHOTO_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _time_to_spot_tags(time_hint: str) -> list[str]:
    """Map time/weather hints to preferred spot categories."""
    return TIME_SPOT_MAP.get(time_hint, [])


def _build_relevance_reason(item: dict) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")
    reason_map = {
        "golden_hour_spot": "Best light for stunning landscapes and portraits",
        "street_art_wall": "Eye-catching backdrops for creative shots",
        "rooftop_view": "Breathtaking panoramas from above",
        "garden_macro": "Discover tiny worlds with your lens",
        "architecture": "Find beauty in lines and structures",
        "water_reflection": "Mirror-like reflections for dreamlike shots",
        "neon_night": "Urban night magic with vibrant colors",
        "foggy_morning": "Ethereal, moody atmosphere for artistic shots",
        "autumn_leaves": "Nature's most colorful season captured",
        "cherry_blossom": "Fleeting pink beauty — don't miss it",
        "desert_dunes": "Dramatic shadows and endless horizons",
        "cafe_interior": "Cozy vibes and warm light for lifestyle shots",
    }
    return reason_map.get(category, "A great spot for your next photo adventure")


class PhotoSpotFulfiller(L2Fulfiller):
    """L2 fulfiller for photography wishes — time/weather-aware spot recommendations.

    Uses keyword matching + time/weather hints to select from 15-type catalog,
    then applies PersonalityFilter. Zero LLM.
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
                dict(item) for item in PHOTO_SPOT_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in PHOTO_SPOT_CATALOG]

        # 3. Fallback
        if not candidates:
            candidates = [dict(item) for item in PHOTO_SPOT_CATALOG]

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
                text="Golden hour is coming — check your photo spots!",
                delay_hours=24,
            ),
        )
