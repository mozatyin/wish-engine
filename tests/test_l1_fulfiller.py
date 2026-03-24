"""Tests for L1 Fulfiller — card type selection and profile extraction (no LLM)."""

import pytest

from wish_engine.models import (
    CardType,
    ClassifiedWish,
    CrossDetectorPattern,
    DetectorResults,
    L1FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l1_fulfiller import (
    _select_card_type,
    _extract_profile_summary,
    _extract_related_stars,
    _build_fulfillment_prompt,
)


# ── Card type selection (zero LLM) ──────────────────────────────────────────


class TestCardTypeSelection:
    @pytest.mark.parametrize("wish_type,expected_card", [
        (WishType.SELF_UNDERSTANDING, CardType.INSIGHT),
        (WishType.SELF_EXPRESSION, CardType.SELF_DIALOGUE),
        (WishType.RELATIONSHIP_INSIGHT, CardType.RELATIONSHIP_ANALYSIS),
        (WishType.EMOTIONAL_PROCESSING, CardType.EMOTION_TRACE),
        (WishType.LIFE_REFLECTION, CardType.SOUL_PORTRAIT),
    ])
    def test_l1_type_to_card(self, wish_type, expected_card):
        assert _select_card_type(wish_type) == expected_card

    def test_unknown_type_defaults_to_insight(self):
        # L2/L3 types should default to INSIGHT (shouldn't reach here normally)
        assert _select_card_type(WishType.LEARN_SKILL) == CardType.INSIGHT


# ── Profile extraction ───────────────────────────────────────────────────────


class TestProfileExtraction:
    def test_empty_results(self):
        results = DetectorResults()
        profile = _extract_profile_summary(results, {}, {})
        assert profile == "No profile data available"

    def test_emotion_data(self):
        results = DetectorResults(
            emotion={"emotions": {"sadness": 0.7, "anxiety": 0.5, "joy": 0.1}, "distress": 0.65}
        )
        profile = _extract_profile_summary(results, {}, {})
        assert "sadness" in profile
        assert "Distress: 0.65" in profile

    def test_conflict_style(self):
        results = DetectorResults(conflict={"style": "avoiding"})
        profile = _extract_profile_summary(results, {}, {})
        assert "avoiding" in profile

    def test_mbti(self):
        results = DetectorResults(mbti={"type": "INFJ"})
        profile = _extract_profile_summary(results, {}, {})
        assert "INFJ" in profile

    def test_soul_type(self):
        results = DetectorResults()
        soul = {"name": "Quiet Storm", "tagline": "Intense beneath the calm"}
        profile = _extract_profile_summary(results, soul, {})
        assert "Quiet Storm" in profile

    def test_life_chapter(self):
        results = DetectorResults()
        chapter = {"theme": "Seeking Connection"}
        profile = _extract_profile_summary(results, {}, chapter)
        assert "Seeking Connection" in profile

    def test_full_profile(self):
        results = DetectorResults(
            emotion={"emotions": {"sadness": 0.7}, "distress": 0.5},
            conflict={"style": "avoiding"},
            mbti={"type": "INFJ"},
            attachment={"style": "anxious"},
            values={"top_values": ["belonging", "benevolence"]},
            fragility={"pattern": "open"},
            eq={"overall": 0.72},
            communication_dna={"dominant_style": "reflective"},
        )
        soul = {"name": "Hidden Depths"}
        chapter = {"theme": "Growth Phase"}
        profile = _extract_profile_summary(results, soul, chapter)
        assert "sadness" in profile
        assert "avoiding" in profile
        assert "INFJ" in profile
        assert "anxious" in profile
        assert "belonging" in profile
        assert "open" in profile
        assert "0.72" in profile
        assert "reflective" in profile
        assert "Hidden Depths" in profile
        assert "Growth Phase" in profile


# ── Related stars extraction ─────────────────────────────────────────────────


class TestRelatedStars:
    def test_insight_card_stars(self):
        results = DetectorResults(
            conflict={"style": "avoiding"},
            attachment={"style": "anxious"},
        )
        stars = _extract_related_stars(CardType.INSIGHT, results)
        assert "conflict:avoiding" in stars
        assert "attachment:anxious" in stars

    def test_relationship_analysis_stars(self):
        results = DetectorResults(
            conflict={"style": "competing"},
            love_language={"primary": "words_of_affirmation"},
        )
        stars = _extract_related_stars(CardType.RELATIONSHIP_ANALYSIS, results)
        assert "conflict:competing" in stars
        assert "love_language:words_of_affirmation" in stars

    def test_emotion_trace_stars(self):
        results = DetectorResults(
            emotion={"emotions": {"anger": 0.8, "frustration": 0.6, "joy": 0.1}}
        )
        stars = _extract_related_stars(CardType.EMOTION_TRACE, results)
        assert "emotion:anger" in stars
        assert "emotion:frustration" in stars
        assert len(stars) == 2  # Only top 2

    def test_soul_portrait_stars(self):
        results = DetectorResults(
            mbti={"type": "ENFP"},
            values={"top_values": ["self_direction", "universalism"]},
        )
        stars = _extract_related_stars(CardType.SOUL_PORTRAIT, results)
        assert "mbti:ENFP" in stars
        assert "values:self_direction" in stars

    def test_self_dialogue_stars(self):
        results = DetectorResults(fragility={"pattern": "defensive"})
        stars = _extract_related_stars(CardType.SELF_DIALOGUE, results)
        assert "fragility:defensive" in stars

    def test_empty_results_empty_stars(self):
        results = DetectorResults()
        stars = _extract_related_stars(CardType.INSIGHT, results)
        assert stars == []


# ── Prompt building ──────────────────────────────────────────────────────────


class TestPromptBuilding:
    def _make_wish(self, wish_type=WishType.SELF_UNDERSTANDING, text="test wish"):
        return ClassifiedWish(
            wish_text=text,
            wish_type=wish_type,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        )

    def test_prompt_contains_wish_text(self):
        wish = self._make_wish(text="why do I avoid conflict")
        prompt = _build_fulfillment_prompt(wish, CardType.INSIGHT, "profile", [])
        assert "why do I avoid conflict" in prompt

    def test_prompt_contains_profile(self):
        wish = self._make_wish()
        prompt = _build_fulfillment_prompt(wish, CardType.INSIGHT, "Conflict: avoiding\nMBTI: INFJ", [])
        assert "Conflict: avoiding" in prompt
        assert "MBTI: INFJ" in prompt

    def test_prompt_contains_patterns(self):
        wish = self._make_wish()
        patterns = [CrossDetectorPattern(pattern_name="safe_silence", confidence=0.8)]
        prompt = _build_fulfillment_prompt(wish, CardType.INSIGHT, "profile", patterns)
        assert "safe_silence" in prompt

    def test_prompt_no_clinical_terms(self):
        wish = self._make_wish()
        prompt = _build_fulfillment_prompt(wish, CardType.INSIGHT, "profile", [])
        assert "No clinical terms" in prompt

    def test_each_card_type_has_instruction(self):
        wish = self._make_wish()
        for card_type in CardType:
            prompt = _build_fulfillment_prompt(wish, card_type, "profile", [])
            assert len(prompt) > 50  # Has meaningful content

    def test_prompt_requests_json(self):
        wish = self._make_wish()
        prompt = _build_fulfillment_prompt(wish, CardType.INSIGHT, "profile", [])
        assert "JSON" in prompt


# ── L1 validation ────────────────────────────────────────────────────────────


class TestL1Validation:
    def test_reject_l2_wish(self):
        from wish_engine.l1_fulfiller import fulfill

        wish = ClassifiedWish(
            wish_text="test",
            wish_type=WishType.LEARN_SKILL,
            level=WishLevel.L2,
            fulfillment_strategy="course_recommendation",
        )
        with pytest.raises(ValueError, match="L1"):
            fulfill(wish, DetectorResults())

    def test_reject_l3_wish(self):
        from wish_engine.l1_fulfiller import fulfill

        wish = ClassifiedWish(
            wish_text="test",
            wish_type=WishType.FIND_COMPANION,
            level=WishLevel.L3,
            fulfillment_strategy="user_matching",
        )
        with pytest.raises(ValueError, match="L1"):
            fulfill(wish, DetectorResults())


# ── V10 design doc card routing ──────────────────────────────────────────────


class TestV10CardRouting:
    """Verify V10 examples map to correct card types."""

    def test_conflict_avoidance_insight(self):
        """想理解为什么我总是回避冲突 → insight card"""
        assert _select_card_type(WishType.SELF_UNDERSTANDING) == CardType.INSIGHT

    def test_relationship_fight_analysis(self):
        """想知道我和他为什么总吵架 → relationship_analysis card"""
        assert _select_card_type(WishType.RELATIONSHIP_INSIGHT) == CardType.RELATIONSHIP_ANALYSIS

    def test_write_letter_dialogue(self):
        """想给自己写一封信 → self_dialogue card"""
        assert _select_card_type(WishType.SELF_EXPRESSION) == CardType.SELF_DIALOGUE

    def test_self_summary_portrait(self):
        """想做一个关于自己的总结 → soul_portrait card"""
        assert _select_card_type(WishType.LIFE_REFLECTION) == CardType.SOUL_PORTRAIT

    def test_anger_origin_trace(self):
        """想理解我的愤怒从哪来 → emotion_trace card"""
        assert _select_card_type(WishType.EMOTIONAL_PROCESSING) == CardType.EMOTION_TRACE
