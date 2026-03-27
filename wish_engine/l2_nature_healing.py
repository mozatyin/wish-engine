"""NatureHealingFulfiller — emotion-matched nature healing route recommendations.

15-type curated catalog of nature experiences with emotion-based mapping
(anxiety→forest, sadness→beach, anger→mountain). Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Emotion → Nature Type Mapping ────────────────────────────────────────────

EMOTION_NATURE_MAP: dict[str, list[str]] = {
    "anxiety": ["forest_bathing", "garden_meditation", "bamboo_forest", "ancient_tree"],
    "sadness": ["beach_walk", "lake", "riverside", "coastal_cliff"],
    "anger": ["mountain_hike", "waterfall", "desert_stargazing"],
    "fear": ["garden_meditation", "flower_field", "hot_spring"],
    "joy": ["flower_field", "wildflower", "beach_walk"],
    "fatigue": ["hot_spring", "lake", "forest_bathing"],
    "loneliness": ["bird_watching", "garden_meditation", "beach_walk"],
}

# ── Nature Healing Catalog (15 entries) ──────────────────────────────────────

NATURE_CATALOG: list[dict] = [
    {
        "title": "Forest Bathing (Shinrin-yoku)",
        "description": "Slow, mindful walk through forest trails — let the trees heal you.",
        "category": "forest_bathing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["forest_bathing", "calming", "quiet", "nature"],
    },
    {
        "title": "Beach Walk & Ocean Sounds",
        "description": "Walk along the shore, feel the sand, listen to the waves.",
        "category": "beach_walk",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["beach_walk", "calming", "quiet", "nature"],
    },
    {
        "title": "Mountain Hike & Summit Views",
        "description": "Climb to a viewpoint and release your energy on the trail.",
        "category": "mountain_hike",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["mountain_hike", "nature", "practical"],
    },
    {
        "title": "Garden Meditation Retreat",
        "description": "Sit among flowers and greenery — a botanical sanctuary for the mind.",
        "category": "garden_meditation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["garden_meditation", "calming", "quiet", "nature"],
    },
    {
        "title": "Riverside Walk & Reflection",
        "description": "Follow the river's path — let the flowing water carry your worries.",
        "category": "riverside",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["riverside", "calming", "quiet", "nature"],
    },
    {
        "title": "Desert Stargazing Night",
        "description": "Under a vast desert sky — constellations, silence, and perspective.",
        "category": "desert_stargazing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["desert_stargazing", "quiet", "nature", "spiritual"],
    },
    {
        "title": "Waterfall Trail Adventure",
        "description": "Hike to a waterfall — the roar of water drowns out the noise of life.",
        "category": "waterfall",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["waterfall", "nature", "practical"],
    },
    {
        "title": "Lakeside Serenity",
        "description": "Sit by a calm lake — mirror-still water reflecting sky and trees.",
        "category": "lake",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["lake", "calming", "quiet", "nature"],
    },
    {
        "title": "Flower Field Immersion",
        "description": "Walk through lavender, sunflower, or wildflower fields in bloom.",
        "category": "flower_field",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["flower_field", "calming", "quiet", "nature"],
    },
    {
        "title": "Bamboo Forest Walk",
        "description": "Tall bamboo swaying in the breeze — a natural cathedral of green.",
        "category": "bamboo_forest",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["bamboo_forest", "calming", "quiet", "nature", "traditional"],
    },
    {
        "title": "Hot Spring Soak",
        "description": "Natural hot springs — mineral-rich water to relax body and mind.",
        "category": "hot_spring",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["hot_spring", "calming", "quiet", "nature"],
    },
    {
        "title": "Coastal Cliff Walk",
        "description": "Walk along dramatic sea cliffs — wind, waves, and wide horizons.",
        "category": "coastal_cliff",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["coastal_cliff", "nature", "quiet"],
    },
    {
        "title": "Wildflower Trail",
        "description": "Discover native wildflowers on a gentle trail — seasonal beauty.",
        "category": "wildflower",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wildflower", "calming", "quiet", "nature"],
    },
    {
        "title": "Ancient Tree Sanctuary",
        "description": "Visit centuries-old trees — feel small in the best possible way.",
        "category": "ancient_tree",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ancient_tree", "calming", "quiet", "nature", "traditional", "heritage"],
    },
    {
        "title": "Bird Watching Expedition",
        "description": "Binoculars, patience, and wonder — discover the birds around you.",
        "category": "bird_watching",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["bird_watching", "quiet", "nature", "calming"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_NATURE_KEYWORDS: dict[str, list[str]] = {
    "自然": ["nature"],
    "nature": ["nature"],
    "森林": ["forest_bathing"],
    "forest": ["forest_bathing"],
    "海边": ["beach_walk"],
    "beach": ["beach_walk"],
    "طبيعة": ["nature"],
    "healing": ["calming"],
    "疗愈": ["calming"],
    "mountain": ["mountain_hike"],
    "山": ["mountain_hike"],
    "جبل": ["mountain_hike"],
    "lake": ["lake"],
    "湖": ["lake"],
    "بحيرة": ["lake"],
    "waterfall": ["waterfall"],
    "瀑布": ["waterfall"],
    "garden": ["garden_meditation"],
    "花园": ["garden_meditation"],
    "stargazing": ["desert_stargazing"],
    "星空": ["desert_stargazing"],
    "hot spring": ["hot_spring"],
    "温泉": ["hot_spring"],
    "bird": ["bird_watching"],
    "观鸟": ["bird_watching"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _NATURE_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _emotion_to_nature_tags(emotions: dict) -> list[str]:
    """Map user's detected emotions to nature healing types."""
    tags: list[str] = []
    for emotion, score in emotions.items():
        if score > 0.3:
            for tag in EMOTION_NATURE_MAP.get(emotion, []):
                if tag not in tags:
                    tags.append(tag)
    return tags


