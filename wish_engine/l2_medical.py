"""MedicalFulfiller — local-compute medical resource navigation.

15-entry curated catalog of medical services. Zero LLM. Keyword matching
(English/Chinese/Arabic) routes wish text to relevant medical categories,
then PersonalityFilter scores and ranks candidates.

Sensitivity: always uses gentle/calming language.
Cultural: traditional_medicine for tradition values, modern for achievement.
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

# ── Medical Catalog (15 entries) ─────────────────────────────────────────────

MEDICAL_CATALOG: list[dict] = [
    {
        "title": "General Clinic",
        "description": "A welcoming neighborhood clinic for everyday health needs — you are in good hands.",
        "category": "general_clinic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["general", "calming", "quiet", "practical", "accessible"],
    },
    {
        "title": "Dental Care",
        "description": "Gentle dental professionals who prioritize your comfort and well-being.",
        "category": "dental",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["dental", "calming", "quiet", "practical"],
    },
    {
        "title": "Eye Doctor",
        "description": "Comprehensive vision care in a calm, reassuring environment.",
        "category": "eye_doctor",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["eye", "calming", "quiet", "practical"],
    },
    {
        "title": "Dermatology Clinic",
        "description": "Skin care specialists — gentle treatments for all skin types and concerns.",
        "category": "dermatology",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["skin", "calming", "quiet", "practical"],
    },
    {
        "title": "Mental Health Center",
        "description": "A safe, compassionate space for your mental well-being — it is okay to ask for help.",
        "category": "mental_health",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["mental", "calming", "quiet", "safe", "supportive"],
    },
    {
        "title": "Physiotherapy & Rehab",
        "description": "Expert movement therapy to help your body heal at its own pace.",
        "category": "physiotherapy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["physio", "calming", "quiet", "practical", "recovery"],
    },
    {
        "title": "Pediatric Clinic",
        "description": "Child-friendly doctors who make little ones feel safe and cared for.",
        "category": "pediatric",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pediatric", "calming", "quiet", "family", "children"],
    },
    {
        "title": "Women's Health Center",
        "description": "Compassionate care dedicated to women's health — a warm, understanding space.",
        "category": "womens_health",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["women", "calming", "quiet", "safe", "supportive"],
    },
    {
        "title": "Emergency Room",
        "description": "24-hour emergency medical care — help is always available when you need it most.",
        "category": "emergency_room",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["emergency", "24h", "urgent", "practical"],
    },
    {
        "title": "24-Hour Pharmacy",
        "description": "A welcoming round-the-clock pharmacy — your medicine is always within safe reach.",
        "category": "pharmacy_24h",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pharmacy", "24h", "calming", "quiet", "practical"],
    },
    {
        "title": "Traditional Medicine Center",
        "description": "Time-honored healing practices rooted in centuries of wisdom and care.",
        "category": "traditional_medicine",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["traditional", "calming", "quiet", "holistic", "cultural"],
    },
    {
        "title": "Sports Medicine Clinic",
        "description": "Caring specialists for active bodies — gentle support to help you heal and return to what you love.",
        "category": "sports_medicine",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sports", "calming", "practical", "recovery", "active"],
    },
    {
        "title": "Allergy Clinic",
        "description": "Expert allergy testing and treatment in a gentle, reassuring setting.",
        "category": "allergy_clinic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["allergy", "calming", "quiet", "practical"],
    },
    {
        "title": "Nutrition Counseling",
        "description": "Personalized guidance to nourish your body and feel your best.",
        "category": "nutrition_counseling",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nutrition", "calming", "quiet", "practical", "holistic"],
    },
    {
        "title": "Sleep Clinic",
        "description": "Restful solutions for better sleep — because you deserve peaceful nights.",
        "category": "sleep_clinic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sleep", "calming", "quiet", "practical", "recovery"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

MEDICAL_KEYWORDS: set[str] = {
    "医院", "doctor", "clinic", "医生", "看病", "طبيب", "مستشفى",
    "pharmacy", "药", "hospital", "dental", "dentist", "牙医",
    "eye doctor", "眼科", "skin", "皮肤", "mental health", "心理",
    "physiotherapy", "儿科", "pediatric", "emergency", "急诊",
    "药店", "traditional medicine", "中医", "sports medicine",
    "allergy", "过敏", "nutrition", "营养", "sleep clinic", "睡眠",
    "صيدلية", "عيادة",
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword and cultural matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    # Cultural preference from values
    top_values = detector_results.values.get("top_values", [])
    prefer_traditional = "tradition" in top_values
    prefer_modern = "achievement" in top_values

    for item in MEDICAL_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0
        tags = set(item.get("tags", []))

        # Keyword matching
        category = item["category"]
        if category in text_lower or any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        # Cultural matching
        if prefer_traditional and "traditional" in tags:
            score_boost += 0.15
        if prefer_modern and "traditional" not in tags:
            score_boost += 0.05

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "general_clinic": ["doctor", "医生", "看病", "طبيب", "clinic", "عيادة"],
    "dental": ["dental", "dentist", "牙医", "أسنان"],
    "eye_doctor": ["eye", "眼科", "عيون", "vision"],
    "dermatology": ["skin", "皮肤", "جلد", "derma"],
    "mental_health": ["mental", "心理", "نفسي", "therapy", "counseling"],
    "physiotherapy": ["physio", "rehab", "康复", "علاج طبيعي"],
    "pediatric": ["pediatric", "child", "儿科", "أطفال"],
    "womens_health": ["women", "gynec", "妇科", "نساء"],
    "emergency_room": ["emergency", "急诊", "طوارئ", "urgent"],
    "pharmacy_24h": ["pharmacy", "药店", "药", "صيدلية"],
    "traditional_medicine": ["traditional", "中医", "طب تقليدي", "herbal", "acupuncture"],
    "sports_medicine": ["sports", "运动", "رياضة", "athletic"],
    "allergy_clinic": ["allergy", "过敏", "حساسية"],
    "nutrition_counseling": ["nutrition", "营养", "تغذية", "diet"],
    "sleep_clinic": ["sleep", "睡眠", "نوم", "insomnia"],
}


def _build_relevance(item: dict) -> str:
    """Build a gentle, calming relevance reason."""
    reasons = {
        "general_clinic": "A caring clinic nearby for your health needs",
        "dental": "Gentle dental care to keep your smile healthy",
        "eye_doctor": "Professional vision care in a calm setting",
        "dermatology": "Expert skin care with your comfort in mind",
        "mental_health": "A safe space for your mental well-being",
        "physiotherapy": "Supportive therapy to help your body heal",
        "pediatric": "Child-friendly care for your little one",
        "womens_health": "Compassionate care dedicated to women's health",
        "emergency_room": "Immediate help is available when you need it",
        "pharmacy_24h": "Your medication is within reach, day or night",
        "traditional_medicine": "Time-honored healing wisdom",
        "sports_medicine": "Get back to the activities you love",
        "allergy_clinic": "Relief and care for your allergy concerns",
        "nutrition_counseling": "Guidance to nourish your body well",
        "sleep_clinic": "Better rest starts with expert support",
    }
    return reasons.get(item["category"], "Caring medical support nearby")


class MedicalFulfiller(L2Fulfiller):
    """L2 fulfiller for medical resource wishes.

    15-entry curated catalog. Gentle language. Cultural awareness.
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
                relevance_reason=c.get("relevance_reason", "Caring medical support nearby"),
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
            map_data=MapData(place_type="hospital", radius_km=10.0),
            reminder_option=ReminderOption(
                text="Would you like to schedule a visit?",
                delay_hours=2,
            ),
        )
