"""RainyDayFulfiller — local-compute rainy day activity recommendation.

12-entry curated catalog of indoor/rainy-day activities. Zero LLM.
Weather-triggered: best suited when raining. Keyword matching
(English/Chinese/Arabic) routes wish text to relevant categories,
then PersonalityFilter scores and ranks candidates.

Tags: indoor/cozy/creative/fitness/learning.
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

# ── Rainy Day Catalog (12 entries) ────────────────────────────────────────────

RAINY_DAY_CATALOG: list[dict] = [
    {
        "title": "Cozy Cafe",
        "description": "Watch the rain through the window with a warm drink and soft music.",
        "category": "cozy_cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "cozy", "quiet", "calming", "cafe"],
    },
    {
        "title": "Indoor Museum",
        "description": "Explore art, history, or science — rainy days make museums magical.",
        "category": "indoor_museum",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["indoor", "quiet", "calming", "learning", "self-paced"],
    },
    {
        "title": "Bookshop Browse",
        "description": "Wander through shelves of books — the perfect rainy day ritual.",
        "category": "bookshop_browse",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "quiet", "calming", "self-paced", "cozy"],
    },
    {
        "title": "Cooking at Home",
        "description": "Try a new recipe while rain taps the window — comfort food weather.",
        "category": "cooking_at_home",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "cozy", "calming", "self-paced", "practical"],
    },
    {
        "title": "Movie Marathon",
        "description": "Blankets, snacks, and a film series — the classic rainy day plan.",
        "category": "movie_marathon",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "cozy", "calming", "entertainment", "self-paced"],
    },
    {
        "title": "Board Game Session",
        "description": "Gather friends for tabletop games — strategy, laughs, and competition.",
        "category": "board_game",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["indoor", "social", "calming", "entertainment", "structured"],
    },
    {
        "title": "Indoor Climbing",
        "description": "Channel rainy-day energy into bouldering walls — fun and physical.",
        "category": "indoor_climbing",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["indoor", "fitness", "calming", "self-paced", "practical"],
    },
    {
        "title": "Spa Day",
        "description": "Rain outside, warmth inside — a full spa day is the ultimate treat.",
        "category": "spa_day",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "quiet", "calming", "self-paced", "cozy"],
    },
    {
        "title": "Art Studio Session",
        "description": "Paint, sketch, or sculpt — let the rain be your creative soundtrack.",
        "category": "art_studio",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "creative", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Music Practice",
        "description": "Pick up an instrument and play — rain creates the perfect ambiance.",
        "category": "music_practice",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "creative", "calming", "self-paced", "cozy"],
    },
    {
        "title": "Online Course",
        "description": "Learn something new from home — rainy days are for growing your mind.",
        "category": "online_course",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "learning", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Rainy Window Seat",
        "description": "Find a window seat and just watch the rain — sometimes that is enough.",
        "category": "rainy_window_seat",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indoor", "cozy", "quiet", "calming", "self-paced"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

RAINY_DAY_KEYWORDS: set[str] = {
    "下雨", "rainy", "rain", "雨天", "مطر", "indoor",
    "雨", "raining", "wet weather", "室内", "داخلي",
    "stay in", "宅", "cozy",
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "cozy_cafe": ["cafe", "coffee", "咖啡", "قهوة"],
    "indoor_museum": ["museum", "博物馆", "متحف", "gallery"],
    "bookshop_browse": ["book", "书", "كتاب", "bookshop"],
    "cooking_at_home": ["cook", "recipe", "做饭", "طبخ"],
    "movie_marathon": ["movie", "film", "电影", "فيلم"],
    "board_game": ["board game", "桌游", "لعبة", "game"],
    "indoor_climbing": ["climb", "boulder", "攀岩", "تسلق"],
    "spa_day": ["spa", "massage", "水疗", "سبا"],
    "art_studio": ["art", "paint", "画", "فن"],
    "music_practice": ["music", "instrument", "音乐", "موسيقى"],
    "online_course": ["course", "learn", "课程", "دورة"],
    "rainy_window_seat": ["window", "rain", "窗", "نافذة"],
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
    is_raining: bool = True,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    for item in RAINY_DAY_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Weather-triggered boost
        if is_raining:
            score_boost += 0.1

        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.2

        # Cozy preference boost
        if any(kw in text_lower for kw in ["cozy", "温暖", "warm", "舒适", "دافئ"]):
            if "cozy" in item.get("tags", []):
                score_boost += 0.15

        # Creative preference boost
        if any(kw in text_lower for kw in ["creative", "创作", "create", "إبداع"]):
            if "creative" in item.get("tags", []):
                score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item, is_raining)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict, is_raining: bool) -> str:
    """Build a relevance reason for rainy day recommendations."""
    weather_prefix = "Perfect for today's rain — " if is_raining else ""
    reasons = {
        "cozy_cafe": f"{weather_prefix}Warm drinks and rain-watching",
        "indoor_museum": f"{weather_prefix}Rainy days make museums magical",
        "bookshop_browse": f"{weather_prefix}Books and rain belong together",
        "cooking_at_home": f"{weather_prefix}Comfort food weather",
        "movie_marathon": f"{weather_prefix}The classic rainy day plan",
        "board_game": f"{weather_prefix}Gather friends for tabletop fun",
        "indoor_climbing": f"{weather_prefix}Channel that energy indoors",
        "spa_day": f"{weather_prefix}Rain outside, warmth inside",
        "art_studio": f"{weather_prefix}Let the rain be your muse",
        "music_practice": f"{weather_prefix}Rain creates the perfect ambiance",
        "online_course": f"{weather_prefix}Grow your mind from home",
        "rainy_window_seat": f"{weather_prefix}Sometimes just watching is enough",
    }
    return reasons.get(item["category"], "A great rainy day activity")


class RainyDayFulfiller(L2Fulfiller):
    """L2 fulfiller for rainy day activity wishes.

    12-entry curated catalog. Weather-triggered: only when raining.
    Tags: indoor/cozy/creative/fitness/learning. Zero LLM.
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
                relevance_reason=c.get("relevance_reason", "A great rainy day activity"),
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
        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Rain check — save this for the next rainy day!",
                delay_hours=24,
            ),
        )
