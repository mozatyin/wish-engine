"""Tests for the score-based L2 router."""

import pytest
from wish_engine.l2_router import FulfillerSpec, route, REGISTRY, _build_registry
from wish_engine.models import WishType


# ── Helper ────────────────────────────────────────────────────────────────────

def _ensure_registry():
    """Make sure registry is built before tests."""
    if not REGISTRY:
        _build_registry()


# ── Crisis routing ────────────────────────────────────────────────────────────

class TestCrisisRouting:
    """Crisis keywords must always route to crisis fulfillers."""

    def test_suicide_english(self):
        _ensure_registry()
        mod, cls = route("I want to kill myself")
        assert cls == "SuicidePreventionFulfiller"

    def test_suicide_chinese(self):
        _ensure_registry()
        mod, cls = route("我不想活了，想自杀")
        assert cls == "SuicidePreventionFulfiller"

    def test_suicide_arabic(self):
        _ensure_registry()
        mod, cls = route("أريد انتحار")
        assert cls == "SuicidePreventionFulfiller"

    def test_suicide_spanish(self):
        _ensure_registry()
        mod, cls = route("no quiero vivir más, suicidio")
        assert cls == "SuicidePreventionFulfiller"

    def test_suicide_french(self):
        _ensure_registry()
        mod, cls = route("je veux me tuer")
        assert cls == "SuicidePreventionFulfiller"

    def test_suicide_japanese(self):
        _ensure_registry()
        mod, cls = route("死にたい")
        assert cls == "SuicidePreventionFulfiller"

    def test_suicide_korean(self):
        _ensure_registry()
        mod, cls = route("죽고 싶다")
        assert cls == "SuicidePreventionFulfiller"

    def test_suicide_hindi(self):
        _ensure_registry()
        mod, cls = route("आत्महत्या करना चाहता हूं")
        assert cls == "SuicidePreventionFulfiller"

    def test_suicide_russian(self):
        _ensure_registry()
        mod, cls = route("не хочу жить больше")
        assert cls == "SuicidePreventionFulfiller"

    def test_suicide_portuguese(self):
        _ensure_registry()
        mod, cls = route("não quero viver mais")
        assert cls == "SuicidePreventionFulfiller"

    def test_domestic_violence(self):
        _ensure_registry()
        mod, cls = route("he hits me every day, domestic violence")
        assert cls == "DomesticViolenceFulfiller"

    def test_domestic_violence_chinese(self):
        _ensure_registry()
        mod, cls = route("他打我，家暴")
        assert cls == "DomesticViolenceFulfiller"

    def test_emergency_shelter(self):
        _ensure_registry()
        mod, cls = route("I'm homeless and have nowhere to go")
        assert cls == "EmergencyShelterFulfiller"

    def test_debt_crisis(self):
        _ensure_registry()
        mod, cls = route("I'm drowning in debt and collectors keep calling")
        assert cls == "DebtCrisisFulfiller"

    def test_collective_trauma(self):
        _ensure_registry()
        mod, cls = route("I have PTSD from war trauma")
        assert cls == "CollectiveTraumaFulfiller"


# ── Substring collision prevention ────────────────────────────────────────────

class TestSubstringCollisions:
    """Ensure substring collisions are fixed."""

    def test_training_not_raining(self):
        """'raining outside' should NOT match 'training' fulfiller."""
        _ensure_registry()
        mod, cls = route("it's raining outside, what to do")
        assert cls != "CourseFulfiller"  # "training" is a courses keyword

    def test_journalist_not_journal(self):
        """'journalist' should NOT route to writing/journaling."""
        _ensure_registry()
        mod, cls = route("I'm a journalist at a newspaper")
        assert cls != "WritingFulfiller"

    def test_sleepover_not_sleep(self):
        """'sleepover' should NOT route to sleep fulfiller."""
        _ensure_registry()
        mod, cls = route("I want to plan a sleepover party for kids")
        assert cls != "SleepEnvFulfiller"

    def test_musician_not_music(self):
        """'musician' in context should not mis-route to music listening."""
        _ensure_registry()
        mod, cls = route("I want to become a professional musician and learn music composition")
        assert cls != "MusicFulfiller"

    def test_financial_ruin_goes_to_debt_not_finance(self):
        """'financial ruin' should go to debt crisis, not finance."""
        _ensure_registry()
        mod, cls = route("I'm facing financial ruin and can't pay my bills")
        assert cls == "DebtCrisisFulfiller"


