"""RemoteCareFulfiller — remote monitoring and care tools for distant caregivers.

10-entry curated catalog of technology solutions for remote care. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Remote Care Catalog (10 entries) ─────────────────────────────────────────

REMOTE_CARE_CATALOG: list[dict] = [
    {
        "title": "Video Call Schedule Planner",
        "description": "Set up regular video calls with elderly family — reminders, easy interface, one-tap connect.",
        "category": "video_call_schedule",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["video_call_schedule", "digital", "calming", "social", "routine"],
    },
    {
        "title": "Health Monitor App",
        "description": "Track vitals remotely — blood pressure, heart rate, glucose — with family dashboard.",
        "category": "health_monitor_app",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["health_monitor_app", "digital", "medical", "calming", "monitoring"],
    },
    {
        "title": "Medication Reminder System",
        "description": "Automated pill reminders with family alerts if doses are missed.",
        "category": "medication_reminder",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["medication_reminder", "digital", "medical", "calming", "routine"],
    },
    {
        "title": "Fall Detection Device",
        "description": "Wearable fall sensor that auto-alerts family and emergency services.",
        "category": "fall_detection",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["fall_detection", "wearable", "safety", "calming", "emergency"],
    },
    {
        "title": "GPS Tracker for Elderly",
        "description": "Discreet GPS tracker for loved ones with dementia — real-time location sharing.",
        "category": "gps_tracker",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["gps_tracker", "wearable", "safety", "calming", "monitoring"],
    },
    {
        "title": "Smart Home Sensor Kit",
        "description": "Motion, door, and activity sensors that alert you if daily routines change.",
        "category": "smart_home_sensor",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["smart_home_sensor", "digital", "home", "calming", "monitoring"],
    },
    {
        "title": "Emergency Button Pendant",
        "description": "One-press emergency button worn as a pendant — connects to family and paramedics.",
        "category": "emergency_button",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["emergency_button", "wearable", "safety", "calming", "emergency"],
    },
    {
        "title": "Care Coordination App",
        "description": "Shared family app to coordinate visits, tasks, appointments, and updates.",
        "category": "care_coordination_app",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["care_coordination_app", "digital", "calming", "coordination", "family"],
    },
    {
        "title": "Daily Check-In Service",
        "description": "Friendly daily phone call to your loved one — wellness check with family reports.",
        "category": "daily_check_in",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["daily_check_in", "social", "calming", "routine", "gentle"],
    },
    {
        "title": "Family Care Group Chat",
        "description": "Dedicated care group with shared calendar, photo updates, and task assignments.",
        "category": "family_care_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["family_care_group", "digital", "social", "calming", "coordination"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_REMOTE_CARE_KEYWORDS: dict[str, list[str]] = {
    "远程看护": [],
    "remote care": [],
    "监护": [],
    "monitor": ["health_monitor_app", "smart_home_sensor"],
    "مراقبة": [],
    "elderly tech": [],
    "video call": ["video_call_schedule"],
    "medication": ["medication_reminder"],
    "fall": ["fall_detection"],
    "gps": ["gps_tracker"],
    "sensor": ["smart_home_sensor"],
    "emergency": ["emergency_button"],
    "check-in": ["daily_check_in"],
    "coordinate": ["care_coordination_app"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _REMOTE_CARE_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "video_call_schedule": "Stay connected even from far away",
        "health_monitor_app": "Peace of mind through real-time health data",
        "medication_reminder": "Never miss a dose — automated and family-linked",
        "fall_detection": "Instant alerts if something goes wrong",
        "gps_tracker": "Know they are safe wherever they go",
        "smart_home_sensor": "Subtle monitoring without intruding on independence",
        "emergency_button": "One press connects to help immediately",
        "care_coordination_app": "Keep the whole family organized and informed",
        "daily_check_in": "A friendly voice every day for your loved one",
        "family_care_group": "Share the caregiving journey with family",
    }
    return reason_map.get(category, "Technology to care from a distance")


class RemoteCareFulfiller(L2Fulfiller):
    """L2 fulfiller for remote care tools — technology for distant caregivers.

    Uses keyword matching to select from 10-entry catalog.
    Applies PersonalityFilter. Zero LLM.
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
                dict(item) for item in REMOTE_CARE_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in REMOTE_CARE_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in REMOTE_CARE_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New remote care tools added regularly — check back!",
                delay_hours=24,
            ),
        )
