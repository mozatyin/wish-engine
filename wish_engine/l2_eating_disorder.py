"""EatingDisorderFulfiller — highest-sensitivity eating disorder resources.

10-entry catalog of professional ED support resources.
HIGHEST SENSITIVITY — all language carefully chosen. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Catalog (10 entries) ─────────────────────────────────────────────────────

ED_CATALOG: list[dict] = [
    {
        "title": "Find an ED-Specialized Therapist",
        "description": "Connect with therapists who specialize in eating disorders — compassionate, evidence-based care.",
        "category": "ed_therapist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["therapist", "professional", "calming", "gentle"],
    },
    {
        "title": "Nutritional Counseling",
        "description": "Work with a registered dietitian who understands eating disorders — no judgment, just support.",
        "category": "nutritional_counseling",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nutrition", "professional", "calming", "gentle"],
    },
    {
        "title": "Body Image Therapy Resources",
        "description": "Evidence-based approaches to healing your relationship with your body.",
        "category": "body_image_therapy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["body_image", "therapy", "calming", "gentle", "self-paced"],
    },
    {
        "title": "ED Support Group",
        "description": "Safe, moderated spaces to share your experience with others who understand.",
        "category": "ed_support_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["support", "community", "calming", "gentle"],
    },
    {
        "title": "Meal Planning Support",
        "description": "Gentle, structured meal planning tools — designed with recovery in mind.",
        "category": "meal_planning_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meal_planning", "structure", "calming", "gentle", "self-paced"],
    },
    {
        "title": "Family ED Support",
        "description": "Resources for family members — how to support a loved one without causing harm.",
        "category": "family_ed_support",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["family", "education", "calming", "gentle"],
    },
    {
        "title": "Recovery Community",
        "description": "Stories of hope and recovery — connect with people at various stages of healing.",
        "category": "recovery_community",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["recovery", "community", "hope", "calming", "gentle"],
    },
    {
        "title": "Intuitive Eating Guide",
        "description": "Learn to trust your body again — gentle introduction to intuitive eating principles.",
        "category": "intuitive_eating",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["intuitive_eating", "education", "calming", "gentle", "self-paced"],
    },
    {
        "title": "ED Crisis Hotline",
        "description": "Immediate support when you need it most — trained counselors available 24/7.",
        "category": "ed_hotline",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["crisis", "hotline", "immediate", "calming", "professional", "gentle"],
    },
    {
        "title": "Relapse Prevention Toolkit",
        "description": "Strategies and warning signs to watch for — building resilience in recovery.",
        "category": "relapse_prevention",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["relapse", "prevention", "recovery", "calming", "self-paced", "gentle"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_ED_KEYWORDS: dict[str, list[str]] = {
    "饮食障碍": [],
    "eating disorder": [],
    "厌食": [],
    "anorexia": [],
    "暴食": [],
    "bulimia": [],
    "اضطراب الأكل": [],
    "binge": [],
    "purge": [],
    "body image": ["body_image"],
    "recovery": ["recovery", "hope"],
    "恢复": ["recovery", "hope"],
    "crisis": ["crisis", "immediate"],
    "危机": ["crisis", "immediate"],
    "hotline": ["crisis", "hotline"],
    "therapist": ["therapist", "professional"],
    "治疗师": ["therapist", "professional"],
    "family": ["family", "education"],
    "家人": ["family", "education"],
}


def _match_ed_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _ED_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class EatingDisorderFulfiller(L2Fulfiller):
    """L2 fulfiller for eating disorder support — HIGHEST SENSITIVITY.

    10 curated entries with carefully chosen language. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_ed_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in ED_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in ED_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in ED_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Recovery is not linear. You deserve support at every step.",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "crisis" in tags:
        return "Immediate support available right now"
    if "professional" in tags:
        return "Expert care from someone who specializes in eating disorders"
    if "community" in tags:
        return "You are not alone — others understand what you are going through"
    if "recovery" in tags:
        return "Recovery is possible — these resources can help"
    return "Gentle, compassionate support for your journey"