# ── Multi-language routing ────────────────────────────────────────────────────

class TestMultiLanguageRouting:
    """Test routing across languages."""

    def test_spanish_addiction(self):
        _ensure_registry()
        mod, cls = route("tengo una adicción al alcohol, necesito rehabilitación")
        assert cls == "AddictionMeetingFulfiller"

    def test_japanese_panic(self):
        _ensure_registry()
        mod, cls = route("パニック発作が起きた")
        assert cls == "PanicReliefFulfiller"

    def test_arabic_bereavement(self):
        _ensure_registry()
        mod, cls = route("أحتاج إلى عزاء بعد فقدان")
        assert cls == "BereavementFulfiller"

    def test_chinese_breakup(self):
        _ensure_registry()
        mod, cls = route("我们分手了，我很失恋")
        assert cls == "BreakupHealingFulfiller"

    def test_russian_breakup(self):
        _ensure_registry()
        mod, cls = route("расставание, я переживаю развод")
        assert cls == "BreakupHealingFulfiller"

    def test_chinese_sleep(self):
        _ensure_registry()
        mod, cls = route("我失眠了，睡不着")
        assert cls == "SleepEnvFulfiller"

    def test_arabic_immigration(self):
        _ensure_registry()
        mod, cls = route("أحتاج تأشيرة هجرة")
        assert cls == "ImmigrationFulfiller"


# ── Priority ordering ─────────────────────────────────────────────────────────

class TestPriorityOrdering:
    """Crisis fulfillers should win over lower-priority matches."""

    def test_crisis_beats_daily(self):
        """Suicide keywords beat any daily life keywords."""
        _ensure_registry()
        mod, cls = route("I want to kill myself, I can't sleep")
        assert cls == "SuicidePreventionFulfiller"

    def test_crisis_beats_grief(self):
        """Suicide with grief context still routes to suicide."""
        _ensure_registry()
        mod, cls = route("after my loss I want to end my life, suicide")
        assert cls == "SuicidePreventionFulfiller"

    def test_grief_beats_daily(self):
        """Grief keywords should beat regular daily life matches."""
        _ensure_registry()
        mod, cls = route("I'm grieving the loss of my loved one, need bereavement support")
        assert cls == "BereavementFulfiller"

    def test_addiction_beats_lifestyle(self):
        """Addiction keywords should beat casual matches."""
        _ensure_registry()
        mod, cls = route("I need to find an AA meeting for my alcoholic recovery")
        assert cls == "AddictionMeetingFulfiller"


# ── Negative keywords ─────────────────────────────────────────────────────────

class TestNegativeKeywords:
    """Negative keywords should prevent routing."""

    def test_journalist_avoids_writing(self):
        _ensure_registry()
        mod, cls = route("I want to become a journalist")
        assert cls != "WritingFulfiller"

    def test_financial_ruin_avoids_finance(self):
        _ensure_registry()
        mod, cls = route("I'm in financial ruin")
        assert cls != "FinanceFulfiller"

    def test_sleepover_avoids_sleep(self):
        _ensure_registry()
        mod, cls = route("organizing a sleepover party")
        assert cls != "SleepEnvFulfiller"


# ── Fallback routing ──────────────────────────────────────────────────────────

