"""Production simulation — models real user sessions with Deep Soul output.

Simulates 10 complete user sessions as they would occur in production:
- User talks to SoulMap
- Deep Soul extracts intentions
- Wish Engine processes intentions
- Results feed into star map

Each session includes multi-turn context with emotion state and patterns.
"""

import pytest

from wish_engine.models import (
    CardType,
    ClassifiedWish,
    CrossDetectorPattern,
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
from wish_engine.l1_fulfiller import _select_card_type, _extract_profile_summary, _build_fulfillment_prompt
from wish_engine.renderer import render, render_lifecycle


class TestSession1_AnxiousAvoider:
    """Session: 25F, anxious attachment, conflict-avoiding, INFJ.
    After 8 turns discussing work stress, Deep Soul extracts a wish.
    """

    PROFILE = DetectorResults(
        emotion={"emotions": {"anxiety": 0.6, "frustration": 0.4}, "distress": 0.45},
        conflict={"style": "avoiding"},
        mbti={"type": "INFJ"},
        attachment={"style": "anxious-preoccupied"},
        values={"top_values": ["belonging", "benevolence"]},
        fragility={"pattern": "approval-seeking"},
        eq={"overall": 0.65},
    )
    SOUL = {"name": "Hidden Depths", "tagline": "Still waters run deep"}
    EMOTION = EmotionState(emotions={"anxiety": 0.6}, distress=0.45, valence=-0.3)
    PATTERNS = [CrossDetectorPattern(pattern_name="safe_silence", confidence=0.82)]

    def test_wish_detected(self):
        intentions = [
            Intention(id="s1_1", text="工作压力很大"),
            Intention(id="s1_2", text="和同事有些摩擦"),
            Intention(id="s1_3", text="想理解为什么自己总是不敢表达不满"),
        ]
        results = detect_wishes(intentions, emotion_state=self.EMOTION,
                                cross_detector_patterns=self.PATTERNS)
        wish_texts = {r.wish_text for r in results}
        assert "想理解为什么自己总是不敢表达不满" in wish_texts
        wish = [r for r in results if "不敢表达" in r.wish_text][0]
        assert wish.confidence > 0.85  # boosted by distress + pattern

    def test_classification(self):
        wish = DetectedWish(
            wish_text="想理解为什么自己总是不敢表达不满",
            wish_type=WishType.SELF_UNDERSTANDING,
            confidence=0.90,
            source_intention_id="s1_3",
        )
        classified = classify(wish)
        assert classified.level == WishLevel.L1
        assert classified.fulfillment_strategy == "personalized_insight"

    def test_prompt_quality(self):
        wish = ClassifiedWish(
            wish_text="想理解为什么自己总是不敢表达不满",
            wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        )
        profile = _extract_profile_summary(self.PROFILE, self.SOUL, {})
        prompt = _build_fulfillment_prompt(wish, CardType.INSIGHT, profile, self.PATTERNS)
        assert "不敢表达不满" in prompt
        assert "avoiding" in prompt
        assert "INFJ" in prompt
        assert "Hidden Depths" in prompt
        assert "safe_silence" in prompt

    def test_render_lifecycle(self):
        wish = ClassifiedWish(
            wish_text="想理解为什么自己总是不敢表达不满",
            wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        )
        fulfillment = L1FulfillmentResult(
            fulfillment_text="你总是选择沉默，不是因为你不在乎...",
            related_stars=["conflict:avoiding", "attachment:anxious-preoccupied"],
            card_type=CardType.INSIGHT,
        )
        stages = render_lifecycle(wish, fulfillment)
        assert stages[0].star_state == WishState.BORN
        assert stages[-1].star_state == WishState.FULFILLED
        assert stages[-1].card_data["fulfillment_text"].startswith("你总是选择沉默")


class TestSession2_GriefProcessor:
    """Session: 35M, recently lost parent, high distress."""

    PROFILE = DetectorResults(
        emotion={"emotions": {"grief": 0.8, "sadness": 0.7, "guilt": 0.4}, "distress": 0.72},
        conflict={"style": "accommodating"},
        attachment={"style": "secure"},
        values={"top_values": ["tradition", "benevolence", "security"]},
    )
    EMOTION = EmotionState(emotions={"grief": 0.8, "sadness": 0.7}, distress=0.72, valence=-0.6)

    def test_grief_wish_detected(self):
        intentions = [
            Intention(id="s2_1", text="I want to process the grief I've been carrying since dad passed"),
        ]
        results = detect_wishes(intentions, emotion_state=self.EMOTION)
        assert len(results) == 1
        assert results[0].wish_type == WishType.EMOTIONAL_PROCESSING
        assert results[0].confidence > 0.85

    def test_card_type_emotion_trace(self):
        assert _select_card_type(WishType.EMOTIONAL_PROCESSING) == CardType.EMOTION_TRACE


class TestSession3_RelationshipConflict:
    """Session: 28F, fighting with partner, seeking relationship insight."""

    def test_relationship_wish_zh(self):
        intentions = [
            Intention(id="s3_1", text="又和他吵架了"),
            Intention(id="s3_2", text="想知道我们为什么每次都因为同样的事情吵"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.RELATIONSHIP_INSIGHT
        assert results[0].source_intention_id == "s3_2"

    def test_non_wish_filtered(self):
        """'又和他吵架了' is a statement, not a wish."""
        intentions = [Intention(id="s3_1", text="又和他吵架了")]
        results = detect_wishes(intentions)
        assert len(results) == 0


class TestSession4_SelfExplorer:
    """Session: 22M, ENFP, first time using SoulMap, curious about self."""

    def test_multiple_l1_wishes(self):
        intentions = [
            Intention(id="s4_1", text="I want to understand who I really am"),
            Intention(id="s4_2", text="I'd love to write a letter to my future self"),
            Intention(id="s4_3", text="I want a portrait of my personality"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 3
        types = {r.wish_type for r in results}
        assert WishType.SELF_UNDERSTANDING in types
        assert WishType.SELF_EXPRESSION in types
        assert WishType.LIFE_REFLECTION in types


class TestSession5_ArabicUser:
    """Session: Arabic-speaking user."""

    def test_arabic_wish(self):
        intentions = [
            Intention(id="s5_1", text="أريد أن أفهم نفسي بشكل أفضل"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.SELF_UNDERSTANDING

    def test_arabic_expression(self):
        intentions = [
            Intention(id="s5_2", text="أتمنى أن أعبر عن مشاعري"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.SELF_EXPRESSION


class TestSession6_LetGoOfPast:
    """Session: User wanting to release attachment to ex-partner."""

    def test_let_go_wish(self):
        intentions = [
            Intention(id="s6_1", text="希望可以放下对前任的执念"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.EMOTIONAL_PROCESSING


class TestSession7_CareerSeeker:
    """Session: User questioning career direction."""

    def test_career_l2(self):
        intentions = [
            Intention(id="s7_1", text="想找一份更有意义的工作"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 1
        classified = classify(results[0])
        assert classified.level == WishLevel.L2


class TestSession8_CompanionSeeker:
    """Session: Introverted user seeking connection."""

    def test_companion_l3(self):
        intentions = [
            Intention(id="s8_1", text="想找一个真正理解内向者的朋友"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 1
        classified = classify(results[0])
        assert classified.level == WishLevel.L3
        assert classified.fulfillment_strategy == "user_matching"

    def test_render_l3_found(self):
        wish = ClassifiedWish(
            wish_text="想找一个真正理解内向者的朋友",
            wish_type=WishType.FIND_COMPANION,
            level=WishLevel.L3,
            fulfillment_strategy="user_matching",
        )
        found = render(WishState.FOUND, wish=wish)
        assert found.color == "#9B59B6"  # purple for L3
        assert found.animation == "glow_purple_extend"


class TestSession9_CrisisEdge:
    """Session: User near crisis but still expressing valid wishes.
    Wish Engine should detect; Crisis Scorer handles safety.
    """

    def test_hopelessness_wish(self):
        intentions = [
            Intention(id="s9_1", text="I want to understand why I feel so hopeless all the time"),
        ]
        emotion = EmotionState(distress=0.75, valence=-0.7)
        results = detect_wishes(intentions, emotion_state=emotion)
        assert len(results) == 1
        # High distress → higher confidence
        assert results[0].confidence >= 0.90


class TestSession10_MixedSessionFullPipeline:
    """Session: 10-turn conversation with multiple intentions, wishes, and noise."""

    def test_full_pipeline(self):
        intentions = [
            Intention(id="t1", text="今天上班迟到了"),
            Intention(id="t2", text="和领导开会讨论了项目进度"),
            Intention(id="t3", text="想理解为什么自己总是拖延"),
            Intention(id="t4", text="中午吃了麻辣烫"),
            Intention(id="t5", text="下午有点困"),
            Intention(id="t6", text="想找一本关于时间管理的书"),
            Intention(id="t7", text="晚上和女朋友视频了"),
            Intention(id="t8", text="想知道我和她为什么最近总是冷战"),
            Intention(id="t9", text="想给自己写一封信"),
            Intention(id="t10", text="今天还行吧"),
        ]
        emotion = EmotionState(distress=0.35, valence=-0.2)
        results = detect_wishes(intentions, emotion_state=emotion)

        # Should detect 4 wishes: t3, t6, t8, t9
        wish_ids = {r.source_intention_id for r in results}
        assert "t3" in wish_ids, "拖延 wish missed"
        assert "t6" in wish_ids, "找书 wish missed"
        assert "t8" in wish_ids, "冷战 wish missed"
        assert "t9" in wish_ids, "写信 wish missed"

        # Non-wishes should not be detected
        for noise_id in ["t1", "t2", "t4", "t5", "t7", "t10"]:
            assert noise_id not in wish_ids, f"FP: {noise_id} detected as wish"

        # Verify levels
        for r in results:
            classified = classify(r)
            if r.source_intention_id == "t3":
                assert classified.level == WishLevel.L1
            elif r.source_intention_id == "t6":
                assert classified.level == WishLevel.L2
            elif r.source_intention_id == "t8":
                assert classified.level == WishLevel.L1
            elif r.source_intention_id == "t9":
                assert classified.level == WishLevel.L1
