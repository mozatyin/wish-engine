"""ParkingFulfiller — local-compute parking spot finder.

10-entry curated catalog of parking options. Zero LLM. Keyword matching
(English/Chinese/Arabic) routes wish text to relevant categories,
then PersonalityFilter scores and ranks candidates.

Tags: free/covered/24h/ev/accessible.
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

# ── Parking Catalog (10 entries) ─────────────────────────────────────────────

PARKING_CATALOG: list[dict] = [
    {
        "title": "Street Parking",
        "description": "Convenient on-street parking spots — check meters and time limits.",
        "category": "street_parking",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["free", "convenient", "practical", "quick"],
    },
    {
        "title": "Parking Garage",
        "description": "Multi-level covered parking — protected from weather with security cameras.",
        "category": "parking_garage",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["covered", "24h", "practical", "secure", "calming"],
    },
    {
        "title": "Valet Parking",
        "description": "Drop off your car and let the valet handle the rest — effortless.",
        "category": "valet_parking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["convenient", "practical", "premium", "quick"],
    },
    {
        "title": "Free Parking Lot",
        "description": "No-cost parking available — save money while you are out.",
        "category": "free_parking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["free", "practical", "affordable", "calming"],
    },
    {
        "title": "EV Charging Parking",
        "description": "Parking spots with built-in EV chargers — park and charge together.",
        "category": "ev_charging_parking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["ev", "practical", "convenient", "calming"],
    },
    {
        "title": "Airport Parking",
        "description": "Long-term parking near the airport with shuttle service.",
        "category": "airport_parking",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "practical", "covered", "travel"],
    },
    {
        "title": "Monthly Parking",
        "description": "Reserved monthly spot — guaranteed parking every day.",
        "category": "monthly_parking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["covered", "practical", "affordable", "secure"],
    },
    {
        "title": "Accessible Parking",
        "description": "Designated accessible parking spots close to entrances.",
        "category": "handicap_parking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["accessible", "practical", "convenient", "calming"],
    },
    {
        "title": "Motorcycle Parking",
        "description": "Dedicated spots for motorcycles and scooters.",
        "category": "motorcycle_parking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "affordable", "quick", "compact"],
    },
    {
        "title": "Bicycle Parking",
        "description": "Secure bike racks and lockers for your bicycle.",
        "category": "bicycle_parking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["free", "practical", "eco", "quick"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

PARKING_KEYWORDS: set[str] = {
    "停车", "parking", "park my car", "泊车", "موقف",
    "garage", "valet", "free parking", "月租", "monthly",
    "机场停车", "airport parking", "自行车", "bicycle",
    "motorcycle", "摩托", "accessible", "无障碍",
    "موقف سيارات", "停车场", "车位",
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    want_free = any(kw in text_lower for kw in ["free", "免费", "مجاني", "no cost"])
    want_covered = any(kw in text_lower for kw in ["covered", "indoor", "室内", "garage", "مغطى"])
    want_ev = any(kw in text_lower for kw in ["ev", "electric", "电动", "charging", "充电", "شحن"])
    want_accessible = any(kw in text_lower for kw in ["accessible", "handicap", "disability", "无障碍", "ذوي الاحتياجات"])

    for item in PARKING_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0
        tags = set(item.get("tags", []))

        # Preference matching
        if want_free and "free" in tags:
            score_boost += 0.2
        if want_covered and "covered" in tags:
            score_boost += 0.15
        if want_ev and "ev" in tags:
            score_boost += 0.2
        if want_accessible and "accessible" in tags:
            score_boost += 0.25

        # Category keyword matching
        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "street_parking": ["street", "路边", "شارع"],
    "parking_garage": ["garage", "停车场", "مرآب"],
    "valet_parking": ["valet", "代客", "خدمة صف"],
    "free_parking": ["free", "免费", "مجاني"],
    "ev_charging_parking": ["ev", "charging", "充电", "شحن", "electric"],
    "airport_parking": ["airport", "机场", "مطار"],
    "monthly_parking": ["monthly", "月租", "شهري"],
    "handicap_parking": ["accessible", "handicap", "disability", "无障碍", "ذوي"],
    "motorcycle_parking": ["motorcycle", "摩托", "scooter", "دراجة نارية"],
    "bicycle_parking": ["bicycle", "bike", "自行车", "دراجة"],
}


def _build_relevance(item: dict) -> str:
    """Build a relevance reason."""
    reasons = {
        "street_parking": "Convenient street-side parking nearby",
        "parking_garage": "Covered garage parking with security",
        "valet_parking": "Effortless valet service available",
        "free_parking": "Free parking to save your wallet",
        "ev_charging_parking": "Park and charge your EV at once",
        "airport_parking": "Long-term airport parking with shuttle",
        "monthly_parking": "Reserved monthly spot for daily convenience",
        "handicap_parking": "Accessible parking close to entrances",
        "motorcycle_parking": "Dedicated motorcycle spots nearby",
        "bicycle_parking": "Secure bike parking available",
    }
    return reasons.get(item["category"], "Parking available nearby")


class ParkingFulfiller(L2Fulfiller):
    """L2 fulfiller for parking wishes.

    10-entry curated catalog. Tags: free/covered/24h/ev/accessible.
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
                relevance_reason=c.get("relevance_reason", "Parking available nearby"),
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
            map_data=MapData(place_type="parking", radius_km=3.0),
            reminder_option=ReminderOption(
                text="Navigate to this parking spot?",
                delay_hours=1,
            ),
        )