class TestFallback:
    """Unknown text should fallback based on WishType."""

    def test_fallback_find_place(self):
        _ensure_registry()
        mod, cls = route("xyzzy gibberish", WishType.FIND_PLACE)
        assert cls == "PlaceFulfiller"

    def test_fallback_find_resource(self):
        _ensure_registry()
        mod, cls = route("xyzzy gibberish", WishType.FIND_RESOURCE)
        assert cls == "BookFulfiller"

    def test_fallback_learn_skill(self):
        _ensure_registry()
        mod, cls = route("xyzzy gibberish", WishType.LEARN_SKILL)
        assert cls == "CourseFulfiller"

    def test_fallback_career(self):
        _ensure_registry()
        mod, cls = route("xyzzy gibberish", WishType.CAREER_DIRECTION)
        assert cls == "CareerFulfiller"

    def test_fallback_health(self):
        _ensure_registry()
        mod, cls = route("xyzzy gibberish", WishType.HEALTH_WELLNESS)
        assert cls == "WellnessFulfiller"

    def test_fallback_no_type(self):
        _ensure_registry()
        mod, cls = route("xyzzy gibberish")
        assert cls == "BookFulfiller"  # ultimate fallback


# ── FulfillerSpec scoring ─────────────────────────────────────────────────────

class TestFulfillerSpecScoring:
    """Unit tests for the scoring mechanism."""

    def test_exact_phrase_scores_highest(self):
        spec = FulfillerSpec(
            name="test", fulfiller_class="Test", module="test",
            keywords={"en": ["sleep"]},
            exact_phrases=["can't sleep"],
        )
        score_exact = spec.score("I can't sleep at night")
        score_keyword = spec.score("I need better sleep hygiene")
        assert score_exact > score_keyword

    def test_negative_keyword_blocks(self):
        spec = FulfillerSpec(
            name="test", fulfiller_class="Test", module="test",
            keywords={"en": ["writing", "journal"]},
            negative_keywords=["journalist"],
        )
        assert spec.score("I am a journalist") == -1000.0

    def test_word_boundary_beats_substring(self):
        spec = FulfillerSpec(
            name="test", fulfiller_class="Test", module="test",
            keywords={"en": ["rain"]},
        )
        # "rain" has word boundary in "it's rain outside"
        score_boundary = spec.score("it's rain outside")
        # "rain" as substring in "training" — "rain" is only 4 chars
        # but with word boundary, "training" won't match \brain\b
        score_sub = spec.score("I need training")
        assert score_boundary > score_sub

    def test_priority_bonus_applied(self):
        crisis = FulfillerSpec(
            name="crisis", fulfiller_class="Crisis", module="test",
            keywords={"en": ["help"]}, priority=100,
        )
        normal = FulfillerSpec(
            name="normal", fulfiller_class="Normal", module="test",
            keywords={"en": ["help"]}, priority=0,
        )
        assert crisis.score("I need help") > normal.score("I need help")

    def test_multi_match_bonus(self):
        spec = FulfillerSpec(
            name="test", fulfiller_class="Test", module="test",
            keywords={"en": ["grief", "mourning", "bereavement"]},
        )
        score_one = spec.score("I'm in grief")
        score_multi = spec.score("I'm in grief and mourning and bereavement")
        assert score_multi > score_one

    def test_zero_score_for_no_match(self):
        spec = FulfillerSpec(
            name="test", fulfiller_class="Test", module="test",
            keywords={"en": ["zebra"]},
        )
        assert spec.score("I want pizza") == 0.0

    def test_no_priority_bonus_without_match(self):
        spec = FulfillerSpec(
            name="test", fulfiller_class="Test", module="test",
            keywords={"en": ["zebra"]}, priority=100,
        )
        assert spec.score("I want pizza") == 0.0


# ── Specific fulfiller routing ────────────────────────────────────────────────

