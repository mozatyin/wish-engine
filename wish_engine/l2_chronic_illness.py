"""ChronicIllnessFulfiller — curated chronic illness management resources.

12-entry catalog of condition-specific support communities and management tools.
Personality-filtered, values-aware. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Catalog (12 entries) ─────────────────────────────────────────────────────

ILLNESS_CATALOG: list[dict] = [
    {
        "title": "Diabetes Management Community",
        "description": "Connect with others managing diabetes — glucose tracking tips, meal plans, and peer support.",
        "category": "diabetes_management",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["diabetes", "management", "community", "nutrition", "calming"],
    },
    {
        "title": "Asthma Support Network",
        "description": "Breathing exercises, trigger tracking, and peer advice for asthma management.",
        "category": "asthma_support",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["asthma", "breathing", "support", "community", "calming"],
    },
    {
        "title": "Autoimmune Community Hub",
        "description": "Shared experiences from people with lupus, MS, RA and other autoimmune conditions.",
        "category": "autoimmune_community",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["autoimmune", "community", "support", "chronic", "calming"],
    },
    {
        "title": "Chronic Fatigue Support",
        "description": "Energy pacing strategies, rest optimization, and understanding from people who get it.",
        "category": "chronic_fatigue",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["fatigue", "energy", "pacing", "rest", "calming", "gentle"],
    },
    {
        "title": "Thyroid Support Group",
        "description": "Hypo/hyperthyroid management — medication tips, lifestyle adjustments, lab result discussions.",
        "category": "thyroid_support",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["thyroid", "medication", "support", "community", "calming"],
    },
    {
        "title": "IBS Management Toolkit",
        "description": "Low-FODMAP guides, stress-gut connection tips, and food diary templates.",
        "category": "ibs_management",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ibs", "digestion", "nutrition", "management", "calming", "self-paced"],
    },
    {
        "title": "Arthritis-Friendly Exercise",
        "description": "Gentle movement programs designed for joint protection — water therapy, chair yoga, tai chi.",
        "category": "arthritis_exercise",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["arthritis", "exercise", "gentle", "movement", "calming"],
    },
    {
        "title": "Heart Health Program",
        "description": "Cardiac rehab resources, heart-healthy recipes, and monitoring guidance.",
        "category": "heart_health",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["heart", "cardiac", "nutrition", "monitoring", "calming"],
    },
    {
        "title": "Kidney Care Resources",
        "description": "Renal diet guidance, dialysis support communities, and transplant information.",
        "category": "kidney_care",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["kidney", "renal", "diet", "support", "calming"],
    },
    {
        "title": "Liver Health Guide",
        "description": "Liver-friendly nutrition, hepatitis support, and lifestyle modification resources.",
        "category": "liver_health",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["liver", "nutrition", "health", "management", "calming"],
    },
    {
        "title": "Epilepsy Support Circle",
        "description": "Seizure tracking tools, medication management, and community understanding.",
        "category": "epilepsy_support",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["epilepsy", "seizure", "medication", "support", "calming"],
    },
    {
        "title": "Cancer Survivorship Network",
        "description": "Post-treatment life, long-term side effects management, and thriving after cancer.",
        "category": "cancer_survivorship",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["cancer", "survivorship", "recovery", "community", "calming", "gentle"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_ILLNESS_KEYWORDS: dict[str, list[str]] = {
    "慢性病": [],
    "chronic": [],
    "diabetes": ["diabetes", "nutrition"],
    "糖尿病": ["diabetes", "nutrition"],
    "مرض مزمن": [],
    "long-term illness": [],
    "asthma": ["asthma", "breathing"],
    "哮喘": ["asthma", "breathing"],
    "autoimmune": ["autoimmune"],
    "自身免疫": ["autoimmune"],
    "fatigue": ["fatigue", "energy"],
    "疲劳": ["fatigue", "energy"],
    "thyroid": ["thyroid"],
    "甲状腺": ["thyroid"],
    "ibs": ["ibs", "digestion"],
    "肠胃": ["ibs", "digestion"],
    "arthritis": ["arthritis", "exercise"],
    "关节炎": ["arthritis", "exercise"],
    "heart": ["heart", "cardiac"],
    "心脏": ["heart", "cardiac"],
    "kidney": ["kidney", "renal"],
    "肾": ["kidney", "renal"],
    "liver": ["liver"],
    "肝": ["liver"],
    "epilepsy": ["epilepsy", "seizure"],
    "癫痫": ["epilepsy", "seizure"],
    "cancer": ["cancer", "survivorship"],
    "癌": ["cancer", "survivorship"],
}


def _match_illness_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _ILLNESS_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class ChronicIllnessFulfiller(L2Fulfiller):
    """L2 fulfiller for chronic illness management — condition-specific resources.

    12 curated entries covering common chronic conditions. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_illness_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in ILLNESS_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in ILLNESS_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in ILLNESS_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Managing a chronic condition is a marathon, not a sprint. Check in again when you need support.",
                delay_hours=48,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "community" in tags:
        return "You are not alone — connect with others who understand"
    if "gentle" in tags:
        return "Gentle approach designed for your comfort"
    if "nutrition" in tags:
        return "Nutrition guidance tailored to your condition"
    return "Curated resource for chronic condition management"
