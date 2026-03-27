"""PodcastFulfiller — podcast/audiobook recommendation with emotion mapping.

20 genres with emotion-to-genre mapping. Commute-aware: short episodes for
quick commutes, long audiobooks for extended ones.
Multilingual keyword routing (EN/ZH/AR).
Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Podcast Catalog (20 entries) ─────────────────────────────────────────────

PODCAST_CATALOG: list[dict] = [
    {
        "title": "True Crime Deep Dive",
        "description": "Gripping investigative storytelling — mysteries that keep you hooked.",
        "category": "true_crime",
        "tags": ["storytelling", "theory", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "long",
        "emotion_match": ["curiosity"],
    },
    {
        "title": "Psychology Today",
        "description": "Understand the human mind — research-backed insights on behavior.",
        "category": "psychology",
        "tags": ["theory", "calming", "quiet", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": ["curiosity", "anxiety"],
    },
    {
        "title": "Business Builders",
        "description": "How companies are built — strategy, failures, and comebacks.",
        "category": "business",
        "tags": ["practical", "theory", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": [],
    },
    {
        "title": "Tech Frontiers",
        "description": "AI, space, biotech — the innovations shaping tomorrow.",
        "category": "technology",
        "tags": ["tech", "theory", "quiet", "energizing"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": ["curiosity"],
    },
    {
        "title": "Comedy Hour",
        "description": "Laugh out loud — stand-up, improv, and absurd conversations.",
        "category": "comedy",
        "tags": ["fun", "social", "energizing"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "low",
        "duration": "short",
        "emotion_match": ["sadness", "loneliness"],
    },
    {
        "title": "History Unlocked",
        "description": "The stories behind history — wars, revolutions, forgotten heroes.",
        "category": "history",
        "tags": ["storytelling", "theory", "quiet", "traditional"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "long",
        "emotion_match": ["curiosity"],
    },
    {
        "title": "Science Explained",
        "description": "Complex science made simple — from quantum physics to marine biology.",
        "category": "science",
        "tags": ["theory", "quiet", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": ["curiosity"],
    },
    {
        "title": "Philosophy for Life",
        "description": "Ancient wisdom for modern problems — Stoicism, existentialism, and more.",
        "category": "philosophy",
        "tags": ["theory", "quiet", "calming", "traditional"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": ["anxiety", "sadness"],
    },
    {
        "title": "Self-Help Essentials",
        "description": "Practical strategies for growth — habits, mindset, and resilience.",
        "category": "self_help",
        "tags": ["practical", "calming", "quiet", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": ["anxiety", "sadness"],
    },
    {
        "title": "Story Time",
        "description": "Fiction narrated beautifully — short stories and serial dramas.",
        "category": "storytelling",
        "tags": ["storytelling", "creative", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": ["loneliness", "sadness"],
    },
    {
        "title": "News Deep Analysis",
        "description": "Beyond headlines — thoughtful analysis of what's really happening.",
        "category": "news_analysis",
        "tags": ["practical", "theory", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "short",
        "emotion_match": [],
    },
    {
        "title": "Culture Compass",
        "description": "Music, film, food, fashion — the culture that shapes our world.",
        "category": "culture",
        "tags": ["cultural", "social", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": ["curiosity"],
    },
    {
        "title": "Language Lab",
        "description": "Learn a language through stories — immersive audio lessons.",
        "category": "language_learning",
        "tags": ["language", "self-paced", "quiet", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "short",
        "emotion_match": [],
    },
    {
        "title": "Calm Narratives",
        "description": "Soothing voices and gentle stories — perfect for winding down.",
        "category": "meditation_audio",
        "tags": ["calming", "quiet", "relaxation", "sleep"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "short",
        "emotion_match": ["anxiety", "fatigue"],
    },
    {
        "title": "Fiction Audiobook",
        "description": "Full-length novels read by talented narrators — worlds to lose yourself in.",
        "category": "fiction",
        "tags": ["storytelling", "creative", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "long",
        "emotion_match": ["loneliness"],
    },
    {
        "title": "Interview Masters",
        "description": "Long-form conversations with fascinating people — unscripted and deep.",
        "category": "interviews",
        "tags": ["social", "theory", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "long",
        "emotion_match": ["curiosity"],
    },
    {
        "title": "Economics Unpacked",
        "description": "How money, markets, and policy shape everyday life.",
        "category": "economics",
        "tags": ["theory", "practical", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": [],
    },
    {
        "title": "Art & Inspiration",
        "description": "Stories of artists, their struggles, and their masterpieces.",
        "category": "art",
        "tags": ["creative", "calming", "quiet", "cultural"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": ["sadness"],
    },
    {
        "title": "Sports Talk",
        "description": "Analysis, stories, and debates — for the fan who wants more.",
        "category": "sports",
        "tags": ["social", "energizing"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "low",
        "duration": "medium",
        "emotion_match": ["joy"],
    },
    {
        "title": "Music Discussion",
        "description": "Albums, artists, and genres explored — hear music differently.",
        "category": "music_discussion",
        "tags": ["music", "creative", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "duration": "medium",
        "emotion_match": ["sadness", "joy"],
    },
]

# Duration mapping
_DURATION_MINUTES = {"short": 15, "medium": 30, "long": 45}


def _get_dominant_emotion(detector_results: DetectorResults) -> str | None:
    """Get dominant emotion from detector results."""
    emotions = detector_results.emotion.get("emotions", {})
    if not emotions:
        return None
    for emo in ["anxiety", "sadness", "anger", "loneliness", "fatigue", "joy"]:
        if emotions.get(emo, 0) > 0.4:
            return emo
    return None


def _detect_commute_length(wish_text: str) -> str | None:
    """Detect commute length from wish text."""
    text_lower = wish_text.lower()
    if any(kw in text_lower for kw in ["short commute", "短", "quick", "15min"]):
        return "short"
    if any(kw in text_lower for kw in ["long commute", "长", "audiobook", "有声书", "45min"]):
        return "long"
    return None


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates based on emotion and commute matching."""
    dominant = _get_dominant_emotion(detector_results)
    commute = _detect_commute_length(wish_text)

    candidates: list[dict] = []
    for item in PODCAST_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Emotion matching
        if dominant and dominant in item.get("emotion_match", []):
            score_boost += 0.2
            item_copy["relevance_reason"] = _emotion_reason(dominant)

        # Commute-aware matching
        if commute and item.get("duration") == commute:
            score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


def _emotion_reason(emotion: str) -> str:
    """Build relevance reason for emotion."""
    reasons = {
        "anxiety": "Calming narratives to ease your mind",
        "sadness": "Uplifting content to brighten your mood",
        "anger": "Thought-provoking content for perspective",
        "loneliness": "Stories and voices for companionship",
        "fatigue": "Light, soothing audio to recharge",
        "joy": "Energizing content to ride the wave",
        "curiosity": "Feed your curious mind",
    }
    return reasons.get(emotion, "Matches your current mood")


class PodcastFulfiller(L2Fulfiller):
    """L2 fulfiller for podcast/audiobook wishes — emotion and commute-aware.

    20-entry curated catalog. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "A great listen for you"

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
            reminder_option=ReminderOption(
                text="Got your headphones? Time to listen.",
                delay_hours=8,
            ),
        )
