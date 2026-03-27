"""CaregiverRespiteFulfiller — respite care services for exhausted caregivers.

12-entry curated catalog with gentle, supportive options. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Respite Care Catalog (12 entries) ────────────────────────────────────────

RESPITE_CATALOG: list[dict] = [
    {
        "title": "Respite Care Home",
        "description": "Short-term residential care so you can take a break — trained staff on-site 24/7.",
        "category": "respite_care_home",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["respite_care_home", "residential", "calming", "professional", "overnight"],
    },
    {
        "title": "Temporary Nurse Service",
        "description": "Licensed nurse visits your home for a few hours while you rest or run errands.",
        "category": "temporary_nurse",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["temporary_nurse", "home", "professional", "calming", "medical"],
    },
    {
        "title": "Adult Day Care Center",
        "description": "Supervised daytime activities, meals, and social engagement for your loved one.",
        "category": "adult_daycare",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["adult_daycare", "daytime", "social", "calming", "structured"],
    },
    {
        "title": "Volunteer Companion Program",
        "description": "Trained volunteers spend time with your loved one — reading, chatting, companionship.",
        "category": "volunteer_companion",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["volunteer_companion", "social", "calming", "gentle", "community"],
    },
    {
        "title": "Meal Delivery for Care Families",
        "description": "Nutritious prepared meals delivered to your door — one less thing to worry about.",
        "category": "meal_delivery",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meal_delivery", "practical", "calming", "home", "nutrition"],
    },
    {
        "title": "Home Help Service",
        "description": "Housekeeping, laundry, and errands handled so you can focus on what matters.",
        "category": "home_help",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["home_help", "practical", "calming", "home", "daily"],
    },
    {
        "title": "Night Care Service",
        "description": "Overnight caregiver stays so you can finally get a full night of sleep.",
        "category": "night_care",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["night_care", "overnight", "calming", "professional", "home"],
    },
    {
        "title": "Weekend Respite Program",
        "description": "Weekend care programs — drop off Saturday morning, pick up Sunday evening.",
        "category": "weekend_respite",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["weekend_respite", "weekend", "calming", "structured", "residential"],
    },
    {
        "title": "Emergency Respite Care",
        "description": "Same-day respite when you hit a wall — because emergencies don't wait.",
        "category": "emergency_respite",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["emergency_respite", "urgent", "calming", "professional", "immediate"],
    },
    {
        "title": "Sibling Relief Coordination",
        "description": "Tools and templates to share caregiving duties fairly among family members.",
        "category": "sibling_relief",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["sibling_relief", "family", "calming", "practical", "coordination"],
    },
    {
        "title": "Online Caregiver Break Activities",
        "description": "Guided meditation, gentle yoga, and creative sessions — designed for 15-minute breaks.",
        "category": "online_caregiver_break",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["online_caregiver_break", "digital", "calming", "self-paced", "gentle"],
    },
    {
        "title": "Caregiver Respite Retreat",
        "description": "Multi-day retreat designed for caregivers — rest, recharge, reconnect with yourself.",
        "category": "respite_retreat",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["respite_retreat", "residential", "calming", "gentle", "restorative"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_RESPITE_KEYWORDS: dict[str, list[str]] = {
    "照护": [],
    "caregiver": [],
    "respite": [],
    "看护": [],
    "رعاية": [],
    "relief": [],
    "喘息": [],
    "break": ["online_caregiver_break", "respite_retreat"],
    "nurse": ["temporary_nurse"],
    "night": ["night_care"],
    "daycare": ["adult_daycare"],
    "meal": ["meal_delivery"],
    "volunteer": ["volunteer_companion"],
    "sibling": ["sibling_relief"],
    "emergency": ["emergency_respite"],
    "weekend": ["weekend_respite"],
    "retreat": ["respite_retreat"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _RESPITE_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "respite_care_home": "A safe place for your loved one while you recharge",
        "temporary_nurse": "Professional care at home so you can step away",
        "adult_daycare": "Daytime engagement and socialization for your loved one",
        "volunteer_companion": "Warm companionship from a trained volunteer",
        "meal_delivery": "One less thing on your plate — literally",
        "home_help": "Practical support so you can breathe",
        "night_care": "Finally, a full night of sleep",
        "weekend_respite": "A whole weekend to rest and recover",
        "emergency_respite": "Immediate help when you need it most",
        "sibling_relief": "Fair caregiving starts with good coordination",
        "online_caregiver_break": "A quick break you can take right now",
        "respite_retreat": "You deserve rest too — take time to recharge",
    }
    return reason_map.get(category, "Support for caregivers who give so much")


class CaregiverRespiteFulfiller(L2Fulfiller):
    """L2 fulfiller for caregiver respite — gentle, supportive recommendations.

    Uses keyword matching to select from 12-entry catalog. All entries are
    calming and caregiver-focused. Applies PersonalityFilter. Zero LLM.
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
                dict(item) for item in RESPITE_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in RESPITE_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in RESPITE_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="You deserve a break — check back for more respite options!",
                delay_hours=24,
            ),
        )
