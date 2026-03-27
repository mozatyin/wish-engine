"""MovingFulfiller — relocation service recommendations.

12-type curated catalog of moving and relocation services. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Moving Catalog (12 entries) ───────────────────────────────────────────────

MOVING_CATALOG: list[dict] = [
    {
        "title": "Moving Company",
        "description": "Licensed movers with packing, loading, and delivery — stress-free relocation.",
        "category": "moving_company",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["moving_company", "practical", "calming"],
    },
    {
        "title": "Packing Service",
        "description": "Professional packers — bubble wrap, boxes, and careful handling.",
        "category": "packing_service",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["packing_service", "practical", "calming", "quiet"],
    },
    {
        "title": "Storage Unit Rental",
        "description": "Secure storage for items you need to keep — short-term or long-term.",
        "category": "storage_unit",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["storage_unit", "practical", "calming", "quiet"],
    },
    {
        "title": "Cleaning Service",
        "description": "Deep cleaning for move-out or move-in — leave it spotless.",
        "category": "cleaning_service",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cleaning_service", "practical", "calming", "quiet"],
    },
    {
        "title": "Utility Setup Guide",
        "description": "Set up electricity, water, gas, and internet at your new address.",
        "category": "utility_setup",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["utility_setup", "practical", "calming", "quiet"],
    },
    {
        "title": "Address Change Checklist",
        "description": "Everything you need to update — bank, ID, subscriptions, and more.",
        "category": "address_change",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["address_change", "practical", "calming", "quiet"],
    },
    {
        "title": "Furniture Assembly Service",
        "description": "IKEA builds, bed frames, shelving — assembled and ready to use.",
        "category": "furniture_assembly",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["furniture_assembly", "practical", "calming"],
    },
    {
        "title": "Internet & WiFi Setup",
        "description": "Compare ISPs and get connected fast — router setup included.",
        "category": "internet_setup",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["internet_setup", "practical", "calming", "quiet"],
    },
    {
        "title": "Locksmith Service",
        "description": "Change locks, copy keys, or install smart locks at your new home.",
        "category": "locksmith",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["locksmith", "practical", "calming", "quiet"],
    },
    {
        "title": "Pest Control Inspection",
        "description": "Check your new place for pests — prevention is easier than treatment.",
        "category": "pest_control",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["pest_control", "practical", "calming", "quiet"],
    },
    {
        "title": "Home Insurance Quote",
        "description": "Compare home insurance plans — protect your new space from day one.",
        "category": "home_insurance",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["home_insurance", "practical", "calming", "quiet"],
    },
    {
        "title": "Neighborhood Guide",
        "description": "Discover your new neighborhood — shops, restaurants, parks, and services.",
        "category": "neighborhood_guide",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["neighborhood_guide", "practical", "calming", "quiet", "local"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_MOVING_KEYWORDS: dict[str, list[str]] = {
    "搬家": [],
    "moving": [],
    "relocate": [],
    "搬": [],
    "نقل": [],
    "new home": [],
    "新房": [],
    "relocation": [],
    "packing": ["packing_service"],
    "打包": ["packing_service"],
    "storage": ["storage_unit"],
    "仓储": ["storage_unit"],
    "cleaning": ["cleaning_service"],
    "打扫": ["cleaning_service"],
    "utility": ["utility_setup"],
    "水电": ["utility_setup"],
    "furniture": ["furniture_assembly"],
    "家具": ["furniture_assembly"],
    "internet": ["internet_setup"],
    "网络": ["internet_setup"],
    "lock": ["locksmith"],
    "换锁": ["locksmith"],
    "pest": ["pest_control"],
    "insurance": ["home_insurance"],
    "保险": ["home_insurance"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _MOVING_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "moving_company": "Take the heavy lifting off your plate",
        "packing_service": "Pack smart — let the pros handle it",
        "storage_unit": "Safe space for your stuff while you settle in",
        "cleaning_service": "Start fresh in a sparkling clean home",
        "utility_setup": "Get connected from day one",
        "address_change": "Don't miss a bill or a letter — update everything",
        "furniture_assembly": "Get your new space set up and livable fast",
        "internet_setup": "Stay connected — get WiFi running quickly",
        "locksmith": "New home, new locks — peace of mind from day one",
        "pest_control": "Make sure your new home is truly yours",
        "home_insurance": "Protect your new home from the start",
        "neighborhood_guide": "Get to know your new neighborhood like a local",
    }
    return reason_map.get(category, "Making your move smoother and easier")


class MovingFulfiller(L2Fulfiller):
    """L2 fulfiller for moving/relocation wishes.

    Uses keyword matching to select from 12-type catalog,
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
                dict(item) for item in MOVING_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in MOVING_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in MOVING_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More moving services available — check back anytime!",
                delay_hours=24,
            ),
        )
