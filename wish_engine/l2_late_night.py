"""LateNightFulfiller — local-compute late-night / 24-hour service finder.

15-entry curated catalog of late-night and 24-hour services. Zero LLM.
Keyword matching (English/Chinese/Arabic) routes wish text to relevant
categories, then PersonalityFilter scores and ranks candidates.

Time-aware: best suited for late hours (10pm-6am).
Tags: 24h/emergency/late-night/always-open.
"""

from __future__ import annotations

from datetime import datetime

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    ReminderOption,
)

# ── Late Night Catalog (15 entries) ──────────────────────────────────────────

LATE_NIGHT_CATALOG: list[dict] = [
    {
        "title": "24-Hour Pharmacy",
        "description": "Round-the-clock pharmacy for when you need medicine at any hour.",
        "category": "pharmacy_24h",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "emergency", "calming", "quiet", "practical"],
    },
    {
        "title": "24-Hour Convenience Store",
        "description": "Snacks, drinks, and essentials available all night long.",
        "category": "convenience_store_24h",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "always-open", "calming", "quiet", "practical"],
    },
    {
        "title": "Hospital Emergency Room",
        "description": "Emergency medical care available 24/7 — help is always ready.",
        "category": "hospital_emergency",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["24h", "emergency", "practical", "urgent"],
    },
    {
        "title": "Late Night Restaurant",
        "description": "Hot meals served late into the night — a warm place to refuel.",
        "category": "late_night_restaurant",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["late-night", "calming", "social", "warm"],
    },
    {
        "title": "24-Hour Cafe",
        "description": "Coffee and quiet vibes at any hour — a cozy late-night refuge.",
        "category": "24h_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "always-open", "calming", "quiet", "cafe"],
    },
    {
        "title": "24-Hour Gym",
        "description": "Work out on your own schedule — the gym never closes.",
        "category": "24h_gym",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "always-open", "practical", "exercise"],
    },
    {
        "title": "Late Night Laundry",
        "description": "Self-service laundromat open late — get your clothes clean anytime.",
        "category": "late_night_laundry",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["late-night", "always-open", "practical", "calming", "quiet"],
    },
    {
        "title": "24-Hour Gas Station",
        "description": "Fuel up at any hour — convenience store attached.",
        "category": "gas_station_24h",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "always-open", "practical", "quick"],
    },
    {
        "title": "24-Hour ATM",
        "description": "Cash withdrawal available around the clock.",
        "category": "atm_24h",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "always-open", "practical", "quick", "financial"],
    },
    {
        "title": "Late Night Supermarket",
        "description": "Groceries and household items available late into the evening.",
        "category": "late_night_supermarket",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["late-night", "always-open", "practical", "calming", "quiet"],
    },
    {
        "title": "24-Hour Fast Food",
        "description": "Quick bites available all night — drive-through or dine-in.",
        "category": "24h_fast_food",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "always-open", "quick", "practical"],
    },
    {
        "title": "Night Bus Stop",
        "description": "Late-night public transit to get you home safely.",
        "category": "night_bus_stop",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["late-night", "practical", "transit", "affordable"],
    },
    {
        "title": "Taxi Stand",
        "description": "Reliable taxi pickup points for safe late-night rides.",
        "category": "taxi_stand",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["late-night", "practical", "quick", "safe"],
    },
    {
        "title": "Hotel Lobby (24h)",
        "description": "A safe, warm, and staffed space open around the clock.",
        "category": "hotel_lobby_24h",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "always-open", "calming", "quiet", "safe"],
    },
    {
        "title": "24-Hour Print Shop",
        "description": "Urgent printing and copying at any hour of the night.",
        "category": "24h_print_shop",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "always-open", "practical", "urgent", "quick"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

LATE_NIGHT_KEYWORDS: set[str] = {
    "药店", "pharmacy", "24小时", "24h", "便利店", "convenience",
    "late night", "半夜", "صيدلية", "midnight", "all night",
    "open now", "还开着", "深夜", "凌晨", "夜宵",
    "24 hour", "around the clock", "night", "emergency",
    "مفتوح", "طوال الليل",
}


def is_late_night(hour: int | None = None) -> bool:
    """Check if current time is late night (10pm-6am)."""
    if hour is None:
        hour = datetime.now().hour
    return hour >= 22 or hour < 6


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
    current_hour: int | None = None,
) -> list[dict]:
    """Select catalog candidates based on keyword and time matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    late = is_late_night(current_hour)
    want_emergency = any(kw in text_lower for kw in ["emergency", "急诊", "طوارئ", "urgent", "紧急"])
    want_pharmacy = any(kw in text_lower for kw in ["pharmacy", "药店", "药", "صيدلية", "medicine"])
    want_food = any(kw in text_lower for kw in ["food", "eat", "吃", "夜宵", "hungry", "طعام"])

    for item in LATE_NIGHT_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0
        tags = set(item.get("tags", []))

        # Time-aware boosting
        if late and ("24h" in tags or "late-night" in tags):
            score_boost += 0.1

        # Specific need matching
        if want_emergency and "emergency" in tags:
            score_boost += 0.25
        if want_pharmacy and item["category"] == "pharmacy_24h":
            score_boost += 0.25
        if want_food and item["category"] in ("late_night_restaurant", "24h_fast_food", "convenience_store_24h"):
            score_boost += 0.2

        # Category keyword matching
        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item, late)
        candidates.append(item_copy)

    return candidates


_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "pharmacy_24h": ["pharmacy", "药店", "药", "صيدلية", "medicine"],
    "convenience_store_24h": ["convenience", "便利店", "بقالة", "snack"],
    "hospital_emergency": ["emergency", "hospital", "医院", "急诊", "مستشفى"],
    "late_night_restaurant": ["restaurant", "dinner", "supper", "夜宵", "晚餐"],
    "24h_cafe": ["cafe", "coffee", "咖啡", "قهوة"],
    "24h_gym": ["gym", "workout", "健身", "رياضة"],
    "late_night_laundry": ["laundry", "洗衣", "غسيل"],
    "gas_station_24h": ["gas", "fuel", "加油", "وقود"],
    "atm_24h": ["atm", "cash", "取钱", "صراف"],
    "late_night_supermarket": ["supermarket", "grocery", "超市", "بقالة"],
    "24h_fast_food": ["fast food", "快餐", "مطعم سريع"],
    "night_bus_stop": ["bus", "公交", "باص", "transit"],
    "taxi_stand": ["taxi", "cab", "打车", "سيارة أجرة"],
    "hotel_lobby_24h": ["hotel", "lobby", "酒店", "فندق"],
    "24h_print_shop": ["print", "打印", "طباعة", "copy"],
}


def _build_relevance(item: dict, is_late: bool) -> str:
    """Build a relevance reason."""
    time_prefix = "Open right now — " if is_late else ""
    reasons = {
        "pharmacy_24h": f"{time_prefix}Medicine and health supplies around the clock",
        "convenience_store_24h": f"{time_prefix}Essentials available anytime",
        "hospital_emergency": f"{time_prefix}Emergency medical help is ready",
        "late_night_restaurant": f"{time_prefix}Hot food when you need it",
        "24h_cafe": f"{time_prefix}A warm, quiet spot for a late coffee",
        "24h_gym": f"{time_prefix}Work out whenever inspiration strikes",
        "late_night_laundry": f"{time_prefix}Clean clothes on your schedule",
        "gas_station_24h": f"{time_prefix}Fuel up at any hour",
        "atm_24h": f"{time_prefix}Cash available when banks are closed",
        "late_night_supermarket": f"{time_prefix}Groceries when you need them",
        "24h_fast_food": f"{time_prefix}Quick bites day or night",
        "night_bus_stop": f"{time_prefix}Late-night transit to get you home",
        "taxi_stand": f"{time_prefix}A safe ride home anytime",
        "hotel_lobby_24h": f"{time_prefix}A safe, warm waiting space",
        "24h_print_shop": f"{time_prefix}Printing at any hour",
    }
    return reasons.get(item["category"], "Available late at night")


class LateNightFulfiller(L2Fulfiller):
    """L2 fulfiller for late-night / 24-hour service wishes.

    15-entry curated catalog. Time-aware (10pm-6am boost).
    Tags: 24h/emergency/late-night/always-open. Zero LLM.
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
                relevance_reason=c.get("relevance_reason", "Available late at night"),
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
            map_data=MapData(place_type="late_night_service", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Need this service now?",
                delay_hours=1,
            ),
        )
