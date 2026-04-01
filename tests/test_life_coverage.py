"""Tests: Life need coverage expansion — 30+ new attention types.

Covers:
  1. Detection tests for each new attention type
  2. Bridge tests: crisis types must have crisis_apis as first action
  3. Coverage test: all 77+ attention types have SOUL_API_MAP entries
"""
import pytest
from wish_engine.soul_recommender import detect_surface_attention
from wish_engine.soul_api_bridge import SOUL_API_MAP, get_api_actions
from wish_engine.apis.crisis_apis import get_crisis_resources, is_available


# ── Crisis APIs ───────────────────────────────────────────────────────────────

class TestCrisisApis:
    def test_is_available(self):
        assert is_available() is True

    def test_suicide_resources_returns_dict(self):
        result = get_crisis_resources(crisis_type="suicide")
        assert isinstance(result, dict)
        assert "title" in result
        assert "description" in result
        assert "hotlines" in result
        assert "result" in result
        assert "primary_name" in result

    def test_domestic_violence_resources(self):
        result = get_crisis_resources(crisis_type="domestic_violence")
        assert result["title"] == "DV Hotline — Confidential 24/7"
        assert len(result["hotlines"]) > 0

    def test_addiction_resources(self):
        result = get_crisis_resources(crisis_type="addiction")
        assert result["title"] == "Addiction Support Line"

    def test_mental_health_resources(self):
        result = get_crisis_resources(crisis_type="mental_health")
        assert result["title"] == "Mental Health Support"

    def test_country_specific(self):
        result = get_crisis_resources(crisis_type="suicide", country_code="GB")
        names = [r["name"] for r in result["hotlines"]]
        assert any("Samaritans" in n for n in names)

    def test_unknown_type_falls_back_to_suicide(self):
        result = get_crisis_resources(crisis_type="unknown_type")
        assert result is not None
        assert len(result["hotlines"]) > 0

    def test_primary_number_present(self):
        result = get_crisis_resources(crisis_type="suicide")
        # primary_number can be None for text-only entries but result should exist
        assert "primary_number" in result
        assert "primary_name" in result


# ── Detection Tests ───────────────────────────────────────────────────────────

class TestCriticalSafetyDetection:
    def test_suicidal_ideation_direct(self):
        assert "suicidal_ideation" in detect_surface_attention(["I'm feeling suicidal"])

    def test_suicidal_ideation_indirect(self):
        assert "suicidal_ideation" in detect_surface_attention(["thinking about ending things"])

    def test_suicidal_ideation_want_to_die(self):
        assert "suicidal_ideation" in detect_surface_attention(["I want to die"])

    def test_suicidal_ideation_chinese(self):
        assert "suicidal_ideation" in detect_surface_attention(["我不想活了"])

    def test_domestic_violence_direct(self):
        assert "domestic_violence" in detect_surface_attention(["he hit me last night"])

    def test_domestic_violence_indirect(self):
        assert "domestic_violence" in detect_surface_attention(["I'm walking on eggshells all the time"])

    def test_domestic_violence_scared(self):
        assert "domestic_violence" in detect_surface_attention(["I'm scared to go home"])

    def test_domestic_violence_chinese(self):
        assert "domestic_violence" in detect_surface_attention(["他家暴我"])

    def test_addiction_crisis_direct(self):
        assert "addiction_crisis" in detect_surface_attention(["I relapsed yesterday"])

    def test_addiction_crisis_indirect(self):
        assert "addiction_crisis" in detect_surface_attention(["drinking is out of control"])

    def test_addiction_crisis_withdrawal(self):
        assert "addiction_crisis" in detect_surface_attention(["going through withdrawal"])

    def test_homelessness_direct(self):
        assert "homelessness" in detect_surface_attention(["I'm homeless"])

    def test_homelessness_sleeping_rough(self):
        assert "homelessness" in detect_surface_attention(["I've been sleeping rough for a week"])

    def test_homelessness_car(self):
        assert "homelessness" in detect_surface_attention(["I'm sleeping in my car now"])


