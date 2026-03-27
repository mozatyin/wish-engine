"""SafeRouteFulfiller — local-compute safe space recommendation with personality filtering.

15-entry curated catalog of safe spaces. Zero LLM. Keyword matching
(English/Chinese/Arabic) routes wish text to relevant safe space categories,
then PersonalityFilter scores and ranks candidates.

Special handling: anxiety + late night = extra emphasis on calming, well-lit spaces.
"""

from __future__ import annotations

from wish_engine.apis import safety_scorer
from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    ReminderOption,
)

# ── Safe Space Catalog (15 entries) ──────────────────────────────────────────

SAFE_CATALOG: list[dict] = [
    # ── 24h Safe Havens (4) ──────────────────────────────────────────────────
    {
        "title": "24-Hour Cafe",
        "description": "Well-lit cafe open all night with warm drinks and Wi-Fi.",
        "category": "safe_haven",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "24h", "well-lit", "calming", "late-night"],
    },
    {
        "title": "24-Hour Convenience Store",
        "description": "Brightly lit store with staff present around the clock.",
        "category": "safe_haven",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "24h", "well-lit", "late-night", "practical"],
    },
    {
        "title": "Hotel Lobby",
        "description": "Staffed hotel lobby — safe, warm, and open 24 hours.",
        "category": "safe_haven",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "24h", "well-lit", "calming", "late-night"],
    },
    {
        "title": "Airport Terminal",
        "description": "Secure, well-lit public space open 24 hours with security presence.",
        "category": "safe_haven",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["safe", "24h", "well-lit", "late-night", "security"],
    },
    # ── Emergency & Authority (3) ────────────────────────────────────────────
    {
        "title": "Police Station",
        "description": "Nearest police station for emergency assistance.",
        "category": "emergency",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "emergency", "authority", "24h"],
    },
    {
        "title": "Hospital Emergency Room",
        "description": "Hospital ER — always open, always staffed, always safe.",
        "category": "emergency",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["safe", "emergency", "medical", "24h"],
    },
    {
        "title": "Fire Station",
        "description": "Fire stations are staffed 24/7 and a safe place to seek help.",
        "category": "emergency",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "emergency", "authority", "24h"],
    },
    # ── Daytime Safe Spaces (4) ──────────────────────────────────────────────
    {
        "title": "Public Library",
        "description": "Quiet, safe public space with staff and free resources.",
        "category": "public_space",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "quiet", "calming", "daytime", "self-paced"],
    },
    {
        "title": "Community Center",
        "description": "Local community hub with staff, activities, and a safe environment.",
        "category": "public_space",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["safe", "social", "daytime", "calming"],
    },
    {
        "title": "Shopping Mall",
        "description": "Well-lit, security-patrolled shopping center with many people around.",
        "category": "public_space",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["safe", "well-lit", "daytime", "social", "practical"],
    },
    {
        "title": "Place of Worship",
        "description": "Mosque, church, or temple — welcoming, safe, and community-oriented.",
        "category": "public_space",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "quiet", "calming", "traditional", "peaceful"],
    },
    # ── Transportation Hubs (2) ──────────────────────────────────────────────
    {
        "title": "Main Train Station",
        "description": "Major transit hub with security, staff, and 24h activity.",
        "category": "transit",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["safe", "well-lit", "late-night", "transit"],
    },
    {
        "title": "Bus Terminal",
        "description": "Central bus terminal with lighting and staff presence.",
        "category": "transit",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["safe", "well-lit", "transit"],
    },
    # ── Calming Spaces (2) ───────────────────────────────────────────────────
    {
        "title": "Well-Lit Park (Daytime)",
        "description": "Populated park with good lighting and open sightlines — daytime only.",
        "category": "outdoor",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "calming", "daytime", "nature", "peaceful"],
    },
    {
        "title": "Bookstore Cafe",
        "description": "Cozy bookstore with cafe area, well-lit, staffed, and welcoming.",
        "category": "safe_haven",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "calming", "well-lit", "quiet", "self-paced"],
    },
]


# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_SAFETY_KEYWORDS: dict[str, list[str]] = {
    # safety / going home
    "safe": ["safe"],
    "safety": ["safe"],
    "安全": ["safe"],
    "回家": ["safe", "late-night"],
    "أمان": ["safe"],
    "آمن": ["safe"],
    # night / dark
    "night": ["late-night"],
    "late": ["late-night"],
    "dark": ["late-night"],
    "晚上": ["late-night"],
    "深夜": ["late-night"],
    "天黑": ["late-night"],
    "ليل": ["late-night"],
    "مظلم": ["late-night"],
    # emergency
    "emergency": ["emergency"],
    "help": ["emergency"],
    "紧急": ["emergency"],
    "救命": ["emergency"],
    "طوارئ": ["emergency"],
    # calm / anxiety
    "calm": ["calming"],
    "anxiety": ["calming"],
    "scared": ["calming", "safe"],
    "害怕": ["calming", "safe"],
    "焦虑": ["calming"],
    "خوف": ["calming", "safe"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _SAFETY_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


class SafeRouteFulfiller(L2Fulfiller):
    """L2 fulfiller for safe space wishes — safety-aware recommendations.

    Uses keyword matching to select from 15-entry safe space catalog, then
    applies PersonalityFilter for scoring. Extra emphasis for anxiety + late
    night combinations. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match tag categories
        matched_categories = _match_categories(wish.wish_text)

        # 2. Filter catalog
        if matched_categories:
            matched_set = set(matched_categories)
            candidates = [
                dict(item) for item in SAFE_CATALOG
                if matched_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in SAFE_CATALOG]

        # 3. Fallback to full catalog
        if not candidates:
            candidates = [dict(item) for item in SAFE_CATALOG]

        # 4. Anxiety + late night boost: prioritize calming + well-lit
        anxiety = detector_results.emotion.get("emotions", {}).get("anxiety", 0.0)
        has_late_night = "late-night" in matched_categories if matched_categories else False
        if anxiety > 0.5 and has_late_night:
            for c in candidates:
                tags = set(c.get("tags", []))
                if "calming" in tags and "well-lit" in tags:
                    c.setdefault("_personality_score", 0.5)
                    c["_personality_score"] = min(c["_personality_score"] + 0.2, 1.0)

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="safe_space", radius_km=3.0),
            reminder_option=ReminderOption(
                text="Did you get to a safe place?",
                delay_hours=1,
            ),
        )


def _build_relevance_reason(item: dict, detector_results: DetectorResults) -> str:
    """Build a personalized relevance reason."""
    parts: list[str] = []

    anxiety = detector_results.emotion.get("emotions", {}).get("anxiety", 0.0)
    if anxiety > 0.5 and "calming" in item.get("tags", []):
        parts.append("Calming space to help ease anxiety")

    fragility = detector_results.fragility.get("pattern", "")
    if fragility == "overwhelmed" and "quiet" in item.get("tags", []):
        parts.append("Quiet environment to decompress")

    if not parts:
        tags = item.get("tags", [])
        if "24h" in tags:
            parts.append("Open around the clock for safety")
        elif "emergency" in tags:
            parts.append("Emergency services available")
        elif "calming" in tags:
            parts.append("Safe, calming environment")
        else:
            parts.append("Safe space nearby")

    return ". ".join(parts)
