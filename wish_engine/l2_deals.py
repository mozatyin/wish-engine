"""DealsFulfiller — local-compute deal recommendation with values-based personality mapping.

20-entry curated deal catalog with values→preference mapping. Zero LLM.
Key innovation: maps detector values (security, stimulation, self-direction, etc.)
to deal categories for personalized recommendations.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Values → Deal Category Mapping ───────────────────────────────────────────

VALUES_DEAL_MAP: dict[str, list[str]] = {
    "security": ["groceries", "household", "subscription", "insurance"],
    "stimulation": ["experience", "travel", "dining", "adventure"],
    "self-direction": ["learning", "books", "tools", "creative"],
    "tradition": ["cultural", "religious", "traditional", "family"],
    "benevolence": ["gifts", "charity", "family", "helping"],
    "hedonism": ["spa", "luxury_food", "entertainment", "fashion"],
    "achievement": ["fitness", "productivity", "professional", "tech"],
    "conformity": ["household", "subscription", "family", "practical"],
    "universalism": ["eco", "charity", "organic", "sustainable"],
    "power": ["luxury_food", "fashion", "tech", "professional"],
}

# ── Deal Catalog (20 entries) ────────────────────────────────────────────────

DEAL_CATALOG: list[dict] = [
    # ── Practical / Security (3) ─────────────────────────────────────────────
    {
        "title": "Weekly Grocery Bundle Deal",
        "description": "Save 20% on weekly grocery essentials at partner stores.",
        "category": "groceries",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "groceries", "household", "security", "budget"],
    },
    {
        "title": "Home Essentials Package",
        "description": "Bulk household supplies at 30% off — cleaning, storage, and more.",
        "category": "household",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "household", "security", "budget"],
    },
    {
        "title": "Streaming Subscription Bundle",
        "description": "Get 3 months of premium streaming for the price of 1.",
        "category": "subscription",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["subscription", "entertainment", "digital", "self-paced"],
    },
    # ── Experience / Stimulation (3) ─────────────────────────────────────────
    {
        "title": "Adventure Activity Pass",
        "description": "40% off zip-lining, rock climbing, or kayaking this weekend.",
        "category": "experience",
        "noise": "loud",
        "social": "medium",
        "mood": "intense",
        "tags": ["experience", "stimulation", "adventure", "outdoor", "social"],
    },
    {
        "title": "Weekend Travel Deal",
        "description": "Last-minute hotel + flight bundles at 35% off for spontaneous trips.",
        "category": "travel",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["travel", "stimulation", "experience", "adventure"],
    },
    {
        "title": "Restaurant Discovery Deal",
        "description": "50% off first visit to top-rated local restaurants.",
        "category": "dining",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["dining", "stimulation", "experience", "social", "food"],
    },
    # ── Learning / Self-Direction (3) ────────────────────────────────────────
    {
        "title": "Online Course Subscription",
        "description": "50% off annual learning platform subscription — thousands of courses.",
        "category": "learning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["learning", "self-direction", "digital", "self-paced", "theory"],
    },
    {
        "title": "Book Bundle Deal",
        "description": "Buy 3 get 1 free on bestselling books across all genres.",
        "category": "books",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["books", "self-direction", "learning", "self-paced", "quiet"],
    },
    {
        "title": "Creative Tools Kit",
        "description": "25% off digital creative tools — design, music, video editing.",
        "category": "tools",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["tools", "self-direction", "creative", "digital", "self-paced"],
    },
    # ── Cultural / Tradition (2) ─────────────────────────────────────────────
    {
        "title": "Traditional Craft Workshop",
        "description": "Learn traditional arts and crafts at 30% off — pottery, calligraphy, weaving.",
        "category": "cultural",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["cultural", "traditional", "tradition", "learning", "calming"],
    },
    {
        "title": "Religious Books & Items",
        "description": "Special discounts on religious texts, prayer items, and spiritual resources.",
        "category": "religious",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["religious", "traditional", "tradition", "quiet", "peaceful"],
    },
    # ── Gifts / Benevolence (2) ──────────────────────────────────────────────
    {
        "title": "Gift Bundle for Loved Ones",
        "description": "Curated gift sets at 25% off — perfect for birthdays, holidays, or just because.",
        "category": "gifts",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["gifts", "benevolence", "family", "helping", "calming"],
    },
    {
        "title": "Charity Donation Match",
        "description": "Your donation doubled — partner charities matching contributions this week.",
        "category": "charity",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["charity", "benevolence", "helping", "universalism", "peaceful"],
    },
    # ── Indulgence / Hedonism (3) ────────────────────────────────────────────
    {
        "title": "Spa & Wellness Day",
        "description": "50% off full-day spa packages — massage, facial, and relaxation.",
        "category": "spa",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["spa", "hedonism", "calming", "quiet", "self-paced"],
    },
    {
        "title": "Gourmet Food Box",
        "description": "Premium artisanal food box delivered at 30% off — cheeses, chocolates, wines.",
        "category": "luxury_food",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["luxury_food", "hedonism", "food", "indulgence", "self-paced"],
    },
    {
        "title": "Entertainment VIP Pass",
        "description": "VIP concert and event tickets at 40% off for premium experiences.",
        "category": "entertainment",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["entertainment", "hedonism", "social", "experience"],
    },
    # ── Achievement / Fitness (2) ────────────────────────────────────────────
    {
        "title": "Fitness Equipment Deal",
        "description": "30% off home gym equipment — resistance bands, dumbbells, mats.",
        "category": "fitness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["fitness", "achievement", "practical", "self-paced"],
    },
    {
        "title": "Productivity Software Bundle",
        "description": "Premium productivity apps at 60% off — task management, note-taking, focus tools.",
        "category": "productivity",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["productivity", "achievement", "digital", "self-paced", "tools"],
    },
    # ── Eco / Universalism (2) ───────────────────────────────────────────────
    {
        "title": "Organic Grocery Box",
        "description": "Weekly organic produce box delivered at 20% off from local farms.",
        "category": "organic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["organic", "eco", "sustainable", "universalism", "practical"],
    },
    {
        "title": "Eco-Friendly Home Products",
        "description": "Sustainable household products at 25% off — reusable, biodegradable, zero-waste.",
        "category": "eco",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["eco", "sustainable", "universalism", "practical", "household"],
    },
]


# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_DEAL_KEYWORDS: dict[str, list[str]] = {
    # general deal terms
    "deal": [],
    "deals": [],
    "discount": [],
    "折扣": [],
    "优惠": [],
    "省钱": [],
    "便宜": [],
    "sale": [],
    "تخفيض": [],
    "خصم": [],
    # category-specific
    "grocery": ["groceries", "practical"],
    "food": ["food", "dining"],
    "restaurant": ["dining", "social"],
    "travel": ["travel", "experience"],
    "旅行": ["travel", "experience"],
    "book": ["books", "learning"],
    "书": ["books", "learning"],
    "course": ["learning", "self-paced"],
    "课程": ["learning", "self-paced"],
    "spa": ["spa", "calming"],
    "gift": ["gifts", "benevolence"],
    "礼物": ["gifts", "benevolence"],
    "fitness": ["fitness", "achievement"],
    "健身": ["fitness", "achievement"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _DEAL_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _values_to_deal_tags(top_values: list[str]) -> list[str]:
    """Map user's top values to preferred deal tag categories."""
    tags: list[str] = []
    for value in top_values:
        for tag in VALUES_DEAL_MAP.get(value, []):
            if tag not in tags:
                tags.append(tag)
    return tags


