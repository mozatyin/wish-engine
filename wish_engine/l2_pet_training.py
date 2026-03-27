"""PetTrainingFulfiller — pet behavior and training recommendations.

10-type curated catalog of pet training services and resources. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Pet Training Catalog (10 entries) ─────────────────────────────────────────

PET_TRAINING_CATALOG: list[dict] = [
    {
        "title": "Dog Obedience Training",
        "description": "Basic commands — sit, stay, come, heel. Foundation for a well-behaved dog.",
        "category": "dog_obedience",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["dog_obedience", "dog", "practical", "calming"],
    },
    {
        "title": "Puppy Socialization Class",
        "description": "Introduce your puppy to other dogs and people — build confidence early.",
        "category": "puppy_socialization",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["puppy_socialization", "dog", "social", "calming"],
    },
    {
        "title": "Cat Behavior Consultation",
        "description": "Understand and address scratching, litter issues, and cat aggression.",
        "category": "cat_behavior",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cat_behavior", "cat", "practical", "calming", "quiet"],
    },
    {
        "title": "Pet Agility Course",
        "description": "Obstacle courses, jumps, and tunnels — active fun for dogs and owners.",
        "category": "pet_agility",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["pet_agility", "dog", "outdoor", "social", "active"],
    },
    {
        "title": "Therapy Pet Certification",
        "description": "Train your pet for therapy visits — hospitals, schools, and care homes.",
        "category": "therapy_pet_certification",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["therapy_pet_certification", "dog", "cat", "calming", "helping", "quiet"],
    },
    {
        "title": "Dog Walking Group",
        "description": "Organized group walks — socialization for dogs and their humans.",
        "category": "dog_walking_group",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["dog_walking_group", "dog", "outdoor", "social", "calming"],
    },
    {
        "title": "Pet First Aid Course",
        "description": "Learn CPR, wound care, and emergency response for your pet.",
        "category": "pet_first_aid",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["pet_first_aid", "practical", "calming", "quiet", "learning"],
    },
    {
        "title": "Pet Nutrition Guide",
        "description": "Personalized diet plans — raw, grain-free, or special needs nutrition.",
        "category": "pet_nutrition",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pet_nutrition", "practical", "calming", "quiet", "learning"],
    },
    {
        "title": "DIY Pet Grooming",
        "description": "Learn to groom at home — bathing, nail trimming, and coat care basics.",
        "category": "pet_grooming_diy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pet_grooming_diy", "practical", "calming", "quiet"],
    },
    {
        "title": "Separation Anxiety Training",
        "description": "Help your pet cope when you're away — gradual desensitization techniques.",
        "category": "separation_anxiety_training",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["separation_anxiety_training", "dog", "cat", "calming", "quiet", "practical"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_PET_TRAINING_KEYWORDS: dict[str, list[str]] = {
    "训练": [],
    "training": [],
    "训犬": ["dog"],
    "dog training": ["dog"],
    "تدريب": [],
    "pet behavior": [],
    "obedience": ["dog_obedience"],
    "服从": ["dog_obedience"],
    "puppy": ["puppy_socialization"],
    "小狗": ["puppy_socialization"],
    "cat": ["cat_behavior"],
    "猫": ["cat_behavior"],
    "agility": ["pet_agility"],
    "therapy": ["therapy_pet_certification"],
    "walk": ["dog_walking_group"],
    "遛狗": ["dog_walking_group"],
    "first aid": ["pet_first_aid"],
    "急救": ["pet_first_aid"],
    "nutrition": ["pet_nutrition"],
    "diet": ["pet_nutrition"],
    "groom": ["pet_grooming_diy"],
    "美容": ["pet_grooming_diy"],
    "separation": ["separation_anxiety_training"],
    "分离焦虑": ["separation_anxiety_training"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _PET_TRAINING_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "dog_obedience": "A well-trained dog is a happy dog",
        "puppy_socialization": "Early socialization builds a confident pup",
        "cat_behavior": "Understand your cat — solve problems with compassion",
        "pet_agility": "Active fun that strengthens the bond with your dog",
        "therapy_pet_certification": "Your pet can bring joy to those who need it most",
        "dog_walking_group": "Exercise and socializing — for you and your dog",
        "pet_first_aid": "Be ready for any emergency your pet might face",
        "pet_nutrition": "The right diet for a longer, healthier life",
        "pet_grooming_diy": "Save money and bond through grooming at home",
        "separation_anxiety_training": "Help your pet feel safe even when you're away",
    }
    return reason_map.get(category, "Better training for a happier pet and owner")


class PetTrainingFulfiller(L2Fulfiller):
    """L2 fulfiller for pet training wishes.

    Uses keyword matching to select from 10-type catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        matched_categories = _match_categories(wish.wish_text)

        if matched_categories:
            tag_set = set(matched_categories)
            candidates = [
                dict(item) for item in PET_TRAINING_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in PET_TRAINING_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in PET_TRAINING_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More pet training resources — check back soon!",
                delay_hours=48,
            ),
        )
