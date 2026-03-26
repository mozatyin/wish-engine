"""End-to-end tests — full pipeline from intention to render output (no LLM)."""

from __future__ import annotations

import pytest

from wish_engine.models import (
    CardType,
    ClassifiedWish,
    DetectedWish,
    DetectorResults,
    EmotionState,
    Intention,
    L1FulfillmentResult,
    WishLevel,
    WishState,
    WishType,
)
from wish_engine.detector import detect_wishes
from wish_engine.classifier import classify
from wish_engine.l1_fulfiller import _select_card_type, _extract_related_stars
from wish_engine.renderer import render, render_lifecycle


# ── V10 Healing Cases ────────────────────────────────────────────────────────


class TestV10HealingCases:
    """12 healing case validations from V10 design doc + user specs."""

    def _run_pipeline(self, text: str, detector_results: DetectorResults | None = None):
        """Run full pipeline without LLM (detector → classifier → card type → render)."""
        intentions = [Intention(id="heal", text=text)]
        wishes = detect_wishes(intentions)
        if not wishes:
            return None, None, None
        wish = wishes[0]
        classified = classify(wish)
        card_type = _select_card_type(classified.wish_type)
        return classified, card_type, wish

    # Case 1: Conflict avoidance insight
    def test_case1_conflict_avoidance(self):
        classified, card, _ = self._run_pipeline("想理解为什么我总是回避冲突")
        assert classified is not None
        assert classified.level == WishLevel.L1
        assert card == CardType.INSIGHT

    # Case 2: Relationship fight analysis
    def test_case2_relationship_fight(self):
        classified, card, _ = self._run_pipeline("想知道我和他为什么总吵架")
        assert classified is not None
        assert classified.level == WishLevel.L1
        assert card == CardType.RELATIONSHIP_ANALYSIS

    # Case 3: Letter to self
    def test_case3_letter_to_self(self):
        classified, card, _ = self._run_pipeline("想给自己写一封信")
        assert classified is not None
        assert classified.level == WishLevel.L1
        assert card == CardType.SELF_DIALOGUE

    # Case 4: Self summary
    def test_case4_self_summary(self):
        classified, card, _ = self._run_pipeline("想做一个关于自己的总结")
        assert classified is not None
        assert classified.level == WishLevel.L1
        assert card == CardType.SOUL_PORTRAIT

    # Case 5: Anger origin
    def test_case5_anger_origin(self):
        classified, card, _ = self._run_pipeline("想理解我的愤怒从哪来")
        assert classified is not None
        assert classified.level == WishLevel.L1
        assert card == CardType.EMOTION_TRACE

    # Case 6: English — understand conflict avoidance
    def test_case6_en_conflict(self):
        classified, card, _ = self._run_pipeline("I want to understand why I always avoid conflict")
        assert classified is not None
        assert classified.level == WishLevel.L1
        assert card == CardType.INSIGHT

    # Case 7: English — relationship
    def test_case7_en_relationship(self):
        classified, card, _ = self._run_pipeline("I wish I could understand the relationship between us")
        assert classified is not None
        assert classified.level == WishLevel.L1
        assert card == CardType.RELATIONSHIP_ANALYSIS

    # Case 8: English — express feelings
    def test_case8_en_express(self):
        classified, card, _ = self._run_pipeline("I want to write a letter to express my feelings")
        assert classified is not None
        assert classified.level == WishLevel.L1
        assert card == CardType.SELF_DIALOGUE

    # Case 9: English — self reflection
    def test_case9_en_reflection(self):
        classified, card, _ = self._run_pipeline("I'd like to have a summary of who I am")
        assert classified is not None
        assert classified.level == WishLevel.L1
        assert card == CardType.SOUL_PORTRAIT

    # Case 10: English — anger trace
    def test_case10_en_anger(self):
        classified, card, _ = self._run_pipeline("I need to understand where my anger comes from")
        assert classified is not None
        assert classified.level == WishLevel.L1
        assert card == CardType.EMOTION_TRACE

    # Case 11: L2 routing
    def test_case11_learn_meditation(self):
        classified, card, _ = self._run_pipeline("想学会冥想")
        assert classified is not None
        assert classified.level == WishLevel.L2

    # Case 12: L3 routing
    def test_case12_find_companion(self):
        classified, card, _ = self._run_pipeline("想找人聊聊创业的孤独感")
        assert classified is not None
        assert classified.level == WishLevel.L3