class TestMentalHealthDetection:
    def test_need_therapy_direct(self):
        assert "need_therapy" in detect_surface_attention(["I need to find a therapist"])

    def test_need_therapy_indirect(self):
        assert "need_therapy" in detect_surface_attention(["I'm thinking about starting therapy"])

    def test_trauma_ptsd_direct(self):
        assert "trauma_ptsd" in detect_surface_attention(["I have ptsd from what happened"])

    def test_trauma_ptsd_flashbacks(self):
        assert "trauma_ptsd" in detect_surface_attention(["these flashbacks won't stop"])

    def test_trauma_ptsd_intrusive(self):
        assert "trauma_ptsd" in detect_surface_attention(["I keep having intrusive thoughts"])

    def test_eating_disorder_direct(self):
        assert "eating_disorder" in detect_surface_attention(["I have an eating disorder"])

    def test_eating_disorder_purging(self):
        assert "eating_disorder" in detect_surface_attention(["I've been purging after every meal"])

    def test_postpartum_direct(self):
        assert "postpartum" in detect_surface_attention(["I have postpartum depression"])

    def test_postpartum_indirect(self):
        assert "postpartum" in detect_surface_attention(["since having the baby i can't stop crying"])


class TestFinancialDetection:
    def test_debt_crisis_eviction(self):
        assert "debt_crisis" in detect_surface_attention(["I got an eviction notice"])

    def test_debt_crisis_rent(self):
        assert "debt_crisis" in detect_surface_attention(["I can't pay rent this month"])

    def test_debt_crisis_bankruptcy(self):
        assert "debt_crisis" in detect_surface_attention(["I'm considering bankruptcy"])

    def test_job_loss_fired(self):
        assert "job_loss" in detect_surface_attention(["I just got fired today"])

    def test_job_loss_laid_off(self):
        assert "job_loss" in detect_surface_attention(["I got laid off from my job"])

    def test_job_loss_redundant(self):
        assert "job_loss" in detect_surface_attention(["I was made redundant last week"])


class TestCareerDetection:
    def test_job_seeking_hunting(self):
        assert "job_seeking" in detect_surface_attention(["I've been job hunting for months"])

    def test_job_seeking_cant_find(self):
        assert "job_seeking" in detect_surface_attention(["I can't find a job anywhere"])

    def test_career_change_direct(self):
        assert "career_change" in detect_surface_attention(["I want a career change"])

    def test_career_change_indirect(self):
        assert "career_change" in detect_surface_attention(["I'm stuck in the wrong career"])


class TestHousingDetection:
    def test_need_housing_hunting(self):
        assert "need_housing" in detect_surface_attention(["I'm apartment hunting right now"])

    def test_need_housing_affordable(self):
        assert "need_housing" in detect_surface_attention(["where can I find affordable housing"])


class TestFamilyDetection:
    def test_parenting_stress_indirect(self):
        assert "parenting_stress" in detect_surface_attention(["I feel like a terrible parent"])

    def test_parenting_stress_patience(self):
        assert "parenting_stress" in detect_surface_attention(["I keep losing patience with my kids"])

    def test_need_childcare_direct(self):
        assert "need_childcare" in detect_surface_attention(["I can't find childcare anywhere"])

    def test_need_childcare_babysitter(self):
        assert "need_childcare" in detect_surface_attention(["I need a babysitter urgently"])

    def test_family_conflict_estranged(self):
        assert "family_conflict" in detect_surface_attention(["I'm estranged from my family"])

    def test_family_conflict_argument(self):
        assert "family_conflict" in detect_surface_attention(["huge argument with my dad yesterday"])

    def test_elder_care_parent(self):
        assert "elder_care" in detect_surface_attention(["my mom can't live alone anymore"])

    def test_elder_care_burnout(self):
        assert "elder_care" in detect_surface_attention(["caregiver burnout is real"])

    def test_divorce_direct(self):
        assert "divorce" in detect_surface_attention(["I'm going through a divorce"])

    def test_divorce_custody(self):
        assert "divorce" in detect_surface_attention(["we have a custody battle going on"])


class TestLegalDetection:
    def test_legal_trouble_arrested(self):
        assert "legal_trouble" in detect_surface_attention(["I got arrested yesterday"])

    def test_legal_trouble_sued(self):
        assert "legal_trouble" in detect_surface_attention(["I'm being sued"])

    def test_legal_trouble_lawyer(self):
        assert "legal_trouble" in detect_surface_attention(["I can't afford a lawyer"])

    def test_immigration_stress_deported(self):
        assert "immigration_stress" in detect_surface_attention(["I'm scared of being deported"])

    def test_immigration_stress_visa(self):
        assert "immigration_stress" in detect_surface_attention(["my visa is running out"])

    def test_immigration_stress_papers(self):
        assert "immigration_stress" in detect_surface_attention(["I don't have papers"])


