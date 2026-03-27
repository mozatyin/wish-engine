"""PregnancyFulfiller — local-compute pregnancy and maternity recommendation.

12-entry curated catalog of pregnancy-friendly resources and activities. Zero LLM.
Gentle/calming only. Keyword matching (English/Chinese/Arabic) routes wish
text to relevant categories, then PersonalityFilter scores and ranks candidates.

Tags: prenatal/baby/health/social/calming.
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

# ── Pregnancy Catalog (12 entries) ────────────────────────────────────────────

PREGNANCY_CATALOG: list[dict] = [
    {
        "title": "Prenatal Yoga Class",
        "description": "Gentle yoga designed for expecting mothers — safe poses and breathing.",
        "category": "prenatal_yoga",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["prenatal", "exercise", "quiet", "calming", "structured"],
    },
    {
        "title": "Baby-Friendly Cafe",
        "description": "Cafes with nursing rooms, changing stations, and welcoming staff.",
        "category": "baby_friendly_cafe",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["baby", "cafe", "quiet", "calming", "social"],
    },
    {
        "title": "Maternity Store",
        "description": "Comfortable maternity wear and essentials — clothes that grow with you.",
        "category": "maternity_store",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["prenatal", "shopping", "quiet", "calming", "practical"],
    },
    {
        "title": "Prenatal Clinic",
        "description": "Trusted prenatal care with experienced OB-GYNs and midwives.",
        "category": "prenatal_clinic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["prenatal", "health", "quiet", "calming", "practical"],
    },
    {
        "title": "Birthing Class",
        "description": "Prepare for delivery with expert-led classes — breathing, positions, and plans.",
        "category": "birthing_class",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["prenatal", "health", "quiet", "calming", "structured"],
    },
    {
        "title": "Pregnancy Massage",
        "description": "Gentle massage designed for pregnant bodies — relief for aching backs.",
        "category": "pregnancy_massage",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["prenatal", "quiet", "calming", "self-paced", "relaxation"],
    },
    {
        "title": "Baby Shower Venue",
        "description": "Beautiful, comfortable venues perfect for celebrating the arrival.",
        "category": "baby_shower_venue",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["baby", "social", "calming", "celebration", "indoor"],
    },
    {
        "title": "Nursery Shopping",
        "description": "Cribs, strollers, car seats, and everything for the nursery.",
        "category": "nursery_shopping",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["baby", "shopping", "quiet", "calming", "practical"],
    },
    {
        "title": "Lactation Consultant",
        "description": "Expert breastfeeding support — one-on-one guidance for new mothers.",
        "category": "lactation_consultant",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["baby", "health", "quiet", "calming", "practical"],
    },
    {
        "title": "Mommy Group",
        "description": "Connect with other expecting and new mothers — share, learn, and support.",
        "category": "mommy_group",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["prenatal", "social", "calming", "structured", "helping"],
    },
    {
        "title": "Pregnancy Exercise Class",
        "description": "Safe, low-impact exercise classes designed for each trimester.",
        "category": "pregnancy_exercise",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["prenatal", "exercise", "quiet", "calming", "structured"],
    },
    {
        "title": "Nutrition Counseling",
        "description": "Personalized dietary guidance for a healthy pregnancy journey.",
        "category": "nutrition_counseling",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["prenatal", "health", "quiet", "calming", "practical"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

PREGNANCY_KEYWORDS: set[str] = {
    "孕期", "pregnancy", "prenatal", "baby", "怀孕", "حمل",
    "expecting", "孕妇", "产前", "حامل", "maternity",
    "宝宝", "母婴", "رضيع", "newborn",
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "prenatal_yoga": ["yoga", "瑜伽", "يوغا"],
    "baby_friendly_cafe": ["cafe", "coffee", "咖啡", "قهوة"],
    "maternity_store": ["clothes", "store", "衣服", "ملابس", "maternity"],
    "prenatal_clinic": ["clinic", "doctor", "医生", "طبيب", "checkup"],
    "birthing_class": ["birth", "delivery", "分娩", "ولادة", "lamaze"],
    "pregnancy_massage": ["massage", "按摩", "تدليك", "spa"],
    "baby_shower_venue": ["shower", "party", "派对", "حفلة"],
    "nursery_shopping": ["nursery", "crib", "stroller", "婴儿房", "سرير"],
    "lactation_consultant": ["breastfeed", "lactation", "哺乳", "رضاعة"],
    "mommy_group": ["group", "mommy", "妈妈", "أمهات", "mother"],
    "pregnancy_exercise": ["exercise", "fitness", "运动", "رياضة"],
    "nutrition_counseling": ["nutrition", "diet", "营养", "تغذية"],
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    for item in PREGNANCY_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        # Health concern boost
        if any(kw in text_lower for kw in ["health", "健康", "صحة", "safe", "安全"]):
            if "health" in item.get("tags", []):
                score_boost += 0.1

        # Social connection boost
        if any(kw in text_lower for kw in ["group", "connect", "社交", "اجتماعي"]):
            if "social" in item.get("tags", []):
                score_boost += 0.1

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict) -> str:
    """Build a relevance reason for pregnancy recommendations."""
    reasons = {
        "prenatal_yoga": "Gentle movement designed for your body right now",
        "baby_friendly_cafe": "A welcoming space for you and baby",
        "maternity_store": "Comfortable wear that grows with you",
        "prenatal_clinic": "Trusted care for your pregnancy journey",
        "birthing_class": "Prepare confidently for delivery day",
        "pregnancy_massage": "Relief for your aching body — you deserve it",
        "baby_shower_venue": "Celebrate this special moment beautifully",
        "nursery_shopping": "Getting the nursery ready — exciting times",
        "lactation_consultant": "Expert breastfeeding support when you need it",
        "mommy_group": "Connect with others on the same journey",
        "pregnancy_exercise": "Safe, gentle exercise for your trimester",
        "nutrition_counseling": "Eat well for you and baby",
    }
    return reasons.get(item["category"], "A pregnancy-friendly resource nearby")


class PregnancyFulfiller(L2Fulfiller):
    """L2 fulfiller for pregnancy and maternity wishes.

    12-entry curated catalog. Gentle/calming only.
    Tags: prenatal/baby/health/social/calming. Zero LLM.
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

        return [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "A pregnancy-friendly resource nearby"),
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
            map_data=MapData(place_type="pregnancy_friendly", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Prenatal check-in — how are you feeling this week?",
                delay_hours=168,
            ),
        )
