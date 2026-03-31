"""Tests: every attention in SOUL_API_MAP is detectable by soul_recommender.
Also covers new life-needs detection and expanded middle-soul mapping.
"""
import pytest
from wish_engine.soul_recommender import detect_surface_attention, detect_middle_history
from wish_engine.soul_api_bridge import SOUL_API_MAP, get_api_actions


# ── Coverage: every bridge attention must be reachable ───────────────────────

class TestBridgeCoverage:
    """Every key in SOUL_API_MAP should be triggerable by detect_surface_attention
    OR by detect_middle_history (some are middle/deep layer only)."""

    SURFACE_TRIGGER: dict[str, str] = {
        # existing
        "hungry":       "I'm so hungry right now",
        "thirsty":      "I'm really thirsty",
        "need_money":   "I'm broke and need money",
        "need_medicine":"I'm sick and need medicine",
        "anxious":      "I'm feeling very anxious",
        "sad":          "I'm so sad and crying",
        "angry":        "I'm furious and angry",
        "lonely":       "I feel so lonely and alone",
        "scared":       "I'm scared and afraid",
        "panicking":    "I'm having a panic attack",
        "grieving":     "my grandmother died yesterday",
        "guilty":       "I feel so guilty it's my fault",
        "want_read":    "I want to read a book",
        "want_learn":   "I want to study and learn",
        "want_art":     "I want to see art and a gallery",
        "want_music":   "I love music and concerts",
        "want_work":    "I need to work and be productive",
        "need_exercise":"I want to exercise and go to the gym",
        "need_pray":    "I need to pray at the mosque",
        "need_meaning": "what's the meaning and purpose of life",
        "need_talk":    "I need to talk to someone",
        "want_friends": "I want to meet friends",
        "need_wifi":    "I need wifi and internet",
        "need_quiet":   "I need some quiet and peace",
        # previously unreachable
        "bored":        "I'm so bored with nothing to do",
        "morning":      "good morning just woke up",
        "evening":      "winding down tonight this evening",
        "weekend":      "it's the weekend on saturday",
        "new_place":    "I'm new here just arrived visiting",
        "insomnia":     "I can't sleep lying awake with insomnia",
        "confidence":   "I'm not confident and insecure",
        "reflection":   "Looking back and reflecting on my choices in hindsight",
        # new life needs
        "celebrating":  "I'm celebrating my birthday promotion",
        "homesick":     "I'm homesick and miss home and my family",
        "headache":     "I have such a bad headache migraine",
        "overwhelmed":  "I'm overwhelmed and can't handle all this",
        "want_outdoor": "I want to go outdoors and into nature",
        "want_create":  "I want to create something draw and paint",
        # temperature
        "cold":         "I'm so cold and freezing",
        "hot":          "I'm really hot and burning up",
        "tired":        "I'm so tired and exhausted",
        # relationship / emotional pain (from real data)
        "heartbreak":        "we broke up and I want her back",
        "missing_someone":   "I'm missing him so much, can't stop thinking about him",
        "relationship_pain": "he's so controlling and won't let me go out",
    }

    def test_all_bridge_keys_are_detectable(self):
        """Every SOUL_API_MAP key should be triggerable from text."""
        unreachable = []
        for attention, trigger_text in self.SURFACE_TRIGGER.items():
            detected = detect_surface_attention([trigger_text])
            if attention not in detected:
                unreachable.append((attention, trigger_text, detected))

        if unreachable:
            msg = "\n".join(
                f"  '{att}' not detected from '{text}' (got: {got})"
                for att, text, got in unreachable
            )
            pytest.fail(f"Unreachable attentions:\n{msg}")

    def test_bridge_has_actions_for_all_new_attentions(self):
        new_attentions = [
            "cold", "hot", "tired",
            "celebrating", "homesick", "headache", "overwhelmed",
            "want_outdoor", "want_create",
            "heartbreak", "missing_someone", "relationship_pain",
        ]
        for att in new_attentions:
            actions = get_api_actions(att)
            assert len(actions) > 0, f"No bridge actions for '{att}'"

    def test_bridge_total_attentions_grew(self):
        """Bridge should now have more than 35 attention types."""
        assert len(SOUL_API_MAP) > 35


# ── New Life-Need Detections ──────────────────────────────────────────────────

