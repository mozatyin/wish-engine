"""SafeSpaceFulfiller — local-compute safe/inclusive venue recommendation.

15-entry curated catalog of safe space types for marginalized groups.
Categories: lgbtq_friendly, women_only, disability_accessible, multicultural,
quiet_space, therapy_friendly. Multilingual keyword routing. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    ReminderOption,
)

# ── Safe Space Catalog (15 entries) ──────────────────────────────────────────

SAFE_SPACE_CATALOG: list[dict] = [
    # ── LGBTQ+ Friendly (3) ─────────────────────────────────────────────────
    {
        "title": "Rainbow Community Center",
        "description": "A welcoming space for LGBTQ+ individuals — events, counseling, and community.",
        "category": "lgbtq_friendly",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["inclusive", "safe", "welcoming", "lgbtq", "social"],
    },
    {
        "title": "Pride Cafe & Lounge",
        "description": "Cafe and social lounge with a zero-tolerance policy for discrimination.",
        "category": "lgbtq_friendly",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["inclusive", "safe", "welcoming", "social", "modern"],
    },
    {
        "title": "Queer Art Collective",
        "description": "Creative space for LGBTQ+ artists — exhibitions, workshops, and open mics.",
        "category": "lgbtq_friendly",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["inclusive", "safe", "creative", "welcoming"],
    },
    # ── Women Only (2) ──────────────────────────────────────────────────────
    {
        "title": "Women's Wellness Lounge",
        "description": "A private, women-only space for relaxation, fitness, and support groups.",
        "category": "women_only",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "private", "welcoming", "quiet", "calming"],
    },
    {
        "title": "Sisters' Co-Working Hub",
        "description": "Women-only co-working space with mentorship programs and networking events.",
        "category": "women_only",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["safe", "welcoming", "quiet", "practical"],
    },
    # ── Disability Accessible (3) ───────────────────────────────────────────
    {
        "title": "Universal Access Community Center",
        "description": "Fully accessible venue — ramps, elevators, sign language support, sensory rooms.",
        "category": "disability_accessible",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["inclusive", "safe", "welcoming", "quiet", "non-judgmental"],
    },
    {
        "title": "Adaptive Sports Center",
        "description": "Sports and recreation programs designed for all ability levels.",
        "category": "disability_accessible",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["inclusive", "safe", "welcoming", "social", "physical"],
    },
    {
        "title": "Sensory-Friendly Library",
        "description": "Library with quiet hours, sensory rooms, and assistive technology.",
        "category": "disability_accessible",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["inclusive", "safe", "quiet", "non-judgmental", "calming"],
    },
    # ── Multicultural (2) ───────────────────────────────────────────────────
    {
        "title": "Multicultural Exchange Center",
        "description": "Celebrate diversity — language exchanges, cultural events, and shared meals.",
        "category": "multicultural",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["inclusive", "welcoming", "social", "traditional"],
    },
    {
        "title": "International Friendship House",
        "description": "A home away from home for expats and immigrants — support, community, and belonging.",
        "category": "multicultural",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["inclusive", "safe", "welcoming", "non-judgmental"],
    },
    # ── Quiet Space (3) ─────────────────────────────────────────────────────
    {
        "title": "Silent Meditation Room",
        "description": "A dedicated silent space for meditation, prayer, or simply being still.",
        "category": "quiet_space",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "quiet", "calming", "private", "non-judgmental"],
    },
    {
        "title": "Introvert-Friendly Lounge",
        "description": "Low-stimulation environment — soft lighting, no music, comfortable seating.",
        "category": "quiet_space",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "quiet", "calming", "private"],
    },
    {
        "title": "Nature Healing Garden",
        "description": "A tranquil garden space designed for reflection, healing, and solitude.",
        "category": "quiet_space",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "quiet", "calming", "outdoor", "non-judgmental"],
    },
    # ── Therapy Friendly (2) ────────────────────────────────────────────────
    {
        "title": "Peer Support Drop-In",
        "description": "Walk-in support center staffed by trained peer counselors — no appointment needed.",
        "category": "therapy_friendly",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["safe", "welcoming", "non-judgmental", "private", "calming"],
    },
    {
        "title": "Community Therapy Circle",
        "description": "Facilitated group therapy sessions in a warm, confidential environment.",
        "category": "therapy_friendly",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["safe", "welcoming", "non-judgmental", "calming", "social"],
    },
]

# ── Keywords ──────────────────────────────────────────────────────────────────

_SAFE_SPACE_KEYWORDS: set[str] = {
    "安全", "safe space", "inclusive", "friendly", "welcoming", "آمن",
    "safe", "包容", "无障碍", "accessible", "support",
}


class SafeSpaceFulfiller(L2Fulfiller):
    """L2 fulfiller for safe space wishes — inclusive venue recommendation.

    15-entry curated catalog. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = [dict(item) for item in SAFE_SPACE_CATALOG]

        # Add relevance reasons based on category
        for c in candidates:
            cat = c.get("category", "")
            reasons = {
                "lgbtq_friendly": "A welcoming, judgment-free community space",
                "women_only": "A private, safe environment just for you",
                "disability_accessible": "Fully accessible and designed for comfort",
                "multicultural": "Celebrate diversity and find belonging",
                "quiet_space": "A peaceful retreat when you need stillness",
                "therapy_friendly": "Professional support in a warm setting",
            }
            c["relevance_reason"] = reasons.get(cat, "A safe, welcoming space for you")

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="safe_space", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Visit a safe space this week?",
                delay_hours=12,
            ),
        )
