"""L2 Router — score-based fulfiller selection replacing sequential if-else.

Each fulfiller registers keywords with scores. All fulfillers scored simultaneously.
Highest total score wins. No order dependency. No substring collisions.

Scoring:
  - Exact phrase match: +10 points
  - Word-boundary keyword match: +5 points
  - Substring match: +2 points (only if no word-boundary match)
  - Priority bonus: crisis fulfillers get +20
  - Multi-match bonus: multiple keyword hits = +3 per additional hit
"""

from __future__ import annotations

import re
from typing import Any

from wish_engine.models import WishType


# ── Fulfiller Registry ───────────────────────────────────────────────────────

class FulfillerSpec:
    """Registration spec for a fulfiller."""

    def __init__(
        self,
        name: str,
        fulfiller_class: str,  # e.g. "SuicidePreventionFulfiller"
        module: str,  # e.g. "wish_engine.l2_suicide_prevention"
        keywords: dict[str, list[str]],  # lang → keyword list
        priority: int = 0,  # higher = checked with bonus (crisis=100, grief=50, etc.)
        exact_phrases: list[str] | None = None,  # phrases that must match exactly
        negative_keywords: list[str] | None = None,  # if present, DON'T route here
    ):
        self.name = name
        self.fulfiller_class = fulfiller_class
        self.module = module
        self.keywords = keywords
        self.priority = priority
        self.exact_phrases = exact_phrases or []
        self.negative_keywords = negative_keywords or []

    def score(self, text: str) -> float:
        """Score this fulfiller against wish text. Higher = better match."""
        text_lower = text.lower()
        total = 0.0

        # Negative keyword check — if present, score = -1000
        for neg in self.negative_keywords:
            if neg in text_lower:
                return -1000.0

        # Exact phrase match (highest value)
        for phrase in self.exact_phrases:
            if phrase.lower() in text_lower:
                total += 10.0

        # Keyword matches across all languages (deduplicate same keyword across langs)
        hits = 0
        seen_keywords: set[str] = set()
        for lang, kws in self.keywords.items():
            for kw in kws:
                kw_lower = kw.lower()
                if kw_lower in seen_keywords:
                    continue  # don't double-count same keyword in multiple languages
                # Check if keyword is non-Latin (CJK, Arabic, Cyrillic, Devanagari, etc.)
                is_non_latin = any(ord(c) > 0x024F for c in kw_lower if not c.isspace())
                if is_non_latin:
                    # Non-Latin: substring match is the best we can do (no word boundaries)
                    if kw_lower in text_lower:
                        total += 5.0
                        hits += 1
                        seen_keywords.add(kw_lower)
                else:
                    # Latin: word boundary match (preferred)
                    pattern = r'\b' + re.escape(kw_lower) + r'\b'
                    if re.search(pattern, text_lower):
                        total += 5.0
                        hits += 1
                        seen_keywords.add(kw_lower)
                    # Substring match only for multi-word phrases (4+ chars)
                    elif len(kw_lower) >= 4 and kw_lower in text_lower:
                        total += 2.0
                        hits += 1
                        seen_keywords.add(kw_lower)

        # Multi-match bonus
        if hits > 1:
            total += (hits - 1) * 3.0

        # Priority bonus (only if at least one keyword matched)
        if total > 0:
            total += self.priority * 0.1

        return total


# ── The Registry ─────────────────────────────────────────────────────────────

REGISTRY: list[FulfillerSpec] = []


def register(spec: FulfillerSpec):
    REGISTRY.append(spec)


def route(wish_text: str, wish_type: WishType | None = None) -> tuple[str, str]:
    """Route wish text to best fulfiller.

    Returns (module_path, class_name) of the winning fulfiller.
    """
    if not REGISTRY:
        _build_registry()

    best_score = -1.0
    best_spec = None

    for spec in REGISTRY:
        score = spec.score(wish_text)
        if score > best_score:
            best_score = score
            best_spec = spec

    if best_spec and best_score > 0:
        return best_spec.module, best_spec.fulfiller_class

    # Fallback by WishType
    fallback_map = {
        WishType.FIND_PLACE: ("wish_engine.l2_places", "PlaceFulfiller"),
        WishType.FIND_RESOURCE: ("wish_engine.l2_books", "BookFulfiller"),
        WishType.LEARN_SKILL: ("wish_engine.l2_courses", "CourseFulfiller"),
        WishType.CAREER_DIRECTION: ("wish_engine.l2_career", "CareerFulfiller"),
        WishType.HEALTH_WELLNESS: ("wish_engine.l2_wellness", "WellnessFulfiller"),
    }
    if wish_type and wish_type in fallback_map:
        return fallback_map[wish_type]
    return ("wish_engine.l2_books", "BookFulfiller")


def get_fulfiller_instance(wish_text: str, wish_type: WishType | None = None):
    """Route and instantiate the fulfiller."""
    module_path, class_name = route(wish_text, wish_type)
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls()


# ── Build Registry ───────────────────────────────────────────────────────────

_built = False


