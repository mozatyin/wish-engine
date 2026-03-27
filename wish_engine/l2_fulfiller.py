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
    from wish_engine.l2_medical import MedicalFulfiller
    from wish_engine.l2_pet_friendly import PetFriendlyFulfiller
    from wish_engine.l2_ev_charging import EVChargingFulfiller
    from wish_engine.l2_services import LocalServiceFulfiller
    from wish_engine.l2_parking import ParkingFulfiller
    from wish_engine.l2_late_night import LateNightFulfiller
    from wish_engine.l2_hometown_food import HometownFoodFulfiller
    from wish_engine.l2_coworking import CoworkingFulfiller
    from wish_engine.l2_secondhand import SecondhandFulfiller
    from wish_engine.l2_free_activities import FreeActivityFulfiller
    from wish_engine.l2_finance import FinanceFulfiller
    from wish_engine.l2_housing import HousingFulfiller
    from wish_engine.l2_habit_tracker import HabitTrackerFulfiller
    from wish_engine.l2_skill_exchange import SkillExchangeFulfiller
    from wish_engine.l2_micro_challenge import MicroChallengeFulfiller
    from wish_engine.l2_mindfulness import MindfulnessFulfiller
    from wish_engine.l2_writing import WritingFulfiller
    from wish_engine.l2_podcast import PodcastFulfiller
    from wish_engine.l2_course_tracker import CourseTrackerFulfiller
    from wish_engine.l2_health_sync import HealthSyncFulfiller
    from wish_engine.l2_focus_mode import FocusModeFulfiller
    from wish_engine.l2_bucket_list import BucketListFulfiller

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

    # Check for hometown food keywords (before generic food)
    hometown_food_keywords = {
        "家乡", "hometown", "正宗", "authentic", "家的味道",
        "بلدي", "وطني",
    }
    if any(kw in text_lower for kw in hometown_food_keywords):
        return HometownFoodFulfiller()

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

    # Check for medical keywords
    medical_keywords = {
        "医院", "doctor", "clinic", "医生", "看病", "طبيب", "مستشفى",
        "pharmacy", "药", "hospital", "dental", "dentist",
    }
    if any(kw in text_lower for kw in medical_keywords):
        return MedicalFulfiller()

    # Check for pet-friendly keywords
    pet_keywords = {
        "宠物", "pet", "dog", "cat", "狗", "猫", "حيوان أليف",
    }
    if any(kw in text_lower for kw in pet_keywords):
        return PetFriendlyFulfiller()

    # Check for EV charging / gas keywords
    ev_keywords = {
        "充电", "charging", "加油", "gas", "电动", "شحن",
        "ev", "charger", "supercharger",
    }
    if any(kw in text_lower for kw in ev_keywords):
        return EVChargingFulfiller()

    # Check for local service keywords
    service_keywords = {
        "打印", "print", "快递", "courier", "寄存", "storage",
        "修", "repair", "洗衣", "laundry",
    }
    if any(kw in text_lower for kw in service_keywords):
        return LocalServiceFulfiller()

    # Check for parking keywords
    parking_keywords = {
        "停车", "parking", "park my car", "泊车", "موقف",
    }
    if any(kw in text_lower for kw in parking_keywords):
        return ParkingFulfiller()

    # Check for coworking keywords
    coworking_keywords = {
        "工作", "办公", "cowork", "workspace", "cafe", "写代码", "办公空间",
    }
    if any(kw in text_lower for kw in coworking_keywords):
        return CoworkingFulfiller()

    # Check for secondhand keywords
    secondhand_keywords = {
        "二手", "闲置", "exchange", "swap", "旧物", "secondhand", "مستعمل",
    }
    if any(kw in text_lower for kw in secondhand_keywords):
        return SecondhandFulfiller()

    # Check for free activity keywords
    free_activity_keywords = {
        "免费", "free", "低价", "budget", "مجاني", "no cost",
    }
    if any(kw in text_lower for kw in free_activity_keywords):
        return FreeActivityFulfiller()

    # Check for finance keywords
    finance_keywords = {
        "理财", "finance", "money", "投资", "存钱", "مال",
    }
    if any(kw in text_lower for kw in finance_keywords):
        return FinanceFulfiller()

    # Check for housing keywords
    housing_keywords = {
        "租房", "housing", "合租", "roommate", "neighborhood", "搬家", "سكن",
    }
    if any(kw in text_lower for kw in housing_keywords):
        return HousingFulfiller()

    # Check for late-night / 24h keywords
    late_night_keywords = {
        "药店", "24小时", "24h", "便利店", "convenience",
        "late night", "半夜", "صيدلية", "深夜", "凌晨",
    }
    if any(kw in text_lower for kw in late_night_keywords):
        return LateNightFulfiller()

    # Check for habit tracker keywords
    habit_keywords = {
        "习惯", "habit", "打卡", "track", "追踪", "عادة",
    }
    if any(kw in text_lower for kw in habit_keywords):
        return HabitTrackerFulfiller()

    # Check for skill exchange keywords
    skill_exchange_keywords = {
        "技能交换", "skill exchange", "互换", "teach me", "swap skills", "تبادل",
    }
    if any(kw in text_lower for kw in skill_exchange_keywords):
        return SkillExchangeFulfiller()

    # Check for micro-challenge keywords
    challenge_keywords = {
        "挑战", "challenge", "试试", "dare", "تحدي", "push myself",
    }
    if any(kw in text_lower for kw in challenge_keywords):
        return MicroChallengeFulfiller()

    # Check for mindfulness/meditation keywords
    mindfulness_keywords = {
        "冥想", "正念", "mindfulness", "meditation", "静心", "تأمل", "calm",
    }
    if any(kw in text_lower for kw in mindfulness_keywords):
        return MindfulnessFulfiller()

    # Check for writing/journal keywords
    writing_keywords = {
        "写", "write", "日记", "journal", "diary", "记录", "كتابة",
    }
    if any(kw in text_lower for kw in writing_keywords):
        return WritingFulfiller()

    # Check for podcast/audiobook keywords
    podcast_keywords = {
        "播客", "podcast", "有声书", "audiobook", "听", "listen", "بودكاست",
    }
    if any(kw in text_lower for kw in podcast_keywords):
        return PodcastFulfiller()

    # Check for course tracker keywords
    course_tracker_keywords = {
        "课程进度", "course", "学习进度", "progress", "完成", "continue",
    }
    if any(kw in text_lower for kw in course_tracker_keywords):
        return CourseTrackerFulfiller()

    # Check for health sync keywords
    health_sync_keywords = {
        "健康", "health", "sleep", "步数", "steps", "心率", "heartrate", "صحة",
    }
    if any(kw in text_lower for kw in health_sync_keywords):
        return HealthSyncFulfiller()

    # Check for focus mode keywords
    focus_keywords = {
        "专注", "focus", "集中", "deep work", "productivity", "تركيز",
    }
    if any(kw in text_lower for kw in focus_keywords):
        return FocusModeFulfiller()

    # Check for bucket list keywords
    bucket_list_keywords = {
        "清单", "bucket list", "想做的事", "life list", "实验", "try", "قائمة أمنيات",
    }
    if any(kw in text_lower for kw in bucket_list_keywords):
        return BucketListFulfiller()

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
