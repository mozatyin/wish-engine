"""DateSpotFulfiller — personality-matched date spot recommendations.

15-entry curated date catalog with Bond Comparator style: matches BOTH
people's MBTI for the ideal date. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── MBTI Pair → Date Style Mapping ───────────────────────────────────────────
# For solo use, maps own MBTI traits to preferred date types.

TRAIT_DATE_MAP: dict[str, list[str]] = {
    "I": ["quiet_dinner", "bookstore_cafe", "art_gallery_date", "stargazing", "sunset_walk"],
    "E": ["rooftop_bar", "live_music", "comedy_show", "escape_room", "farmers_market"],
    "N": ["art_gallery_date", "stargazing", "bookstore_cafe", "pottery_class", "sunset_walk"],
    "S": ["cooking_class_together", "farmers_market", "kayaking", "picnic_park", "wine_tasting"],
    "T": ["escape_room", "wine_tasting", "cooking_class_together", "kayaking"],
    "F": ["sunset_walk", "picnic_park", "stargazing", "pottery_class", "art_gallery_date"],
    "J": ["quiet_dinner", "cooking_class_together", "wine_tasting", "art_gallery_date"],
    "P": ["farmers_market", "live_music", "rooftop_bar", "comedy_show", "kayaking"],
}

# ── Date Catalog (15 entries) ────────────────────────────────────────────────

DATE_CATALOG: list[dict] = [
    {
        "title": "Quiet Dinner at a Hidden Gem",
        "description": "Intimate candlelit restaurant with no crowds — just the two of you.",
        "category": "quiet_dinner",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet_dinner", "quiet", "calming", "intimate", "food"],
    },
    {
        "title": "Rooftop Bar with City Views",
        "description": "Cocktails, city lights, and conversation above it all.",
        "category": "rooftop_bar",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["rooftop_bar", "social", "vibrant", "nightlife"],
    },
    {
        "title": "Cooking Class for Two",
        "description": "Learn a new cuisine together — pasta, sushi, or Thai curry.",
        "category": "cooking_class_together",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["cooking_class_together", "practical", "hands_on", "food", "creative"],
    },
    {
        "title": "Art Gallery Date",
        "description": "Wander through exhibitions and discover each other's taste in art.",
        "category": "art_gallery_date",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["art_gallery_date", "quiet", "calming", "cultural", "reflective"],
    },
    {
        "title": "Sunset Walk by the Water",
        "description": "Golden hour along the shore or river — simple and unforgettable.",
        "category": "sunset_walk",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sunset_walk", "quiet", "calming", "nature", "romantic"],
    },
    {
        "title": "Bookstore Cafe Afternoon",
        "description": "Browse books, share finds, and sip coffee in a cozy corner.",
        "category": "bookstore_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["bookstore_cafe", "quiet", "calming", "intellectual", "self-paced"],
    },
    {
        "title": "Live Music Night",
        "description": "Jazz club, indie gig, or open mic — shared rhythm and energy.",
        "category": "live_music",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["live_music", "social", "vibrant", "nightlife", "energetic"],
    },
    {
        "title": "Escape Room Challenge",
        "description": "Solve puzzles together under pressure — see how you collaborate.",
        "category": "escape_room",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["escape_room", "practical", "hands_on", "challenge", "teamwork"],
    },
    {
        "title": "Farmers Market Morning",
        "description": "Fresh produce, street food, and lazy morning strolls together.",
        "category": "farmers_market",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["farmers_market", "social", "food", "nature", "casual"],
    },
    {
        "title": "Kayaking for Two",
        "description": "Paddle together through calm waters — adventure at your own pace.",
        "category": "kayaking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["kayaking", "nature", "adventure", "hands_on", "active"],
    },
    {
        "title": "Pottery Class Together",
        "description": "Get your hands dirty and make something beautiful side by side.",
        "category": "pottery_class",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pottery_class", "quiet", "creative", "hands_on", "reflective"],
    },
    {
        "title": "Stargazing Picnic",
        "description": "Blanket, thermos, star chart — the universe as your backdrop.",
        "category": "stargazing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["stargazing", "quiet", "calming", "nature", "romantic", "reflective"],
    },
    {
        "title": "Picnic in the Park",
        "description": "Homemade sandwiches, a good playlist, and afternoon sunshine.",
        "category": "picnic_park",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["picnic_park", "quiet", "calming", "nature", "casual", "romantic"],
    },
    {
        "title": "Wine Tasting Experience",
        "description": "Swirl, sniff, sip — explore a vineyard or urban wine bar together.",
        "category": "wine_tasting",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wine_tasting", "quiet", "calming", "food", "practical"],
    },
    {
        "title": "Comedy Show Night",
        "description": "Shared laughter is the fastest shortcut to connection.",
        "category": "comedy_show",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["comedy_show", "social", "vibrant", "nightlife", "energetic"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_DATE_KEYWORDS: dict[str, list[str]] = {
    "dinner": ["quiet_dinner", "food"],
    "晚餐": ["quiet_dinner", "food"],
    "coffee": ["bookstore_cafe", "quiet"],
    "咖啡": ["bookstore_cafe", "quiet"],
    "outdoor": ["nature", "active"],
    "户外": ["nature", "active"],
    "cooking": ["cooking_class_together", "hands_on"],
    "做饭": ["cooking_class_together", "hands_on"],
    "art": ["art_gallery_date", "cultural"],
    "艺术": ["art_gallery_date", "cultural"],
    "music": ["live_music", "vibrant"],
    "音乐": ["live_music", "vibrant"],
    "adventure": ["adventure", "active"],
    "quiet": ["quiet", "calming"],
    "安静": ["quiet", "calming"],
    "fun": ["social", "vibrant"],
    "有趣": ["social", "vibrant"],
}


def _match_date_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _DATE_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


def _mbti_to_date_tags(det: DetectorResults) -> list[str]:
    tags: list[str] = []
    mbti_type = det.mbti.get("type", "")
    if len(mbti_type) == 4:
        for letter in mbti_type:
            for t in TRAIT_DATE_MAP.get(letter, []):
                if t not in tags:
                    tags.append(t)
    return tags


class DateSpotFulfiller(L2Fulfiller):
    """L2 fulfiller for date wishes — matches BOTH people's MBTI for ideal date.

    15 date types, personality-driven recommendations. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_date_tags(wish.wish_text)
        mbti_tags = _mbti_to_date_tags(detector_results)

        all_tags = list(keyword_tags)
        for t in mbti_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in DATE_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in DATE_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in DATE_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Save this date idea for the weekend!",
                delay_hours=48,
            ),
        )


def _build_relevance_reason(item: dict, det: DetectorResults) -> str:
    tags = set(item.get("tags", []))
    mbti_type = det.mbti.get("type", "")

    if mbti_type and len(mbti_type) == 4:
        if mbti_type[0] == "I" and "quiet" in tags:
            return "Intimate setting perfect for an introvert date"
        if mbti_type[0] == "E" and "social" in tags:
            return "Social energy matching your extroverted personality"
        if mbti_type[1] == "N" and "reflective" in tags:
            return "Thought-provoking experience for your intuitive side"
        if mbti_type[1] == "S" and "practical" in tags:
            return "Hands-on experience you will both enjoy"

    return f"A {item.get('category', '').replace('_', ' ')} date recommended for you"
