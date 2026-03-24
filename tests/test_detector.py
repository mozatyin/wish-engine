"""Tests for Wish Detector — rule-based fast path and edge cases."""

import pytest

from wish_engine.models import (
    CrossDetectorPattern,
    DetectedWish,
    EmotionState,
    Intention,
    WishType,
)
from wish_engine.detector import (
    detect_wishes,
    _detect_language,
    _has_desire_marker,
    _classify_wish_type,
)


# ── Language detection ───────────────────────────────────────────────────────


class TestLanguageDetection:
    def test_english(self):
        assert _detect_language("I want to understand myself") == "en"

    def test_chinese(self):
        assert _detect_language("我想理解自己") == "zh"

    def test_arabic(self):
        assert _detect_language("أتمنى أن أفهم نفسي") == "ar"

    def test_mixed_defaults_to_chinese_if_present(self):
        assert _detect_language("I want 理解 myself") == "zh"


# ── Desire marker detection ─────────────────────────────────────────────────


class TestDesireMarker:
    @pytest.mark.parametrize("text", [
        "I want to understand why I avoid conflict",
        "I wish I could express my feelings",
        "I'd love to find a quiet place",
        "I need to talk to someone",
        "If only I could be more confident",
        "I hope to learn meditation",
    ])
    def test_english_desire_markers(self, text):
        assert _has_desire_marker(text, "en")

    @pytest.mark.parametrize("text", [
        "我想理解为什么我总是回避冲突",
        "希望能找到一个安静的地方",
        "渴望被理解",
        "如果能学会冥想就好了",
        "我需要一个人的空间",
    ])
    def test_chinese_desire_markers(self, text):
        assert _has_desire_marker(text, "zh")

    @pytest.mark.parametrize("text", [
        "أتمنى أن أفهم نفسي",
        "أريد أن أتعلم",
        "أحتاج وقت",
    ])
    def test_arabic_desire_markers(self, text):
        assert _has_desire_marker(text, "ar")

    @pytest.mark.parametrize("text", [
        "The weather is nice today",
        "I had a meeting at 3pm",
        "My boss told me about the project",
        "今天天气不错",
        "الطقس جميل اليوم",
    ])
    def test_non_wish_texts(self, text):
        lang = _detect_language(text)
        assert not _has_desire_marker(text, lang)


# ── Wish type classification ────────────────────────────────────────────────


class TestWishTypeClassification:
    def test_self_understanding_en(self):
        assert _classify_wish_type("I want to understand myself better") == WishType.SELF_UNDERSTANDING

    def test_self_understanding_why(self):
        assert _classify_wish_type("why do I always avoid conflict") == WishType.SELF_UNDERSTANDING

    def test_self_understanding_zh(self):
        assert _classify_wish_type("我想理解自己为什么总是逃避") == WishType.SELF_UNDERSTANDING

    def test_self_expression(self):
        assert _classify_wish_type("I want to write a letter to myself") == WishType.SELF_EXPRESSION

    def test_self_expression_zh(self):
        assert _classify_wish_type("我想写一封信给自己") == WishType.SELF_EXPRESSION

    def test_relationship_insight(self):
        assert _classify_wish_type("I want to understand the relationship between us") == WishType.RELATIONSHIP_INSIGHT

    def test_relationship_insight_zh(self):
        assert _classify_wish_type("我和他为什么总吵架") == WishType.RELATIONSHIP_INSIGHT

    def test_emotional_processing(self):
        assert _classify_wish_type("where does my anger come from") == WishType.EMOTIONAL_PROCESSING

    def test_emotional_processing_zh(self):
        assert _classify_wish_type("我想理解我的愤怒从哪来") == WishType.EMOTIONAL_PROCESSING

    def test_life_reflection(self):
        assert _classify_wish_type("I want a summary of my growth") == WishType.LIFE_REFLECTION

    def test_life_reflection_zh(self):
        assert _classify_wish_type("我想做一个关于自己的总结") == WishType.LIFE_REFLECTION

    def test_learn_skill(self):
        assert _classify_wish_type("I want to learn meditation") == WishType.LEARN_SKILL

    def test_find_place(self):
        assert _classify_wish_type("I want to find a quiet place to think") == WishType.FIND_PLACE

    def test_find_resource(self):
        assert _classify_wish_type("I want to read a book about attachment") == WishType.FIND_RESOURCE

    def test_find_companion(self):
        assert _classify_wish_type("I want to find someone who understands me") == WishType.FIND_COMPANION

    def test_health_wellness(self):
        assert _classify_wish_type("I want to try meditation") == WishType.HEALTH_WELLNESS

    def test_no_match(self):
        assert _classify_wish_type("the sky is blue") is None


# ── End-to-end detection (rule path only, no LLM) ───────────────────────────


