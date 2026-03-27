"""FocusModeFulfiller — focus environments with MBTI-aware recommendations.

10 focus environments. I types get silent/solo spots, E types get cafe/study groups.
Time-aware: morning=productive spots, evening=wind-down.
Zero LLM.
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

# ── Focus Environment Catalog (10 entries) ───────────────────────────────────

FOCUS_CATALOG: list[dict] = [
    {
        "title": "Silent Library",
        "description": "Absolute quiet — the classic focus environment for deep work.",
        "category": "silent_library",
        "tags": ["quiet", "calming", "self-paced", "autonomous"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_pref": "I",
        "time_pref": "morning",
    },
    {
        "title": "Quiet Cafe",
        "description": "Ambient noise, good coffee, and a corner seat — productive and cozy.",
        "category": "quiet_cafe",
        "tags": ["quiet", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_pref": "I",
        "time_pref": "morning",
    },
    {
        "title": "Nature Spot",
        "description": "Park bench, garden, or lakeside — fresh air fuels creative thinking.",
        "category": "nature_spot",
        "tags": ["nature", "quiet", "calming", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_pref": "I",
        "time_pref": "morning",
    },
    {
        "title": "Home Office Tips",
        "description": "Optimize your WFH setup — lighting, chair height, and distraction blockers.",
        "category": "home_office_tips",
        "tags": ["practical", "quiet", "autonomous", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_pref": "I",
        "time_pref": "morning",
    },
    {
        "title": "Pomodoro Guide",
        "description": "25 min focus + 5 min break — the proven rhythm for sustained productivity.",
        "category": "pomodoro_guide",
        "tags": ["practical", "quiet", "simple", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_pref": None,
        "time_pref": None,
    },
    {
        "title": "Noise-Canceling Spots",
        "description": "Places with booths, pods, or excellent soundproofing — zero distractions.",
        "category": "noise_canceling_spots",
        "tags": ["quiet", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_pref": "I",
        "time_pref": "morning",
    },
    {
        "title": "Study Group",
        "description": "Co-study with motivated peers — accountability through presence.",
        "category": "study_group",
        "tags": ["social", "energizing", "practical"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "mbti_pref": "E",
        "time_pref": "morning",
    },
    {
        "title": "Deep Work Schedule",
        "description": "Block 2-4 hours of uninterrupted time — no meetings, no notifications.",
        "category": "deep_work_schedule",
        "tags": ["practical", "quiet", "autonomous", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_pref": "I",
        "time_pref": "morning",
    },
    {
        "title": "Digital Detox Spot",
        "description": "Leave your phone behind — focus with pen, paper, and pure thought.",
        "category": "digital_detox_spot",
        "tags": ["quiet", "calming", "digital-detox", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_pref": "I",
        "time_pref": "evening",
    },
    {
        "title": "Flow State Playlist",
        "description": "Curated lo-fi, ambient, or classical music — audio fuel for deep focus.",
        "category": "flow_state_playlist",
        "tags": ["music", "calming", "quiet", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "mbti_pref": None,
        "time_pref": None,
    },
]


def _get_mbti_ei(detector_results: DetectorResults) -> str | None:
    """Get E/I dimension from MBTI."""
    mbti = detector_results.mbti.get("type", "")
    if len(mbti) == 4:
        return mbti[0]  # "E" or "I"
    return None


def _detect_time(wish_text: str) -> str | None:
    """Detect time of day from wish text."""
    text_lower = wish_text.lower()
    if any(kw in text_lower for kw in ["morning", "早上", "上午", "صباح"]):
        return "morning"
    if any(kw in text_lower for kw in ["evening", "晚上", "night", "مساء"]):
        return "evening"
    return None


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates based on MBTI and time awareness."""
    ei = _get_mbti_ei(detector_results)
    time_pref = _detect_time(wish_text)

    candidates: list[dict] = []
    for item in FOCUS_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # MBTI E/I matching
        item_pref = item.get("mbti_pref")
        if ei and item_pref:
            if ei == item_pref:
                score_boost += 0.2
                if ei == "I":
                    item_copy["relevance_reason"] = "Perfect for your introverted focus style"
                else:
                    item_copy["relevance_reason"] = "Social energy to boost your focus"
            else:
                score_boost -= 0.1

        # Time matching
        if time_pref and item.get("time_pref") == time_pref:
            score_boost += 0.1

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


class FocusModeFulfiller(L2Fulfiller):
    """L2 fulfiller for focus mode wishes — MBTI and time-aware environments.

    10-entry curated catalog. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "An environment designed for deep focus"

        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:3]

        from wish_engine.models import Recommendation

        recommendations = [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "Matches your profile"),
                score=c.get("_personality_score", 0.5),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="focus_space", radius_km=3.0),
            reminder_option=ReminderOption(
                text="Ready for a focus session?",
                delay_hours=4,
            ),
        )