class TestHealthDetection:
    def test_chronic_pain_direct(self):
        assert "chronic_pain" in detect_surface_attention(["I have chronic pain every day"])

    def test_chronic_pain_months(self):
        assert "chronic_pain" in detect_surface_attention(["been in pain for months"])

    def test_need_dental_toothache(self):
        assert "need_dental" in detect_surface_attention(["I have a terrible toothache"])

    def test_need_dental_cant_afford(self):
        assert "need_dental" in detect_surface_attention(["I can't afford a dentist"])

    def test_disability_access_direct(self):
        assert "disability_access" in detect_surface_attention(["I use a wheelchair and need accessibility"])

    def test_disability_access_benefits(self):
        assert "disability_access" in detect_surface_attention(["I need disability benefits"])

    def test_pregnancy_direct(self):
        assert "pregnancy" in detect_surface_attention(["I just found out I'm pregnant"])

    def test_pregnancy_prenatal(self):
        assert "pregnancy" in detect_surface_attention(["I need prenatal care"])


class TestPracticalDetection:
    def test_need_vet_sick_dog(self):
        assert "need_vet" in detect_surface_attention(["my dog is sick and I need a vet"])

    def test_need_vet_emergency(self):
        assert "need_vet" in detect_surface_attention(["pet emergency, where is the nearest vet"])

    def test_home_emergency_gas(self):
        assert "home_emergency" in detect_surface_attention(["I smell gas in my apartment"])

    def test_home_emergency_locked_out(self):
        assert "home_emergency" in detect_surface_attention(["I'm locked out of my house"])

    def test_need_translation_barrier(self):
        assert "need_translation" in detect_surface_attention(["there's a language barrier and I need help"])

    def test_need_translation_direct(self):
        assert "need_translation" in detect_surface_attention(["I need a translator"])

    def test_food_insecurity_bank(self):
        assert "food_insecurity" in detect_surface_attention(["where is the nearest food bank"])

    def test_food_insecurity_cant_afford(self):
        assert "food_insecurity" in detect_surface_attention(["I can't afford groceries this week"])

    def test_food_insecurity_children(self):
        assert "food_insecurity" in detect_surface_attention(["my children haven't eaten today"])

    def test_need_clothes_warm(self):
        assert "need_clothes" in detect_surface_attention(["I don't have a winter coat"])

    def test_need_clothes_free(self):
        assert "need_clothes" in detect_surface_attention(["where to find free clothing"])

    def test_tech_help_broken_laptop(self):
        assert "tech_help" in detect_surface_attention(["my laptop is broken"])

    def test_tech_help_free(self):
        assert "tech_help" in detect_surface_attention(["where to get tech help for free"])


# ── Bridge Tests: crisis types must call crisis_apis first ────────────────────

class TestCrisisBridgeOrdering:
    def test_suicidal_ideation_first_action_is_crisis_apis(self):
        actions = get_api_actions("suicidal_ideation")
        assert len(actions) > 0, "No actions for suicidal_ideation"
        first = actions[0]
        assert first["api"] == "wish_engine.apis.crisis_apis", (
            f"First action for suicidal_ideation must be crisis_apis, got: {first['api']}"
        )
        assert first["fn"] == "get_crisis_resources"
        assert first["params"]["crisis_type"] == "suicide"

    def test_domestic_violence_first_action_is_crisis_apis(self):
        actions = get_api_actions("domestic_violence")
        assert len(actions) > 0, "No actions for domestic_violence"
        first = actions[0]
        assert first["api"] == "wish_engine.apis.crisis_apis", (
            f"First action for domestic_violence must be crisis_apis, got: {first['api']}"
        )
        assert first["fn"] == "get_crisis_resources"
        assert first["params"]["crisis_type"] == "domestic_violence"

    def test_addiction_crisis_first_action_is_crisis_apis(self):
        actions = get_api_actions("addiction_crisis")
        assert len(actions) > 0, "No actions for addiction_crisis"
        first = actions[0]
        assert first["api"] == "wish_engine.apis.crisis_apis", (
            f"First action for addiction_crisis must be crisis_apis, got: {first['api']}"
        )
        assert first["fn"] == "get_crisis_resources"
        assert first["params"]["crisis_type"] == "addiction"

    def test_need_therapy_first_action_is_crisis_apis(self):
        actions = get_api_actions("need_therapy")
        assert len(actions) > 0
        first = actions[0]
        assert first["api"] == "wish_engine.apis.crisis_apis"
        assert first["params"]["crisis_type"] == "mental_health"

    def test_trauma_ptsd_first_action_is_crisis_apis(self):
        actions = get_api_actions("trauma_ptsd")
        assert len(actions) > 0
        assert actions[0]["api"] == "wish_engine.apis.crisis_apis"

    def test_eating_disorder_first_action_is_crisis_apis(self):
        actions = get_api_actions("eating_disorder")
        assert len(actions) > 0
        assert actions[0]["api"] == "wish_engine.apis.crisis_apis"

    def test_postpartum_first_action_is_crisis_apis(self):
        actions = get_api_actions("postpartum")
        assert len(actions) > 0
        assert actions[0]["api"] == "wish_engine.apis.crisis_apis"


