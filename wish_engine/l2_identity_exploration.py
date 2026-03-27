"""IdentityExplorationFulfiller — identity exploration with compass integration.

15 exploration types supporting hidden identity signals. Zero LLM.
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

# ── Identity Exploration Catalog (15 entries) ────────────────────────────────

IDENTITY_CATALOG: list[dict] = [
    {
        "title": "Values Clarification Exercise",
        "description": "Rank these 10 values by importance — notice which ones you live and which you only admire.",
        "category": "values_clarification",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Cultural Identity Map",
        "description": "Draw a map of all cultures you belong to — by birth, by choice, by accident. All count.",
        "category": "cultural_identity",
        "tags": ["quiet", "self-paced", "calming", "creative", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Gender Expression Journal",
        "description": "Write about how you express your gender — what feels authentic? What feels performed?",
        "category": "gender_exploration",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Spiritual Questions List",
        "description": "Write 10 questions about meaning that you can't answer — the questions matter more than answers.",
        "category": "spiritual_seeking",
        "tags": ["quiet", "self-paced", "calming", "introspective", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Career Identity Reflection",
        "description": "Separate who you are from what you do — write: 'I am ___, and my job is ___.'",
        "category": "career_identity",
        "tags": ["quiet", "self-paced", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Creative Identity Experiment",
        "description": "Try a creative form you've never tried — paint, dance, code, cook. See what feels like you.",
        "category": "creative_identity",
        "tags": ["creative", "self-paced", "energizing"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Relationship Style Inventory",
        "description": "Write about your ideal relationship — not the person, but how you want to relate to them.",
        "category": "relationship_style",
        "tags": ["quiet", "self-paced", "calming", "warm", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Attachment Story",
        "description": "Write the story of your earliest bond — how did you learn to trust (or not trust)?",
        "category": "attachment_understanding",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "bold",
    },
    {
        "title": "Family Role Awareness",
        "description": "What role do you play in your family? The fixer? The peacemaker? The rebel? Name it.",
        "category": "family_role",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Social Identity Circles",
        "description": "Draw circles for each group you belong to — work, friends, online, culture. Where do they overlap?",
        "category": "social_identity",
        "tags": ["quiet", "self-paced", "calming", "creative"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Political Awareness Check",
        "description": "Write 3 issues you care about and why — not what party, but what values drive your stance.",
        "category": "political_awareness",
        "tags": ["quiet", "self-paced", "calming", "introspective", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Ethical Framework Builder",
        "description": "When is it OK to lie? To break a rule? To stay silent? — write your personal ethics code.",
        "category": "ethical_framework",
        "tags": ["quiet", "self-paced", "calming", "theory", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Life Purpose Exploration",
        "description": "Finish this sentence 20 different ways: 'I was put here to ___.' — see what pattern emerges.",
        "category": "life_purpose",
        "tags": ["quiet", "self-paced", "calming", "introspective"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "moderate",
    },
    {
        "title": "Personality Deep Dive",
        "description": "Take a personality test — then disagree with the parts that don't fit. The disagreement is data.",
        "category": "personality_deep_dive",
        "tags": ["quiet", "self-paced", "calming", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
    {
        "title": "Heritage Connection Ritual",
        "description": "Cook a family recipe, learn a word in your ancestors' language, or visit a place that connects you to your roots.",
        "category": "heritage_connection",
        "tags": ["quiet", "self-paced", "calming", "warm", "traditional"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "difficulty": "gentle",
    },
]


def _detect_identity_signals(wish_text: str, detector_results: DetectorResults) -> list[str]:
    """Detect identity exploration signals from wish text and detectors."""
    signals: list[str] = []
    text_lower = wish_text.lower()

    # Text-based signals
    signal_keywords: dict[str, list[str]] = {
        "values_clarification": ["value", "价值", "قيم", "believe"],
        "cultural_identity": ["culture", "文化", "ثقافة", "heritage"],
        "career_identity": ["career", "job", "work", "职业", "مهنة"],
        "spiritual_seeking": ["spiritual", "meaning", "灵性", "روحاني"],
        "life_purpose": ["purpose", "meaning", "目的", "هدف"],
        "relationship_style": ["relationship", "love", "关系", "علاقة"],
    }
    for signal, keywords in signal_keywords.items():
        if any(kw in text_lower for kw in keywords):
            signals.append(signal)

    # Detector-based signals (compass integration)
    attachment = detector_results.attachment.get("style", "")
    if attachment in ("anxious", "avoidant", "fearful"):
        signals.append("attachment_understanding")

    values_data = detector_results.values.get("top_values", [])
    if "tradition" in values_data:
        signals.append("heritage_connection")

    return list(dict.fromkeys(signals))


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Score candidates based on identity signals."""
    signals = _detect_identity_signals(wish_text, detector_results)
    fragility = detector_results.fragility.get("pattern", "")
    is_fragile = fragility in ("defensive", "fragile", "avoidant")

    candidates: list[dict] = []
    for item in IDENTITY_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        if item["category"] in signals:
            score_boost += 0.30

        if is_fragile and item["difficulty"] == "gentle":
            score_boost += 0.10
        elif is_fragile and item["difficulty"] == "bold":
            score_boost -= 0.15

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_reason(item, signals)
        candidates.append(item_copy)

    return candidates


def _build_reason(item: dict, signals: list[str]) -> str:
    """Build relevance reason."""
    if item["category"] in signals:
        return f"Matches your identity signal: {item['category'].replace('_', ' ')}"
    return f"Explore your {item['category'].replace('_', ' ')}"


class IdentityExplorationFulfiller(L2Fulfiller):
    """L2 fulfiller for identity exploration wishes — compass-integrated.

    15-entry curated catalog. Supports hidden identity signals. Zero LLM.
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
                text="Did you explore a piece of your identity today?",
                delay_hours=48,
            ),
        )
