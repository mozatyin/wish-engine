"""Tests for production-depth features: panic_relief, real_places, compass_action."""

from __future__ import annotations

import pytest

from wish_engine.features.panic_relief import (
    BOX_BREATHING,
    SLOW_EXHALE,
    GROUNDING_54321,
    HOTLINES,
    PanicReliefResponse,
    get_panic_relief,
)
from wish_engine.features.real_places import (
    PlaceScore,
    _score_place,
    find_real_places,
)
from wish_engine.features.compass_action import (
    CompassActionResult,
    process_conversation,
)
from wish_engine.compass.compass import WishCompass
from wish_engine.models import DetectorResults


# ── Helpers ─────────────────────────────────────────────────────────────────

def _det(**overrides) -> DetectorResults:
    return DetectorResults(**overrides)


# ── Panic Relief Tests ──────────────────────────────────────────────────────


class TestPanicRelief:
    def test_basic_response(self):
        resp = get_panic_relief("I feel stressed")
        assert isinstance(resp, PanicReliefResponse)
        assert resp.severity == "mild"
        assert resp.breathing_exercise["name"]  # has a breathing exercise
        assert len(resp.grounding["steps"]) == 5  # 5-4-3-2-1

    def test_severe_detection(self):
        resp = get_panic_relief("I want to kill myself")
        assert resp.severity == "severe"
        assert resp.breathing_exercise == SLOW_EXHALE  # calming exhale for severe

    def test_moderate_detection(self):
        resp = get_panic_relief("I'm having a panic attack and can't breathe")
        assert resp.severity == "moderate"
        assert resp.breathing_exercise == BOX_BREATHING

    def test_country_detection_uae(self):
        resp = get_panic_relief("I'm in Dubai and feeling terrible", country_hint="UAE")
        assert resp.country_detected == "AE"
        assert any(h["code"] == "AE" for h in resp.hotlines)

    def test_country_detection_china(self):
        resp = get_panic_relief("我在中国，很害怕")
        assert resp.country_detected == "CN"
        assert any(h["code"] == "CN" for h in resp.hotlines)

    def test_breathing_steps(self):
        assert len(BOX_BREATHING["steps"]) == 4
        assert BOX_BREATHING["rounds"] == 4
        assert BOX_BREATHING["total_duration_sec"] == 64

        assert len(SLOW_EXHALE["steps"]) == 3
        assert SLOW_EXHALE["rounds"] == 4

    def test_grounding_steps(self):
        steps = GROUNDING_54321["steps"]
        assert len(steps) == 5
        counts = [s["count"] for s in steps]
        assert counts == [5, 4, 3, 2, 1]
        senses = [s["sense"] for s in steps]
        assert senses == ["see", "touch", "hear", "smell", "taste"]

    def test_hotlines_cover_key_regions(self):
        codes = {h["code"] for h in HOTLINES}
        for required in ["US", "GB", "AE", "CN", "JP", "IN", "ES", "FR", "BR", "DE", "AU"]:
            assert required in codes, f"Missing hotline for {required}"
        assert len(HOTLINES) >= 25

    def test_detector_crisis_triggers_severe(self):
        resp = get_panic_relief(
            "I feel bad",
            detector_results={"crisis": {"is_crisis": True}},
        )
        assert resp.severity == "severe"


# ── Real Places Tests ───────────────────────────────────────────────────────


class TestRealPlaces:
    def test_fallback_without_location(self):
        det = _det()
        result = find_real_places("find a quiet cafe", det)
        assert len(result.recommendations) >= 1

    def test_introvert_score_for_quiet_place(self):
        det = _det(mbti={"type": "INFP"})
        place = {"tags": ["quiet", "library", "peaceful"], "noise": "quiet", "social": "low"}
        score = _score_place(place, det)
        assert score.introvert_friendly > 0.7

    def test_anxiety_score_for_calming_place(self):
        det = _det(emotion={"distress": 0.8})
        place = {"tags": ["garden", "outdoor", "calm", "spacious"], "noise": "quiet", "social": "low"}
        score = _score_place(place, det)
        assert score.anxiety_friendly > 0.7

    def test_social_place_low_introvert_score(self):
        det = _det()
        place = {"tags": ["club", "party", "nightlife", "crowd"], "noise": "loud", "social": "high"}
        score = _score_place(place, det)
        assert score.introvert_friendly < 0.5


# ── Compass Action Tests ───────────────────────────────────────────────────


class TestCompassAction:
    def test_basic_scan_works(self):
        compass = WishCompass()
        det = _det()
        result = process_conversation(
            compass=compass,
            text="I keep thinking about Ashley but I tell everyone I don't care about him",
            detector_results=det,
            session_id="s1",
            entity_names={"Ashley": ["ashley"]},
        )
        assert isinstance(result, CompassActionResult)
        assert result.scan is not None
        assert result.action_taken in ("scan_only", "revelation_triggered", "bloom_fulfilled")

    def test_multiple_turns_accumulate_shells(self):
        compass = WishCompass()
        det = _det()
        # Turn 1
        r1 = process_conversation(
            compass=compass,
            text="I hate talking about Rhett, he means nothing to me",
            detector_results=det,
            session_id="s1",
            entity_names={"Rhett": ["rhett"]},
        )
        shells_after_1 = len(r1.shells)
        # Turn 2 — same entity, contradictory
        r2 = process_conversation(
            compass=compass,
            text="Actually I dream about Rhett every night, I miss him so much",
            detector_results=det,
            session_id="s2",
            entity_names={"Rhett": ["rhett"]},
        )
        # Should have at least as many shells (may create new ones or update)
        assert len(r2.shells) >= shells_after_1
