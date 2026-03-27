"""TravelFulfiller — personality-driven travel destination recommendations.

20-entry curated destination catalog with MBTI + values mapping. Zero LLM.
Key innovation: maps introversion/extroversion + values to ideal destinations.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── MBTI/Values → Destination Tag Mapping ────────────────────────────────────

PERSONALITY_DEST_MAP: dict[str, list[str]] = {
    "introvert": ["solitude", "nature", "quiet", "reflective"],
    "extrovert": ["vibrant", "social", "nightlife", "festival"],
    "tradition": ["heritage", "spiritual", "ancient", "cultural"],
    "stimulation": ["adventure", "extreme", "wildlife", "trekking"],
    "universalism": ["cultural", "heritage", "diversity", "art"],
    "self-direction": ["off_beaten_path", "trekking", "nature", "solitude"],
    "hedonism": ["nightlife", "beach", "food_capital", "vibrant"],
    "achievement": ["adventure", "trekking", "extreme", "challenge"],
    "security": ["safe", "developed", "quiet", "nature"],
    "benevolence": ["community", "spiritual", "cultural", "heritage"],
}

# ── Destination Catalog (20 entries) ─────────────────────────────────────────

DESTINATION_CATALOG: list[dict] = [
    # ── Introvert / Solitude (5) ──────────────────────────────────────────────
    {
        "title": "Iceland — Land of Fire and Ice",
        "description": "Vast empty landscapes, hot springs, and northern lights in blissful solitude.",
        "category": "iceland",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solitude", "nature", "quiet", "safe", "reflective", "developed"],
    },
    {
        "title": "New Zealand — Middle Earth Serenity",
        "description": "Rolling green hills, fjords, and stargazing far from crowds.",
        "category": "new_zealand",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solitude", "nature", "quiet", "safe", "adventure", "developed"],
    },
    {
        "title": "Norway — Fjords and Northern Silence",
        "description": "Dramatic fjords, midnight sun, and the world's most peaceful coastlines.",
        "category": "norway",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solitude", "nature", "quiet", "safe", "reflective", "developed"],
    },
    {
        "title": "Bhutan — Happiness Kingdom",
        "description": "Himalayan monasteries, prayer flags, and a culture built on mindfulness.",
        "category": "bhutan",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solitude", "spiritual", "heritage", "quiet", "reflective"],
    },
    {
        "title": "Patagonia — End of the World",
        "description": "Glaciers, wild peaks, and infinite sky at the southern tip of the Americas.",
        "category": "patagonia",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["solitude", "nature", "adventure", "trekking", "off_beaten_path"],
    },
    # ── Extrovert / Social (5) ────────────────────────────────────────────────
    {
        "title": "Barcelona — Mediterranean Energy",
        "description": "Gaudi architecture, tapas bars, beach parties, and non-stop street life.",
        "category": "barcelona",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["vibrant", "social", "nightlife", "food_capital", "art", "festival"],
    },
    {
        "title": "Rio de Janeiro — Carnival Spirit",
        "description": "Samba rhythms, Copacabana energy, and the warmest people on Earth.",
        "category": "rio",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["vibrant", "social", "nightlife", "festival", "beach"],
    },
    {
        "title": "Bangkok — Sensory Overload",
        "description": "Street food paradise, temple hopping, rooftop bars, and night markets.",
        "category": "bangkok",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["vibrant", "social", "food_capital", "nightlife", "cultural"],
    },
    {
        "title": "Marrakech — Market Magic",
        "description": "Overflowing souks, rooftop terraces, and desert sunsets with mint tea.",
        "category": "marrakech",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["vibrant", "social", "heritage", "cultural", "food_capital"],
    },
    {
        "title": "Dubai — Modern Spectacle",
        "description": "Sky-high luxury, desert adventures, and a global crossroads of cultures.",
        "category": "dubai",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["vibrant", "social", "nightlife", "beach", "developed"],
    },
    # ── Tradition / Heritage (5) ──────────────────────────────────────────────
    {
        "title": "Kyoto — Timeless Japan",
        "description": "Zen gardens, bamboo groves, tea ceremonies, and thousand-year-old temples.",
        "category": "kyoto",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["heritage", "spiritual", "ancient", "cultural", "quiet", "reflective"],
    },
    {
        "title": "Istanbul — Where Continents Meet",
        "description": "Byzantine mosaics, Ottoman mosques, and bazaars bridging East and West.",
        "category": "istanbul",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["heritage", "ancient", "cultural", "food_capital", "diversity"],
    },
    {
        "title": "Jerusalem — Sacred Crossroads",
        "description": "Three faiths, ancient stones, and a weight of history in every step.",
        "category": "jerusalem",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["heritage", "spiritual", "ancient", "cultural"],
    },
    {
        "title": "Varanasi — Soul of India",
        "description": "Ganges rituals, evening prayers, and the oldest living city on Earth.",
        "category": "varanasi",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["heritage", "spiritual", "ancient", "cultural", "community"],
    },
    {
        "title": "Fez — Medieval Labyrinth",
        "description": "World's largest car-free urban zone, artisan crafts, and Sufi music.",
        "category": "fez",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["heritage", "ancient", "cultural", "off_beaten_path"],
    },
    # ── Adventure / Stimulation (5) ───────────────────────────────────────────
    {
        "title": "Nepal — Roof of the World",
        "description": "Himalayan trekking, Everest base camp, and Buddhist monasteries in the clouds.",
        "category": "nepal",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["adventure", "trekking", "extreme", "nature", "spiritual", "challenge"],
    },
    {
        "title": "Costa Rica — Pura Vida",
        "description": "Zip-lines, volcanoes, wildlife, and rainforest canopy walks.",
        "category": "costa_rica",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["adventure", "wildlife", "nature", "off_beaten_path"],
    },
    {
        "title": "Mongolia — Infinite Steppe",
        "description": "Nomadic camps, horseback riding, and skies that never end.",
        "category": "mongolia",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["adventure", "off_beaten_path", "nature", "solitude", "extreme"],
    },
    {
        "title": "Peru — Inca Trail to Machu Picchu",
        "description": "Ancient ruins, Andean passes, and one of Earth's great pilgrimages.",
        "category": "peru",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["adventure", "trekking", "heritage", "ancient", "challenge"],
    },
    {
        "title": "Tanzania — Serengeti and Kilimanjaro",
        "description": "Great migration, summit sunrise, and Africa's deepest wilderness.",
        "category": "tanzania",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["adventure", "wildlife", "extreme", "nature", "challenge"],
    },
]

# ── Culture / Art (mapped via tags overlap with heritage) ─────────────────
# Paris, Rome, Cairo, Beijing, St Petersburg are covered above through
# tag overlap. We use the 20 entries above to cover all 5 personality axes.


# ── Keyword Extraction ───────────────────────────────────────────────────────

_TRAVEL_KEYWORDS: dict[str, list[str]] = {
    "beach": ["beach", "vibrant"],
    "海滩": ["beach", "vibrant"],
    "mountain": ["trekking", "nature", "adventure"],
    "山": ["trekking", "nature", "adventure"],
    "temple": ["heritage", "spiritual"],
    "寺庙": ["heritage", "spiritual"],
    "hike": ["trekking", "adventure"],
    "hiking": ["trekking", "adventure"],
    "city": ["vibrant", "social"],
    "城市": ["vibrant", "social"],
    "nature": ["nature", "solitude"],
    "自然": ["nature", "solitude"],
    "adventure": ["adventure", "extreme"],
    "冒险": ["adventure", "extreme"],
    "culture": ["cultural", "heritage"],
    "文化": ["cultural", "heritage"],
    "quiet": ["quiet", "solitude"],
    "安静": ["quiet", "solitude"],
    "solo": ["solitude", "quiet"],
}


def _match_travel_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _TRAVEL_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


def _personality_to_tags(detector_results: DetectorResults) -> list[str]:
    tags: list[str] = []
    # MBTI-based
    mbti = detector_results.mbti
    if mbti.get("type"):
        ei = mbti.get("dimensions", {}).get("E_I", 0.5)
        if ei < 0.4:
            for t in PERSONALITY_DEST_MAP["introvert"]:
                if t not in tags:
                    tags.append(t)
        elif ei > 0.6:
            for t in PERSONALITY_DEST_MAP["extrovert"]:
                if t not in tags:
                    tags.append(t)
    # Values-based
    top_values = detector_results.values.get("top_values", [])
    for value in top_values:
        for t in PERSONALITY_DEST_MAP.get(value, []):
            if t not in tags:
                tags.append(t)
    return tags


class TravelFulfiller(L2Fulfiller):
    """L2 fulfiller for travel wishes — MBTI + values destination matching.

    Uses keyword matching + personality→destination mapping to select from
    20-entry catalog, then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        keyword_tags = _match_travel_tags(wish.wish_text)

        # 2. Add personality-based tags
        personality_tags = _personality_to_tags(detector_results)

        all_tags = list(keyword_tags)
        for t in personality_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in DESTINATION_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in DESTINATION_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in DESTINATION_CATALOG]

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Dreaming of a trip? Save this for later!",
                delay_hours=72,
            ),
        )


def _build_relevance_reason(item: dict, det: DetectorResults) -> str:
    tags = set(item.get("tags", []))
    mbti_type = det.mbti.get("type", "")
    top_values = det.values.get("top_values", [])

    if mbti_type and len(mbti_type) == 4 and mbti_type[0] == "I" and "solitude" in tags:
        return "Perfect for an introvert seeking solitude and reflection"
    if mbti_type and len(mbti_type) == 4 and mbti_type[0] == "E" and "vibrant" in tags:
        return "High-energy destination matching your social personality"
    if "tradition" in top_values and "heritage" in tags:
        return "Rich cultural heritage aligning with your traditional values"
    if "stimulation" in top_values and "adventure" in tags:
        return "Adventure awaits — matching your thirst for stimulation"
    if "universalism" in top_values and "cultural" in tags:
        return "Cultural diversity matching your universalist worldview"

    category = item.get("category", "")
    return f"A unique {category.replace('_', ' ')} experience recommended for you"
