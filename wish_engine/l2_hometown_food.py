"""HometownFoodFulfiller — authentic hometown cuisine for diaspora users.

25-entry curated catalog of cuisine types. Core innovation: emotion -> comfort/feast
mapping for homesick diaspora users.
Cultural tags: halal, vegetarian, spicy, comfort, family_style, street_food.
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
    Recommendation,
    ReminderOption,
)

# ── Hometown Cuisine Catalog (25 entries) ────────────────────────────────────

HOMETOWN_FOOD_CATALOG: list[dict] = [
    # ── Chinese Regional ────────────────────────────────────────────────────
    {
        "title": "Sichuan Mala Hot Pot",
        "description": "Numbing, fiery broth with authentic Sichuan peppercorns — taste of home.",
        "category": "chinese_sichuan",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["spicy", "comfort", "family_style", "chinese"],
        "emotion_match": ["homesick", "celebration"],
        "cultural_tags": ["spicy", "family_style"],
    },
    {
        "title": "Cantonese Dim Sum Brunch",
        "description": "Steamer baskets of har gow, siu mai, and char siu bao — Sunday tradition.",
        "category": "chinese_cantonese",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["comfort", "family_style", "chinese", "traditional"],
        "emotion_match": ["homesick", "lonely"],
        "cultural_tags": ["family_style", "comfort"],
    },
    {
        "title": "Hunan Smoked Meat & Chili",
        "description": "Smoky preserved meats with fresh chilies — bold Hunan flavors.",
        "category": "chinese_hunan",
        "noise": "moderate",
        "social": "medium",
        "mood": "intense",
        "tags": ["spicy", "comfort", "chinese", "street_food"],
        "emotion_match": ["homesick"],
        "cultural_tags": ["spicy", "street_food"],
    },
    {
        "title": "Dongbei Jiaozi & Stew",
        "description": "Hand-wrapped dumplings and hearty stews — northeastern soul food.",
        "category": "chinese_dongbei",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["comfort", "family_style", "chinese"],
        "emotion_match": ["homesick", "lonely"],
        "cultural_tags": ["comfort", "family_style"],
    },
    # ── South & Southeast Asian ─────────────────────────────────────────────
    {
        "title": "Filipino Adobo & Sinigang",
        "description": "Tangy tamarind soup and savory adobo — unmistakable Filipino flavors.",
        "category": "filipino",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["comfort", "family_style"],
        "emotion_match": ["homesick", "lonely"],
        "cultural_tags": ["comfort", "family_style"],
    },
    {
        "title": "Pakistani Biryani House",
        "description": "Fragrant layered rice with tender meat and whole spices — celebration dish.",
        "category": "pakistani",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["halal", "spicy", "comfort", "family_style"],
        "emotion_match": ["homesick", "celebration"],
        "cultural_tags": ["halal", "spicy", "family_style"],
    },
    {
        "title": "South Indian Dosa & Sambar",
        "description": "Crispy dosa with coconut chutney and warm sambar — morning ritual.",
        "category": "indian_south",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["vegetarian", "comfort", "street_food"],
        "emotion_match": ["homesick"],
        "cultural_tags": ["vegetarian", "street_food"],
    },
    {
        "title": "North Indian Butter Chicken & Naan",
        "description": "Creamy tomato curry with fresh tandoori naan — rich and comforting.",
        "category": "indian_north",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "comfort", "family_style"],
        "emotion_match": ["homesick", "celebration"],
        "cultural_tags": ["halal", "comfort"],
    },
    {
        "title": "Thai Street Food Night",
        "description": "Pad Thai, som tum, mango sticky rice — Bangkok night market vibes.",
        "category": "thai",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["spicy", "street_food", "comfort"],
        "emotion_match": ["homesick", "celebration"],
        "cultural_tags": ["spicy", "street_food"],
    },
    {
        "title": "Vietnamese Pho & Banh Mi",
        "description": "Aromatic beef pho and crusty banh mi — Saigon in a bowl.",
        "category": "vietnamese",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["comfort", "street_food"],
        "emotion_match": ["homesick", "lonely"],
        "cultural_tags": ["comfort", "street_food"],
    },
    {
        "title": "Korean Kimchi Jjigae",
        "description": "Bubbling kimchi stew with tofu and pork — Korean winter comfort.",
        "category": "korean",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["spicy", "comfort", "family_style"],
        "emotion_match": ["homesick", "lonely"],
        "cultural_tags": ["spicy", "comfort"],
    },
    {
        "title": "Japanese Ramen & Izakaya",
        "description": "Rich tonkotsu ramen and small plates — late-night Tokyo nostalgia.",
        "category": "japanese",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["comfort", "street_food"],
        "emotion_match": ["homesick"],
        "cultural_tags": ["comfort", "street_food"],
    },
    {
        "title": "Indonesian Nasi Goreng & Satay",
        "description": "Fragrant fried rice and grilled satay with peanut sauce — island soul food.",
        "category": "indonesian",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "street_food", "comfort"],
        "emotion_match": ["homesick"],
        "cultural_tags": ["halal", "street_food"],
    },
    # ── Middle Eastern ──────────────────────────────────────────────────────
    {
        "title": "Lebanese Mezze Feast",
        "description": "Hummus, tabbouleh, fattoush, and grilled halloumi — shared and generous.",
        "category": "lebanese",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["halal", "vegetarian", "family_style", "comfort"],
        "emotion_match": ["homesick", "lonely", "celebration"],
        "cultural_tags": ["halal", "vegetarian", "family_style"],
    },
    {
        "title": "Egyptian Koshari & Ful",
        "description": "Layered rice, lentils, and pasta with spicy tomato sauce — Cairo street classic.",
        "category": "egyptian",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "vegetarian", "street_food", "comfort"],
        "emotion_match": ["homesick"],
        "cultural_tags": ["halal", "vegetarian", "street_food"],
    },
    {
        "title": "Jordanian Mansaf",
        "description": "Lamb in fermented yogurt sauce over rice — the national celebration dish.",
        "category": "jordanian",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["halal", "family_style", "comfort"],
        "emotion_match": ["homesick", "celebration"],
        "cultural_tags": ["halal", "family_style"],
    },
    {
        "title": "Iraqi Masgouf Fish",
        "description": "Whole grilled carp with tamarind — Tigris riverbank tradition.",
        "category": "iraqi",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "comfort", "traditional"],
        "emotion_match": ["homesick"],
        "cultural_tags": ["halal", "comfort"],
    },
    {
        "title": "Syrian Shawarma & Fatayer",
        "description": "Thinly sliced meat wraps and savory pastries — Damascus street food.",
        "category": "syrian",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "street_food", "comfort"],
        "emotion_match": ["homesick"],
        "cultural_tags": ["halal", "street_food"],
    },
    {
        "title": "Turkish Kebab & Pide",
        "description": "Charcoal-grilled kebabs with fresh pide bread — Anatolian hospitality.",
        "category": "turkish",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "comfort", "family_style"],
        "emotion_match": ["homesick", "celebration"],
        "cultural_tags": ["halal", "comfort", "family_style"],
    },
    {
        "title": "Moroccan Tagine & Couscous",
        "description": "Slow-cooked tagine with preserved lemons and fluffy couscous — Fez warmth.",
        "category": "moroccan",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "comfort", "family_style"],
        "emotion_match": ["homesick", "lonely"],
        "cultural_tags": ["halal", "comfort", "family_style"],
    },
    {
        "title": "Persian Kebab & Saffron Rice",
        "description": "Juicy koobideh with tahdig — crispy rice bottom is the prize.",
        "category": "persian",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["halal", "comfort", "family_style"],
        "emotion_match": ["homesick", "celebration"],
        "cultural_tags": ["halal", "comfort"],
    },
    # ── Latin American ──────────────────────────────────────────────────────
    {
        "title": "Mexican Tacos Al Pastor",
        "description": "Spit-roasted pork with pineapple on fresh tortillas — Mexico City nights.",
        "category": "mexican",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["spicy", "street_food", "comfort"],
        "emotion_match": ["homesick", "celebration"],
        "cultural_tags": ["spicy", "street_food"],
    },
    # ── European ────────────────────────────────────────────────────────────
    {
        "title": "Italian Nonna's Pasta",
        "description": "Fresh handmade pasta with slow-cooked ragu — Sunday family tradition.",
        "category": "italian",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["comfort", "family_style"],
        "emotion_match": ["homesick", "lonely"],
        "cultural_tags": ["comfort", "family_style"],
    },
    {
        "title": "French Bistro Classics",
        "description": "Coq au vin, croque monsieur, and tarte tatin — Parisian nostalgia.",
        "category": "french",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["comfort"],
        "emotion_match": ["homesick"],
        "cultural_tags": ["comfort"],
    },
    # ── African ─────────────────────────────────────────────────────────────
    {
        "title": "Ethiopian Injera & Wot",
        "description": "Spongy injera topped with spiced stews — eat with your hands, share with friends.",
        "category": "ethiopian",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["halal", "vegetarian", "family_style", "spicy", "comfort"],
        "emotion_match": ["homesick", "lonely", "celebration"],
        "cultural_tags": ["halal", "vegetarian", "family_style", "spicy"],
    },
]

# ── Emotion -> comfort mapping ───────────────────────────────────────────────

_EMOTION_TO_STYLE: dict[str, list[str]] = {
    "homesick": ["comfort", "family_style", "street_food"],
    "celebration": ["family_style", "spicy"],
    "lonely": ["family_style", "comfort"],
}

# ── Keywords ─────────────────────────────────────────────────────────────────

HOMETOWN_FOOD_KEYWORDS: set[str] = {
    "家乡", "hometown", "正宗", "authentic", "家的味道",
    "بلدي", "وطني",
}


def _detect_emotion_from_text(wish_text: str) -> list[str]:
    """Detect emotion hints from wish keywords."""
    text_lower = wish_text.lower()
    emotions: list[str] = []
    homesick_kw = {"想家", "homesick", "miss home", "想念", "怀念", "家乡", "hometown", "بلدي", "وطني"}
    celebration_kw = {"庆祝", "celebrate", "feast", "聚会", "احتفال"}
    lonely_kw = {"lonely", "孤独", "一个人", "وحيد"}
    if any(kw in text_lower for kw in homesick_kw):
        emotions.append("homesick")
    if any(kw in text_lower for kw in celebration_kw):
        emotions.append("celebration")
    if any(kw in text_lower for kw in lonely_kw):
        emotions.append("lonely")
    return emotions or ["homesick"]  # default to homesick for this fulfiller


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on emotion and cultural preference."""
    text_lower = wish_text.lower()
    emotions = _detect_emotion_from_text(wish_text)

    # Determine preferred style tags from emotions
    preferred_tags: set[str] = set()
    for emo in emotions:
        preferred_tags.update(_EMOTION_TO_STYLE.get(emo, []))

    # Cultural filtering
    want_halal = any(kw in text_lower for kw in ["halal", "حلال", "清真"])

    candidates: list[dict] = []
    for item in HOMETOWN_FOOD_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Emotion tag matching
        item_emotions = set(item.get("emotion_match", []))
        matched = set(emotions) & item_emotions
        if matched:
            score_boost += 0.2 * len(matched)
            item_copy["relevance_reason"] = _emotion_reason(list(matched)[0])

        # Preferred style matching
        item_tags = set(item.get("tags", []))
        if preferred_tags & item_tags:
            score_boost += 0.1

        # Halal filter
        if want_halal and "halal" not in item_tags:
            continue

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates or [dict(item) for item in HOMETOWN_FOOD_CATALOG]


def _emotion_reason(emotion: str) -> str:
    reasons = {
        "homesick": "A taste of home to warm your heart",
        "celebration": "A festive feast to share with loved ones",
        "lonely": "Family-style dishes meant to be shared",
    }
    return reasons.get(emotion, "Authentic flavors from your homeland")


class HometownFoodFulfiller(L2Fulfiller):
    """L2 fulfiller for hometown cuisine wishes — diaspora comfort food.

    25-entry curated catalog across 25 cuisine types. Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:max_results]

        from wish_engine.models import Recommendation
        return [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "Authentic flavors from your homeland"),
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
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "Authentic flavors from your homeland"

        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="restaurant", radius_km=10.0),
            reminder_option=ReminderOption(
                text="Visit this hometown restaurant this week?",
                delay_hours=24,
            ),
        )
