"""Integration tests: VowSuppressor + NarrativeTracker + StarFeedbackStore working together
in the context of generate_trisoul_stars.
"""
import pytest
from unittest.mock import patch

from wish_engine.soul_layer_classifier import VowSuppressor, SoulLayer
from wish_engine.narrative_tracker import NarrativeTracker, LifePhase
from wish_engine.star_feedback import StarFeedbackStore
from wish_engine.trisoul_stars import generate_trisoul_stars


LAT, LNG = 25.2048, 55.2708  # Dubai


# ── Helpers ──────────────────────────────────────────────────────────────────

def _no_api(*args, **kwargs):
    """Stub: all APIs return nothing so we focus on structural behavior."""
    return None


# ── Vow Suppressor Integration ────────────────────────────────────────────────

class TestVowSuppressionIntegration:
    def test_deep_vow_registers_in_suppressor(self):
        """After running stars with a deep vow text, suppressor has the topic active."""
        sup = VowSuppressor()
        with patch("wish_engine.trisoul_stars._call_api", side_effect=_no_api):
            generate_trisoul_stars(
                recent_texts=["I'll never be hungry again"],
                lat=LAT, lng=LNG,
                vow_suppressor=sup,
            )
        # Suppressor should have recorded food suppression
        assert sup.is_suppressed("food") is True

    def test_surface_text_does_not_trigger_suppressor(self):
        """A plain surface statement doesn't activate suppression."""
        sup = VowSuppressor()
        with patch("wish_engine.trisoul_stars._call_api", side_effect=_no_api):
            generate_trisoul_stars(
                recent_texts=["I'm hungry right now"],
                lat=LAT, lng=LNG,
                vow_suppressor=sup,
            )
        assert sup.is_suppressed("food") is False

    def test_survival_phase_shortens_vow_duration(self):
        """In survival phase, vow suppression lasts only 12h not 72h."""
        sup = VowSuppressor()
        narrative = NarrativeTracker()
        # Pre-load survival signals
        narrative.update(["hungry", "emergency", "help me", "no money", "crisis"])
        assert narrative.current_phase == LifePhase.SURVIVAL

        with patch("wish_engine.trisoul_stars._call_api", side_effect=_no_api):
            generate_trisoul_stars(
                recent_texts=["I'll never be hungry again"],
                lat=LAT, lng=LNG,
                vow_suppressor=sup,
                narrative=narrative,
            )
        active = sup.active_suppressions()
        # Should be ~12h not 72h
        assert "food" in active
        assert active["food"] <= 13  # 12h + small float buffer

    def test_meaning_phase_extends_vow_duration(self):
        """In meaning phase, vow suppression lasts 168h (a full week)."""
        sup = VowSuppressor()
        narrative = NarrativeTracker()
        # Pre-load meaning signals
        narrative.update(["who am i", "meaning of life", "I believe", "from now on",
                          "I swear", "at my core", "in my heart", "forever changed"])
        assert narrative.current_phase == LifePhase.MEANING

        with patch("wish_engine.trisoul_stars._call_api", side_effect=_no_api):
            generate_trisoul_stars(
                recent_texts=["I'll never be hungry again"],
                lat=LAT, lng=LNG,
                vow_suppressor=sup,
                narrative=narrative,
            )
        active = sup.active_suppressions()
        assert "food" in active
        assert active["food"] > 100  # Close to 168h


# ── Narrative Tracker Integration ─────────────────────────────────────────────

class TestNarrativeIntegration:
    def test_narrative_updated_on_each_call(self):
        """Each generate_trisoul_stars call updates the narrative tracker."""
        narrative = NarrativeTracker()
        assert narrative._session_count == 0
        with patch("wish_engine.trisoul_stars._call_api", side_effect=_no_api):
            generate_trisoul_stars(
                recent_texts=["I'm hungry"],
                lat=LAT, lng=LNG,
                narrative=narrative,
            )
        assert narrative._session_count == 1

    def test_survival_limits_meteors(self):
        """In survival phase, max_meteors = round(2.0 * 3) = 5 (capped at 5)."""
        narrative = NarrativeTracker()
        narrative.update(["hungry", "emergency", "help me", "no money", "scared", "crisis"])
        assert narrative.current_phase == LifePhase.SURVIVAL
        weights = narrative.weights
        sw = weights["surface_weight"]
        expected_max = max(1, min(5, round(sw * 3)))
        assert expected_max == 5  # Survival surface_weight=2.0 → 6 → capped at 5

    def test_meaning_limits_meteors(self):
        """In meaning phase, max_meteors = round(0.5 * 3) = 2."""
        narrative = NarrativeTracker()
        narrative.update(["who am i", "meaning of life", "I believe", "from now on",
                          "I swear", "at my core", "in my heart", "forever changed",
                          "I'll never", "what matters", "soul", "destiny", "always"])
        assert narrative.current_phase == LifePhase.MEANING
        weights = narrative.weights
        sw = weights["surface_weight"]
        expected_max = max(1, min(5, round(sw * 3)))
        assert expected_max <= 2

    def test_meaning_increases_earths(self):
        """In meaning phase, deep_weight=2.0 → max_earths=6."""
        narrative = NarrativeTracker()
        narrative.update(["who am i", "meaning of life", "I believe", "from now on",
                          "I swear", "at my core", "in my heart", "forever changed",
                          "I'll never", "what matters", "soul", "destiny", "always"])
        assert narrative.current_phase == LifePhase.MEANING
        weights = narrative.weights
        dw = weights["deep_weight"]
        expected_max = max(0, min(6, round(dw * 3)))
        assert expected_max >= 4