class DealsFulfiller(L2Fulfiller):
    """L2 fulfiller for deal/discount wishes — values-aware deal recommendations.

    Uses keyword matching + values→deal mapping to select from 20-entry catalog,
    then applies PersonalityFilter. Budget-aware filtering. Zero LLM.
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
        values_tags = _values_to_deal_tags(top_values)

        # Combine keyword + values tags
        all_tags = list(matched_categories)
        for t in values_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in DEAL_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in DEAL_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in DEAL_CATALOG]

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
                text="Check back for new deals tomorrow!",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict, top_values: list[str]) -> str:
    """Build a personalized relevance reason based on values."""
    tags = set(item.get("tags", []))

    # Values-based reasons
    for value in top_values:
        if value == "security" and tags & {"practical", "groceries", "household"}:
            return "Practical deal that supports your value of security"
        if value == "stimulation" and tags & {"experience", "travel", "adventure"}:
            return "Exciting experience matching your love of stimulation"
        if value == "self-direction" and tags & {"learning", "books", "tools"}:
            return "Supports your independent learning journey"
        if value == "tradition" and tags & {"cultural", "traditional", "religious"}:
            return "Aligns with your cultural and traditional values"
        if value == "benevolence" and tags & {"gifts", "charity", "helping"}:
            return "Perfect for someone who loves giving to others"
        if value == "hedonism" and tags & {"spa", "luxury_food", "entertainment"}:
            return "Treat yourself — you deserve it"

    # Category-based fallback
    category = item.get("category", "")
    reason_map = {
        "groceries": "Save on everyday essentials",
        "learning": "Invest in yourself at a great price",
        "travel": "Explore new places for less",
        "spa": "Relaxation at a great value",
        "gifts": "Great deal for gifts",
        "fitness": "Stay active and save",
    }
    return reason_map.get(category, "Great deal recommended for you")
