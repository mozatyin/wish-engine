"""FoodFulfiller — local-compute restaurant recommendation with emotion-to-food mapping.

25-entry curated catalog across cuisine types. Core innovation: emotion -> food type
mapping (anxiety -> comfort food, sadness -> sweet, anger -> spicy, etc.).
Cultural awareness: halal, Chinese, vegetarian tags.
Multilingual keyword routing (EN/ZH/AR).
Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    ReminderOption,
)

# ── Food Catalog (25 entries) ────────────────────────────────────────────────

FOOD_CATALOG: list[dict] = [
    # ── Comfort Food (anxiety relief) ────────────────────────────────────────
    {
        "title": "Warm Noodle Soup",
        "description": "A steaming bowl of hand-pulled noodles in rich broth — the ultimate comfort.",
        "category": "comfort_food",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["comfort", "warm", "calming", "noodles", "soup", "quiet"],
        "cuisine": "asian",
        "emotion_match": ["anxiety", "fatigue"],
    },
    {
        "title": "Congee & Dim Sum",
        "description": "Gentle rice porridge with small shared plates — warm and soothing.",
        "category": "comfort_food",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["comfort", "warm", "calming", "chinese", "halal-option", "quiet"],
        "cuisine": "chinese",
        "emotion_match": ["anxiety", "sadness"],
    },
    {
        "title": "Homestyle Stew",
        "description": "Slow-cooked stew with root vegetables — like a warm hug in a bowl.",
        "category": "comfort_food",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["comfort", "warm", "calming", "hearty", "quiet"],
        "cuisine": "western",
        "emotion_match": ["anxiety", "loneliness"],
    },
    # ── Sweet & Indulgent (sadness relief) ───────────────────────────────────
    {
        "title": "Artisan Dessert Cafe",
        "description": "Handcrafted pastries, chocolate fondant, and specialty desserts.",
        "category": "dessert",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sweet", "dessert", "chocolate", "calming", "indulgent", "quiet"],
        "cuisine": "international",
        "emotion_match": ["sadness"],
    },
    {
        "title": "Ice Cream & Waffle House",
        "description": "Freshly made waffles with artisan ice cream — pure joy in every bite.",
        "category": "dessert",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["sweet", "dessert", "fun", "calming", "indulgent"],
        "cuisine": "international",
        "emotion_match": ["sadness", "joy"],
    },
    {
        "title": "Traditional Bakery",
        "description": "Freshly baked bread, pastries, and cakes — the aroma alone is therapy.",
        "category": "dessert",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sweet", "bakery", "calming", "quiet", "traditional"],
        "cuisine": "international",
        "emotion_match": ["sadness", "anxiety"],
    },
    # ── Spicy & Intense (anger release) ──────────────────────────────────────
    {
        "title": "Sichuan Hot Pot",
        "description": "Fiery broth with numbing Sichuan peppercorns — intense and cathartic.",
        "category": "spicy",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["spicy", "intense", "hot-pot", "social", "chinese"],
        "cuisine": "chinese",
        "emotion_match": ["anger"],
    },
    {
        "title": "Korean BBQ",
        "description": "Grill your own meat at the table — interactive, smoky, and satisfying.",
        "category": "spicy",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["spicy", "intense", "bbq", "social", "interactive"],
        "cuisine": "korean",
        "emotion_match": ["anger", "joy"],
    },
    {
        "title": "Thai Curry House",
        "description": "Authentic green and red curries with fresh herbs and bold flavors.",
        "category": "spicy",
        "noise": "moderate",
        "social": "medium",
        "mood": "intense",
        "tags": ["spicy", "intense", "curry", "aromatic"],
        "cuisine": "thai",
        "emotion_match": ["anger"],
    },
    {
        "title": "Indian Curry & Tandoori",
        "description": "Rich curries, fresh naan, and smoky tandoori — a feast for the senses.",
        "category": "spicy",
        "noise": "moderate",
        "social": "medium",
        "mood": "intense",
        "tags": ["spicy", "intense", "curry", "vegetarian-option", "halal-option"],
        "cuisine": "indian",
        "emotion_match": ["anger"],
    },
    # ── Celebration (joy) ────────────────────────────────────────────────────
    {
        "title": "Fine Dining Experience",
        "description": "Multi-course tasting menu with wine pairing — celebrate life's moments.",
        "category": "celebration",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["celebration", "fancy", "calming", "quiet", "special"],
        "cuisine": "international",
        "emotion_match": ["joy"],
    },
    {
        "title": "Sushi Omakase",
        "description": "Chef's choice sushi — artful, intimate, and unforgettable.",
        "category": "celebration",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["celebration", "fancy", "calming", "quiet", "japanese"],
        "cuisine": "japanese",
        "emotion_match": ["joy"],
    },
    {
        "title": "Rooftop Restaurant",
        "description": "Panoramic views with curated dishes — dining above the city lights.",
        "category": "celebration",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["celebration", "fancy", "social", "scenic"],
        "cuisine": "international",
        "emotion_match": ["joy"],
    },
    # ── Social Dining (loneliness relief) ────────────────────────────────────
    {
        "title": "Family-Style Chinese Restaurant",
        "description": "Big round table, shared dishes, lazy Susan — food brings people together.",
        "category": "social_dining",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "shared", "chinese", "family", "warm"],
        "cuisine": "chinese",
        "emotion_match": ["loneliness"],
    },
    {
        "title": "Hotpot Gathering",
        "description": "Cook together, share stories — the most social way to eat.",
        "category": "social_dining",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "shared", "hot-pot", "interactive", "warm"],
        "cuisine": "asian",
        "emotion_match": ["loneliness", "joy"],
    },
    {
        "title": "Mezze Platter Restaurant",
        "description": "Endless small plates to share — hummus, falafel, tabbouleh, and more.",
        "category": "social_dining",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "shared", "halal", "arabic", "traditional"],
        "cuisine": "arabic",
        "emotion_match": ["loneliness"],
    },
    {
        "title": "Tapas Bar",
        "description": "Spanish small plates meant for sharing — order many, taste everything.",
        "category": "social_dining",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "shared", "tapas", "fun"],
        "cuisine": "spanish",
        "emotion_match": ["loneliness", "joy"],
    },
    # ── Energizing (fatigue relief) ──────────────────────────────────────────
    {
        "title": "Specialty Coffee & Light Bites",
        "description": "Single-origin pour-over with avocado toast — fuel up without the heaviness.",
        "category": "energizing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["energizing", "coffee", "light", "calming", "quiet"],
        "cuisine": "international",
        "emotion_match": ["fatigue"],
    },
    {
        "title": "Fresh Juice & Smoothie Bar",
        "description": "Cold-pressed juices, acai bowls, and energy smoothies.",
        "category": "energizing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["energizing", "healthy", "light", "calming", "quiet"],
        "cuisine": "international",
        "emotion_match": ["fatigue"],
    },
    {
        "title": "Poke & Salad Bowl",
        "description": "Fresh, colorful, and nutritious — build your own bowl of energy.",
        "category": "energizing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["energizing", "healthy", "light", "calming", "quiet", "fresh"],
        "cuisine": "international",
        "emotion_match": ["fatigue"],
    },
    # ── Halal / Arabic ───────────────────────────────────────────────────────
    {
        "title": "Traditional Arabic Grill",
        "description": "Grilled kebabs, rice, and fresh bread — halal and deeply satisfying.",
        "category": "comfort_food",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "arabic", "traditional", "warm", "calming"],
        "cuisine": "arabic",
        "emotion_match": ["anxiety", "loneliness"],
    },
    {
        "title": "Emirati Seafood Restaurant",
        "description": "Fresh catch with traditional spices and rice — coastal comfort food.",
        "category": "comfort_food",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "arabic", "seafood", "calming", "traditional"],
        "cuisine": "arabic",
        "emotion_match": ["anxiety"],
    },
    # ── Vegetarian / Indian ──────────────────────────────────────────────────
    {
        "title": "South Indian Thali",
        "description": "Complete vegetarian meal on a banana leaf — balanced, colorful, satisfying.",
        "category": "comfort_food",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["vegetarian-option", "indian", "healthy", "calming", "traditional"],
        "cuisine": "indian",
        "emotion_match": ["anxiety", "fatigue"],
    },
    # ── Breakfast / Brunch ───────────────────────────────────────────────────
    {
        "title": "Cozy Brunch Spot",
        "description": "Eggs benedict, pancakes, and fresh coffee — a slow morning ritual.",
        "category": "comfort_food",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["comfort", "warm", "calming", "quiet", "brunch"],
        "cuisine": "western",
        "emotion_match": ["sadness", "fatigue"],
    },
    {
        "title": "Turkish Breakfast Spread",
        "description": "Cheese, olives, eggs, honey, bread — a leisurely feast to start the day.",
        "category": "comfort_food",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["comfort", "warm", "calming", "halal-option", "traditional", "shared"],
        "cuisine": "turkish",
        "emotion_match": ["sadness", "loneliness"],
    },
]


# ── Keyword -> Emotion/Category Mapping ──────────────────────────────────────

_FOOD_KEYWORDS: dict[str, list[str]] = {
    # General food keywords (broad match)
    "吃饭": [],
    "餐厅": [],
    "美食": [],
    "comfort food": ["anxiety"],
    "hungry": [],
    "مطعم": [],
    "restaurant": [],
    "dinner": [],
    "lunch": [],
    "breakfast": [],
    "brunch": ["sadness", "fatigue"],
    # Emotion-linked keywords
    "安慰": ["anxiety", "sadness"],
    "comfort": ["anxiety", "sadness"],
    "辣": ["anger"],
    "spicy": ["anger"],
    "甜": ["sadness"],
    "sweet": ["sadness"],
    "dessert": ["sadness"],
    "甜点": ["sadness"],
    "حلويات": ["sadness"],
    "火锅": ["loneliness", "anger"],
    "hotpot": ["loneliness", "anger"],
    "hot pot": ["loneliness", "anger"],
    "bbq": ["anger"],
    "烧烤": ["anger"],
    "شواء": ["anger"],
    "coffee": ["fatigue"],
    "咖啡": ["fatigue"],
    "قهوة": ["fatigue"],
    "celebrate": ["joy"],
    "庆祝": ["joy"],
    "احتفال": ["joy"],
    "fancy": ["joy"],
    "halal": [],
    "حلال": [],
    "清真": [],
    "vegetarian": [],
    "素食": [],
    "نباتي": [],
}

# ── Emotion -> food category mapping ─────────────────────────────────────────

_EMOTION_TO_FOOD: dict[str, list[str]] = {
    "anxiety": ["comfort_food"],
    "sadness": ["dessert", "comfort_food"],
    "anger": ["spicy"],
    "joy": ["celebration"],
    "loneliness": ["social_dining"],
    "fatigue": ["energizing"],
}


def _detect_emotions_from_text(wish_text: str) -> list[str]:
    """Detect emotion hints from wish keywords."""
    text_lower = wish_text.lower()
    emotions: list[str] = []
    for keyword, emo_list in _FOOD_KEYWORDS.items():
        if keyword in text_lower and emo_list:
            for e in emo_list:
                if e not in emotions:
                    emotions.append(e)
    return emotions


def _get_dominant_emotion(detector_results: DetectorResults) -> str | None:
    """Get the user's dominant negative emotion from detector results."""
    emotions = detector_results.emotion.get("emotions", {})
    if not emotions:
        return None
    # Check key emotions in priority order
    for emo in ["anxiety", "sadness", "anger", "loneliness", "fatigue", "joy"]:
        if emotions.get(emo, 0) > 0.4:
            return emo
    return None


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on emotion and keyword matching."""
    # 1. Detect emotions from text keywords
    text_emotions = _detect_emotions_from_text(wish_text)

    # 2. Get dominant emotion from detectors
    dominant = _get_dominant_emotion(detector_results)
    if dominant and dominant not in text_emotions:
        text_emotions.append(dominant)

    # 3. Cultural filtering hints
    text_lower = wish_text.lower()
    culture_tags: list[str] = []
    if any(kw in text_lower for kw in ["halal", "حلال", "清真", "arabic", "عربي"]):
        culture_tags.append("halal")
    if any(kw in text_lower for kw in ["中餐", "chinese", "中国"]):
        culture_tags.append("chinese")
    if any(kw in text_lower for kw in ["vegetarian", "素食", "نباتي", "indian"]):
        culture_tags.append("vegetarian-option")

    # 4. Filter candidates
    candidates: list[dict] = []
    for item in FOOD_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Emotion matching
        if text_emotions:
            item_emotions = set(item.get("emotion_match", []))
            matched_emotions = set(text_emotions) & item_emotions
            if matched_emotions:
                score_boost += 0.2 * len(matched_emotions)
                item_copy["relevance_reason"] = _emotion_reason(list(matched_emotions)[0])
            else:
                score_boost -= 0.1

        # Cultural matching
        item_tags = set(item.get("tags", []))
        if culture_tags:
            if set(culture_tags) & item_tags:
                score_boost += 0.15
            # If halal requested, skip non-halal-compatible
            if "halal" in culture_tags and "halal" not in item_tags and "halal-option" not in item_tags:
                continue

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    # 5. If no emotion match narrowed things, return full catalog
    if not candidates:
        candidates = [dict(item) for item in FOOD_CATALOG]

    return candidates


def _emotion_reason(emotion: str) -> str:
    """Build a relevance reason based on the matched emotion."""
    reasons = {
        "anxiety": "Warm comfort food to ease your mind",
        "sadness": "Something sweet to lift your spirits",
        "anger": "Bold, intense flavors for emotional release",
        "joy": "A celebration-worthy dining experience",
        "loneliness": "Shared plates to enjoy with company",
        "fatigue": "Light and energizing to recharge you",
    }
    return reasons.get(emotion, "Matches your current mood")


class FoodFulfiller(L2Fulfiller):
    """L2 fulfiller for food/restaurant wishes — emotion-to-cuisine mapping.

    Uses emotion detection + cultural awareness + personality filtering.
    25-entry curated catalog. Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
        """Filter, score with personality + emotion boost, convert to Recommendations."""
        from wish_engine.models import Recommendation

        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        # Add emotion boost on top of personality score
        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:max_results]

        return [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "Matches your profile"),
                score=c.get("_personality_score", 0.5),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match candidates from catalog
        candidates = _match_candidates(wish.wish_text, detector_results)

        # 2. Add default relevance reasons where missing
        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = _build_food_relevance(c, detector_results)

        # 3. Build recommendations via personality filter with emotion boost
        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="restaurant", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Try this restaurant today?",
                delay_hours=4,
            ),
        )


def _build_food_relevance(item: dict, detector_results: DetectorResults) -> str:
    """Build a personalized relevance reason for food recommendations."""
    dominant = _get_dominant_emotion(detector_results)
    if dominant and dominant in item.get("emotion_match", []):
        return _emotion_reason(dominant)

    category = item.get("category", "")
    reasons = {
        "comfort_food": "Warm and comforting — just what you need",
        "dessert": "A sweet treat to brighten your day",
        "spicy": "Bold flavors for an intense experience",
        "celebration": "Something special to celebrate",
        "social_dining": "Best enjoyed with good company",
        "energizing": "Light and fresh to recharge",
    }
    return reasons.get(category, "A great dining recommendation for you")