def _build_relevance_reason(item: dict, emotions: dict) -> str:
    """Build a personalized relevance reason based on emotions."""
    category = item.get("category", "")

    # Emotion-based reasons
    if emotions.get("anxiety", 0) > 0.3 and category in ("forest_bathing", "bamboo_forest", "garden_meditation"):
        return "Nature's calm to soothe your restless mind"
    if emotions.get("sadness", 0) > 0.3 and category in ("beach_walk", "lake", "riverside"):
        return "Water has a way of washing away sadness"
    if emotions.get("anger", 0) > 0.3 and category in ("mountain_hike", "waterfall"):
        return "Release your energy on the trail"

    reason_map = {
        "forest_bathing": "Let the forest restore your inner peace",
        "beach_walk": "The ocean's rhythm syncs with your heartbeat",
        "mountain_hike": "Climb above it all for fresh perspective",
        "garden_meditation": "A living sanctuary for quiet reflection",
        "desert_stargazing": "The universe puts everything in perspective",
        "hot_spring": "Warm mineral waters to melt away tension",
        "bird_watching": "Slow down and notice the beauty around you",
        "lake": "Still water reflects a still mind",
        "ancient_tree": "Stand beneath centuries of quiet wisdom",
    }
    return reason_map.get(category, "Nature heals — step outside and feel it")


class NatureHealingFulfiller(L2Fulfiller):
    """L2 fulfiller for nature healing wishes — emotion-matched recommendations.

    Uses keyword matching + emotion→nature mapping to select from 15-type
    catalog, then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Add emotion-based categories
        emotions = detector_results.emotion.get("emotions", {})
        emotion_tags = _emotion_to_nature_tags(emotions)

        all_tags = list(matched_categories)
        for t in emotion_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in NATURE_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in NATURE_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in NATURE_CATALOG]

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, emotions)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Nature is always here for you — come back for more healing routes!",
                delay_hours=24,
            ),
        )
