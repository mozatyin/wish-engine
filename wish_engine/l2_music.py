"""MusicFulfiller — local-compute music recommendation with emotion-to-genre mapping.

20-entry curated catalog of mood-genre combinations. Core innovation: emotion -> music
mapping (anxiety -> calming acoustic, sadness -> gentle uplifting, anger -> release rock).
Personality filtering via MBTI and cultural preferences.
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

# ── Music Catalog (20 entries) ───────────────────────────────────────────────

MUSIC_CATALOG: list[dict] = [
    # ── Calming / Anxiety Relief (4) ─────────────────────────────────────────
    {
        "title": "Calming Acoustic",
        "description": "Gentle guitar and piano for anxious moments — breathe and let go.",
        "category": "playlist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "acoustic", "quiet", "anxiety-relief", "self-paced"],
        "emotion_match": ["anxiety"],
        "genres": ["acoustic", "singer-songwriter"],
        "valence": 0.3,
        "energy": 0.2,
    },
    {
        "title": "Ambient Soundscapes",
        "description": "Ethereal ambient textures — perfect background for meditation or deep focus.",
        "category": "playlist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "ambient", "quiet", "meditation", "focus", "self-paced"],
        "emotion_match": ["anxiety"],
        "genres": ["ambient", "new-age"],
        "valence": 0.3,
        "energy": 0.1,
    },
    {
        "title": "Lo-Fi Beats to Relax",
        "description": "Chill lo-fi hip-hop beats — calming without silence.",
        "category": "playlist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "lo-fi", "quiet", "focus", "self-paced"],
        "emotion_match": ["anxiety", "fatigue"],
        "genres": ["chill", "study"],
        "valence": 0.4,
        "energy": 0.3,
    },
    {
        "title": "Classical Piano Meditation",
        "description": "Chopin, Debussy, Satie — timeless piano for inner peace.",
        "category": "playlist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "classical", "piano", "quiet", "traditional", "self-paced"],
        "emotion_match": ["anxiety", "sadness"],
        "genres": ["classical", "piano"],
        "valence": 0.3,
        "energy": 0.15,
    },
    # ── Gentle Uplifting / Sadness (3) ───────────────────────────────────────
    {
        "title": "Indie Folk Comfort",
        "description": "Warm indie folk melodies that acknowledge sadness and gently lift you up.",
        "category": "playlist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["uplifting", "indie", "folk", "quiet", "gentle", "self-paced"],
        "emotion_match": ["sadness"],
        "genres": ["indie-folk", "folk"],
        "valence": 0.45,
        "energy": 0.3,
    },
    {
        "title": "Soft Pop Sunshine",
        "description": "Light, breezy pop songs — like sunshine after rain.",
        "category": "playlist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["uplifting", "pop", "gentle", "quiet", "soft"],
        "emotion_match": ["sadness"],
        "genres": ["pop", "indie-pop"],
        "valence": 0.55,
        "energy": 0.4,
    },
    {
        "title": "Piano Ballads",
        "description": "Beautiful piano-driven ballads — feel your feelings, then find hope.",
        "category": "playlist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["uplifting", "piano", "quiet", "emotional", "gentle", "self-paced"],
        "emotion_match": ["sadness"],
        "genres": ["piano", "singer-songwriter"],
        "valence": 0.35,
        "energy": 0.2,
    },
    # ── Release / Anger (3) ──────────────────────────────────────────────────
    {
        "title": "Rock Catharsis",
        "description": "Raw guitar riffs and pounding drums — channel your anger into sound.",
        "category": "playlist",
        "noise": "loud",
        "social": "low",
        "mood": "intense",
        "tags": ["release", "rock", "intense", "loud", "cathartic"],
        "emotion_match": ["anger"],
        "genres": ["rock", "alternative"],
        "valence": 0.4,
        "energy": 0.9,
    },
    {
        "title": "Metal & Heavy",
        "description": "Thunderous metal for when you need maximum intensity.",
        "category": "playlist",
        "noise": "loud",
        "social": "low",
        "mood": "intense",
        "tags": ["release", "metal", "intense", "loud", "cathartic"],
        "emotion_match": ["anger"],
        "genres": ["metal", "hard-rock"],
        "valence": 0.3,
        "energy": 0.95,
    },
    {
        "title": "Intense Electronic",
        "description": "Driving synths and heavy bass — electronic rage fuel.",
        "category": "playlist",
        "noise": "loud",
        "social": "low",
        "mood": "intense",
        "tags": ["release", "electronic", "intense", "loud", "cathartic"],
        "emotion_match": ["anger"],
        "genres": ["electronic", "dubstep"],
        "valence": 0.35,
        "energy": 0.9,
    },
    # ── Upbeat / Joy (3) ─────────────────────────────────────────────────────
    {
        "title": "Feel-Good Pop Hits",
        "description": "The happiest pop songs ever made — instant smile guaranteed.",
        "category": "playlist",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["upbeat", "pop", "happy", "dance", "social", "fun"],
        "emotion_match": ["joy"],
        "genres": ["pop", "dance"],
        "valence": 0.9,
        "energy": 0.75,
    },
    {
        "title": "Funk & Groove",
        "description": "Irresistible grooves and bass lines — impossible not to move.",
        "category": "playlist",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["upbeat", "funk", "groove", "social", "fun", "dance"],
        "emotion_match": ["joy"],
        "genres": ["funk", "disco"],
        "valence": 0.85,
        "energy": 0.8,
    },
    {
        "title": "Dance Party Mix",
        "description": "High-energy dance tracks for maximum celebration.",
        "category": "playlist",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["upbeat", "dance", "electronic", "party", "social", "loud"],
        "emotion_match": ["joy"],
        "genres": ["dance", "electronic"],
        "valence": 0.9,
        "energy": 0.9,
    },
    # ── Warm Connection / Loneliness (3) ─────────────────────────────────────
    {
        "title": "Soul & R&B Warmth",
        "description": "Rich vocals and warm harmonies — like being held by music.",
        "category": "playlist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["warm", "soul", "rnb", "quiet", "emotional", "calming"],
        "emotion_match": ["loneliness"],
        "genres": ["soul", "r-n-b"],
        "valence": 0.5,
        "energy": 0.4,
    },
    {
        "title": "Singer-Songwriter Stories",
        "description": "Intimate vocals and honest lyrics — you are not alone in what you feel.",
        "category": "playlist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["warm", "singer-songwriter", "quiet", "emotional", "calming", "self-paced"],
        "emotion_match": ["loneliness"],
        "genres": ["singer-songwriter", "folk"],
        "valence": 0.4,
        "energy": 0.3,
    },
    {
        "title": "Jazz for Quiet Evenings",
        "description": "Smooth jazz piano and saxophone — gentle company for lonely nights.",
        "category": "playlist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["warm", "jazz", "quiet", "calming", "traditional", "self-paced"],
        "emotion_match": ["loneliness"],
        "genres": ["jazz"],
        "valence": 0.45,
        "energy": 0.3,
    },
    # ── Energizing / Fatigue (4) ─────────────────────────────────────────────
    {
        "title": "Morning Energy Electronic",
        "description": "Bright electronic beats to jumpstart your day.",
        "category": "playlist",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["energizing", "electronic", "upbeat", "morning"],
        "emotion_match": ["fatigue"],
        "genres": ["electronic", "house"],
        "valence": 0.7,
        "energy": 0.75,
    },
    {
        "title": "Hip-Hop Motivation",
        "description": "Confident beats and empowering lyrics — get up and go.",
        "category": "playlist",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["energizing", "hip-hop", "upbeat", "motivation"],
        "emotion_match": ["fatigue"],
        "genres": ["hip-hop"],
        "valence": 0.65,
        "energy": 0.7,
    },
    {
        "title": "Upbeat Pop Energy",
        "description": "High-energy pop anthems to power through your afternoon.",
        "category": "playlist",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["energizing", "pop", "upbeat", "social"],
        "emotion_match": ["fatigue", "joy"],
        "genres": ["pop"],
        "valence": 0.75,
        "energy": 0.8,
    },
    {
        "title": "Workout Power Mix",
        "description": "High BPM tracks for running, gym, or any physical activity.",
        "category": "playlist",
        "noise": "loud",
        "social": "low",
        "mood": "intense",
        "tags": ["energizing", "workout", "intense", "loud", "fitness"],
        "emotion_match": ["fatigue"],
        "genres": ["electronic", "hip-hop"],
        "valence": 0.6,
        "energy": 0.95,
    },
]


# ── Keyword -> Emotion Mapping ───────────────────────────────────────────────

_MUSIC_KEYWORDS: dict[str, list[str]] = {
    # General music keywords (broad match)
    "音乐": [],
    "歌": [],
    "playlist": [],
    "听": [],
    "Spotify": [],
    "موسيقى": [],
    "music": [],
    "song": [],
    "songs": [],
    # Emotion-linked keywords
    "calm": ["anxiety"],
    "calming": ["anxiety"],
    "relax": ["anxiety"],
    "放松": ["anxiety"],
    "冥想": ["anxiety"],
    "meditation": ["anxiety"],
    "sad": ["sadness"],
    "伤心": ["sadness"],
    "难过": ["sadness"],
    "حزين": ["sadness"],
    "angry": ["anger"],
    "生气": ["anger"],
    "发泄": ["anger"],
    "غاضب": ["anger"],
    "rock": ["anger"],
    "摇滚": ["anger"],
    "happy": ["joy"],
    "开心": ["joy"],
    "dance": ["joy"],
    "party": ["joy"],
    "سعيد": ["joy"],
    "lonely": ["loneliness"],
    "孤独": ["loneliness"],
    "寂寞": ["loneliness"],
    "وحيد": ["loneliness"],
    "tired": ["fatigue"],
    "疲惫": ["fatigue"],
    "累": ["fatigue"],
    "energy": ["fatigue"],
    "تعب": ["fatigue"],
    "workout": ["fatigue"],
}

# ── Emotion -> music tag mapping ─────────────────────────────────────────────

_EMOTION_TO_MUSIC: dict[str, list[str]] = {
    "anxiety": ["calming", "quiet", "ambient"],
    "sadness": ["uplifting", "gentle", "soft"],
    "anger": ["release", "intense", "cathartic"],
    "joy": ["upbeat", "dance", "fun"],
    "loneliness": ["warm", "soul", "emotional"],
    "fatigue": ["energizing", "upbeat", "motivation"],
}


def _detect_emotions_from_text(wish_text: str) -> list[str]:
    """Detect emotion hints from wish keywords."""
    text_lower = wish_text.lower()
    emotions: list[str] = []
    for keyword, emo_list in _MUSIC_KEYWORDS.items():
        if keyword in text_lower and emo_list:
            for e in emo_list:
                if e not in emotions:
                    emotions.append(e)
    return emotions


def _get_dominant_emotion(detector_results: DetectorResults) -> str | None:
    """Get the user's dominant emotion from detector results."""
    emotions = detector_results.emotion.get("emotions", {})
    if not emotions:
        return None
    for emo in ["anxiety", "sadness", "anger", "loneliness", "fatigue", "joy"]:
        if emotions.get(emo, 0) > 0.4:
            return emo
    return None


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on emotion and keyword matching."""
    text_emotions = _detect_emotions_from_text(wish_text)

    dominant = _get_dominant_emotion(detector_results)
    if dominant and dominant not in text_emotions:
        text_emotions.append(dominant)

    candidates: list[dict] = []
    for item in MUSIC_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        if text_emotions:
            item_emotions = set(item.get("emotion_match", []))
            matched_emotions = set(text_emotions) & item_emotions
            if matched_emotions:
                score_boost += 0.2 * len(matched_emotions)
                item_copy["relevance_reason"] = _emotion_reason(list(matched_emotions)[0])
            else:
                score_boost -= 0.1

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    if not candidates:
        candidates = [dict(item) for item in MUSIC_CATALOG]

    return candidates


def _emotion_reason(emotion: str) -> str:
    """Build a relevance reason based on the matched emotion."""
    reasons = {
        "anxiety": "Calming sounds to ease your mind",
        "sadness": "Gentle melodies to lift your spirits",
        "anger": "Intense music for emotional release",
        "joy": "Upbeat tracks to match your energy",
        "loneliness": "Warm vocals that feel like company",
        "fatigue": "Energizing beats to recharge you",
    }
    return reasons.get(emotion, "Music matched to your current mood")


class MusicFulfiller(L2Fulfiller):
    """L2 fulfiller for music wishes — emotion-to-genre mapping.

    Uses emotion detection + personality filtering on a 20-entry curated catalog.
    Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
        """Filter, score with personality + emotion boost, convert to Recommendations."""
        from wish_engine.models import Recommendation

        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        # Add emotion boost on top of personality score
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
                relevance_reason=c.get("relevance_reason", "Matches your profile"),
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
        # 1. Match candidates
        candidates = _match_candidates(wish.wish_text, detector_results)

        # 2. Add default relevance reasons
        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = _build_music_relevance(c, detector_results)

        # 3. Build recommendations via personality filter with emotion boost
        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Listen to this playlist now?",
                delay_hours=2,
            ),
        )


def _build_music_relevance(item: dict, detector_results: DetectorResults) -> str:
    """Build a personalized relevance reason for music recommendations."""
    dominant = _get_dominant_emotion(detector_results)
    if dominant and dominant in item.get("emotion_match", []):
        return _emotion_reason(dominant)

    tags = set(item.get("tags", []))
    if "calming" in tags:
        return "Soothing music to help you unwind"
    if "upbeat" in tags:
        return "Energetic tunes to brighten your mood"
    if "warm" in tags:
        return "Warm, soulful music for the moment"
    if "release" in tags:
        return "Intense sounds for emotional expression"
    return "A great playlist recommendation for you"