class TestSpecificRouting:
    """Test that specific wish texts route to expected fulfillers."""

    def test_coworking(self):
        _ensure_registry()
        _, cls = route("I want to find a coworking space with fast wifi")
        assert cls == "CoworkingFulfiller"

    def test_confidence(self):
        _ensure_registry()
        _, cls = route("I have social anxiety, I need confidence to talk to people")
        assert cls == "ConfidenceFulfiller"

    def test_eq_training(self):
        _ensure_registry()
        _, cls = route("I need to build my emotional intelligence")
        assert cls == "EQTrainingFulfiller"

    def test_deep_social(self):
        _ensure_registry()
        _, cls = route("I want deep social connections, not small talk")
        assert cls == "DeepSocialFulfiller"

    def test_music(self):
        _ensure_registry()
        _, cls = route("I want to listen to music alone that matches my melancholy")
        assert cls == "MusicFulfiller"

    def test_startup(self):
        _ensure_registry()
        _, cls = route("I need to find investors for my startup")
        assert cls == "StartupResourceFulfiller"

    def test_legacy(self):
        _ensure_registry()
        _, cls = route("I want to plan my legacy — what will I leave behind")
        assert cls == "LegacyPlanningFulfiller"

    def test_hometown_food(self):
        _ensure_registry()
        _, cls = route("I want authentic food that reminds me of home, I miss home")
        assert cls == "HometownFoodFulfiller"

    def test_events(self):
        _ensure_registry()
        _, cls = route("I want to attend a literary event or book signing tonight")
        assert cls == "EventFulfiller"

    def test_identity_exploration(self):
        _ensure_registry()
        _, cls = route("I need to explore my identity — who am I really?")
        assert cls == "IdentityExplorationFulfiller"

    def test_pet_loss(self):
        _ensure_registry()
        _, cls = route("my dog died yesterday, I'm devastated")
        assert cls == "PetLossFulfiller"

    def test_pregnancy_loss(self):
        _ensure_registry()
        _, cls = route("I had a miscarriage last week")
        assert cls == "PregnancyLossFulfiller"

    def test_caregiver_respite(self):
        _ensure_registry()
        _, cls = route("I'm exhausted from caring for my mother, need caregiver respite")
        assert cls == "CaregiverRespiteFulfiller"

    def test_legal_aid(self):
        _ensure_registry()
        _, cls = route("I need a lawyer for legal aid")
        assert cls == "LegalAidFulfiller"

    def test_volunteer(self):
        _ensure_registry()
        _, cls = route("I want to volunteer and give back to the community")
        assert cls == "VolunteerFulfiller"

    def test_nature_healing(self):
        _ensure_registry()
        _, cls = route("I want to go hiking in the forest for nature healing")
        assert cls == "NatureHealingFulfiller"

    def test_poetry(self):
        _ensure_registry()
        _, cls = route("I want to read poetry and find poems")
        assert cls == "PoetryFulfiller"

    def test_breakup(self):
        _ensure_registry()
        _, cls = route("we broke up and I'm heartbroken, need breakup healing")
        assert cls == "BreakupHealingFulfiller"

    def test_panic(self):
        _ensure_registry()
        _, cls = route("I'm having a panic attack, help me calm down")
        assert cls == "PanicReliefFulfiller"

    def test_sleep(self):
        _ensure_registry()
        _, cls = route("I can't sleep, I have insomnia")
        assert cls == "SleepEnvFulfiller"


# ── Registry completeness ────────────────────────────────────────────────────

class TestRegistryCompleteness:
    """Ensure the registry covers all expected fulfillers."""

    def test_registry_not_empty(self):
        _ensure_registry()
        assert len(REGISTRY) > 100

    def test_all_crisis_registered(self):
        _ensure_registry()
        names = {s.name for s in REGISTRY}
        for crisis in ["suicide_prevention", "domestic_violence", "emergency_shelter",
                       "debt_crisis", "collective_trauma"]:
            assert crisis in names, f"Missing crisis: {crisis}"

    def test_all_grief_registered(self):
        _ensure_registry()
        names = {s.name for s in REGISTRY}
        for grief in ["bereavement", "pet_loss", "pregnancy_loss", "farewell_ritual", "estate_items"]:
            assert grief in names, f"Missing grief: {grief}"

    def test_unique_names(self):
        _ensure_registry()
        names = [s.name for s in REGISTRY]
        assert len(names) == len(set(names)), "Duplicate names in registry"
