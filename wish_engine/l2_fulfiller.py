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
    from wish_engine.l2_travel import TravelFulfiller
    from wish_engine.l2_home_decor import HomeDecorFulfiller
    from wish_engine.l2_date_spots import DateSpotFulfiller
    from wish_engine.l2_breakup_healing import BreakupHealingFulfiller
    from wish_engine.l2_sleep_env import SleepEnvFulfiller
    from wish_engine.l2_panic_relief import PanicReliefFulfiller
    from wish_engine.l2_gift import GiftFulfiller
    from wish_engine.l2_solo_friendly import SoloFriendlyFulfiller
    from wish_engine.l2_deep_social import DeepSocialFulfiller
    from wish_engine.l2_startup_resources import StartupResourceFulfiller
    from wish_engine.l2_poetry import PoetryFulfiller
    from wish_engine.l2_crafts import CraftsFulfiller
    from wish_engine.l2_volunteer import VolunteerFulfiller
    from wish_engine.l2_nature_healing import NatureHealingFulfiller
    from wish_engine.l2_reviews import ReviewsFulfiller
    from wish_engine.l2_personality_growth import PersonalityGrowthFulfiller
    from wish_engine.l2_emotion_calendar import EmotionCalendarFulfiller
    from wish_engine.l2_dream_journal import DreamJournalFulfiller
    from wish_engine.l2_digital_detox import DigitalDetoxFulfiller
    from wish_engine.l2_personal_brand import PersonalBrandFulfiller
    from wish_engine.l2_public_speaking import PublicSpeakingFulfiller
    from wish_engine.l2_interview_prep import InterviewPrepFulfiller
    from wish_engine.l2_confidence import ConfidenceFulfiller
    from wish_engine.l2_eq_training import EQTrainingFulfiller
    from wish_engine.l2_identity_exploration import IdentityExplorationFulfiller
    from wish_engine.l2_kids_activities import KidsActivityFulfiller
    from wish_engine.l2_elderly_care import ElderlyCareFulfiller
    from wish_engine.l2_family_dining import FamilyDiningFulfiller
    from wish_engine.l2_wedding import WeddingFulfiller
    from wish_engine.l2_neighborhood import NeighborhoodFulfiller
    from wish_engine.l2_memory_map import MemoryMapFulfiller
    from wish_engine.l2_gratitude import GratitudeFulfiller
    from wish_engine.l2_moving import MovingFulfiller
    from wish_engine.l2_intergenerational import IntergenerationalFulfiller
    from wish_engine.l2_pet_training import PetTrainingFulfiller
    from wish_engine.l2_games import GameFulfiller
    from wish_engine.l2_photo_spots import PhotoSpotFulfiller
    from wish_engine.l2_seasonal_wellness import SeasonalWellnessFulfiller
    from wish_engine.l2_fashion import FashionFulfiller
    from wish_engine.l2_weekend_planner import WeekendPlannerFulfiller
    from wish_engine.l2_seasonal_activities import SeasonalActivityFulfiller
    from wish_engine.l2_birthday_planning import BirthdayPlannerFulfiller
    from wish_engine.l2_documentaries import DocumentaryFulfiller
    from wish_engine.l2_collecting import CollectingFulfiller
    from wish_engine.l2_astro_fun import AstroFunFulfiller
    from wish_engine.l2_accessibility import AccessibilityFulfiller
    from wish_engine.l2_allergy_friendly import AllergyFriendlyFulfiller
    from wish_engine.l2_noise_map import NoiseMapFulfiller
    from wish_engine.l2_air_quality import AirQualityFulfiller
    from wish_engine.l2_night_owl import NightOwlFulfiller
    from wish_engine.l2_early_bird import EarlyBirdFulfiller
    from wish_engine.l2_rainy_day import RainyDayFulfiller
    from wish_engine.l2_extreme_weather import ExtremeWeatherFulfiller
    from wish_engine.l2_pregnancy import PregnancyFulfiller
    from wish_engine.l2_life_stage import LifeStageFulfiller
    from wish_engine.l2_caregiver_respite import CaregiverRespiteFulfiller
    from wish_engine.l2_remote_care import RemoteCareFulfiller
    from wish_engine.l2_caregiver_support import CaregiverSupportFulfiller
    from wish_engine.l2_caregiver_emotional import CaregiverEmotionalFulfiller
    from wish_engine.l2_legal_aid import LegalAidFulfiller
    from wish_engine.l2_labor_rights import LaborRightsFulfiller
    from wish_engine.l2_tenant_rights import TenantRightsFulfiller
    from wish_engine.l2_immigration import ImmigrationFulfiller
    from wish_engine.l2_anti_discrimination import AntiDiscriminationFulfiller
    from wish_engine.l2_bereavement import BereavementFulfiller
    from wish_engine.l2_pregnancy_loss import PregnancyLossFulfiller
    from wish_engine.l2_pet_loss import PetLossFulfiller
    from wish_engine.l2_farewell_ritual import FarewellRitualFulfiller
    from wish_engine.l2_estate_items import EstateItemsFulfiller
    from wish_engine.l2_addiction_meetings import AddictionMeetingFulfiller
    from wish_engine.l2_trigger_alert import TriggerAlertFulfiller
    from wish_engine.l2_craving_alternatives import CravingAlternativeFulfiller
    from wish_engine.l2_sobriety_tracker import SobrietyTrackerFulfiller
    from wish_engine.l2_behavioral_addiction import BehavioralAddictionFulfiller
    from wish_engine.l2_suicide_prevention import SuicidePreventionFulfiller
    from wish_engine.l2_domestic_violence import DomesticViolenceFulfiller
    from wish_engine.l2_debt_crisis import DebtCrisisFulfiller
    from wish_engine.l2_emergency_shelter import EmergencyShelterFulfiller
    from wish_engine.l2_collective_trauma import CollectiveTraumaFulfiller
    from wish_engine.l2_chronic_illness import ChronicIllnessFulfiller
    from wish_engine.l2_chronic_pain import ChronicPainFulfiller
    from wish_engine.l2_eating_disorder import EatingDisorderFulfiller
    from wish_engine.l2_disability_social import DisabilitySocialFulfiller
    from wish_engine.l2_postpartum import PostpartumFulfiller
    from wish_engine.l2_cyberbullying import CyberbullyingFulfiller
    from wish_engine.l2_privacy_protection import PrivacyProtectionFulfiller
    from wish_engine.l2_child_safety_online import ChildSafetyOnlineFulfiller
    from wish_engine.l2_scam_detection import ScamDetectionFulfiller
    from wish_engine.l2_legacy_planning import LegacyPlanningFulfiller
    from wish_engine.l2_social_justice import SocialJusticeFulfiller
    from wish_engine.l2_environmental_action import EnvironmentalActionFulfiller
    from wish_engine.l2_oral_history import OralHistoryFulfiller
    from wish_engine.l2_roots_journey import RootsJourneyFulfiller
    from wish_engine.l2_mother_tongue import MotherTongueFulfiller
    from wish_engine.l2_cultural_recovery import CulturalRecoveryFulfiller

    text_lower = wish_text.lower()

    # ── CRISIS (highest priority — check first) ─────────────────────────────
    suicide_kw = {
        "自杀", "suicide", "不想活", "kill myself", "انتحار", "想死",
        "end my life", "结束生命", "活不下去", "self harm", "自残",
        "don't want to live", "want to die", "rather be dead",
        "can't go on", "end it all", "no reason to live",
        "not worth living", "take my own life",
    }
    if any(kw in text_lower for kw in suicide_kw):
        return SuicidePreventionFulfiller()

    dv_kw = {
        "家暴", "domestic violence", "abuse", "عنف أسري", "被打",
        "hurt me", "他打我", "她打我",
        "he hits me", "she hurts me", "scared of him", "scared of her",
        "violent partner", "被他打", "escape", "flee",
    }
    if any(kw in text_lower for kw in dv_kw):
        return DomesticViolenceFulfiller()

    emergency_shelter_kw = {
        "庇护", "emergency housing", "无家可归", "homeless", "مأوى",
        "nowhere to go", "没地方住", "流浪",
    }
    if any(kw in text_lower for kw in emergency_shelter_kw):
        return EmergencyShelterFulfiller()

    debt_crisis_kw = {
        "债务", "bankruptcy", "催收", "破产", "ديون", "欠钱", "还不起",
        "debt", "can't pay", "owe money", "collectors", "催债",
        "financial ruin", "bankrupt", "in debt",
    }
    if any(kw in text_lower for kw in debt_crisis_kw):
        return DebtCrisisFulfiller()

    collective_trauma_kw = {
        "灾后", "ptsd", "创伤后", "صدمة", "war trauma", "战争创伤",
        "mass shooting", "refugee trauma", "难民创伤",
        "trauma", "collective trauma", "survivor guilt",
    }
    if any(kw in text_lower for kw in collective_trauma_kw):
        return CollectiveTraumaFulfiller()

    # ── GRIEF ────────────────────────────────────────────────────────────────
    pregnancy_loss_kw = {
        "流产", "miscarriage", "stillbirth", "失去孩子", "إجهاض",
        "pregnancy loss", "baby loss", "死产", "nicu",
    }
    if any(kw in text_lower for kw in pregnancy_loss_kw):
        return PregnancyLossFulfiller()

    pet_loss_kw = {
        "宠物去世", "pet loss", "rainbow bridge", "失去宠物",
        "فقدان حيوان", "pet died", "dog died", "cat died",
        "lost my pet", "pet passed", "my dog passed", "my cat passed",
    }
    if any(kw in text_lower for kw in pet_loss_kw):
        return PetLossFulfiller()

    farewell_ritual_kw = {
        "告别仪式", "farewell ritual", "葬礼", "funeral", "جنازة",
        "janazah", "头七", "scattering ceremony", "memorial service",
    }
    if any(kw in text_lower for kw in farewell_ritual_kw):
        return FarewellRitualFulfiller()

    estate_items_kw = {
        "遗物", "estate items", "belongings of deceased", "تركة",
        "遗产整理", "sort belongings",
    }
    if any(kw in text_lower for kw in estate_items_kw):
        return EstateItemsFulfiller()

    bereavement_kw = {
        "丧亲", "bereavement", "فقدان", "mourning", "grief support",
        "loss of loved one", "grief", "grieving", "in mourning",
    }
    if any(kw in text_lower for kw in bereavement_kw):
        return BereavementFulfiller()

    # ── ADDICTION ─────────────────────────────────────────────────────────────
    craving_kw = {
        "渴望", "craving", "urge", "想喝", "想抽", "رغبة",
    }
    if any(kw in text_lower for kw in craving_kw):
        return CravingAlternativeFulfiller()

    sobriety_kw = {
        "清醒天数", "sober days", "sobriety", "days clean", "نظافة",
        "recovery track",
    }
    if any(kw in text_lower for kw in sobriety_kw):
        return SobrietyTrackerFulfiller()

    behavioral_addiction_kw = {
        "行为成瘾", "gaming addiction", "赌博", "gambling", "قمار",
        "shopping addiction", "购物成瘾", "phone addiction", "手机成瘾",
    }
    if any(kw in text_lower for kw in behavioral_addiction_kw):
        return BehavioralAddictionFulfiller()

    trigger_alert_kw = {
        "触发预警", "trigger alert", "avoid triggers", "تجنب",
        "temptation alert", "triggered", "tempt",
    }
    if any(kw in text_lower for kw in trigger_alert_kw):
        return TriggerAlertFulfiller()

    addiction_meeting_kw = {
        "戒瘾", "addiction meeting", "aa meeting", "na meeting",
        "إدمان", "戒酒", "戒毒", "recovery meeting",
        " aa ", "stop drinking", "sober", "rehab",
    }
    if any(kw in text_lower for kw in addiction_meeting_kw):
        return AddictionMeetingFulfiller()

    # Check for personality growth keywords
    growth_keywords = {
        "成长", "growth", "提升", "improve", "نمو", "develop",
    }
    if any(kw in text_lower for kw in growth_keywords):
        return PersonalityGrowthFulfiller()

    # Check for emotion calendar keywords
    emotion_calendar_keywords = {
        "情绪日历", "emotion", "mood", "calendar", "日历", "مزاج",
    }
    if any(kw in text_lower for kw in emotion_calendar_keywords):
        return EmotionCalendarFulfiller()

    # Check for dream journal keywords
    dream_keywords = {
        "梦", "dream", "حلم", "nightmare", "sleep", "梦境",
    }
    if any(kw in text_lower for kw in dream_keywords):
        return DreamJournalFulfiller()

    # Check for digital detox keywords
    detox_keywords = {
        "排毒", "detox", "屏幕", "screen time", "手机", "digital", "إزالة السموم",
    }
    if any(kw in text_lower for kw in detox_keywords):
        return DigitalDetoxFulfiller()

    # Check for personal brand keywords
    brand_keywords = {
        "品牌", "brand", "展示", "portfolio", "showcase", "作品集",
    }
    if any(kw in text_lower for kw in brand_keywords):
        return PersonalBrandFulfiller()

    # Check for public speaking keywords
    speaking_keywords = {
        "演讲", "speaking", "public", "speech", "خطاب", "talk",
    }
    if any(kw in text_lower for kw in speaking_keywords):
        return PublicSpeakingFulfiller()

    # Check for interview prep keywords
    interview_keywords = {
        "面试", "interview", "简历", "resume", "مقابلة", "job",
    }
    if any(kw in text_lower for kw in interview_keywords):
        return InterviewPrepFulfiller()

    # Check for confidence keywords
    confidence_keywords = {
        "自信", "confidence", "勇气", "courage", "ثقة", "brave",
    }
    if any(kw in text_lower for kw in confidence_keywords):
        return ConfidenceFulfiller()

    # Check for EQ training keywords
    eq_keywords = {
        "情商", "eq", "emotional intelligence", "同理心", "empathy", "ذكاء عاطفي",
    }
    if any(kw in text_lower for kw in eq_keywords):
        return EQTrainingFulfiller()

    # Check for identity exploration keywords
    identity_keywords = {
        "身份", "identity", "探索", "explore", "هوية", "who am i", "我是谁",
    }
    if any(kw in text_lower for kw in identity_keywords):
        return IdentityExplorationFulfiller()

    # Check for game/play keywords
    game_keywords = {
        "游戏", "game", "play", "桌游", "board game", "لعبة",
        "chess", "象棋", "mahjong", "麻将", "trivia", "escape room", "密室",
    }
    if any(kw in text_lower for kw in game_keywords):
        return GameFulfiller()

    # Check for photography keywords
    photo_keywords = {
        "拍照", "photo", "photography", "摄影", "تصوير", "instagram", "打卡",
    }
    if any(kw in text_lower for kw in photo_keywords):
        return PhotoSpotFulfiller()

    # Check for seasonal wellness keywords
    seasonal_wellness_keywords = {
        "节气", "二十四节气", "seasonal wellness", "养生", "فصل",
        "ramadan", "رمضان", "斋月", "monsoon", "dust storm", "沙尘暴",
    }
    if any(kw in text_lower for kw in seasonal_wellness_keywords):
        return SeasonalWellnessFulfiller()

    # Check for fashion/style keywords
    fashion_keywords = {
        "穿搭", "fashion", "style", "衣服", "clothing", "أزياء", "outfit",
    }
    if any(kw in text_lower for kw in fashion_keywords):
        return FashionFulfiller()

    # Check for weekend planner keywords
    weekend_keywords = {
        "周末", "weekend", "عطلة", "what to do",
    }
    if any(kw in text_lower for kw in weekend_keywords):
        return WeekendPlannerFulfiller()

    # Check for seasonal activity keywords
    seasonal_activity_keywords = {
        "当季", "seasonal", "spring", "summer", "autumn", "winter",
        "春", "夏", "秋", "冬", "cherry blossom", "樱花",
        "picnic", "野餐", "camping", "露营", "skating", "溜冰",
    }
    if any(kw in text_lower for kw in seasonal_activity_keywords):
        return SeasonalActivityFulfiller()

    # Check for birthday planning keywords
    birthday_keywords = {
        "生日", "birthday", "عيد ميلاد", "party", "派对", "celebrate", "庆祝",
    }
    if any(kw in text_lower for kw in birthday_keywords):
        return BirthdayPlannerFulfiller()

    # Check for documentary keywords
    documentary_keywords = {
        "纪录片", "documentary", "وثائقي", "doc",
    }
    if any(kw in text_lower for kw in documentary_keywords):
        return DocumentaryFulfiller()

    # Check for collecting/hobby keywords
    collecting_keywords = {
        "收藏", "collect", "collection", "vintage", "黑胶",
        "vinyl", "stamp", "邮票", "古董", "antique",
    }
    if any(kw in text_lower for kw in collecting_keywords):
        return CollectingFulfiller()

    # Check for astrology/fun quiz keywords
    astro_fun_keywords = {
        "星座", "astrology", "zodiac", "塔罗", "tarot", "أبراج",
        "horoscope", "运势", "生肖", "spirit animal", "灵魂动物",
    }
    if any(kw in text_lower for kw in astro_fun_keywords):
        return AstroFunFulfiller()

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
        "充电", "charging", "加油", "gas station", "电动", "شحن",
        "ev charging", "ev charger", "charger", "supercharger",
        "electric vehicle", "电动车",
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

    # Check for panic relief keywords (before sleep to catch anxiety/breathing)
    panic_keywords = {
        "panic", "恐慌", "calm down", "emergency", "紧急",
        "焦虑发作", "breathing exercise",
    }
    if any(kw in text_lower for kw in panic_keywords):
        return PanicReliefFulfiller()

    # Check for travel keywords
    travel_keywords = {
        "旅行", "travel", "旅游", "destination", "سفر", "trip", "去哪",
    }
    if any(kw in text_lower for kw in travel_keywords):
        return TravelFulfiller()

    # Check for home decor keywords
    decor_keywords = {
        "家居", "home decor", "装修", "decor", "interior", "ديكور", "furnish",
    }
    if any(kw in text_lower for kw in decor_keywords):
        return HomeDecorFulfiller()

    # Check for date spot keywords
    date_keywords = {
        "约会", "date", "约", "romantic", "رومانسي", "两个人", "together",
    }
    if any(kw in text_lower for kw in date_keywords):
        return DateSpotFulfiller()

    # Check for breakup healing keywords
    breakup_keywords = {
        "分手", "breakup", "失恋", "heartbreak", "انفصال", "move on", "healing",
    }
    if any(kw in text_lower for kw in breakup_keywords):
        return BreakupHealingFulfiller()

    # Check for sleep environment keywords
    sleep_keywords = {
        "睡眠", "insomnia", "失眠", "نوم", "bedtime", "rest",
    }
    if any(kw in text_lower for kw in sleep_keywords):
        return SleepEnvFulfiller()

    # Check for gift keywords
    gift_keywords_new = {
        "礼物", "gift", "birthday", "生日", "هدية", "anniversary", "纪念日",
    }
    if any(kw in text_lower for kw in gift_keywords_new):
        return GiftFulfiller()

    # Check for solo-friendly keywords
    solo_keywords = {
        "一个人", "solo", "alone", "独自", "وحدي", "by myself", "独处",
    }
    if any(kw in text_lower for kw in solo_keywords):
        return SoloFriendlyFulfiller()

    # Check for deep social keywords
    deep_social_keywords = {
        "深度", "deep", "meaningful", "有意义", "عميق", "genuine", "真诚",
    }
    if any(kw in text_lower for kw in deep_social_keywords):
        return DeepSocialFulfiller()

    # Check for poetry / literature keywords
    poetry_keywords = {
        "诗", "poetry", "poem", "文学", "literature", "شعر",
    }
    if any(kw in text_lower for kw in poetry_keywords):
        return PoetryFulfiller()

    # Check for crafts / handwork keywords
    crafts_keywords = {
        "手工", "craft", "陶艺", "pottery", "木工", "diy", "حرف",
    }
    if any(kw in text_lower for kw in crafts_keywords):
        return CraftsFulfiller()

    # Check for volunteer / charity keywords
    volunteer_keywords = {
        "志愿", "volunteer", "公益", "charity", "متطوع",
    }
    if any(kw in text_lower for kw in volunteer_keywords):
        return VolunteerFulfiller()

    # Check for nature healing keywords
    nature_healing_keywords = {
        "自然", "nature", "森林", "forest", "海边", "beach", "طبيعة", "healing",
    }
    if any(kw in text_lower for kw in nature_healing_keywords):
        return NatureHealingFulfiller()

    # Check for review / rating keywords
    review_keywords = {
        "评价", "review", "评分", "rating", "推荐", "تقييم",
    }
    if any(kw in text_lower for kw in review_keywords):
        return ReviewsFulfiller()

    # Check for startup resource keywords
    startup_keywords = {
        "创业", "startup", "创新", "innovation", "ريادة", "founder", "incubator",
    }
    if any(kw in text_lower for kw in startup_keywords):
        return StartupResourceFulfiller()

    # Check for kids activity keywords
    kids_activity_keywords = {
        "孩子", "kids", "children", "亲子", "أطفال", "带娃",
    }
    if any(kw in text_lower for kw in kids_activity_keywords):
        return KidsActivityFulfiller()

    # Check for elderly care keywords
    elderly_keywords = {
        "长辈", "elderly", "老人", "senior", "كبار السن", "爸妈",
    }
    if any(kw in text_lower for kw in elderly_keywords):
        return ElderlyCareFulfiller()

    # Check for family dining keywords
    family_dining_keywords = {
        "聚餐", "family dinner", "家庭", "大桌", "包间", "عائلة",
    }
    if any(kw in text_lower for kw in family_dining_keywords):
        return FamilyDiningFulfiller()

    # Check for wedding keywords
    wedding_keywords_check = {
        "婚礼", "wedding", "结婚", "marriage", "زفاف", "bridal",
    }
    if any(kw in text_lower for kw in wedding_keywords_check):
        return WeddingFulfiller()

    # Check for neighborhood / community keywords
    neighborhood_kw = {
        "邻里", "جيران",
    }
    if any(kw in text_lower for kw in neighborhood_kw):
        return NeighborhoodFulfiller()

    # Check for memory map keywords
    memory_map_keywords = {
        "回忆", "纪念", "remember", "ذكرى", "special place",
    }
    if any(kw in text_lower for kw in memory_map_keywords):
        return MemoryMapFulfiller()

    # Check for gratitude keywords
    gratitude_keywords = {
        "感恩", "gratitude", "感谢", "شكر", "appreciate",
    }
    if any(kw in text_lower for kw in gratitude_keywords):
        return GratitudeFulfiller()

    # Check for moving / relocation keywords
    moving_kw = {
        "搬家", "relocate", "نقل", "new home",
    }
    if any(kw in text_lower for kw in moving_kw):
        return MovingFulfiller()

    # Check for intergenerational keywords
    intergenerational_kw = {
        "代际", "intergenerational", "跨代", "传承", "أجيال", "generations",
    }
    if any(kw in text_lower for kw in intergenerational_kw):
        return IntergenerationalFulfiller()

    # Check for pet training keywords
    pet_training_kw = {
        "训犬", "dog training", "تدريب", "pet behavior", "pet training",
    }
    if any(kw in text_lower for kw in pet_training_kw):
        return PetTrainingFulfiller()

    # Check for accessibility keywords
    accessibility_kw = {
        "无障碍", "accessible", "wheelchair", "disability", "إعاقة",
        "barrier-free", "轮椅", "braille", "hearing loop", "guide dog",
    }
    if any(kw in text_lower for kw in accessibility_kw):
        return AccessibilityFulfiller()

    # Check for allergy-friendly keywords
    allergy_kw = {
        "过敏", "allergy", "gluten free", "素食", "vegan", "حساسية",
        "nut free", "dairy free", "celiac", "allergen",
    }
    if any(kw in text_lower for kw in allergy_kw):
        return AllergyFriendlyFulfiller()

    # Check for noise map keywords
    noise_kw = {
        "噪音", "noise level", "quiet place", "安静的地方", "هدوء",
        "sound level", "noise map",
    }
    if any(kw in text_lower for kw in noise_kw):
        return NoiseMapFulfiller()

    # Check for air quality keywords
    air_quality_kw = {
        "空气质量", "air quality", "pm2.5", "pollution", "雾霾",
        "جودة الهواء", "aqi", "smog",
    }
    if any(kw in text_lower for kw in air_quality_kw):
        return AirQualityFulfiller()

    # Check for night owl keywords
    night_owl_kw = {
        "夜猫子", "night owl", "深夜活动", "ليلي",
        "insomnia", "睡不着", "midnight activity",
    }
    if any(kw in text_lower for kw in night_owl_kw):
        return NightOwlFulfiller()

    # Check for early bird keywords
    early_bird_kw = {
        "早起", "early bird", "sunrise", "日出", "صباحي",
        "dawn", "清晨",
    }
    if any(kw in text_lower for kw in early_bird_kw):
        return EarlyBirdFulfiller()

    # Check for rainy day keywords
    rainy_day_kw = {
        "下雨", "rainy day", "雨天", "مطر", "raining",
    }
    if any(kw in text_lower for kw in rainy_day_kw):
        return RainyDayFulfiller()

    # Check for extreme weather keywords
    extreme_weather_kw = {
        "极端天气", "extreme weather", "暴风", "عاصفة",
        "heatwave", "blizzard", "沙尘暴", "typhoon", "earthquake",
    }
    if any(kw in text_lower for kw in extreme_weather_kw):
        return ExtremeWeatherFulfiller()

    # Check for pregnancy keywords
    pregnancy_kw = {
        "孕期", "pregnancy", "prenatal", "怀孕", "حمل",
        "expecting", "maternity", "孕妇",
    }
    if any(kw in text_lower for kw in pregnancy_kw):
        return PregnancyFulfiller()

    # Check for life stage keywords
    life_stage_kw = {
        "人生阶段", "life stage", "毕业", "graduation", "退休",
        "retirement", "مرحلة", "milestone", "career change",
    }
    if any(kw in text_lower for kw in life_stage_kw):
        return LifeStageFulfiller()

    # Check for caregiver respite keywords
    caregiver_respite_kw = {
        "照护", "caregiver", "respite", "看护", "رعاية", "relief", "喘息",
        "caring for", "taking care of", "exhausted from caring",
    }
    if any(kw in text_lower for kw in caregiver_respite_kw):
        # Disambiguate among caregiver sub-fulfillers
        emotional_kw = {"情绪", "emotion", "guilt", "内疚", "burnout", "疲惫", "anger", "breathing"}
        support_kw = {"支持", "support group", "互助", "therapy", "training", "forum"}
        remote_kw = {"远程", "remote", "monitor", "监护", "sensor", "gps", "fall detection"}

        if any(kw in text_lower for kw in emotional_kw):
            return CaregiverEmotionalFulfiller()
        if any(kw in text_lower for kw in support_kw):
            return CaregiverSupportFulfiller()
        if any(kw in text_lower for kw in remote_kw):
            return RemoteCareFulfiller()
        return CaregiverRespiteFulfiller()

    # Check for remote care keywords (standalone)
    remote_care_kw = {
        "远程看护", "remote care", "监护", "مراقبة", "elderly tech",
    }
    if any(kw in text_lower for kw in remote_care_kw):
        return RemoteCareFulfiller()

    # Check for caregiver support keywords (standalone)
    caregiver_support_kw = {
        "照护者支持", "caregiver support", "互助", "دعم مقدمي الرعاية",
    }
    if any(kw in text_lower for kw in caregiver_support_kw):
        return CaregiverSupportFulfiller()

    # Check for caregiver emotional keywords (standalone)
    caregiver_emotional_kw = {
        "照护者情绪", "caregiver emotion",
    }
    if any(kw in text_lower for kw in caregiver_emotional_kw):
        return CaregiverEmotionalFulfiller()

    # Check for legal aid keywords
    legal_aid_kw = {
        "法律", "legal", "律师", "lawyer", "محامي", "rights", "权益", "法援",
        "legal aid", "attorney", "court",
    }
    if any(kw in text_lower for kw in legal_aid_kw):
        # Disambiguate: labor, tenant, immigration, or general legal
        labor_kw = {"劳动", "labor", "加班", "overtime", "欠薪", "wage", "عمال", "worker rights",
                     "harassment", "fired", "union", "gig"}
        tenant_kw = {"租客", "tenant", "房东", "landlord", "إيجار", "rent", "eviction",
                      "deposit", "lease", "sublet"}
        immigration_kw = {"移民", "immigration", "签证", "visa", "هجرة", "refugee", "难民",
                          "居留", "asylum"}
        discrimination_kw = {"歧视", "discrimination", "反歧视", "تمييز", "racism", "bias", "平等",
                             "hate crime"}

        if any(kw in text_lower for kw in labor_kw):
            return LaborRightsFulfiller()
        if any(kw in text_lower for kw in tenant_kw):
            return TenantRightsFulfiller()
        if any(kw in text_lower for kw in immigration_kw):
            return ImmigrationFulfiller()
        if any(kw in text_lower for kw in discrimination_kw):
            return AntiDiscriminationFulfiller()
        return LegalAidFulfiller()

    # Check for labor rights keywords (standalone)
    labor_rights_kw = {
        "劳动", "labor", "加班", "overtime", "欠薪", "wage", "عمال", "worker rights",
    }
    if any(kw in text_lower for kw in labor_rights_kw):
        return LaborRightsFulfiller()

    # Check for tenant rights keywords (standalone)
    tenant_rights_kw = {
        "租客", "tenant", "房东", "landlord", "إيجار", "eviction",
    }
    if any(kw in text_lower for kw in tenant_rights_kw):
        return TenantRightsFulfiller()

    # Check for immigration keywords (standalone)
    immigration_kw = {
        "移民", "immigration", "签证", "visa", "هجرة", "refugee", "难民", "居留",
    }
    if any(kw in text_lower for kw in immigration_kw):
        return ImmigrationFulfiller()

    # Check for anti-discrimination keywords (standalone)
    anti_discrimination_kw = {
        "歧视", "discrimination", "反歧视", "تمييز", "racism", "bias", "平等",
    }
    if any(kw in text_lower for kw in anti_discrimination_kw):
        return AntiDiscriminationFulfiller()

    # ── NURTURING (养) ────────────────────────────────────────────────────────

    # Check for eating disorder keywords (highest sensitivity — before chronic)
    eating_disorder_kw = {
        "饮食障碍", "eating disorder", "厌食", "anorexia", "暴食",
        "bulimia", "اضطراب الأكل", "binge", "purge",
        "binge eating", "can't eat normally", "starving myself",
    }
    if any(kw in text_lower for kw in eating_disorder_kw):
        return EatingDisorderFulfiller()

    # Check for chronic pain keywords (before generic chronic illness)
    chronic_pain_kw = {
        "慢性疼痛", "chronic pain", "疼痛", "ألم", "pain management",
        "pain never stops", "constant pain", "pain relief",
    }
    if any(kw in text_lower for kw in chronic_pain_kw):
        return ChronicPainFulfiller()

    # Check for chronic illness keywords
    chronic_illness_kw = {
        "慢性病", "chronic", "diabetes", "糖尿病", "مرض مزمن",
        "long-term illness", "autoimmune", "thyroid", "epilepsy",
    }
    if any(kw in text_lower for kw in chronic_illness_kw):
        return ChronicIllnessFulfiller()

    # Check for disability social keywords
    disability_social_kw = {
        "残障社交", "disabled", "残疾", "adaptive",
        "wheelchair", "轮椅", "blind", "视障", "deaf", "听障",
        "neurodivergent",
    }
    if any(kw in text_lower for kw in disability_social_kw):
        return DisabilitySocialFulfiller()

    # Check for postpartum keywords
    postpartum_kw = {
        "产后", "postpartum", "新妈妈", "new mom", "ما بعد الولادة",
        "baby blues", "after giving birth", "postnatal depression",
    }
    if any(kw in text_lower for kw in postpartum_kw):
        return PostpartumFulfiller()

    # ── DIGITAL SAFETY (安) ───────────────────────────────────────────────────

    # Check for cyberbullying keywords
    cyberbullying_kw = {
        "网络霸凌", "cyberbullying", "网暴", "online harassment",
        "تنمر إلكتروني",
    }
    if any(kw in text_lower for kw in cyberbullying_kw):
        return CyberbullyingFulfiller()

    # Check for child safety online keywords
    child_safety_kw = {
        "儿童安全", "child safety", "kids online", "أمان الأطفال",
        "parental control", "家长控制",
    }
    if any(kw in text_lower for kw in child_safety_kw):
        return ChildSafetyOnlineFulfiller()

    # Check for scam detection keywords
    scam_kw = {
        "诈骗", "scam", "fraud", "骗", "احتيال", "fake", "deepfake",
        "杀猪盘",
    }
    if any(kw in text_lower for kw in scam_kw):
        return ScamDetectionFulfiller()

    # Check for privacy protection keywords
    privacy_kw = {
        "隐私", "privacy", "密码", "password", "خصوصية",
        "stalkerware", "phishing", "钓鱼", "vpn",
    }
    if any(kw in text_lower for kw in privacy_kw):
        return PrivacyProtectionFulfiller()

    # ── PURPOSE (义) ──────────────────────────────────────────────────────────

    # Check for legacy planning keywords
    legacy_kw = {
        "遗产", "legacy", "留给", "leave behind", "إرث",
        "what i leave", "my legacy", "legacy planning",
    }
    if any(kw in text_lower for kw in legacy_kw):
        return LegacyPlanningFulfiller()

    # Check for social justice keywords
    social_justice_kw = {
        "社会正义", "social justice", "公正", "عدالة", "activism",
        "advocacy", "petition", "请愿", "justice",
    }
    if any(kw in text_lower for kw in social_justice_kw):
        return SocialJusticeFulfiller()

    # Check for environmental action keywords
    environmental_kw = {
        "环保", "climate", "碳", "carbon", "بيئة", "sustainable",
        "可持续", "zero waste", "零浪费", "renewable", "wildlife",
    }
    if any(kw in text_lower for kw in environmental_kw):
        return EnvironmentalActionFulfiller()

    # Check for oral history keywords
    oral_history_kw = {
        "口述历史", "oral history", "تاريخ شفوي", "family story",
    }
    if any(kw in text_lower for kw in oral_history_kw):
        return OralHistoryFulfiller()

    # ── ROOTS (根) ────────────────────────────────────────────────────────────

    # Check for roots journey keywords
    roots_kw = {
        "寻根", "roots", "جذور", "homeland", "故乡", "diaspora",
        "genealogy", "族谱", "heritage", "ancestry", "where i come from",
    }
    if any(kw in text_lower for kw in roots_kw):
        return RootsJourneyFulfiller()

    # Check for mother tongue keywords
    mother_tongue_kw = {
        "母语", "mother tongue", "heritage language", "لغة أم",
        "native language",
    }
    if any(kw in text_lower for kw in mother_tongue_kw):
        return MotherTongueFulfiller()

    # Check for cultural recovery keywords
    cultural_recovery_kw = {
        "文化恢复", "cultural recovery", "复兴", "indigenous",
        "原住民", "cultural traditions", "revive",
    }
    if any(kw in text_lower for kw in cultural_recovery_kw):
        return CulturalRecoveryFulfiller()

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
