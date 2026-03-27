"""ChronicPainFulfiller — curated chronic pain management resources.

10-entry catalog of gentle, calming pain management approaches.
All entries designed to be non-threatening and comforting. Zero LLM.
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

PAIN_CATALOG: list[dict] = [
    {
        "title": "Pain Management Clinic Finder",
        "description": "Find multidisciplinary pain clinics near you — specialists who understand chronic pain.",
        "category": "pain_management_clinic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["clinic", "professional", "management", "calming"],
    },
    {
        "title": "Gentle Exercise for Pain",
        "description": "Low-impact movement programs — water walking, chair stretches, gentle yoga for pain relief.",
        "category": "gentle_exercise",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["exercise", "gentle", "movement", "calming", "self-paced"],
    },
    {
        "title": "Pain Psychology Resources",
        "description": "CBT-based pain management, pain catastrophizing reduction, and acceptance therapy.",
        "category": "pain_psychology",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["psychology", "cbt", "therapy", "calming", "self-paced"],
    },
    {
        "title": "Meditation for Pain Relief",
        "description": "Guided body scan meditations and mindfulness practices specifically designed for pain.",
        "category": "meditation_for_pain",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meditation", "mindfulness", "calming", "gentle", "self-paced"],
    },
    {
        "title": "Warm Therapy Guide",
        "description": "Heat pad techniques, warm baths, and thermal therapy approaches for pain relief.",
        "category": "warm_therapy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["warmth", "therapy", "home", "calming", "gentle"],
    },
    {
        "title": "Cold Therapy Guide",
        "description": "Ice application techniques, cold compresses, and cryotherapy information.",
        "category": "cold_therapy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cold", "therapy", "home", "calming"],
    },
    {
        "title": "Acupuncture Resources",
        "description": "Find licensed acupuncturists, understand what to expect, and track treatment progress.",
        "category": "acupuncture",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["acupuncture", "alternative", "professional", "calming"],
    },
    {
        "title": "Physical Therapy Guide",
        "description": "At-home PT exercises, finding specialists, and tracking your rehabilitation progress.",
        "category": "physical_therapy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["physical_therapy", "exercise", "professional", "calming", "self-paced"],
    },
    {
        "title": "Chronic Pain Support Group",
        "description": "Connect with others who live with chronic pain — validation, tips, and understanding.",
        "category": "pain_support_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["support", "community", "calming", "gentle"],
    },
    {
        "title": "Pain Journaling Toolkit",
        "description": "Track pain levels, triggers, and patterns. Templates for communicating with doctors.",
        "category": "pain_journaling",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["journaling", "tracking", "management", "calming", "self-paced"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_PAIN_KEYWORDS: dict[str, list[str]] = {
    "慢性疼痛": [],
    "chronic pain": [],
    "疼痛": [],
    "ألم": [],
    "pain management": ["management"],
    "pain": [],
    "ache": [],
    "hurt": [],
    "疼": [],
    "exercise": ["exercise", "gentle", "movement"],
    "运动": ["exercise", "gentle", "movement"],
    "meditation": ["meditation", "mindfulness"],
    "冥想": ["meditation", "mindfulness"],
    "therapy": ["therapy", "professional"],
    "治疗": ["therapy", "professional"],
    "support": ["support", "community"],
    "支持": ["support", "community"],
    "journal": ["journaling", "tracking"],
}


def _match_pain_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _PAIN_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class ChronicPainFulfiller(L2Fulfiller):
    """L2 fulfiller for chronic pain management — gentle, calming resources.

    10 curated entries all designed to be comforting and non-threatening. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_pain_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in PAIN_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in PAIN_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in PAIN_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Your pain is real and valid. These resources are here whenever you need them.",
                delay_hours=24,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "gentle" in tags:
        return "Gentle approach designed for comfort, not performance"
    if "community" in tags:
        return "Connect with people who truly understand chronic pain"
    if "professional" in tags:
        return "Expert guidance for pain management"
    if "self-paced" in tags:
        return "Go at your own pace — no pressure"
    return "Calming resource for pain management"
