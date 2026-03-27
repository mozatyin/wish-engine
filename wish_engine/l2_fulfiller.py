"""L2 Fulfiller — local-compute recommendation engine with personality filtering.

Routes L2 wishes to domain-specific fulfillers. Each fulfiller has a curated
knowledge base and applies personality-based filtering. Zero LLM.

8 fulfillment types:
  a) Place search (parks, cafes, meditation centers, gyms)
  b) Book recommendation (values + MBTI matching)
  c) Course recommendation (cognitive style matching)
  d) Career direction (values + MBTI career mapping)
  e) Wellness recommendation (emotion + fragility matching)
  f) Safe route / safe space (time + gender + personality safety)
  g) Deals / discounts (values → deal preference mapping)
  h) Prayer times (astronomical local computation)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
    WishLevel,
    WishType,
)


class PersonalityFilter:
    """Applies personality-based filtering and scoring to recommendation candidates.

    Hard filters (exclude):
      - MBTI I + introversion > 0.6 -> exclude noisy/crowded
      - emotion anxiety > 0.5 -> exclude high-stimulation
      - fragility defensive -> exclude confrontational

    Soft filters (score boost):
      - values tradition -> boost traditional
      - values self-direction -> boost autonomous
      - attachment anxious -> boost calming/structured
      - MBTI N -> boost theory-heavy
      - MBTI S -> boost practical/hands-on
    """

    def __init__(self, detector_results: DetectorResults):
        self._det = detector_results

    @property
    def _is_introvert(self) -> bool:
        mbti = self._det.mbti
        if not mbti.get("type"):
            return False
        ei = mbti.get("dimensions", {}).get("E_I", 0.5)
        return ei < 0.4

    @property
    def _anxiety_level(self) -> float:
        return self._det.emotion.get("emotions", {}).get("anxiety", 0.0)

    @property
    def _fragility_pattern(self) -> str:
        return self._det.fragility.get("pattern", "")

    @property
    def _top_values(self) -> list[str]:
        return self._det.values.get("top_values", [])

    @property
    def _mbti_type(self) -> str:
        return self._det.mbti.get("type", "")

    @property
    def _attachment_style(self) -> str:
        return self._det.attachment.get("style", "")

    def apply(self, candidates: list[dict]) -> list[dict]:
        """Apply hard exclusion filters. Returns surviving candidates."""
        result = []
        for c in candidates:
            if self._is_introvert and c.get("noise") == "loud" and c.get("social") == "high":
                continue
            if self._anxiety_level > 0.5 and c.get("mood") == "intense":
                continue
            if self._fragility_pattern == "defensive" and c.get("mood") == "confrontational":
                continue
            result.append(c)
        return result

    def score(self, candidates: list[dict]) -> list[dict]:
        """Add _personality_score to each candidate based on trait alignment."""
        for c in candidates:
            s = 0.5
            tags = set(c.get("tags", []))

            # Value-based boosts
            if "tradition" in self._top_values and "traditional" in tags:
                s += 0.15
            if "self-direction" in self._top_values and ("self-paced" in tags or "autonomous" in tags):
                s += 0.15
            if "benevolence" in self._top_values and "helping" in tags:
                s += 0.10

            # MBTI-based boosts
            if len(self._mbti_type) == 4:
                if self._mbti_type[1] == "N" and "theory" in tags:
                    s += 0.10
                if self._mbti_type[1] == "S" and "practical" in tags:
                    s += 0.10
                if self._mbti_type[0] == "I" and "quiet" in tags:
                    s += 0.10
                if self._mbti_type[0] == "E" and "social" in tags:
                    s += 0.10

            # Attachment-based boosts
            if self._attachment_style == "anxious" and "calming" in tags:
                s += 0.10

            # Emotion-based boosts
            if self._anxiety_level > 0.5 and "calming" in tags:
                s += 0.10

            c["_personality_score"] = min(s, 1.0)
        return candidates

    def filter_and_rank(self, candidates: list[dict], max_results: int = 3) -> list[dict]:
        """Apply hard filter, score, sort descending, return top N."""
        filtered = self.apply(candidates)
        scored = self.score(filtered)
        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        return scored[:max_results]


class L2Fulfiller(ABC):
    """Base class for L2 domain-specific fulfillers."""

    @abstractmethod
    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        ...

    def _build_recommendations(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list[Recommendation]:
        """Filter, score, and convert candidates to Recommendation models."""
        pf = PersonalityFilter(detector_results)
        ranked = pf.filter_and_rank(candidates, max_results=max_results)
        return [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "Matches your profile"),
                score=c.get("_personality_score", 0.5),
                action_url=c.get("action_url"),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]


def _get_fulfiller(wish_type: WishType, wish_text: str = "") -> L2Fulfiller:
    """Get the fulfiller instance for a wish type.

    Lazy imports to avoid circular dependencies and allow incremental
    development of domain fulfillers.
    """
    from wish_engine.l2_places import PlaceFulfiller
    from wish_engine.l2_books import BookFulfiller
    from wish_engine.l2_courses import CourseFulfiller
    from wish_engine.l2_career import CareerFulfiller
    from wish_engine.l2_wellness import WellnessFulfiller
    from wish_engine.l2_events import EventFulfiller
    from wish_engine.l2_food import FoodFulfiller
    from wish_engine.l2_music import MusicFulfiller
    from wish_engine.l2_safety import SafeRouteFulfiller
    from wish_engine.l2_deals import DealsFulfiller
    from wish_engine.l2_interest_circles import InterestCircleFulfiller
    from wish_engine.l2_safe_spaces import SafeSpaceFulfiller
    from wish_engine.l2_mentor_enhanced import MentorFulfiller
    from wish_engine.l2_progress_groups import ProgressGroupFulfiller
    from wish_engine.l2_emotion_weather import EmotionWeatherFulfiller
    from wish_engine.l2_virtual_companion import VirtualCompanionFulfiller

    text_lower = wish_text.lower()

    # Check for prayer keywords (cross-cuts multiple wish types)
    prayer_keywords = {
        "祈祷", "prayer", "صلاة", "mosque", "مسجد", "清真寺",
        "fajr", "dhuhr", "asr", "maghrib", "isha",
    }
    if any(kw in text_lower for kw in prayer_keywords):
        return PlaceFulfiller()  # Routes to place search with mosque focus

    # Check for emotion weather keywords (before safety to avoid "mood" clash)
    emotion_weather_keywords = {
        "情绪天气", "mood", "atmosphere", "氛围", "مزاج",
        "vibe", "emotion weather",
    }
    if any(kw in text_lower for kw in emotion_weather_keywords):
        return EmotionWeatherFulfiller()

    # Check for safe space keywords (before safety route)
    safe_space_keywords = {
        "safe space", "inclusive", "friendly", "welcoming", "آمن",
        "包容", "无障碍", "accessible",
    }
    if any(kw in text_lower for kw in safe_space_keywords):
        return SafeSpaceFulfiller()

    # Check for safety keywords (cross-cuts multiple wish types)
    safety_keywords = {
        "安全", "回家", "safe", "night", "late", "晚上", "dark",
        "scared", "害怕", "خوف", "أمان",
    }
    if any(kw in text_lower for kw in safety_keywords):
        return SafeRouteFulfiller()

    # Check for virtual companion keywords
    companion_keywords = {
        "陪伴", "companion", "陪我", "虚拟", "مرافق",
        "buddy", "陪",
    }
    if any(kw in text_lower for kw in companion_keywords):
        return VirtualCompanionFulfiller()

    # Check for mentor keywords
    mentor_keywords = {
        "导师", "mentor", "前辈", "指导", "مرشد", "guidance", "coach",
    }
    if any(kw in text_lower for kw in mentor_keywords):
        return MentorFulfiller()

    # Check for interest circle keywords
    interest_keywords = {
        "兴趣", "hobby", "爱好", "circle", "圈子", "同好", "هواية",
    }
    if any(kw in text_lower for kw in interest_keywords):
        return InterestCircleFulfiller()

    # Check for progress group keywords
    progress_keywords = {
        "打卡", "accountability", "互助", "challenge",
    }
    if any(kw in text_lower for kw in progress_keywords):
        return ProgressGroupFulfiller()

    # Check for deals keywords (cross-cuts multiple wish types)
    deals_keywords = {
        "折扣", "优惠", "deal", "discount", "省钱", "便宜", "sale",
        "تخفيض", "خصم", "coupon", "promo",
    }
    if any(kw in text_lower for kw in deals_keywords):
        return DealsFulfiller()

    # Check for food keywords (cross-cuts multiple wish types)
    food_keywords = {
        "吃饭", "餐厅", "美食", "comfort food", "hungry", "مطعم",
        "restaurant", "dinner", "lunch", "breakfast", "brunch",
        "甜点", "火锅", "烧烤", "halal", "حلال", "清真",
    }
    if any(kw in text_lower for kw in food_keywords):
        return FoodFulfiller()

    # Check for music keywords (cross-cuts multiple wish types)
    music_keywords = {
        "音乐", "歌", "playlist", "听", "Spotify", "spotify",
        "موسيقى", "music", "song", "songs",
    }
    if any(kw in text_lower for kw in music_keywords):
        return MusicFulfiller()

    # Check for event keywords (cross-cuts multiple wish types)
    event_keywords = {
        "演出", "表演", "concert", "exhibition", "展览", "市集", "festival",
        "comedy", "opera", "ballet", "theater", "theatre", "话剧", "歌剧",
        "meetup", "聚会", "workshop", "工作坊", "film", "电影", "volunteer",
        "志愿者",
    }
    if any(kw in text_lower for kw in event_keywords):
        return EventFulfiller()

    _FULFILLER_MAP: dict[WishType, L2Fulfiller] = {
        WishType.FIND_PLACE: PlaceFulfiller(),
        WishType.FIND_RESOURCE: BookFulfiller(),
        WishType.LEARN_SKILL: CourseFulfiller(),
        WishType.CAREER_DIRECTION: CareerFulfiller(),
        WishType.HEALTH_WELLNESS: WellnessFulfiller(),
    }
    fulfiller = _FULFILLER_MAP.get(wish_type)
    if not fulfiller:
        raise ValueError(f"No L2 fulfiller for wish type: {wish_type}")
    return fulfiller


def fulfill_l2(
    wish: ClassifiedWish,
    detector_results: DetectorResults,
) -> L2FulfillmentResult:
    """Route an L2 wish to the appropriate fulfiller and return recommendations.

    Zero LLM — all local-compute with curated knowledge bases.
    """
    if wish.level != WishLevel.L2:
        raise ValueError(f"L2Fulfiller only handles L2 wishes, got {wish.level}")

    fulfiller = _get_fulfiller(wish.wish_type, wish_text=wish.wish_text)
    return fulfiller.fulfill(wish, detector_results)