class TestDetectWishes:
    def test_empty_intentions(self):
        assert detect_wishes([]) == []

    def test_single_wish_en(self):
        intentions = [
            Intention(id="i1", text="I want to understand why I always avoid conflict"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.SELF_UNDERSTANDING
        assert results[0].confidence >= 0.8
        assert results[0].source_intention_id == "i1"

    def test_single_wish_zh(self):
        intentions = [
            Intention(id="i2", text="我想理解为什么我总是回避冲突"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.SELF_UNDERSTANDING

    def test_non_wish_filtered_out(self):
        intentions = [
            Intention(id="i1", text="The weather is nice"),
            Intention(id="i2", text="I had a meeting today"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 0

    def test_mixed_wish_and_non_wish(self):
        intentions = [
            Intention(id="i1", text="The weather is nice"),
            Intention(id="i2", text="I want to understand myself better"),
            Intention(id="i3", text="My boss called me"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].source_intention_id == "i2"

    def test_multiple_wishes(self):
        intentions = [
            Intention(id="i1", text="I want to understand why I avoid conflict"),
            Intention(id="i2", text="I wish I could write a letter to myself"),
            Intention(id="i3", text="I need to find a quiet place"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 3

    def test_distress_boosts_confidence(self):
        intentions = [
            Intention(id="i1", text="I want to understand myself"),
        ]
        emotion = EmotionState(distress=0.5)
        results = detect_wishes(intentions, emotion_state=emotion)
        assert results[0].confidence > 0.85

    def test_cross_detector_pattern_boosts_confidence(self):
        intentions = [
            Intention(id="i1", text="I want to understand myself"),
        ]
        patterns = [CrossDetectorPattern(pattern_name="safe_silence", confidence=0.8)]
        results = detect_wishes(intentions, cross_detector_patterns=patterns)
        assert results[0].confidence > 0.85

    def test_sorted_by_confidence(self):
        intentions = [
            Intention(id="i1", text="I want to understand myself"),
            Intention(id="i2", text="I want to find a quiet place"),
        ]
        # With distress boost for first one only via pattern
        patterns = [CrossDetectorPattern(pattern_name="safe_silence", confidence=0.9)]
        emotion = EmotionState(distress=0.5)
        results = detect_wishes(intentions, emotion_state=emotion, cross_detector_patterns=patterns)
        assert len(results) == 2
        assert results[0].confidence >= results[1].confidence


# ── V10 design doc examples ──────────────────────────────────────────────────


class TestV10Examples:
    """Test cases directly from the V10 design document."""

    def test_understand_conflict_avoidance(self):
        """想理解为什么我总是回避冲突 → L1 → 个性化洞察"""
        intentions = [Intention(id="v10_1", text="想理解为什么我总是回避冲突")]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.SELF_UNDERSTANDING

    def test_why_we_fight(self):
        """想知道我和他为什么总吵架 → L1 → 关系动态分析"""
        intentions = [Intention(id="v10_2", text="想知道我和他为什么总吵架")]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.RELATIONSHIP_INSIGHT

    def test_write_letter_to_self(self):
        """想给自己写一封信 → L1 → 辅助写作"""
        intentions = [Intention(id="v10_3", text="想给自己写一封信")]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.SELF_EXPRESSION

    def test_self_summary(self):
        """想做一个关于自己的总结 → L1 → Soul Portrait"""
        intentions = [Intention(id="v10_4", text="想做一个关于自己的总结")]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.LIFE_REFLECTION

    def test_anger_origin(self):
        """想理解我的愤怒从哪来 → L1 → 情绪溯源"""
        intentions = [Intention(id="v10_5", text="想理解我的愤怒从哪来")]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.EMOTIONAL_PROCESSING

    def test_learn_meditation(self):
        """想学会冥想 → L2"""
        intentions = [Intention(id="v10_6", text="想学会冥想")]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type in (WishType.LEARN_SKILL, WishType.HEALTH_WELLNESS)

    def test_find_quiet_place(self):
        """想找一个安静的地方想想 → L2"""
        intentions = [Intention(id="v10_7", text="想找一个安静的地方想想")]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.FIND_PLACE

    def test_find_companion(self):
        """想找人聊聊创业的孤独感 → L3"""
        intentions = [Intention(id="v10_8", text="想找人聊聊创业的孤独感")]
        results = detect_wishes(intentions)
        assert len(results) == 1
        assert results[0].wish_type == WishType.FIND_COMPANION


# ── Edge cases ───────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_text(self):
        intentions = [Intention(id="e1", text="")]
        results = detect_wishes(intentions)
        assert len(results) == 0

    def test_very_short_text(self):
        intentions = [Intention(id="e2", text="ok")]
        results = detect_wishes(intentions)
        assert len(results) == 0

    def test_duplicate_intentions(self):
        intentions = [
            Intention(id="e3", text="I want to understand myself"),
            Intention(id="e4", text="I want to understand myself"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 2  # Both detected, dedup is caller's job

    def test_ambiguous_without_api_key(self):
        """Ambiguous intentions without API key → no Haiku fallback, just skip."""
        intentions = [
            Intention(id="e5", text="I want to do something about this situation"),
        ]
        # "this situation" has desire marker but no clear type match
        results = detect_wishes(intentions, api_key="")
        # Either detected via rule or skipped — should not crash
        assert isinstance(results, list)
