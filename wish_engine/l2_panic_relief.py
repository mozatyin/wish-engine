"""PanicReliefFulfiller — immediate relief techniques for panic/anxiety.

10-entry curated catalog of techniques that can be done ANYWHERE in SECONDS.
Plus nearest safe space recommendation concept. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Relief Catalog (10 entries) ──────────────────────────────────────────────

RELIEF_CATALOG: list[dict] = [
    {
        "title": "Box Breathing (4-4-4-4)",
        "description": "Inhale 4 sec, hold 4 sec, exhale 4 sec, hold 4 sec. Repeat 4 rounds. Navy SEALs use this.",
        "category": "box_breathing_4_4_4_4",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["breathing", "immediate", "anywhere", "calming", "structured", "self-paced"],
    },
    {
        "title": "5-4-3-2-1 Grounding",
        "description": "Name 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste. Anchors you to now.",
        "category": "grounding_5_4_3_2_1",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["grounding", "immediate", "anywhere", "calming", "structured", "sensory"],
    },
    {
        "title": "Cold Water on Face",
        "description": "Splash cold water on face or hold ice cubes. Triggers dive reflex — heart rate drops instantly.",
        "category": "cold_water_face",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["body", "immediate", "calming", "sensory", "quick"],
    },
    {
        "title": "Progressive Muscle Release",
        "description": "Tense each muscle group 5 sec, release. Start fists, work up to shoulders. Feel the contrast.",
        "category": "muscle_tension_release",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["body", "immediate", "anywhere", "calming", "structured", "self-paced"],
    },
    {
        "title": "Count Backward from 100 by 7s",
        "description": "100, 93, 86, 79... Forces your brain to switch from panic to logic.",
        "category": "counting_backward",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cognitive", "immediate", "anywhere", "calming", "structured"],
    },
    {
        "title": "Safe Place Visualization",
        "description": "Close eyes. Picture the safest place you know. Engage all 5 senses there.",
        "category": "safe_place_visualization",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["visualization", "immediate", "anywhere", "calming", "gentle", "self-paced"],
    },
    {
        "title": "Butterfly Hug",
        "description": "Cross arms on chest, tap alternating shoulders slowly. Used in EMDR therapy.",
        "category": "butterfly_hug",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["body", "immediate", "anywhere", "calming", "gentle", "sensory"],
    },
    {
        "title": "Bilateral Tapping",
        "description": "Tap knees alternately left-right at a slow pace. Activates both brain hemispheres.",
        "category": "bilateral_tapping",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["body", "immediate", "anywhere", "calming", "structured", "sensory"],
    },
    {
        "title": "Slow Exhale (4-7-8 Breathing)",
        "description": "Inhale 4 sec, hold 7 sec, exhale 8 sec. Long exhale activates parasympathetic system.",
        "category": "slow_exhale",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["breathing", "immediate", "anywhere", "calming", "structured", "self-paced"],
    },
    {
        "title": "Quick Body Scan (60 sec)",
        "description": "Start at toes, scan up to head. Notice tension without judging. Just observe.",
        "category": "body_scan_quick",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["body", "immediate", "anywhere", "calming", "gentle", "structured", "self-paced"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_PANIC_KEYWORDS: dict[str, list[str]] = {
    "breathing": ["breathing"],
    "呼吸": ["breathing"],
    "ground": ["grounding", "sensory"],
    "grounding": ["grounding", "sensory"],
    "cold": ["body", "sensory"],
    "muscle": ["body"],
    "count": ["cognitive"],
    "visualize": ["visualization"],
    "想象": ["visualization"],
    "hug": ["body", "gentle"],
    "tap": ["body", "sensory"],
    "body": ["body"],
    "身体": ["body"],
    "scan": ["body", "gentle"],
    "calm": ["calming", "breathing"],
    "冷静": ["calming", "breathing"],
}


def _match_panic_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _PANIC_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class PanicReliefFulfiller(L2Fulfiller):
    """L2 fulfiller for panic/anxiety relief — immediate techniques.

    10 techniques all doable anywhere in seconds. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_panic_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in RELIEF_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in RELIEF_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in RELIEF_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Remember: this feeling is temporary. You have survived every panic before.",
                delay_hours=1,
            ),
        )


def _build_relevance_reason(item: dict, det: DetectorResults) -> str:
    tags = set(item.get("tags", []))
    emotions = det.emotion.get("emotions", {})

    if emotions.get("anxiety", 0) > 0.5 and "breathing" in tags:
        return "Breathing is the fastest way to reduce anxiety right now"
    if emotions.get("anxiety", 0) > 0.5 and "grounding" in tags:
        return "Grounding pulls you out of the anxiety spiral"
    if "immediate" in tags and "body" in tags:
        return "Body-based technique — works even when thinking is hard"

    return "Can be done right now, right where you are"