def _build_registry():
    global _built
    if _built:
        return
    _built = True

    # ═══ CRISIS (priority=100) ═══
    register(FulfillerSpec(
        name="suicide_prevention", fulfiller_class="SuicidePreventionFulfiller",
        module="wish_engine.l2_suicide_prevention", priority=100,
        exact_phrases=["kill myself", "end my life", "don't want to live", "want to die"],
        keywords={
            "en": ["suicide", "suicidal", "self harm", "end it all", "no reason to live", "rather be dead", "take my own life"],
            "zh": ["自杀", "不想活", "想死", "活不下去", "自残", "结束生命"],
            "ar": ["انتحار", "أريد الموت"],
            "es": ["suicidio", "no quiero vivir", "matarme"],
            "fr": ["suicide", "me tuer", "envie de mourir"],
            "ja": ["自殺", "死にたい"],
            "ko": ["자살", "죽고 싶"],
            "hi": ["आत्महत्या", "मरना चाहता"],
            "ru": ["суицид", "не хочу жить"],
            "pt": ["suicídio", "não quero viver"],
        },
    ))

    register(FulfillerSpec(
        name="domestic_violence", fulfiller_class="DomesticViolenceFulfiller",
        module="wish_engine.l2_domestic_violence", priority=100,
        exact_phrases=["he hits me", "she hits me", "domestic violence", "he beats me"],
        keywords={
            "en": ["abuse", "abusive", "violent partner", "battered", "beaten"],
            "zh": ["家暴", "被打", "他打我", "她打我"],
            "ar": ["عنف أسري", "يضربني"],
            "es": ["violencia doméstica", "me pega", "maltrato"],
            "fr": ["violence conjugale", "il me frappe"],
            "ja": ["家庭内暴力", "DV"],
            "ru": ["домашнее насилие", "бьёт меня"],
        },
    ))

    register(FulfillerSpec(
        name="emergency_shelter", fulfiller_class="EmergencyShelterFulfiller",
        module="wish_engine.l2_emergency_shelter", priority=100,
        keywords={
            "en": ["emergency shelter", "homeless", "nowhere to go", "need shelter", "safe place to stay"],
            "zh": ["庇护", "无家可归", "没地方住", "流浪"],
            "ar": ["مأوى", "بلا مأوى"],
            "es": ["refugio", "sin hogar"],
            "ru": ["приют", "бездомный"],
        },
    ))

    register(FulfillerSpec(
        name="debt_crisis", fulfiller_class="DebtCrisisFulfiller",
        module="wish_engine.l2_debt_crisis", priority=80,
        exact_phrases=["drowning in debt", "can't pay", "bankruptcy"],
        keywords={
            "en": ["debt", "bankrupt", "collectors", "owe money", "financial ruin", "in debt"],
            "zh": ["债务", "破产", "催收", "欠钱", "还不起", "催债"],
            "ar": ["ديون", "إفلاس"],
            "es": ["deuda", "bancarrota", "debo dinero"],
            "fr": ["dette", "faillite"],
            "ja": ["借金", "破産"],
            "ru": ["долг", "банкротство"],
        },
    ))

    register(FulfillerSpec(
        name="collective_trauma", fulfiller_class="CollectiveTraumaFulfiller",
        module="wish_engine.l2_collective_trauma", priority=80,
        keywords={
            "en": ["ptsd", "trauma", "collective trauma", "war trauma", "survivor guilt", "mass shooting"],
            "zh": ["创伤", "PTSD", "战争创伤", "灾后"],
            "ar": ["صدمة", "صدمة جماعية"],
            "es": ["trauma", "tept", "trauma colectivo"],
            "ja": ["トラウマ", "PTSD"],
            "ru": ["травма", "ПТСР"],
        },
    ))

    # ═══ GRIEF (priority=50) ═══
    register(FulfillerSpec(
        name="bereavement", fulfiller_class="BereavementFulfiller",
        module="wish_engine.l2_bereavement", priority=50,
        keywords={
            "en": ["grief", "grieving", "bereavement", "mourning", "loss of loved", "someone died"],
            "zh": ["丧亲", "哀悼", "失去亲人"],
            "ar": ["فقدان", "حداد", "عزاء"],
            "es": ["duelo", "luto", "pérdida"],
            "fr": ["deuil", "perte"],
            "ja": ["死別", "悲嘆"],
            "ru": ["горе", "утрата", "скорбь"],
        },
    ))

    register(FulfillerSpec(
        name="pet_loss", fulfiller_class="PetLossFulfiller",
        module="wish_engine.l2_pet_loss", priority=50,
        exact_phrases=["pet died", "dog died", "cat died", "lost my pet", "pet passed"],
        keywords={
            "en": ["pet loss", "rainbow bridge", "my pet", "pet grief"],
            "zh": ["宠物去世", "失去宠物"],
            "ar": ["فقدان حيوان"],
            "es": ["mascota murió", "perdí mi mascota"],
        },
    ))

    register(FulfillerSpec(
        name="pregnancy_loss", fulfiller_class="PregnancyLossFulfiller",
        module="wish_engine.l2_pregnancy_loss", priority=50,
        keywords={
            "en": ["miscarriage", "stillbirth", "pregnancy loss", "baby loss", "nicu"],
            "zh": ["流产", "死产", "失去孩子"],
            "ar": ["إجهاض"],
            "es": ["aborto espontáneo", "pérdida del bebé"],
        },
    ))

    register(FulfillerSpec(
        name="farewell_ritual", fulfiller_class="FarewellRitualFulfiller",
        module="wish_engine.l2_farewell_ritual", priority=40,
        keywords={
            "en": ["funeral", "memorial", "farewell", "ceremony", "celebration of life"],
            "zh": ["葬礼", "告别仪式", "头七", "追悼"],
            "ar": ["جنازة", "وداع"],
        },
    ))

    register(FulfillerSpec(
        name="estate_items", fulfiller_class="EstateItemsFulfiller",
        module="wish_engine.l2_estate_items", priority=40,
        keywords={
            "en": ["estate", "belongings", "deceased", "inheritance", "sort belongings"],
            "zh": ["遗物", "遗产整理"],
            "ar": ["تركة", "ميراث"],
        },
    ))

    # ═══ ADDICTION (priority=60) ═══
    register(FulfillerSpec(
        name="addiction_meetings", fulfiller_class="AddictionMeetingFulfiller",
        module="wish_engine.l2_addiction_meetings", priority=60,
        exact_phrases=["aa meeting", "na meeting", "stop drinking"],
        keywords={
            "en": ["addiction", "recovery", "alcoholic", "rehab", "sober", "twelve step"],
            "zh": ["戒瘾", "戒酒", "戒毒"],
            "ar": ["إدمان"],
            "es": ["adicción", "rehabilitación", "alcohólico"],
            "ja": ["依存症", "断酒"],
            "ru": ["зависимость", "реабилитация"],
        },
    ))

    register(FulfillerSpec(
        name="sobriety_tracker", fulfiller_class="SobrietyTrackerFulfiller",
        module="wish_engine.l2_sobriety_tracker", priority=55,
        exact_phrases=["days clean", "days sober", "sobriety"],
        keywords={
            "en": ["sobriety", "sober days", "clean days", "recovery track"],
            "zh": ["清醒天数"],
        },
    ))

    register(FulfillerSpec(
        name="trigger_alert", fulfiller_class="TriggerAlertFulfiller",
        module="wish_engine.l2_trigger_alert", priority=55,
        keywords={
            "en": ["trigger", "triggered", "temptation", "avoid triggers", "trigger alert"],
            "zh": ["触发", "预警", "诱惑"],
            "ar": ["تجنب"],
        },
    ))

    register(FulfillerSpec(
        name="craving_alternatives", fulfiller_class="CravingAlternativeFulfiller",
        module="wish_engine.l2_craving_alternatives", priority=55,
        keywords={
            "en": ["craving", "urge", "want to drink", "want to smoke"],
            "zh": ["渴望", "想喝", "想抽"],
        },
    ))

    register(FulfillerSpec(
        name="behavioral_addiction", fulfiller_class="BehavioralAddictionFulfiller",
        module="wish_engine.l2_behavioral_addiction", priority=55,
        exact_phrases=["gaming addiction", "gambling addiction", "shopping addiction"],
        keywords={
            "en": ["gambling", "gaming addiction", "phone addiction"],
            "zh": ["赌博", "游戏成瘾", "手机成瘾"],
            "ar": ["قمار"],
        },
    ))

    # ═══ CAREGIVING (priority=40) ═══
    register(FulfillerSpec(
        name="caregiver_respite", fulfiller_class="CaregiverRespiteFulfiller",
        module="wish_engine.l2_caregiver_respite", priority=40,
        exact_phrases=["caregiver respite", "need respite", "caregiver exhausted"],
        keywords={
            "en": ["caregiver", "respite", "caring for", "exhausted from caring"],
            "zh": ["照护", "看护", "喘息"],
            "ar": ["رعاية", "مقدم رعاية"],
            "es": ["cuidador", "respiro", "agotado de cuidar"],
        },
    ))

    register(FulfillerSpec(
        name="caregiver_emotional", fulfiller_class="CaregiverEmotionalFulfiller",
        module="wish_engine.l2_caregiver_emotional", priority=40,
        keywords={
            "en": ["caregiver guilt", "caregiver burnout", "compassion fatigue"],
            "zh": ["照护者情绪", "内疚", "疲惫"],
        },
    ))

    register(FulfillerSpec(
        name="caregiver_support", fulfiller_class="CaregiverSupportFulfiller",
        module="wish_engine.l2_caregiver_support", priority=40,
        keywords={
            "en": ["caregiver support group", "caregiver community"],
            "zh": ["照护者支持", "互助"],
        },
    ))

    register(FulfillerSpec(
        name="remote_care", fulfiller_class="RemoteCareFulfiller",
        module="wish_engine.l2_remote_care", priority=40,
        exact_phrases=["remote care", "remote monitor"],
        keywords={
            "en": ["remote care", "monitor elderly", "from far away", "remote caregiver"],
            "zh": ["远程看护", "远程监护"],
        },
    ))

    # ═══ RIGHTS (priority=40) ═══
    register(FulfillerSpec(
        name="legal_aid", fulfiller_class="LegalAidFulfiller",
        module="wish_engine.l2_legal_aid", priority=40,
        keywords={
            "en": ["legal aid", "lawyer", "attorney", "legal help", "legal protection", "court"],
            "zh": ["法律", "律师", "法援", "权益"],
            "ar": ["محامي", "قانوني"],
            "es": ["abogado", "asistencia legal", "ayuda legal"],
            "ja": ["弁護士", "法律相談"],
            "ru": ["юрист", "адвокат", "правовая помощь"],
        },
    ))

    register(FulfillerSpec(
        name="labor_rights", fulfiller_class="LaborRightsFulfiller",
        module="wish_engine.l2_labor_rights", priority=40,
        keywords={
            "en": ["labor rights", "overtime", "wage theft", "worker rights", "workplace safety"],
            "zh": ["劳动", "加班", "欠薪"],
            "ar": ["عمال", "حقوق العمال"],
            "es": ["derechos laborales", "horas extra"],
        },
    ))

    register(FulfillerSpec(
        name="tenant_rights", fulfiller_class="TenantRightsFulfiller",
        module="wish_engine.l2_tenant_rights", priority=40,
        keywords={
            "en": ["tenant", "landlord", "rent increase", "eviction", "deposit"],
            "zh": ["租客", "房东", "租金"],
            "ar": ["إيجار", "مالك العقار"],
            "es": ["inquilino", "alquiler", "desahucio"],
        },
    ))

    register(FulfillerSpec(
        name="immigration", fulfiller_class="ImmigrationFulfiller",
        module="wish_engine.l2_immigration", priority=40,
        keywords={
            "en": ["immigration", "visa", "residency", "asylum", "refugee", "emigrate", "work permit"],
            "zh": ["移民", "签证", "居留", "难民"],
            "ar": ["هجرة", "تأشيرة", "لجوء"],
            "es": ["inmigración", "visa", "residencia", "asilo"],
            "fr": ["immigration", "visa", "résidence"],
            "ja": ["移民", "ビザ"],
            "ru": ["иммиграция", "виза", "убежище"],
        },
    ))

    register(FulfillerSpec(
        name="anti_discrimination", fulfiller_class="AntiDiscriminationFulfiller",
        module="wish_engine.l2_anti_discrimination", priority=40,
        keywords={
            "en": ["discrimination", "racism", "bias", "prejudice", "anti-discrimination", "hate crime"],
            "zh": ["歧视", "反歧视", "平等"],
            "ar": ["تمييز", "عنصرية"],
            "es": ["discriminación", "racismo"],
        },
    ))

    # ═══ NURTURING (priority=30) ═══
    register(FulfillerSpec(
        name="chronic_illness", fulfiller_class="ChronicIllnessFulfiller",
        module="wish_engine.l2_chronic_illness", priority=30,
        keywords={
            "en": ["chronic illness", "diabetes", "autoimmune", "chronic fatigue", "long-term illness"],
            "zh": ["慢性病", "糖尿病"],
            "ar": ["مرض مزمن"],
            "es": ["enfermedad crónica", "diabetes"],
        },
    ))

    register(FulfillerSpec(
        name="chronic_pain", fulfiller_class="ChronicPainFulfiller",
        module="wish_engine.l2_chronic_pain", priority=30,
        exact_phrases=["chronic pain", "pain management"],
        keywords={
            "en": ["chronic pain", "pain never stops", "pain management"],
            "zh": ["慢性疼痛", "疼痛"],
            "ar": ["ألم مزمن"],
            "es": ["dolor crónico"],
        },
    ))

    register(FulfillerSpec(
        name="eating_disorder", fulfiller_class="EatingDisorderFulfiller",
        module="wish_engine.l2_eating_disorder", priority=50,
        keywords={
            "en": ["eating disorder", "anorexia", "bulimia", "binge eating", "body image"],
            "zh": ["饮食障碍", "厌食", "暴食"],
            "ar": ["اضطراب الأكل"],
            "es": ["trastorno alimentario", "anorexia", "bulimia"],
        },
    ))

    register(FulfillerSpec(
        name="disability_social", fulfiller_class="DisabilitySocialFulfiller",
        module="wish_engine.l2_disability_social", priority=30,
        keywords={
            "en": ["disability", "disabled", "adaptive", "inclusive", "wheelchair", "blind", "deaf"],
            "zh": ["残障", "残疾", "无障碍"],
            "ar": ["إعاقة"],
            "es": ["discapacidad", "inclusivo"],
        },
    ))

    register(FulfillerSpec(
        name="postpartum", fulfiller_class="PostpartumFulfiller",
        module="wish_engine.l2_postpartum", priority=40,
        keywords={
            "en": ["postpartum", "new mom", "baby blues", "after birth", "postnatal"],
            "zh": ["产后", "新妈妈"],
            "ar": ["ما بعد الولادة"],
            "es": ["postparto", "posparto"],
        },
    ))

    # ═══ DIGITAL SAFETY (priority=30) ═══
    register(FulfillerSpec(
        name="cyberbullying", fulfiller_class="CyberbullyingFulfiller",
        module="wish_engine.l2_cyberbullying", priority=30,
        keywords={
            "en": ["cyberbullying", "online harassment", "trolling", "cyberbully"],
            "zh": ["网络霸凌", "网暴"],
            "ar": ["تنمر إلكتروني"],
            "es": ["ciberacoso", "acoso online"],
        },
    ))

    register(FulfillerSpec(
        name="privacy_protection", fulfiller_class="PrivacyProtectionFulfiller",
        module="wish_engine.l2_privacy_protection", priority=20,
        keywords={
            "en": ["privacy", "password", "data protection", "vpn", "phishing"],
            "zh": ["隐私", "密码", "数据保护"],
            "ar": ["خصوصية"],
            "es": ["privacidad", "contraseña"],
        },
    ))

    register(FulfillerSpec(
        name="child_safety_online", fulfiller_class="ChildSafetyOnlineFulfiller",
        module="wish_engine.l2_child_safety_online", priority=30,
        exact_phrases=["child safety", "kids online", "parental control"],
        keywords={
            "en": ["child safety", "parental control", "kids online", "screen time kids"],
            "zh": ["儿童安全", "家长控制"],
            "ar": ["أمان الأطفال"],
        },
    ))

    register(FulfillerSpec(
        name="scam_detection", fulfiller_class="ScamDetectionFulfiller",
        module="wish_engine.l2_scam_detection", priority=30,
        keywords={
            "en": ["scam", "fraud", "phishing", "deepfake", "identity theft"],
            "zh": ["诈骗", "骗子"],
            "ar": ["احتيال"],
            "es": ["estafa", "fraude"],
        },
    ))

    # ═══ PURPOSE (priority=20) ═══
    register(FulfillerSpec(
        name="legacy_planning", fulfiller_class="LegacyPlanningFulfiller",
        module="wish_engine.l2_legacy_planning", priority=20,
        exact_phrases=["plan my legacy", "leave behind", "what will I leave"],
        keywords={
            "en": ["legacy", "leave behind", "ethical will", "what I leave"],
            "zh": ["遗产规划", "留给后代"],
            "ar": ["إرث", "وصية"],
            "es": ["legado", "herencia"],
        },
    ))

    register(FulfillerSpec(
        name="social_justice", fulfiller_class="SocialJusticeFulfiller",
        module="wish_engine.l2_social_justice", priority=20,
        exact_phrases=["social justice", "fight for justice"],
        keywords={
            "en": ["social justice", "advocacy", "activism", "petition", "civic"],
            "zh": ["社会正义", "公正", "维权"],
            "ar": ["عدالة اجتماعية"],
            "es": ["justicia social", "activismo"],
        },
    ))

    register(FulfillerSpec(
        name="environmental_action", fulfiller_class="EnvironmentalActionFulfiller",
        module="wish_engine.l2_environmental_action", priority=20,
        keywords={
            "en": ["environment", "climate", "carbon", "sustainable", "green", "eco"],
            "zh": ["环保", "气候", "碳"],
            "ar": ["بيئة"],
            "es": ["medio ambiente", "clima", "sostenible"],
        },
    ))

    register(FulfillerSpec(
        name="oral_history", fulfiller_class="OralHistoryFulfiller",
        module="wish_engine.l2_oral_history", priority=20,
        exact_phrases=["oral history", "family story", "record story"],
        keywords={
            "en": ["oral history", "family story", "record stories", "ancestry research"],
            "zh": ["口述历史", "家族故事"],
            "ar": ["تاريخ شفوي"],
        },
    ))

    # ═══ ROOTS (priority=20) ═══
    register(FulfillerSpec(
        name="roots_journey", fulfiller_class="RootsJourneyFulfiller",
        module="wish_engine.l2_roots_journey", priority=20,
        exact_phrases=["find my roots", "discover my heritage"],
        keywords={
            "en": ["roots", "heritage", "ancestry", "homeland", "genealogy", "where I come from"],
            "zh": ["寻根", "故乡", "祖籍"],
            "ar": ["جذور", "وطن"],
            "es": ["raíces", "herencia", "genealogía"],
        },
    ))

    register(FulfillerSpec(
        name="mother_tongue", fulfiller_class="MotherTongueFulfiller",
        module="wish_engine.l2_mother_tongue", priority=20,
        exact_phrases=["mother tongue", "heritage language"],
        keywords={
            "en": ["mother tongue", "heritage language", "native language"],
            "zh": ["母语", "方言"],
            "ar": ["لغة أم"],
        },
    ))

    register(FulfillerSpec(
        name="cultural_recovery", fulfiller_class="CulturalRecoveryFulfiller",
        module="wish_engine.l2_cultural_recovery", priority=20,
        exact_phrases=["cultural recovery", "revive tradition"],
        keywords={
            "en": ["cultural recovery", "indigenous", "traditional ceremony", "cultural revival"],
            "zh": ["文化恢复", "传统复兴"],
            "ar": ["تراث", "استعادة ثقافية"],
        },
    ))

    # ═══ LIFE QUALITY — High frequency ═══

    register(FulfillerSpec(
        name="panic_relief", fulfiller_class="PanicReliefFulfiller",
        module="wish_engine.l2_panic_relief", priority=70,
        exact_phrases=["panic attack", "can't breathe", "help me calm"],
        keywords={
            "en": ["panic", "panic attack", "calm down", "breathing exercise", "anxiety attack"],
            "zh": ["恐慌", "焦虑发作", "喘不过气"],
            "ar": ["نوبة هلع"],
            "es": ["ataque de pánico", "no puedo respirar"],
            "ja": ["パニック"],
        },
    ))

    register(FulfillerSpec(
        name="sleep_env", fulfiller_class="SleepEnvFulfiller",
        module="wish_engine.l2_sleep_env", priority=30,
        exact_phrases=["can't sleep", "trouble sleeping"],
        keywords={
            "en": ["insomnia", "sleep", "sleepless", "bedtime", "nightmares"],
            "zh": ["失眠", "睡眠", "睡不着"],
            "ar": ["أرق", "نوم"],
            "es": ["insomnio", "no puedo dormir"],
            "ja": ["不眠", "眠れない"],
            "ru": ["бессонница"],
        },
        negative_keywords=["sleepover"],
    ))

    register(FulfillerSpec(
        name="confidence", fulfiller_class="ConfidenceFulfiller",
        module="wish_engine.l2_confidence", priority=20,
        exact_phrases=["build confidence", "believe in myself"],
        keywords={
            "en": ["confidence", "courage", "self-doubt", "self-esteem", "social anxiety", "not confident", "believe in myself"],
            "zh": ["自信", "勇气", "自我怀疑"],
            "ar": ["ثقة", "شجاعة"],
            "es": ["confianza", "autoestima", "creer en mí"],
            "ja": ["自信", "勇気"],
            "ru": ["уверенность"],
        },
    ))

    register(FulfillerSpec(
        name="focus_mode", fulfiller_class="FocusModeFulfiller",
        module="wish_engine.l2_focus_mode", priority=20,
        exact_phrases=["deep work", "can't focus", "can't concentrate", "place to study", "quiet study"],
        keywords={
            "en": ["focus", "concentrate", "productivity", "adhd", "distracted", "study space", "study spaces", "quiet space"],
            "zh": ["专注", "集中", "学习空间"],
            "ar": ["تركيز"],
            "es": ["concentración", "enfoque", "productividad"],
            "ja": ["集中", "勉強スペース"],
        },
    ))

    register(FulfillerSpec(
        name="breakup_healing", fulfiller_class="BreakupHealingFulfiller",
        module="wish_engine.l2_breakup_healing", priority=30,
        exact_phrases=["breakup healing", "broken heart"],
        keywords={
            "en": ["breakup", "heartbreak", "broke up", "divorce", "ex-boyfriend", "ex-girlfriend", "move on"],
            "zh": ["分手", "失恋", "离婚"],
            "ar": ["انفصال", "طلاق"],
            "es": ["ruptura", "corazón roto", "divorcio"],
            "ja": ["失恋", "離婚"],
            "ru": ["расставание", "развод"],
        },
    ))

    register(FulfillerSpec(
        name="eq_training", fulfiller_class="EQTrainingFulfiller",
        module="wish_engine.l2_eq_training", priority=15,
        exact_phrases=["emotional intelligence", "build empathy"],
        keywords={
            "en": ["emotional intelligence", "empathy", "eq training", "read emotions"],
            "zh": ["情商", "同理心"],
            "ar": ["ذكاء عاطفي"],
            "es": ["inteligencia emocional", "empatía"],
        },
    ))

    register(FulfillerSpec(
        name="identity_exploration", fulfiller_class="IdentityExplorationFulfiller",
        module="wish_engine.l2_identity_exploration", priority=15,
        exact_phrases=["who am I", "explore my identity", "not ready"],
        keywords={
            "en": ["identity", "who am I", "explore myself", "self-discovery", "not ready", "pressure to marry"],
            "zh": ["身份", "我是谁", "探索"],
            "ar": ["هوية", "من أنا"],
            "es": ["identidad", "quién soy"],
        },
    ))

    # ═══ SOCIAL ═══
    register(FulfillerSpec(
        name="safe_spaces", fulfiller_class="SafeSpaceFulfiller",
        module="wish_engine.l2_safe_spaces", priority=30,
        exact_phrases=["safe space", "lgbtq friendly", "lgbtq+"],
        keywords={
            "en": ["safe space", "inclusive", "lgbtq", "welcoming", "non-judgmental"],
            "zh": ["安全空间", "包容"],
            "ar": ["مكان آمن"],
            "es": ["espacio seguro", "inclusivo"],
        },
    ))

    register(FulfillerSpec(
        name="mentor_enhanced", fulfiller_class="MentorFulfiller",
        module="wish_engine.l2_mentor_enhanced", priority=20,
        exact_phrases=["find a mentor", "need a mentor", "connect with other"],
        keywords={
            "en": ["mentor", "guidance", "coach", "advisor", "connect with professionals"],
            "zh": ["导师", "前辈", "指导"],
            "ar": ["مرشد"],
            "es": ["mentor", "guía", "consejero"],
            "ja": ["メンター"],
        },
    ))

    register(FulfillerSpec(
        name="interest_circles", fulfiller_class="InterestCircleFulfiller",
        module="wish_engine.l2_interest_circles", priority=15,
        keywords={
            "en": ["hobby", "interest group", "niche", "like-minded", "people who share", "jam with", "musicians", "art community", "community"],
            "zh": ["兴趣", "圈子", "同好", "爱好"],
            "ar": ["هواية"],
            "es": ["grupo de interés", "hobby", "afición"],
        },
    ))

    register(FulfillerSpec(
        name="virtual_companion", fulfiller_class="VirtualCompanionFulfiller",
        module="wish_engine.l2_virtual_companion", priority=20,
        exact_phrases=["someone to talk to", "need someone", "talk to someone"],
        keywords={
            "en": ["companion", "buddy", "lonely and need", "virtual friend", "talk to"],
            "zh": ["陪伴", "陪我"],
            "ar": ["مرافق"],
            "es": ["compañero", "alguien con quien hablar"],
        },
    ))

    register(FulfillerSpec(
        name="deep_social", fulfiller_class="DeepSocialFulfiller",
        module="wish_engine.l2_deep_social", priority=15,
        exact_phrases=["deep connection", "meaningful conversation"],
        keywords={
            "en": ["deep social", "meaningful", "genuine connection", "real friends", "not small talk"],
            "zh": ["深度社交", "有意义"],
            "ar": ["عميق"],
            "es": ["conexión profunda", "conversación real"],
        },
    ))

    register(FulfillerSpec(
        name="progress_groups", fulfiller_class="ProgressGroupFulfiller",
        module="wish_engine.l2_progress_groups", priority=15,
        keywords={
            "en": ["accountability", "progress group", "weekly goal", "habit group"],
            "zh": ["打卡", "互助小组"],
        },
    ))

    # ═══ DAILY LIFE ═══

    register(FulfillerSpec(
        name="hometown_food", fulfiller_class="HometownFoodFulfiller",
        module="wish_engine.l2_hometown_food", priority=25,
        exact_phrases=["hometown food", "miss home", "authentic food"],
        keywords={
            "en": ["hometown", "authentic", "miss home", "from my country", "homesick",
                   "kenyan", "filipino", "pakistani", "lebanese", "egyptian", "nigerian",
                   "ghanaian", "indian food", "chinese food", "mexican food", "ukrainian",
                   "thai food", "korean food", "japanese food", "vietnamese"],
            "zh": ["家乡", "正宗", "家的味道", "想家"],
            "ar": ["بلدي", "وطني", "طعام بلدي"],
            "es": ["comida de mi país", "nostalgia", "auténtico"],
        },
    ))

    register(FulfillerSpec(
        name="food", fulfiller_class="FoodFulfiller",
        module="wish_engine.l2_food", priority=20,
        keywords={
            "en": ["restaurant", "dinner", "lunch", "breakfast", "brunch", "comfort food", "hungry", "vegan", "vegetarian"],
            "zh": ["吃饭", "餐厅", "美食", "火锅", "烧烤"],
            "ar": ["مطعم", "حلال"],
            "es": ["restaurante", "comer", "comida", "cena", "almuerzo"],
            "fr": ["restaurant", "dîner", "déjeuner"],
            "ja": ["レストラン", "ラーメン", "食事"],
            "ko": ["식당", "맛집"],
        },
    ))

    register(FulfillerSpec(
        name="music", fulfiller_class="MusicFulfiller",
        module="wish_engine.l2_music", priority=15,
        exact_phrases=["listen to music", "music that matches"],
        keywords={
            "en": ["music", "playlist", "songs", "spotify", "melody", "tunes"],
            "zh": ["音乐", "歌", "听"],
            "ar": ["موسيقى", "أغاني"],
            "es": ["música", "canción", "escuchar"],
            "ja": ["音楽", "曲"],
            "ko": ["음악", "노래"],
        },
        negative_keywords=["musician", "music composition"],
    ))

    register(FulfillerSpec(
        name="deals", fulfiller_class="DealsFulfiller",
        module="wish_engine.l2_deals", priority=20,
        keywords={
            "en": ["deal", "discount", "sale", "coupon", "cheap", "save money", "promo", "budget"],
            "zh": ["折扣", "优惠", "省钱", "便宜"],
            "ar": ["تخفيض", "خصم"],
            "es": ["descuento", "oferta", "ahorrar", "barato"],
            "ja": ["割引", "セール"],
        },
    ))

    register(FulfillerSpec(
        name="coworking", fulfiller_class="CoworkingFulfiller",
        module="wish_engine.l2_coworking", priority=15,
        exact_phrases=["coworking space", "workspace", "work from"],
        keywords={
            "en": ["coworking", "workspace", "office space", "work from", "remote work"],
            "zh": ["工作空间", "办公", "共享办公"],
            "ar": ["مساحة عمل"],
            "es": ["coworking", "espacio de trabajo", "oficina"],
        },
    ))

    register(FulfillerSpec(
        name="free_activities", fulfiller_class="FreeActivityFulfiller",
        module="wish_engine.l2_free_activities", priority=15,
        exact_phrases=["free activities", "free things to do"],
        keywords={
            "en": ["free", "no cost", "free events", "free things"],
            "zh": ["免费", "不花钱"],
            "ar": ["مجاني"],
            "es": ["gratis", "gratuito", "sin costo"],
        },
    ))

    register(FulfillerSpec(
        name="finance", fulfiller_class="FinanceFulfiller",
        module="wish_engine.l2_finance", priority=15,
        keywords={
            "en": ["financial", "budgeting", "investing", "savings", "money management", "money", "burning cash", "cash flow"],
            "zh": ["理财", "投资", "存钱"],
            "ar": ["مال", "استثمار"],
            "es": ["finanzas", "ahorro", "inversión"],
        },
        negative_keywords=["financial ruin", "financial crisis"],
    ))

    # ═══ EVENTS & CULTURE ═══
    register(FulfillerSpec(
        name="events", fulfiller_class="EventFulfiller",
        module="wish_engine.l2_events", priority=15,
        keywords={
            "en": ["event", "concert", "exhibition", "festival", "theater", "theatre", "opera", "ballet", "comedy show", "live music", "meetup", "book signing"],
            "zh": ["演出", "表演", "展览", "音乐会", "话剧", "歌剧"],
            "ar": ["حفل", "معرض", "مهرجان"],
            "es": ["concierto", "exposición", "festival", "teatro"],
            "ja": ["コンサート", "展覧会"],
        },
    ))

    register(FulfillerSpec(
        name="poetry", fulfiller_class="PoetryFulfiller",
        module="wish_engine.l2_poetry", priority=15,
        keywords={
            "en": ["poetry", "poem", "poet", "verse", "literature"],
            "zh": ["诗", "诗歌", "文学"],
            "ar": ["شعر", "قصيدة"],
            "es": ["poesía", "poema", "poeta", "lorca", "neruda"],
            "ja": ["詩", "俳句"],
        },
    ))

    register(FulfillerSpec(
        name="volunteer", fulfiller_class="VolunteerFulfiller",
        module="wish_engine.l2_volunteer", priority=20,
        keywords={
            "en": ["volunteer", "charity", "give back", "help others", "community service"],
            "zh": ["志愿", "公益", "义工"],
            "ar": ["متطوع", "خيري"],
            "es": ["voluntario", "caridad", "ayudar"],
            "ja": ["ボランティア"],
        },
    ))

    register(FulfillerSpec(
        name="crafts", fulfiller_class="CraftsFulfiller",
        module="wish_engine.l2_crafts", priority=15,
        keywords={
            "en": ["craft", "pottery", "woodwork", "calligraphy", "sewing", "knitting", "diy"],
            "zh": ["手工", "陶艺", "木工", "书法"],
            "ar": ["حرف يدوية"],
            "es": ["manualidades", "cerámica", "artesanía"],
        },
    ))

    register(FulfillerSpec(
        name="nature_healing", fulfiller_class="NatureHealingFulfiller",
        module="wish_engine.l2_nature_healing", priority=20,
        exact_phrases=["nature healing", "forest bathing"],
        keywords={
            "en": ["nature", "forest", "beach", "mountain", "hiking", "outdoors", "garden", "park"],
            "zh": ["自然", "森林", "海边", "山", "公园"],
            "ar": ["طبيعة", "شاطئ"],
            "es": ["naturaleza", "bosque", "playa", "montaña", "parque"],
            "ja": ["自然", "森", "海"],
        },
    ))

    # ═══ PLACES & PRACTICAL ═══
    register(FulfillerSpec(
        name="safety", fulfiller_class="SafeRouteFulfiller",
        module="wish_engine.l2_safety", priority=30,
        exact_phrases=["safe route", "walk home", "feel unsafe"],
        keywords={
            "en": ["safe route", "safety", "unsafe", "dark street", "walk home at night", "scared"],
            "zh": ["安全", "回家路线", "害怕"],
            "ar": ["أمان", "خوف"],
            "es": ["seguridad", "ruta segura", "miedo"],
        },
    ))

    register(FulfillerSpec(
        name="medical", fulfiller_class="MedicalFulfiller",
        module="wish_engine.l2_medical", priority=25,
        keywords={
            "en": ["doctor", "hospital", "clinic", "medical", "dentist", "pharmacy"],
            "zh": ["医院", "医生", "看病", "药"],
            "ar": ["طبيب", "مستشفى", "صيدلية"],
            "es": ["doctor", "hospital", "clínica", "farmacia"],
            "ja": ["病院", "医者"],
        },
        negative_keywords=["volunteer at a clinic"],
    ))

    register(FulfillerSpec(
        name="kids_activities", fulfiller_class="KidsActivityFulfiller",
        module="wish_engine.l2_kids_activities", priority=20,
        keywords={
            "en": ["kids", "children", "family activity", "playground", "for my kids"],
            "zh": ["孩子", "亲子", "带娃"],
            "ar": ["أطفال", "عائلة"],
            "es": ["niños", "actividades familiares", "hijos"],
        },
    ))

    register(FulfillerSpec(
        name="pet_friendly", fulfiller_class="PetFriendlyFulfiller",
        module="wish_engine.l2_pet_friendly", priority=15,
        keywords={
            "en": ["pet", "dog", "cat", "vet", "pet friendly", "pet cafe"],
            "zh": ["宠物", "狗", "猫", "兽医"],
            "ar": ["حيوان أليف"],
            "es": ["mascota", "perro", "gato", "veterinario"],
        },
    ))

    register(FulfillerSpec(
        name="startup_resources", fulfiller_class="StartupResourceFulfiller",
        module="wish_engine.l2_startup_resources", priority=20,
        keywords={
            "en": ["startup", "incubator", "investor", "entrepreneur", "founder", "accelerator"],
            "zh": ["创业", "孵化器", "投资人"],
            "ar": ["ريادة", "مستثمر"],
            "es": ["startup", "emprendedor", "incubadora", "inversor"],
        },
    ))

    register(FulfillerSpec(
        name="solo_friendly", fulfiller_class="SoloFriendlyFulfiller",
        module="wish_engine.l2_solo_friendly", priority=10,
        exact_phrases=["alone and it's okay", "solo friendly"],
        keywords={
            "en": ["solo", "alone", "by myself", "solo dining", "solo travel"],
            "zh": ["一个人", "独处", "独自"],
            "ar": ["وحدي"],
            "es": ["solo", "sola", "ir sola"],
        },
    ))

    register(FulfillerSpec(
        name="travel", fulfiller_class="TravelFulfiller",
        module="wish_engine.l2_travel", priority=15,
        keywords={
            "en": ["travel", "trip", "destination", "vacation", "visit"],
            "zh": ["旅行", "旅游", "去哪"],
            "ar": ["سفر", "رحلة"],
            "es": ["viajar", "viaje", "destino", "vacaciones"],
            "ja": ["旅行", "旅"],
        },
    ))

    register(FulfillerSpec(
        name="date_spots", fulfiller_class="DateSpotFulfiller",
        module="wish_engine.l2_date_spots", priority=15,
        keywords={
            "en": ["date", "romantic", "date night", "couple"],
            "zh": ["约会", "浪漫"],
            "ar": ["رومانسي", "موعد"],
            "es": ["cita", "romántico"],
        },
    ))

    register(FulfillerSpec(
        name="birthday_planning", fulfiller_class="BirthdayPlannerFulfiller",
        module="wish_engine.l2_birthday_planning", priority=15,
        keywords={
            "en": ["birthday", "party", "celebrate"],
            "zh": ["生日", "派对", "庆祝"],
            "ar": ["عيد ميلاد", "حفلة"],
            "es": ["cumpleaños", "fiesta"],
        },
    ))

    register(FulfillerSpec(
        name="gift", fulfiller_class="GiftFulfiller",
        module="wish_engine.l2_gift", priority=15,
        keywords={
            "en": ["gift", "present", "gift idea", "birthday gift"],
            "zh": ["礼物", "送什么"],
            "ar": ["هدية"],
            "es": ["regalo"],
        },
    ))

    register(FulfillerSpec(
        name="documentary", fulfiller_class="DocumentaryFulfiller",
        module="wish_engine.l2_documentaries", priority=10,
        keywords={
            "en": ["documentary", "documentaries", "doc film"],
            "zh": ["纪录片"],
            "ar": ["وثائقي"],
            "es": ["documental"],
        },
    ))

    register(FulfillerSpec(
        name="writing", fulfiller_class="WritingFulfiller",
        module="wish_engine.l2_writing", priority=10,
        exact_phrases=["write in my journal", "journaling", "diary entry"],
        keywords={
            "en": ["journaling", "diary", "write in journal", "writing prompt"],
            "zh": ["日记", "写作"],
            "ar": ["كتابة"],
            "es": ["diario", "escritura", "escribir"],
        },
        negative_keywords=["journalist", "journalism"],
    ))

    register(FulfillerSpec(
        name="bucket_list", fulfiller_class="BucketListFulfiller",
        module="wish_engine.l2_bucket_list", priority=15,
        exact_phrases=["bucket list", "things to do before", "find purpose"],
        keywords={
            "en": ["bucket list", "life goals", "things I want to do", "purpose", "find meaning"],
            "zh": ["清单", "想做的事", "人生目标"],
            "ar": ["قائمة أمنيات"],
            "es": ["lista de deseos", "metas de vida", "propósito"],
        },
    ))

    # ═══ COURSES & LEARNING ═══
    register(FulfillerSpec(
        name="courses", fulfiller_class="CourseFulfiller",
        module="wish_engine.l2_courses", priority=10,
        exact_phrases=["learn english", "learn spanish", "learn french", "learn arabic", "learn chinese"],
        keywords={
            "en": ["course", "class", "learn", "study", "training", "workshop", "tutorial"],
            "zh": ["课程", "学", "培训"],
            "ar": ["دورة", "تعلم"],
            "es": ["curso", "clase", "aprender", "estudiar", "formación"],
            "ja": ["コース", "学ぶ", "勉強"],
            "ko": ["수업", "배우다"],
        },
        negative_keywords=["course tracker"],
    ))

    register(FulfillerSpec(
        name="books", fulfiller_class="BookFulfiller",
        module="wish_engine.l2_books", priority=5,
        keywords={
            "en": ["book", "read", "reading", "bookshop"],
            "zh": ["书", "读", "阅读"],
            "ar": ["كتاب", "قراءة"],
            "es": ["libro", "leer", "lectura"],
            "ja": ["本", "読む"],
        },
    ))

    # ═══ REMAINING LIFESTYLE (low priority, catch-all) ═══

    for name, cls, mod, kws in [
        ("fashion", "FashionFulfiller", "wish_engine.l2_fashion", {"en": ["fashion", "style", "outfit", "clothing"], "zh": ["穿搭", "时尚"], "es": ["moda", "ropa"]}),
        ("games", "GameFulfiller", "wish_engine.l2_games", {"en": ["game", "board game", "chess", "trivia", "escape room"], "zh": ["游戏", "桌游"], "es": ["juego"]}),
        ("photo_spots", "PhotoSpotFulfiller", "wish_engine.l2_photo_spots", {"en": ["photo", "photography", "instagram", "photo spot"], "zh": ["拍照", "摄影"]}),
        ("podcast", "PodcastFulfiller", "wish_engine.l2_podcast", {"en": ["podcast", "audiobook"], "zh": ["播客", "有声书"]}),
        ("collecting", "CollectingFulfiller", "wish_engine.l2_collecting", {"en": ["collect", "collection", "vintage", "antique"], "zh": ["收藏", "古董"]}),
        ("astro_fun", "AstroFunFulfiller", "wish_engine.l2_astro_fun", {"en": ["zodiac", "astrology", "tarot", "horoscope"], "zh": ["星座", "塔罗"]}),
        ("habit_tracker", "HabitTrackerFulfiller", "wish_engine.l2_habit_tracker", {"en": ["habit", "track habit", "daily habit"], "zh": ["习惯", "打卡"]}),
        ("micro_challenge", "MicroChallengeFulfiller", "wish_engine.l2_micro_challenge", {"en": ["challenge", "dare", "push myself"], "zh": ["挑战", "试试"]}),
        ("mindfulness", "MindfulnessFulfiller", "wish_engine.l2_mindfulness", {"en": ["meditation", "mindfulness", "zen"], "zh": ["冥想", "正念"], "ar": ["تأمل"]}),
        ("weekend_planner", "WeekendPlannerFulfiller", "wish_engine.l2_weekend_planner", {"en": ["weekend", "weekend plan", "what to do this weekend"], "zh": ["周末"]}),
        ("housing", "HousingFulfiller", "wish_engine.l2_housing", {"en": ["housing", "apartment", "roommate", "rent"], "zh": ["租房", "合租"]}),
        ("secondhand", "SecondhandFulfiller", "wish_engine.l2_secondhand", {"en": ["secondhand", "thrift", "swap", "used"], "zh": ["二手", "闲置"]}),
        ("ramadan", "FestivalFulfiller", "wish_engine.l2_ramadan", {"en": ["ramadan", "eid", "festival", "holiday"], "zh": ["斋月", "节日", "春节"], "ar": ["رمضان", "عيد"]}),
        ("local_guide", "LocalGuideFulfiller", "wish_engine.l2_local_guide", {"en": ["local guide", "hidden gem", "secret spot", "local secret"], "zh": ["本地", "隐藏"]}),
        ("prayer_times", "PlaceFulfiller", "wish_engine.l2_places", {"en": ["prayer", "mosque", "fajr", "dhuhr", "asr", "maghrib", "isha"], "zh": ["祈祷", "清真寺"], "ar": ["صلاة", "مسجد"]}),
        ("accessibility", "AccessibilityFulfiller", "wish_engine.l2_accessibility", {"en": ["accessible", "wheelchair", "disability access"], "zh": ["无障碍"]}),
        ("allergy_friendly", "AllergyFriendlyFulfiller", "wish_engine.l2_allergy_friendly", {"en": ["allergy", "gluten free", "nut free", "allergen"], "zh": ["过敏"]}),
        ("noise_map", "NoiseMapFulfiller", "wish_engine.l2_noise_map", {"en": ["noise level", "noise map", "quiet area", "sound level"], "zh": ["噪音"]}),
        ("air_quality", "AirQualityFulfiller", "wish_engine.l2_air_quality", {"en": ["air quality", "pollution", "pm2.5", "smog"], "zh": ["空气质量", "雾霾"]}),
        ("night_owl", "NightOwlFulfiller", "wish_engine.l2_night_owl", {"en": ["late night", "night owl", "midnight", "insomnia activity"], "zh": ["夜猫子", "深夜"]}),
        ("early_bird", "EarlyBirdFulfiller", "wish_engine.l2_early_bird", {"en": ["sunrise", "early morning", "dawn", "early bird"], "zh": ["早起", "日出"]}),
        ("rainy_day", "RainyDayFulfiller", "wish_engine.l2_rainy_day", {"en": ["rainy day", "raining outside", "rain day"], "zh": ["下雨", "雨天"]}),
        ("extreme_weather", "ExtremeWeatherFulfiller", "wish_engine.l2_extreme_weather", {"en": ["heatwave", "storm", "blizzard", "sandstorm", "extreme weather"], "zh": ["极端天气", "暴风"]}),
        ("pregnancy", "PregnancyFulfiller", "wish_engine.l2_pregnancy", {"en": ["pregnant", "prenatal", "expecting", "maternity"], "zh": ["孕期", "怀孕"]}),
        ("life_stage", "LifeStageFulfiller", "wish_engine.l2_life_stage", {"en": ["graduation", "retirement", "milestone", "life stage"], "zh": ["人生阶段", "毕业", "退休"]}),
        ("elderly_care", "ElderlyCareFulfiller", "wish_engine.l2_elderly_care", {"en": ["elderly", "senior", "aging parent"], "zh": ["长辈", "老人"]}),
        ("family_dining", "FamilyDiningFulfiller", "wish_engine.l2_family_dining", {"en": ["family dinner", "family restaurant", "big table"], "zh": ["聚餐", "家庭"]}),
        ("wedding", "WeddingFulfiller", "wish_engine.l2_wedding", {"en": ["wedding", "bridal", "engagement"], "zh": ["婚礼", "结婚"]}),
        ("memory_map", "MemoryMapFulfiller", "wish_engine.l2_memory_map", {"en": ["memory", "remember", "special place"], "zh": ["回忆", "纪念"]}),
        ("gratitude", "GratitudeFulfiller", "wish_engine.l2_gratitude", {"en": ["gratitude", "thankful", "appreciate"], "zh": ["感恩", "感谢"]}),
        ("moving", "MovingFulfiller", "wish_engine.l2_moving", {"en": ["moving", "relocate", "new home"], "zh": ["搬家"]}),
        ("home_decor", "HomeDecorFulfiller", "wish_engine.l2_home_decor", {"en": ["home decor", "interior", "furniture"], "zh": ["家居", "装修"]}),
        ("parking", "ParkingFulfiller", "wish_engine.l2_parking", {"en": ["parking", "park my car"], "zh": ["停车"]}),
        ("ev_charging", "EVChargingFulfiller", "wish_engine.l2_ev_charging", {"en": ["ev charging", "electric vehicle", "charger", "gas station"], "zh": ["充电桩", "加油"]}),
        ("local_services", "LocalServiceFulfiller", "wish_engine.l2_services", {"en": ["print shop", "courier", "laundry", "repair"], "zh": ["打印", "快递", "洗衣"]}),
        ("late_night", "LateNightFulfiller", "wish_engine.l2_late_night", {"en": ["24 hour", "24h", "open late", "all night", "late night pharmacy"], "zh": ["24小时", "便利店", "药店"]}),
        ("personal_brand", "PersonalBrandFulfiller", "wish_engine.l2_personal_brand", {"en": ["portfolio", "personal brand", "showcase"], "zh": ["品牌", "作品集"]}),
        ("public_speaking", "PublicSpeakingFulfiller", "wish_engine.l2_public_speaking", {"en": ["public speaking", "presentation", "ted talk", "toastmasters"], "zh": ["演讲"]}),
        ("interview_prep", "InterviewPrepFulfiller", "wish_engine.l2_interview_prep", {"en": ["interview", "job interview", "resume"], "zh": ["面试", "简历"]}),
        ("personality_growth", "PersonalityGrowthFulfiller", "wish_engine.l2_personality_growth", {"en": ["personal growth", "self-improvement", "develop myself"], "zh": ["成长", "提升"]}),
        ("skill_exchange", "SkillExchangeFulfiller", "wish_engine.l2_skill_exchange", {"en": ["skill exchange", "teach me", "swap skills"], "zh": ["技能交换"]}),
        ("course_tracker", "CourseTrackerFulfiller", "wish_engine.l2_course_tracker", {"en": ["course progress", "continue course", "finish course"], "zh": ["课程进度"]}),
        ("health_sync", "HealthSyncFulfiller", "wish_engine.l2_health_sync", {"en": ["health data", "step count", "heart rate", "apple watch", "fitbit"], "zh": ["健康数据", "步数"]}),
        ("seasonal_wellness", "SeasonalWellnessFulfiller", "wish_engine.l2_seasonal_wellness", {"en": ["seasonal wellness", "hay fever", "winter blues"], "zh": ["节气", "养生"]}),
        ("seasonal_activities", "SeasonalActivityFulfiller", "wish_engine.l2_seasonal_activities", {"en": ["cherry blossom", "autumn leaves", "ice skating", "summer camping"], "zh": ["赏花", "露营"]}),
        ("culture_bridge", "CultureBridgeFulfiller", "wish_engine.l2_culture_bridge", {"en": ["cross-cultural", "intercultural", "culture exchange"], "zh": ["跨文化"]}),
        ("history_stories", "HistoryStoryFulfiller", "wish_engine.l2_history_stories", {"en": ["history", "historic site", "heritage site"], "zh": ["历史", "遗迹"]}),
        ("language_env", "LanguageEnvFulfiller", "wish_engine.l2_language_env", {"en": ["language practice", "language immersion", "practice english"], "zh": ["语言环境", "练口语"]}),
        ("reviews", "ReviewsFulfiller", "wish_engine.l2_reviews", {"en": ["review", "rating", "reviews"], "zh": ["评价", "评分"]}),
        ("emotion_calendar", "EmotionCalendarFulfiller", "wish_engine.l2_emotion_calendar", {"en": ["mood calendar", "emotion calendar", "mood tracker"], "zh": ["情绪日历"]}),
        ("dream_journal", "DreamJournalFulfiller", "wish_engine.l2_dream_journal", {"en": ["dream", "nightmare", "dream journal"], "zh": ["梦", "梦境"]}),
        ("digital_detox", "DigitalDetoxFulfiller", "wish_engine.l2_digital_detox", {"en": ["digital detox", "screen time", "phone addiction"], "zh": ["数字排毒", "屏幕时间"]}),
        ("emotion_weather", "EmotionWeatherFulfiller", "wish_engine.l2_emotion_weather", {"en": ["emotion weather", "local mood", "neighborhood vibe"], "zh": ["情绪天气"]}),
        ("pet_training", "PetTrainingFulfiller", "wish_engine.l2_pet_training", {"en": ["dog training", "pet training", "puppy"], "zh": ["训犬", "宠物训练"]}),
        ("intergenerational", "IntergenerationalFulfiller", "wish_engine.l2_intergenerational", {"en": ["intergenerational", "cross-age", "bridge generations"], "zh": ["代际", "跨代"]}),
        ("neighborhood", "NeighborhoodFulfiller", "wish_engine.l2_neighborhood", {"en": ["neighborhood", "community board", "local community"], "zh": ["邻里", "社区"]}),
    ]:
        register(FulfillerSpec(
            name=name, fulfiller_class=cls, module=mod, priority=10, keywords=kws,
        ))

    # Default fallback fulfillers (by WishType)
    register(FulfillerSpec(
        name="places", fulfiller_class="PlaceFulfiller",
        module="wish_engine.l2_places", priority=5,
        keywords={"en": ["place", "nearby", "around here", "find a place"], "zh": ["附近", "地方"]},
    ))

    register(FulfillerSpec(
        name="career", fulfiller_class="CareerFulfiller",
        module="wish_engine.l2_career", priority=10,
        keywords={"en": ["career", "job", "profession"], "zh": ["职业", "工作方向"]},
    ))

    register(FulfillerSpec(
        name="wellness", fulfiller_class="WellnessFulfiller",
        module="wish_engine.l2_wellness", priority=5,
        keywords={"en": ["wellness", "wellbeing", "health", "relax"], "zh": ["健康", "放松"]},
    ))