class TestNewAttentionDetection:
    def test_bored_detected(self):
        assert "bored" in detect_surface_attention(["I'm so bored, nothing to do"])

    def test_bored_arabic(self):
        assert "bored" in detect_surface_attention(["الأمر ممل جداً"])

    def test_insomnia_detected(self):
        assert "insomnia" in detect_surface_attention(["I can't sleep, lying awake with insomnia"])

    def test_insomnia_chinese(self):
        assert "insomnia" in detect_surface_attention(["我失眠了，完全睡不着"])

    def test_celebrating_detected(self):
        assert "celebrating" in detect_surface_attention(["It's my birthday! Celebrating today"])

    def test_celebrating_promotion(self):
        assert "celebrating" in detect_surface_attention(["I just got a promotion!"])

    def test_homesick_detected(self):
        assert "homesick" in detect_surface_attention(["I really miss home and my family"])

    def test_homesick_chinese(self):
        assert "homesick" in detect_surface_attention(["好想家，思乡的感觉很强烈"])

    def test_headache_detected(self):
        assert "headache" in detect_surface_attention(["I have a terrible headache"])

    def test_headache_migraine(self):
        assert "headache" in detect_surface_attention(["This migraine is killing me"])

    def test_overwhelmed_detected(self):
        assert "overwhelmed" in detect_surface_attention(["I'm completely overwhelmed with everything"])

    def test_overwhelmed_chinese(self):
        assert "overwhelmed" in detect_surface_attention(["我完全不知所措了"])

    def test_want_outdoor_detected(self):
        assert "want_outdoor" in detect_surface_attention(["I want to go outdoors and get some fresh air"])

    def test_want_outdoor_hiking(self):
        assert "want_outdoor" in detect_surface_attention(["Let's go hiking in nature"])

    def test_want_create_detected(self):
        assert "want_create" in detect_surface_attention(["I want to draw and paint something creative"])

    def test_confidence_detected(self):
        assert "confidence" in detect_surface_attention(["I'm not confident and feel insecure about everything"])

    def test_reflection_detected(self):
        assert "reflection" in detect_surface_attention(["Looking back and reflecting on my life in hindsight"])

    def test_morning_detected(self):
        assert "morning" in detect_surface_attention(["Good morning! Just woke up"])

    def test_evening_detected(self):
        assert "evening" in detect_surface_attention(["It's this evening and I'm winding down tonight"])

    def test_weekend_detected(self):
        assert "weekend" in detect_surface_attention(["It's the weekend, Saturday morning"])

    def test_new_place_detected(self):
        assert "new_place" in detect_surface_attention(["I just arrived, I'm visiting and new here"])

    def test_cold_detected(self):
        assert "cold" in detect_surface_attention(["I'm so cold and freezing out here"])

    def test_hot_detected(self):
        assert "hot" in detect_surface_attention(["It's so hot and I'm burning up"])

    def test_tired_detected(self):
        assert "tired" in detect_surface_attention(["I'm really tired and exhausted"])

    def test_heartbreak_detected(self):
        assert "heartbreak" in detect_surface_attention(["we broke up and I want her back"])

    def test_heartbreak_ex(self):
        assert "heartbreak" in detect_surface_attention(["my ex won't stop messaging me"])

    def test_missing_someone_detected(self):
        assert "missing_someone" in detect_surface_attention(["I'm missing him so much"])

    def test_missing_someone_cant_stop_thinking(self):
        assert "missing_someone" in detect_surface_attention(["I can't stop thinking about her"])

    def test_relationship_pain_controlling(self):
        assert "relationship_pain" in detect_surface_attention(["he's so controlling and won't let me go out"])

    def test_relationship_pain_trapped(self):
        assert "relationship_pain" in detect_surface_attention(["I feel trapped in this toxic relationship"])


# ── Middle History Expansion ──────────────────────────────────────────────────

class TestExpandedMiddleHistory:
    def test_cooking_maps_to_hungry(self):
        result = detect_middle_history({"cooking": 5})
        assert "hungry" in result

    def test_running_maps_to_exercise(self):
        result = detect_middle_history({"running": 4})
        assert "need_exercise" in result

    def test_hiking_maps_to_outdoor(self):
        result = detect_middle_history({"hiking": 3})
        assert "want_outdoor" in result

    def test_writing_maps_to_create(self):
        result = detect_middle_history({"writing": 6})
        assert "want_create" in result

    def test_gaming_maps_to_bored(self):
        result = detect_middle_history({"gaming": 4})
        assert "bored" in result

    def test_family_maps_to_homesick(self):
        result = detect_middle_history({"family": 5})
        assert "homesick" in result

    def test_travel_maps_to_new_place(self):
        result = detect_middle_history({"travel": 4})
        assert "new_place" in result

    def test_language_maps_to_learn(self):
        result = detect_middle_history({"language": 5})
        assert "want_learn" in result

    def test_photography_maps_to_art(self):
        result = detect_middle_history({"photography": 4})
        assert "want_art" in result

    def test_below_threshold_not_mapped(self):
        result = detect_middle_history({"cooking": 2})  # < 3 → not recurring
        assert "hungry" not in result

    def test_top_3_only(self):
        """detect_middle_history returns at most 3 attentions."""
        history = {f"topic_{i}": 10 for i in range(10)}
        # Use known mappable topics
        history = {"yoga": 10, "art": 8, "music": 7, "books": 6, "running": 5}
        result = detect_middle_history(history)
        assert len(result) <= 3