# ── Coverage Test: all new attention types have SOUL_API_MAP entries ──────────

class TestNewAttentionCoverage:
    NEW_ATTENTION_TYPES = [
        # Critical
        "suicidal_ideation", "domestic_violence", "addiction_crisis", "homelessness",
        # Mental health
        "need_therapy", "trauma_ptsd", "eating_disorder", "postpartum",
        # Financial
        "debt_crisis", "job_loss",
        # Career
        "job_seeking", "career_change",
        # Housing
        "need_housing",
        # Family
        "parenting_stress", "need_childcare", "family_conflict", "elder_care", "divorce",
        # Legal
        "legal_trouble", "immigration_stress",
        # Health
        "chronic_pain", "need_dental", "disability_access", "pregnancy",
        # Practical
        "need_vet", "home_emergency", "need_translation",
        "food_insecurity", "need_clothes", "tech_help",
    ]

    def test_all_new_types_in_soul_api_map(self):
        missing = [t for t in self.NEW_ATTENTION_TYPES if t not in SOUL_API_MAP]
        assert not missing, f"Missing from SOUL_API_MAP: {missing}"

    def test_all_new_types_have_actions(self):
        for attention in self.NEW_ATTENTION_TYPES:
            actions = get_api_actions(attention)
            assert len(actions) > 0, f"No bridge actions for '{attention}'"

    def test_total_map_has_70_plus_entries(self):
        assert len(SOUL_API_MAP) >= 70, (
            f"SOUL_API_MAP should have 70+ entries, got {len(SOUL_API_MAP)}"
        )

    def test_all_new_types_detectable(self):
        """Smoke test: at least one phrase per type triggers detection."""
        trigger_map = {
            "suicidal_ideation":  "I'm feeling suicidal",
            "domestic_violence":  "he hit me last night",
            "addiction_crisis":   "I relapsed yesterday",
            "homelessness":       "I'm homeless right now",
            "need_therapy":       "I need to find a therapist",
            "trauma_ptsd":        "I have ptsd from what happened",
            "eating_disorder":    "I have an eating disorder",
            "postpartum":         "I have postpartum depression",
            "debt_crisis":        "I can't pay rent this month",
            "job_loss":           "I just got fired",
            "job_seeking":        "I've been job hunting for months",
            "career_change":      "I want a career change",
            "need_housing":       "I'm apartment hunting",
            "parenting_stress":   "I feel like a terrible parent",
            "need_childcare":     "I can't find childcare",
            "family_conflict":    "huge argument with my dad",
            "elder_care":         "my mom can't live alone anymore",
            "divorce":            "I'm going through a divorce",
            "legal_trouble":      "I got arrested",
            "immigration_stress": "scared of being deported",
            "chronic_pain":       "I have chronic pain every day",
            "need_dental":        "I have a terrible toothache",
            "disability_access":  "I use a wheelchair and need accessibility",
            "pregnancy":          "I just found out I'm pregnant",
            "need_vet":           "my dog is sick and I need a vet",
            "home_emergency":     "I smell gas in my apartment",
            "need_translation":   "there's a language barrier",
            "food_insecurity":    "where is the nearest food bank",
            "need_clothes":       "I don't have a winter coat",
            "tech_help":          "my laptop is broken",
        }
        undetected = []
        for attention, text in trigger_map.items():
            detected = detect_surface_attention([text])
            if attention not in detected:
                undetected.append((attention, text, detected))
        if undetected:
            msg = "\n".join(
                f"  '{att}' not detected from '{text}' (got: {got})"
                for att, text, got in undetected
            )
            pytest.fail(f"Undetected new attention types:\n{msg}")
