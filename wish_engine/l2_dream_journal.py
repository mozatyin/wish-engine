"""DreamJournalFulfiller — dream theme analysis with journaling prompts.

15 dream themes with pattern analysis prompts. Personality-filtered. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    Recommendation,
    ReminderOption,
)

# ── Dream Journal Catalog (15 entries) ───────────────────────────────────────

DREAM_CATALOG: list[dict] = [
    {
        "title": "Flying Dreams: Freedom Journal",
        "description": "You dreamed of flying? Write about what freedom means to you right now.",
        "category": "flying",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Falling Dreams: Control Reflection",
        "description": "Falling often means losing control — what in your life feels unsteady right now?",
        "category": "falling",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Chasing Dreams: Anxiety Map",
        "description": "Being chased? Map what you're avoiding — name it, and it loses power.",
        "category": "chasing",
        "tags": ["quiet", "self-paced", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Water Dreams: Emotion Depth",
        "description": "Water reflects your emotional state — was it calm, stormy, or deep? Journal it.",
        "category": "water",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "House Dreams: Inner Architecture",
        "description": "Houses in dreams are your psyche — which rooms did you visit? What was hidden?",
        "category": "house",
        "tags": ["quiet", "self-paced", "calming", "introspective", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Teeth Dreams: Vulnerability Check",
        "description": "Losing teeth often signals vulnerability — where do you feel exposed lately?",
        "category": "teeth",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Death Dreams: Transformation Journal",
        "description": "Death in dreams rarely means death — it's transformation. What's ending so something new can begin?",
        "category": "death",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Animal Dreams: Instinct Guide",
        "description": "Which animal appeared? It carries a message — write about what instinct it represents.",
        "category": "animals",
        "tags": ["quiet", "self-paced", "calming", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Lost Dreams: Direction Finder",
        "description": "Feeling lost in a dream? Write about where you feel directionless in waking life.",
        "category": "lost",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Naked Dreams: Authenticity Journal",
        "description": "Being naked in public = fear of being seen as you truly are. What are you hiding?",
        "category": "naked",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "bold",
    },
    {
        "title": "Exam Dreams: Performance Anxiety Log",
        "description": "The unfinished exam dream — where do you feel tested or unprepared right now?",
        "category": "exam",
        "tags": ["quiet", "self-paced", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Wedding Dreams: Commitment Reflection",
        "description": "Wedding dreams are about commitment — what are you ready (or not ready) to commit to?",
        "category": "wedding",
        "tags": ["quiet", "self-paced", "calming", "warm"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Baby Dreams: New Beginnings",
        "description": "Babies in dreams signal new starts — what new project, idea, or phase is being born?",
        "category": "baby",
        "tags": ["quiet", "self-paced", "calming", "warm", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Travel Dreams: Journey Map",
        "description": "Where were you going? The destination reveals your current life direction — map it.",
        "category": "travel",
        "tags": ["quiet", "self-paced", "calming", "energizing"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Ancestor Dreams: Heritage Connection",
        "description": "Dreaming of ancestors is a gift — write what they might be trying to tell you.",
        "category": "ancestors",
        "tags": ["quiet", "self-paced", "calming", "warm", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
]


def _detect_dream_theme(wish_text: str) -> str | None:
    """Try to detect dream theme from wish text."""
    text_lower = wish_text.lower()
    theme_keywords: dict[str, list[str]] = {
        "flying": ["fly", "flying", "飞", "طيران"],
        "falling": ["fall", "falling", "掉", "سقوط"],
        "chasing": ["chase", "chasing", "pursued", "追", "مطاردة"],
        "water": ["water", "ocean", "sea", "水", "ماء"],
        "house": ["house", "room", "door", "房子", "منزل"],
        "teeth": ["teeth", "tooth", "牙", "أسنان"],
        "death": ["death", "die", "dead", "死", "موت"],
        "animals": ["animal", "dog", "cat", "snake", "动物", "حيوان"],
        "lost": ["lost", "迷路", "找不到", "ضائع"],
        "naked": ["naked", "nude", "裸", "عاري"],
        "exam": ["exam", "test", "考试", "امتحان"],
        "wedding": ["wedding", "marry", "婚", "زفاف"],
        "baby": ["baby", "infant", "婴儿", "طفل"],
        "travel": ["travel", "journey", "旅行", "سفر"],
        "ancestors": ["ancestor", "grandpa", "grandma", "祖", "أجداد"],
    }
    for theme, keywords in theme_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return theme
    return None


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Score candidates based on dream theme and personality."""
    detected_theme = _detect_dream_theme(wish_text)

    candidates: list[dict] = []
    for item in DREAM_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Theme match boost
        if detected_theme and item["category"] == detected_theme:
            score_boost += 0.35

        # Fragility adjustment
        fragility = detector_results.fragility.get("pattern", "")
        if fragility in ("defensive", "fragile") and item["difficulty"] == "bold":
            score_boost -= 0.15
        if fragility in ("defensive", "fragile") and item["difficulty"] == "gentle":
            score_boost += 0.10

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_reason(item, detected_theme)
        candidates.append(item_copy)

    return candidates


def _build_reason(item: dict, detected_theme: str | None) -> str:
    """Build relevance reason."""
    if detected_theme and item["category"] == detected_theme:
        return f"Matches your dream theme — explore what it means"
    return f"Explore {item['category']} dreams — a window into your psyche"


class DreamJournalFulfiller(L2Fulfiller):
    """L2 fulfiller for dream journal wishes — pattern analysis prompts.

    15-entry curated catalog across dream themes. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:3]

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
            reminder_option=ReminderOption(
                text="Did you journal about your dream today?",
                delay_hours=8,
            ),
        )
