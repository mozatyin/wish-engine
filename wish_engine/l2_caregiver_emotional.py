"""CaregiverEmotionalFulfiller — emotional first aid for overwhelmed caregivers.

10-entry curated catalog of calming, gentle, non-judgmental resources. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Caregiver Emotional Catalog (10 entries) ─────────────────────────────────

CAREGIVER_EMOTIONAL_CATALOG: list[dict] = [
    {
        "title": "Caregiver Breathing Exercise",
        "description": "A 3-minute guided breathing exercise designed for moments of overwhelm.",
        "category": "caregiver_breathing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["caregiver_breathing", "calming", "gentle", "immediate", "self-paced"],
    },
    {
        "title": "Guilt Processing Guide",
        "description": "Gentle prompts to name, explore, and release caregiver guilt — no judgment.",
        "category": "guilt_processing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["guilt_processing", "calming", "gentle", "mental_health", "self-paced"],
    },
    {
        "title": "Anger Release Toolkit",
        "description": "Safe ways to express and release frustration — writing, movement, sound.",
        "category": "anger_release",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["anger_release", "calming", "gentle", "expressive", "self-paced"],
    },
    {
        "title": "Compassion Fatigue Help",
        "description": "When you feel numb from caring too much — gentle steps back to feeling.",
        "category": "compassion_fatigue_help",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["compassion_fatigue_help", "calming", "gentle", "mental_health", "recovery"],
    },
    {
        "title": "Boundary Setting Workshop",
        "description": "Learn to say no without guilt — practical scripts and compassionate framing.",
        "category": "boundary_setting",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["boundary_setting", "calming", "gentle", "practical", "skills"],
    },
    {
        "title": "Grief Journaling Prompts",
        "description": "Journaling prompts for the unique grief of watching someone you love change.",
        "category": "grief_journaling",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["grief_journaling", "calming", "gentle", "expressive", "self-paced"],
    },
    {
        "title": "Self-Compassion Meditation",
        "description": "A guided meditation that reminds you: you are doing your best, and that is enough.",
        "category": "self_compassion_meditation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["self_compassion_meditation", "calming", "gentle", "meditation", "self-paced"],
    },
    {
        "title": "Permission to Rest",
        "description": "You are allowed to rest. A gentle affirmation practice for guilt-free breaks.",
        "category": "permission_to_rest",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["permission_to_rest", "calming", "gentle", "affirmation", "self-paced"],
    },
    {
        "title": "Hope Renewal Exercise",
        "description": "Reconnect with hope through gratitude, small wins, and future visioning.",
        "category": "hope_renewal",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["hope_renewal", "calming", "gentle", "positive", "self-paced"],
    },
    {
        "title": "Peer Validation Circle",
        "description": "Hear other caregivers say: I feel that too. Shared stories of struggle and strength.",
        "category": "peer_validation",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["peer_validation", "calming", "gentle", "social", "community"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_CAREGIVER_EMOTIONAL_KEYWORDS: dict[str, list[str]] = {
    "照护者情绪": [],
    "caregiver emotion": [],
    "guilt": ["guilt_processing"],
    "内疚": ["guilt_processing"],
    "burnout": ["compassion_fatigue_help"],
    "疲惫": ["compassion_fatigue_help"],
    "anger": ["anger_release"],
    "boundary": ["boundary_setting"],
    "compassion fatigue": ["compassion_fatigue_help"],
    "grief": ["grief_journaling"],
    "meditation": ["self_compassion_meditation"],
    "rest": ["permission_to_rest"],
    "hope": ["hope_renewal"],
    "breathing": ["caregiver_breathing"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _CAREGIVER_EMOTIONAL_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "caregiver_breathing": "A moment of calm you can access right now",
        "guilt_processing": "Your guilt does not mean you are failing",
        "anger_release": "Anger is valid — here is a safe way to let it out",
        "compassion_fatigue_help": "Feeling numb is your heart asking for rest",
        "boundary_setting": "Boundaries are an act of love, not selfishness",
        "grief_journaling": "Writing makes invisible pain a little more bearable",
        "self_compassion_meditation": "You deserve the same kindness you give others",
        "permission_to_rest": "Resting does not mean giving up",
        "hope_renewal": "Even small sparks of hope can light the way forward",
        "peer_validation": "Hearing 'me too' is more healing than any advice",
    }
    return reason_map.get(category, "Gentle support for the feelings caregivers carry")


class CaregiverEmotionalFulfiller(L2Fulfiller):
    """L2 fulfiller for caregiver emotional first aid — calming, non-judgmental.

    Uses keyword matching to select from 10-entry catalog. All entries are
    quiet, gentle, and non-judgmental. Applies PersonalityFilter. Zero LLM.
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
                dict(item) for item in CAREGIVER_EMOTIONAL_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in CAREGIVER_EMOTIONAL_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in CAREGIVER_EMOTIONAL_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Your feelings matter — more gentle support here anytime.",
                delay_hours=24,
            ),
        )
