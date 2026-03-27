"""PetFriendlyFulfiller — local-compute pet-friendly place recommendation.

15-entry curated catalog of pet-friendly locations. Zero LLM. Keyword matching
(English/Chinese/Arabic) routes wish text to relevant categories,
then PersonalityFilter scores and ranks candidates.

Tags: outdoor/indoor/training/social/quiet.
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

# ── Pet-Friendly Catalog (15 entries) ────────────────────────────────────────

PET_CATALOG: list[dict] = [
    {
        "title": "Dog Park",
        "description": "Open green space where your pup can run free and make furry friends.",
        "category": "dog_park",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["outdoor", "social", "dogs", "exercise", "free"],
    },
    {
        "title": "Pet Cafe",
        "description": "Cozy cafe that welcomes pets — enjoy a latte while your companion relaxes beside you.",
        "category": "pet_cafe",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["indoor", "social", "quiet", "calming", "cafe"],
    },
    {
        "title": "Veterinary Clinic",
        "description": "Trusted vets who care for your pet like family.",
        "category": "vet_clinic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "quiet", "practical", "calming", "medical"],
    },
    {
        "title": "Pet Supply Store",
        "description": "Everything your furry friend needs — food, toys, beds, and more.",
        "category": "pet_store",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "quiet", "practical", "shopping"],
    },
    {
        "title": "Pet Grooming Salon",
        "description": "Professional grooming to keep your pet looking and feeling their best.",
        "category": "pet_grooming",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "quiet", "practical", "grooming"],
    },
    {
        "title": "Pet-Friendly Restaurant",
        "description": "Dine out without leaving your best friend behind — patio seating for pets.",
        "category": "pet_friendly_restaurant",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["outdoor", "social", "dining", "calming"],
    },
    {
        "title": "Pet-Friendly Hotel",
        "description": "Comfortable stays where your pet is a welcome guest.",
        "category": "pet_friendly_hotel",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "quiet", "calming", "travel"],
    },
    {
        "title": "Dog Beach",
        "description": "Sandy shores where dogs can splash, dig, and play in the waves.",
        "category": "dog_beach",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["outdoor", "social", "dogs", "exercise", "beach"],
    },
    {
        "title": "Pet Daycare",
        "description": "Safe, fun daycare so your pet is happy while you are busy.",
        "category": "pet_daycare",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["indoor", "social", "training", "supervised"],
    },
    {
        "title": "Pet Training Center",
        "description": "Expert trainers to help your pet learn new tricks and good manners.",
        "category": "pet_training",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["indoor", "training", "practical", "structured"],
    },
    {
        "title": "Pet-Friendly Shopping Mall",
        "description": "Shop with your companion by your side — pet-welcome policy throughout.",
        "category": "pet_friendly_mall",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["indoor", "social", "shopping", "practical"],
    },
    {
        "title": "Pet Adoption Center",
        "description": "Give a loving home to a pet in need — meet your new best friend.",
        "category": "pet_adoption",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["indoor", "social", "quiet", "adoption", "meaningful"],
    },
    {
        "title": "Pet-Friendly Trail",
        "description": "Scenic walking and hiking trails where pets roam alongside you.",
        "category": "pet_friendly_trail",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["outdoor", "quiet", "exercise", "nature", "calming"],
    },
    {
        "title": "Pet Swimming Pool",
        "description": "A splash-friendly pool just for pets — supervised aquatic fun.",
        "category": "pet_swimming",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["outdoor", "social", "exercise", "water", "fun"],
    },
    {
        "title": "Pet Photography Studio",
        "description": "Capture precious moments with your pet in a professional studio.",
        "category": "pet_photography",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "quiet", "creative", "calming", "memorable"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

PET_KEYWORDS: set[str] = {
    "宠物", "pet", "dog", "cat", "狗", "猫", "حيوان أليف",
    "puppy", "kitten", "vet", "兽医", "grooming", "adoption",
    "遛狗", "walk dog", "pet cafe", "dog park",
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    for item in PET_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Keyword matching for specific categories
        category = item["category"]
        if category in text_lower or any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        # Outdoor preference detection
        if any(kw in text_lower for kw in ["outdoor", "outside", "户外", "park", "trail", "beach"]):
            if "outdoor" in item.get("tags", []):
                score_boost += 0.1

        # Indoor preference detection
        if any(kw in text_lower for kw in ["indoor", "inside", "室内", "cafe", "shop"]):
            if "indoor" in item.get("tags", []):
                score_boost += 0.1

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "dog_park": ["dog park", "狗公园", "遛狗", "حديقة كلاب"],
    "pet_cafe": ["pet cafe", "宠物咖啡", "مقهى حيوانات"],
    "vet_clinic": ["vet", "兽医", "بيطري", "veterinary"],
    "pet_store": ["pet store", "宠物店", "محل حيوانات"],
    "pet_grooming": ["grooming", "美容", "تجميل"],
    "pet_friendly_restaurant": ["pet restaurant", "宠物餐厅"],
    "pet_friendly_hotel": ["pet hotel", "宠物酒店"],
    "dog_beach": ["dog beach", "狗海滩"],
    "pet_daycare": ["daycare", "托管", "رعاية"],
    "pet_training": ["training", "训练", "تدريب"],
    "pet_friendly_mall": ["pet mall", "宠物商场"],
    "pet_adoption": ["adoption", "领养", "تبني"],
    "pet_friendly_trail": ["trail", "hiking", "步道", "ممشى"],
    "pet_swimming": ["swimming", "游泳", "سباحة"],
    "pet_photography": ["photo", "拍照", "تصوير"],
}


def _build_relevance(item: dict) -> str:
    """Build a relevance reason for pet-friendly recommendations."""
    reasons = {
        "dog_park": "A great space for your dog to play and socialize",
        "pet_cafe": "Relax with your pet in a cozy cafe",
        "vet_clinic": "Trusted care for your pet's health",
        "pet_store": "All the essentials for your furry friend",
        "pet_grooming": "Keep your pet looking their best",
        "pet_friendly_restaurant": "Dine out with your pet by your side",
        "pet_friendly_hotel": "Travel comfortably with your companion",
        "dog_beach": "Sandy fun for you and your dog",
        "pet_daycare": "Safe and fun care while you are away",
        "pet_training": "Help your pet learn and grow",
        "pet_friendly_mall": "Shop together with your pet",
        "pet_adoption": "Meet a new companion waiting for a home",
        "pet_friendly_trail": "Explore nature with your pet",
        "pet_swimming": "Splash time for your water-loving pet",
        "pet_photography": "Capture special moments with your pet",
    }
    return reasons.get(item["category"], "A pet-friendly place nearby")


class PetFriendlyFulfiller(L2Fulfiller):
    """L2 fulfiller for pet-friendly place wishes.

    15-entry curated catalog. Tags: outdoor/indoor/training/social/quiet.
    Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
        from wish_engine.models import Recommendation

        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

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
                relevance_reason=c.get("relevance_reason", "A pet-friendly place nearby"),
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
        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="pet_friendly", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Visit this pet-friendly spot today?",
                delay_hours=4,
            ),
        )