# ── Full render pipeline ─────────────────────────────────────────────────────


class TestFullRenderPipeline:
    def test_born_to_found_l1(self):
        """New wish detected → born state → classify → found state with gold color."""
        intentions = [Intention(id="r1", text="I want to understand myself")]
        wishes = detect_wishes(intentions)
        classified = classify(wishes[0])

        # Born state
        born = render(WishState.BORN)
        assert born.color == "#8B7BA8"
        assert born.animation == "pulse_dim"

        # Found state
        found = render(WishState.FOUND, wish=classified)
        assert found.color == "#D4A853"
        assert found.animation == "brighten_gold_halo"

    def test_fulfilled_with_card_data(self):
        """Wish fulfilled → gold burst + card data."""
        intentions = [Intention(id="r2", text="I want to understand why I avoid conflict")]
        wishes = detect_wishes(intentions)
        classified = classify(wishes[0])

        fulfillment = L1FulfillmentResult(
            fulfillment_text="Your tendency to step back from conflict...",
            related_stars=["conflict:avoiding"],
            card_type=CardType.INSIGHT,
        )
        fulfilled = render(WishState.FULFILLED, wish=classified, fulfillment=fulfillment)
        assert fulfilled.color == "#F4C542"
        assert fulfilled.animation == "burst_gold_particles"
        assert "Your tendency to step back" in fulfilled.card_data["fulfillment_text"]

    def test_lifecycle_animation_sequence(self):
        """Full lifecycle generates correct animation sequence."""
        intentions = [Intention(id="r3", text="想理解自己")]
        wishes = detect_wishes(intentions)
        classified = classify(wishes[0])
        fulfillment = L1FulfillmentResult(
            fulfillment_text="test", related_stars=[], card_type=CardType.INSIGHT
        )

        stages = render_lifecycle(classified, fulfillment=fulfillment)
        animations = [s.animation for s in stages]
        assert animations[0] == "pulse_dim"       # born
        assert animations[1] == "rotate_slow"      # searching
        assert animations[2] == "brighten_gold_halo"  # found (L1)
        assert animations[-1] == "burst_gold_particles"  # fulfilled


# ── Non-wish filtering ───────────────────────────────────────────────────────


class TestNonWishFiltering:
    """Ensure non-wish intentions are properly filtered out."""

    @pytest.mark.parametrize("text", [
        "今天天气真好",
        "My boss told me about the project",
        "I had coffee this morning",
        "The meeting was at 3pm",
        "他说了一些有趣的话",
    ])
    def test_observation_not_a_wish(self, text):
        intentions = [Intention(id="nw", text=text)]
        wishes = detect_wishes(intentions)
        assert len(wishes) == 0


# ── Related stars integration ────────────────────────────────────────────────


class TestRelatedStarsIntegration:
    def test_insight_wish_with_full_profile(self):
        results = DetectorResults(
            conflict={"style": "avoiding"},
            attachment={"style": "anxious"},
            emotion={"emotions": {"sadness": 0.7, "anxiety": 0.5}},
            mbti={"type": "INFJ"},
            values={"top_values": ["belonging"]},
        )
        stars = _extract_related_stars(CardType.INSIGHT, results)
        assert "conflict:avoiding" in stars
        assert "attachment:anxious" in stars

    def test_emotion_trace_top_2(self):
        results = DetectorResults(
            emotion={"emotions": {"anger": 0.9, "frustration": 0.7, "sadness": 0.3}}
        )
        stars = _extract_related_stars(CardType.EMOTION_TRACE, results)
        assert len(stars) == 2
        assert "emotion:anger" in stars
        assert "emotion:frustration" in stars
