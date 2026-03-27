"""EVChargingFulfiller — local-compute EV charging and gas station finder.

10-entry curated catalog of charging/fueling stations. Zero LLM. Keyword
matching (English/Chinese/Arabic) routes wish text to relevant categories,
then PersonalityFilter scores and ranks candidates.

Tags: fast/slow/convenient/cafe/parking.
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

# ── EV Charging / Gas Catalog (10 entries) ───────────────────────────────────

EV_CATALOG: list[dict] = [
    {
        "title": "DC Fast Charger",
        "description": "High-speed charging — get 80% in under 30 minutes and back on the road.",
        "category": "fast_charger",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["fast", "ev", "practical", "quick"],
    },
    {
        "title": "Level 2 Slow Charger",
        "description": "Steady overnight or daytime charging at a convenient location.",
        "category": "slow_charger",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["slow", "ev", "practical", "convenient", "calming"],
    },
    {
        "title": "Tesla Supercharger",
        "description": "Tesla-exclusive high-speed charging network with reliable availability.",
        "category": "tesla_supercharger",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["fast", "ev", "tesla", "practical", "quick"],
    },
    {
        "title": "Gas Station",
        "description": "Fuel up quickly at a nearby gas station — convenience store included.",
        "category": "gas_station",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["fast", "gas", "practical", "convenient", "quick"],
    },
    {
        "title": "Hydrogen Station",
        "description": "Hydrogen fuel cell refueling — the future of clean energy, available now.",
        "category": "hydrogen_station",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["fast", "hydrogen", "practical", "clean"],
    },
    {
        "title": "Charging Cafe",
        "description": "Charge your car while you enjoy a coffee — the perfect pit stop.",
        "category": "charging_cafe",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["slow", "ev", "cafe", "calming", "convenient", "social"],
    },
    {
        "title": "Charging at Mall",
        "description": "Shop while your EV charges — make the most of your wait time.",
        "category": "charging_mall",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["slow", "ev", "convenient", "shopping", "practical"],
    },
    {
        "title": "Charging Parking Lot",
        "description": "Park and charge simultaneously — covered spots available.",
        "category": "charging_parking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["slow", "ev", "parking", "convenient", "practical"],
    },
    {
        "title": "Roadside Charging Station",
        "description": "Convenient highway charging for long-distance EV trips.",
        "category": "roadside_charging",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["fast", "ev", "practical", "highway", "quick"],
    },
    {
        "title": "Home Charging Installer",
        "description": "Professional home charger installation — charge conveniently at home every night.",
        "category": "home_charging_installer",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["slow", "ev", "convenient", "home", "practical"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

EV_KEYWORDS: set[str] = {
    "充电", "charging", "加油", "gas", "电动", "EV", "شحن",
    "ev", "electric vehicle", "charge", "charger", "tesla",
    "supercharger", "hydrogen", "fuel", "gas station", "加油站",
    "充电桩", "محطة وقود", "محطة شحن",
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    # Detect EV vs gas preference
    is_ev = any(kw in text_lower for kw in ["ev", "electric", "电动", "充电", "charging", "charge", "شحن", "tesla"])
    is_gas = any(kw in text_lower for kw in ["gas", "加油", "fuel", "وقود", "gasoline", "petrol"])
    want_fast = any(kw in text_lower for kw in ["fast", "quick", "快", "سريع", "urgent"])
    want_cafe = any(kw in text_lower for kw in ["cafe", "coffee", "咖啡", "قهوة"])

    for item in EV_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0
        tags = set(item.get("tags", []))

        # Filter by fuel type preference
        if is_ev and "gas" in tags and "ev" not in tags:
            score_boost -= 0.2
        if is_gas and "ev" in tags and "gas" not in tags:
            score_boost -= 0.2

        # Boost matching preferences
        if want_fast and "fast" in tags:
            score_boost += 0.15
        if want_cafe and "cafe" in tags:
            score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item, is_ev, is_gas)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict, is_ev: bool, is_gas: bool) -> str:
    """Build a relevance reason."""
    reasons = {
        "fast_charger": "Quick charge to get you back on the road",
        "slow_charger": "Steady charging at a convenient spot",
        "tesla_supercharger": "Tesla high-speed charging nearby",
        "gas_station": "Fuel up quickly at a nearby station",
        "hydrogen_station": "Clean hydrogen refueling available",
        "charging_cafe": "Charge your car while enjoying a coffee",
        "charging_mall": "Shop while your EV charges",
        "charging_parking": "Park and charge at the same time",
        "roadside_charging": "Highway charging for your road trip",
        "home_charging_installer": "Get a home charger installed",
    }
    return reasons.get(item["category"], "Charging or fueling nearby")


class EVChargingFulfiller(L2Fulfiller):
    """L2 fulfiller for EV charging and gas station wishes.

    10-entry curated catalog. Tags: fast/slow/convenient/cafe/parking.
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
                relevance_reason=c.get("relevance_reason", "Charging or fueling nearby"),
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
            map_data=MapData(place_type="ev_charging", radius_km=10.0),
            reminder_option=ReminderOption(
                text="Head to this charging station now?",
                delay_hours=1,
            ),
        )
