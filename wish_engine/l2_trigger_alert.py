"""TriggerAlertFulfiller — trigger avoidance and early warning for recovery.

10-entry curated catalog covering location and emotion triggers. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Trigger Alert Catalog (10 entries) ───────────────────────────────────────

TRIGGER_ALERT_CATALOG: list[dict] = [
    {
        "title": "Bar Avoidance Route",
        "description": "Navigate around bars and nightlife areas — safe walking routes for recovery.",
        "category": "bar_avoidance_route",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trigger", "location", "alcohol", "avoidance", "route"],
    },
    {
        "title": "Casino Alert Zone",
        "description": "Get notified when approaching gambling venues — awareness is protection.",
        "category": "casino_alert",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trigger", "location", "gambling", "avoidance", "alert"],
    },
    {
        "title": "Liquor Store Alert",
        "description": "Proximity alerts for liquor stores along your route — plan ahead.",
        "category": "liquor_store_alert",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trigger", "location", "alcohol", "avoidance", "alert"],
    },
    {
        "title": "Party Area Warning",
        "description": "Heads-up about high-nightlife zones — protect your sobriety proactively.",
        "category": "party_area_warning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trigger", "location", "social", "avoidance", "alert"],
    },
    {
        "title": "Stress Trigger Detection",
        "description": "Identify stress patterns that precede cravings — awareness breaks the cycle.",
        "category": "stress_trigger_detect",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trigger", "emotion", "stress", "awareness", "self_paced"],
    },
    {
        "title": "Loneliness Trigger Alert",
        "description": "Recognize loneliness patterns before they become cravings — reach out first.",
        "category": "loneliness_trigger",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trigger", "emotion", "loneliness", "awareness", "gentle"],
    },
    {
        "title": "Anger Trigger Management",
        "description": "Identify anger triggers and have a plan before they escalate to relapse.",
        "category": "anger_trigger",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trigger", "emotion", "anger", "management", "structured"],
    },
    {
        "title": "Boredom Trigger Plan",
        "description": "Boredom is a top relapse trigger — pre-planned activities to fill the void.",
        "category": "boredom_trigger",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trigger", "emotion", "boredom", "activities", "self_paced"],
    },
    {
        "title": "Social Pressure Alert",
        "description": "Scripts and strategies for saying no when others pressure you to use.",
        "category": "social_pressure_alert",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trigger", "social", "pressure", "scripts", "structured"],
    },
    {
        "title": "Holiday Trigger Plan",
        "description": "Navigate holiday seasons sober — plan ahead for gatherings and expectations.",
        "category": "holiday_trigger",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["trigger", "holiday", "planning", "structured", "seasonal"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_TRIGGER_KEYWORDS: dict[str, list[str]] = {
    "trigger": ["trigger", "awareness"],
    "触发": ["trigger", "awareness"],
    "预警": ["trigger", "alert"],
    "avoid": ["trigger", "avoidance"],
    "تجنب": ["trigger", "avoidance"],
    "temptation": ["trigger", "avoidance"],
    "bar": ["trigger", "alcohol"],
    "casino": ["trigger", "gambling"],
    "liquor": ["trigger", "alcohol"],
    "stress": ["trigger", "stress"],
    "lonely": ["trigger", "loneliness"],
    "bored": ["trigger", "boredom"],
    "pressure": ["trigger", "pressure"],
    "holiday": ["trigger", "holiday"],
}


def _match_trigger_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _TRIGGER_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class TriggerAlertFulfiller(L2Fulfiller):
    """L2 fulfiller for trigger alerts — location + emotion trigger avoidance.

    10 curated entries. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_trigger_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in TRIGGER_ALERT_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in TRIGGER_ALERT_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in TRIGGER_ALERT_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Awareness is your strongest tool. Stay vigilant, stay strong.",
                delay_hours=12,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "location" in tags:
        return "Know your environment — avoid trigger zones"
    if "emotion" in tags:
        return "Recognize emotional triggers before they escalate"
    if "social" in tags and "pressure" in tags:
        return "Be prepared when others push you"
    if "holiday" in tags:
        return "Plan ahead for high-risk seasons"
    return "Stay aware and protect your recovery"
