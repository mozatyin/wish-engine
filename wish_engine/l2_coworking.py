"""CoworkingFulfiller — workspace matching based on personality and work style.

15-entry curated catalog of workspace types. Core innovation: MBTI -> workspace
matching (I->private/silent, E->open/social).
Tags: quiet, social, focus, creative, 24h, wifi, standing, outdoor.
Multilingual keyword routing (EN/ZH/AR).
Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
)

# ── Coworking Catalog (15 entries) ───────────────────────────────────────────

COWORKING_CATALOG: list[dict] = [
    {
        "title": "Silent Library Zone",
        "description": "Pin-drop quiet with deep focus desks — ideal for intense concentration.",
        "category": "silent_library",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "focus", "wifi"],
    },
    {
        "title": "Quiet Cafe Corner",
        "description": "Soft jazz, good coffee, and a cozy corner — productive and relaxing.",
        "category": "quiet_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "focus", "wifi", "creative"],
    },
    {
        "title": "Open Coworking Space",
        "description": "Shared desks, networking events, and a buzzing atmosphere.",
        "category": "coworking_open",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "wifi", "creative"],
    },
    {
        "title": "Private Coworking Pod",
        "description": "Glass-walled private pod with noise cancellation — your personal office.",
        "category": "coworking_private",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "focus", "wifi"],
    },
    {
        "title": "Standing Desk Hub",
        "description": "Ergonomic standing desks with treadmill option — work while you move.",
        "category": "standing_desk",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["standing", "focus", "wifi"],
    },
    {
        "title": "Outdoor Workspace",
        "description": "Garden tables with shade and power outlets — fresh air productivity.",
        "category": "outdoor_workspace",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["outdoor", "creative", "wifi"],
    },
    {
        "title": "University Library",
        "description": "Academic atmosphere with research resources — study and work in silence.",
        "category": "university_library",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "focus", "wifi"],
    },
    {
        "title": "Hotel Lobby Lounge",
        "description": "Elegant setting with complimentary wifi and coffee — work in style.",
        "category": "hotel_lobby",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["quiet", "wifi", "creative"],
    },
    {
        "title": "Creative Studio Space",
        "description": "Art-filled walls, whiteboards, and brainstorming zones — think big.",
        "category": "creative_studio",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "social", "wifi"],
    },
    {
        "title": "Tech Hub & Incubator",
        "description": "Startup energy with mentorship and demo days — build the next big thing.",
        "category": "tech_hub",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "wifi", "creative"],
    },
    {
        "title": "Startup Incubator",
        "description": "Shared resources, pitch practice, and founder community — launch faster.",
        "category": "incubator",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "wifi", "creative"],
    },
    {
        "title": "Community Center Desk",
        "description": "Affordable workspace with community programs — connect while you work.",
        "category": "community_center",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["social", "wifi"],
    },
    {
        "title": "Rooftop Workspace",
        "description": "City views and open sky — inspiration at every glance.",
        "category": "rooftop_space",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["outdoor", "creative", "wifi"],
    },
    {
        "title": "Garden Workspace",
        "description": "Quiet garden with wifi and power — nature meets productivity.",
        "category": "garden_workspace",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "outdoor", "focus", "wifi"],
    },
    {
        "title": "24-Hour Workspace",
        "description": "Always open, always ready — for night owls and early birds alike.",
        "category": "24h_workspace",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "focus", "wifi", "quiet"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

COWORKING_KEYWORDS: set[str] = {
    "工作", "办公", "cowork", "workspace", "cafe", "写代码", "办公空间",
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates based on MBTI and work style preferences."""
    text_lower = wish_text.lower()
    mbti = detector_results.mbti

    candidates: list[dict] = []
    for item in COWORKING_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0
        tags = set(item.get("tags", []))

        # MBTI-based matching
        mbti_type = mbti.get("type", "")
        if len(mbti_type) == 4:
            if mbti_type[0] == "I":
                if "quiet" in tags or "focus" in tags:
                    score_boost += 0.2
                    item_copy["relevance_reason"] = "A quiet space perfect for focused work"
            elif mbti_type[0] == "E":
                if "social" in tags:
                    score_boost += 0.2
                    item_copy["relevance_reason"] = "A social space to work and connect"

        # Text-based preference hints
        if any(kw in text_lower for kw in ["quiet", "安静", "focus", "专注"]):
            if "quiet" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["creative", "创意", "brainstorm"]):
            if "creative" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["24h", "通宵", "night", "晚上"]):
            if "24h" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["outdoor", "户外", "garden", "花园"]):
            if "outdoor" in tags:
                score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


class CoworkingFulfiller(L2Fulfiller):
    """L2 fulfiller for workspace wishes — personality-matched workspaces.

    15-entry curated catalog. Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
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
                relevance_reason=c.get("relevance_reason", "A workspace that fits your style"),
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

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "A workspace that fits your style"

        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="coworking_space", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Try this workspace today?",
                delay_hours=2,
            ),
        )