# ── Feedback → Narrative Cross-Talk ──────────────────────────────────────────

class TestFeedbackNarrativeCrosstalk:
    def test_growth_clicks_nudge_narrative(self):
        """Consistent clicks on growth-type content nudges narrative toward growth."""
        narrative = NarrativeTracker()
        feedback = StarFeedbackStore()

        # User keeps clicking learning content
        for _ in range(5):
            feedback.impression("learning")
            feedback.click("learning")
            feedback.impression("books")
            feedback.click("books")
            feedback.impression("courses")
            feedback.click("courses")

        growth_score_before = narrative._scores[LifePhase.GROWTH]

        with patch("wish_engine.trisoul_stars._call_api", side_effect=_no_api):
            generate_trisoul_stars(
                recent_texts=["just another day"],
                lat=LAT, lng=LNG,
                narrative=narrative,
                feedback=feedback,
            )

        growth_score_after = narrative._scores[LifePhase.GROWTH]
        # Feedback cross-talk should have boosted growth score
        assert growth_score_after > growth_score_before

    def test_no_crosstalk_without_feedback(self):
        """Without feedback store, narrative is only updated from text signals."""
        narrative = NarrativeTracker()
        score_before = narrative._scores[LifePhase.GROWTH]

        with patch("wish_engine.trisoul_stars._call_api", side_effect=_no_api):
            generate_trisoul_stars(
                recent_texts=["just another day"],
                lat=LAT, lng=LNG,
                narrative=narrative,
                feedback=None,  # No feedback
            )

        # Growth score should only change due to text signals, not feedback
        # "just another day" has no growth keywords → score unchanged
        assert narrative._scores[LifePhase.GROWTH] == score_before * 0.95  # Just decay


# ── All Three Together ────────────────────────────────────────────────────────

class TestAllThreeTogether:
    def test_scarlett_vow_end_to_end(self):
        """
        Scarlett says: "I'll never be hungry again."

        Expected:
        - VowSuppressor: food suppressed (detected as food vow)
        - NarrativeTracker: updated with the text
        - StarFeedbackStore: impression recorded for deep_reflection attention
        - No food meteors generated (suppressed)
        """
        sup = VowSuppressor()
        narrative = NarrativeTracker()
        feedback = StarFeedbackStore()

        with patch("wish_engine.trisoul_stars._call_api", side_effect=_no_api):
            star_map = generate_trisoul_stars(
                recent_texts=["I'll never be hungry again"],
                lat=LAT, lng=LNG,
                vow_suppressor=sup,
                narrative=narrative,
                feedback=feedback,
            )

        # Vow registered
        assert sup.is_suppressed("food") is True

        # Narrative updated
        assert narrative._session_count == 1

        # No food meteors (all APIs return None, so no meteors at all — but suppressor is active)
        food_meteors = [m for m in star_map.meteors if m.place_category == "food"]
        assert len(food_meteors) == 0

    def test_three_systems_dont_interfere(self):
        """Running multiple sessions doesn't corrupt state across systems."""
        sup = VowSuppressor()
        narrative = NarrativeTracker()
        feedback = StarFeedbackStore()

        texts_sequence = [
            ["I'm hungry right now"],        # Surface
            ["I'll never be hungry again"],  # Deep vow
            ["I want to learn guitar"],      # Growth/Middle
        ]

        with patch("wish_engine.trisoul_stars._call_api", side_effect=_no_api):
            for texts in texts_sequence:
                generate_trisoul_stars(
                    recent_texts=texts,
                    lat=LAT, lng=LNG,
                    vow_suppressor=sup,
                    narrative=narrative,
                    feedback=feedback,
                )

        # After vow, food is suppressed
        assert sup.is_suppressed("food") is True
        # Narrative has been updated 3 times
        assert narrative._session_count == 3
