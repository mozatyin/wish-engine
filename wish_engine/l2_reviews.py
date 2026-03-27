"""ReviewsFulfiller — personality-filtered real-time review aggregation.

15-category curated catalog of reviewable venues/services with introvert-aware
personality filtering (weight "quiet" reviews higher for introverts). Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Reviews Catalog (15 entries) ─────────────────────────────────────────────

REVIEWS_CATALOG: list[dict] = [
    {
        "title": "Restaurant Reviews & Ratings",
        "description": "Top-rated restaurants nearby — filtered by cuisine, price, and atmosphere.",
        "category": "restaurant",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["restaurant", "social", "practical"],
    },
    {
        "title": "Cafe & Coffee Shop Reviews",
        "description": "Best cafes for work, dates, or quiet reading — curated by vibe.",
        "category": "cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cafe", "quiet", "calming", "practical"],
    },
    {
        "title": "Gym & Fitness Center Reviews",
        "description": "Find the right gym — equipment, classes, crowd level, and hours.",
        "category": "gym",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["gym", "social", "practical"],
    },
    {
        "title": "Spa & Wellness Reviews",
        "description": "Top-rated spas, massage centers, and wellness retreats near you.",
        "category": "spa",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["spa", "calming", "quiet"],
    },
    {
        "title": "Hotel & Accommodation Reviews",
        "description": "Best stays for your budget — comfort, location, and service rated.",
        "category": "hotel",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["hotel", "practical", "quiet"],
    },
    {
        "title": "Event & Experience Reviews",
        "description": "What others thought of local events, shows, and experiences.",
        "category": "event",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["event", "social"],
    },
    {
        "title": "Online Course Reviews",
        "description": "Honest reviews of courses on Coursera, Udemy, Skillshare, and more.",
        "category": "course",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["course", "quiet", "practical", "theory"],
    },
    {
        "title": "Therapist & Counselor Reviews",
        "description": "Find the right therapist — approach, speciality, and patient ratings.",
        "category": "therapist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["therapist", "calming", "quiet", "helping"],
    },
    {
        "title": "Coworking Space Reviews",
        "description": "Best coworking spots — WiFi, noise level, community, and pricing.",
        "category": "coworking",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["coworking", "practical", "quiet"],
    },
    {
        "title": "Park & Outdoor Space Reviews",
        "description": "Best parks for running, picnics, dog-walking, or quiet strolls.",
        "category": "park",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["park", "nature", "quiet", "calming"],
    },
    {
        "title": "Museum & Gallery Reviews",
        "description": "Art, history, and science museums — visitor ratings and must-see exhibits.",
        "category": "museum",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["museum", "quiet", "traditional", "theory"],
    },
    {
        "title": "Movie & Film Reviews",
        "description": "Latest releases and hidden gems — ratings, trailers, and recommendations.",
        "category": "movie",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["movie", "quiet", "practical"],
    },
    {
        "title": "Book Reviews & Reading Lists",
        "description": "Curated book reviews by genre — find your next great read.",
        "category": "book",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["book", "quiet", "theory"],
    },
    {
        "title": "Product Reviews & Comparisons",
        "description": "Tech, gadgets, and everyday products — honest ratings and comparisons.",
        "category": "product",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["product", "practical", "quiet"],
    },
    {
        "title": "Service Provider Reviews",
        "description": "Plumbers, electricians, cleaners — trusted local service ratings.",
        "category": "service",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["service", "practical", "quiet"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_REVIEW_KEYWORDS: dict[str, list[str]] = {
    "评价": ["review"],
    "review": ["review"],
    "评分": ["review"],
    "rating": ["review"],
    "推荐": ["review"],
    "تقييم": ["review"],
    "restaurant": ["restaurant"],
    "餐厅": ["restaurant"],
    "مطعم": ["restaurant"],
    "cafe": ["cafe"],
    "咖啡": ["cafe"],
    "gym": ["gym"],
    "健身": ["gym"],
    "spa": ["spa"],
    "hotel": ["hotel"],
    "酒店": ["hotel"],
    "فندق": ["hotel"],
    "course": ["course"],
    "课程": ["course"],
    "therapist": ["therapist"],
    "心理": ["therapist"],
    "movie": ["movie"],
    "电影": ["movie"],
    "book review": ["book"],
    "书评": ["book"],
    "museum": ["museum"],
    "博物馆": ["museum"],
    "park": ["park"],
    "公园": ["park"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _REVIEW_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict, is_introvert: bool) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")

    if is_introvert and item.get("noise") == "quiet":
        return "Highly rated and introvert-friendly — a quiet, comfortable choice"

    reason_map = {
        "restaurant": "Top-rated dining options curated for you",
        "cafe": "The best cafes for your perfect coffee moment",
        "gym": "Find a gym that fits your fitness style",
        "spa": "Relax and recharge at a top-rated spa",
        "hotel": "Trusted reviews for your next stay",
        "therapist": "Find a therapist who's right for you",
        "course": "Learn from courses others loved",
        "coworking": "The best workspaces rated by real users",
        "museum": "Discover exhibits worth your time",
        "movie": "Watch what others are raving about",
        "book": "Your next great read, recommended by readers",
        "park": "The best green spaces near you",
    }
    return reason_map.get(category, "Trusted reviews to help you decide")


class ReviewsFulfiller(L2Fulfiller):
    """L2 fulfiller for review/rating wishes — personality-filtered aggregation.

    Uses keyword matching + introvert-aware filtering to select from 15-category
    catalog, then applies PersonalityFilter (introverts weight "quiet" higher).
    Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Check introversion
        mbti_type = detector_results.mbti.get("type", "")
        ei_dim = detector_results.mbti.get("dimensions", {}).get("E_I", 0.5)
        is_introvert = len(mbti_type) >= 1 and mbti_type[0] == "I" and ei_dim < 0.4

        # 3. Filter catalog
        if matched_categories:
            tag_set = set(matched_categories)
            candidates = [
                dict(item) for item in REVIEWS_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in REVIEWS_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in REVIEWS_CATALOG]

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, is_introvert)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New reviews coming in — check back for updated ratings!",
                delay_hours=12,
            ),
        )
