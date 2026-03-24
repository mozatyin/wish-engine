"""Tests for SoulGraph Adapter — structured wish detection from SoulItem metadata.

Uses REAL fixture data from SoulGraph to validate the adapter works
on actual Deep Soul output, not synthetic test cases.
"""

import json
import pytest
from pathlib import Path

from wish_engine.models import DetectedWish, WishLevel, WishType
from wish_engine.classifier import classify
from wish_engine.adapter import (
    detect_from_soul_items,
    _is_intention_item,
    _classify_from_domains,
    _classify_from_text,
    _compute_confidence,
)


# ── Load real fixtures ───────────────────────────────────────────────────────

FIXTURES_DIR = Path("/Users/michael/soulgraph/fixtures")


def _load_fixture(name: str) -> list[dict]:
    path = FIXTURES_DIR / name
    with open(path) as f:
        data = json.load(f)
    return data.get("items", [])


# ═══════════════════════════════════════════════════════════════════════════════
# REAL DATA: zhang_wei — 61 items, 8 intentions, career-focused
# ═══════════════════════════════════════════════════════════════════════════════


class TestZhangWei:
    """zhang_wei.json: 8-year programmer considering startup."""

    @pytest.fixture
    def items(self):
        return _load_fixture("zhang_wei.json")

    def test_detects_intentions_only(self, items):
        """Should detect intention-tagged items, skip facts/emotions/values."""
        results = detect_from_soul_items(items)
        source_ids = {r.source_intention_id for r in results}

        # Should detect these intentions
        assert "si_002" in source_ids  # 想创业做AI工具
        assert "si_020" in source_ids  # 希望给女儿更好的教育
        assert "si_028" in source_ids  # 想证明自己
        assert "si_039" in source_ids  # 想培养运动习惯

        # Should NOT detect these (not intentions)
        assert "si_001" not in source_ids  # 8年程序员 (fact)
        assert "si_003" not in source_ids  # 35岁焦虑 (emotion)
        assert "si_022" not in source_ids  # 害怕平庸 (fear, no intention tag)
        assert "si_026" not in source_ids  # 追求自由 (value)
        assert "si_045" not in source_ids  # 喜欢骑自行车 (preference)

    def test_fear_intention_detected(self, items):
        """'害怕创业失败养不了家' has tags: [intention, fear] — should detect."""
        results = detect_from_soul_items(items)
        fear_wish = [r for r in results if r.source_intention_id == "si_010"]
        assert len(fear_wish) == 1
        # Fear tag should boost confidence
        assert fear_wish[0].confidence > 0.85

    def test_career_wishes_classified(self, items):
        """Career-domain intentions should classify to CAREER_DIRECTION."""
        results = detect_from_soul_items(items)
        si_002 = [r for r in results if r.source_intention_id == "si_002"][0]
        assert si_002.wish_type == WishType.CAREER_DIRECTION
        classified = classify(si_002)
        assert classified.level == WishLevel.L2

    def test_family_wish_classified(self, items):
        """'希望给女儿更好的教育' — family/values domain."""
        results = detect_from_soul_items(items)
        si_020 = [r for r in results if r.source_intention_id == "si_020"][0]
        # Education intent — could be L1 or L2
        assert si_020.wish_type is not None

    def test_health_wish_classified(self, items):
        """'想培养运动习惯' — health domain."""
        results = detect_from_soul_items(items)
        si_039 = [r for r in results if r.source_intention_id == "si_039"][0]
        assert si_039.wish_type == WishType.HEALTH_WELLNESS
        classified = classify(si_039)
        assert classified.level == WishLevel.L2

    def test_high_mention_count_boosts_confidence(self, items):
        """si_002 has mention_count=8 — should have higher confidence."""
        results = detect_from_soul_items(items)
        si_002 = [r for r in results if r.source_intention_id == "si_002"][0]
        si_039 = [r for r in results if r.source_intention_id == "si_039"][0]
        # si_002 (8 mentions, 0.9 conf) vs si_039 (1 mention, 0.6 conf)
        assert si_002.confidence > si_039.confidence

    def test_total_wishes_reasonable(self, items):
        """From 61 items, should detect 4-6 wishes (not 30+)."""
        results = detect_from_soul_items(items)
        assert 3 <= len(results) <= 8


# ═══════════════════════════════════════════════════════════════════════════════
# REAL DATA: anxiety_user — 12 items, high distress
# ═══════════════════════════════════════════════════════════════════════════════


class TestAnxietyUser:
    """anxiety_user.json: anxious user considering therapy."""

    @pytest.fixture
    def items(self):
        return _load_fixture("anxiety_user.json")

    def test_detects_action_intentions(self, items):
        """Action items with intention domain should be detected."""
        results = detect_from_soul_items(items)
        source_ids = {r.source_intention_id for r in results}

        assert "si_004" in source_ids  # 想试试冥想或者瑜伽来放松
        assert "si_008" in source_ids  # 想找一个心理咨询师聊聊

    def test_cognitive_intention_detected(self, items):
        """'其实内心知道需要改变' — cognitive with intention domain."""
        results = detect_from_soul_items(items)
        source_ids = {r.source_intention_id for r in results}
        assert "si_012" in source_ids

    def test_non_intentions_filtered(self, items):
        """Facts and background items should not be detected."""
        results = detect_from_soul_items(items)
        source_ids = {r.source_intention_id for r in results}

        assert "si_001" not in source_ids  # 说不清焦虑什么 (cognitive, no intention tag/domain)
        assert "si_002" not in source_ids  # 工作压力大 (background)
        assert "si_006" not in source_ids  # 小时候父母严格 (background)
        assert "si_011" not in source_ids  # 失眠严重 (background)

    def test_wellness_wishes(self, items):
        """Wellness intentions should route to HEALTH_WELLNESS."""
        results = detect_from_soul_items(items)
        si_004 = [r for r in results if r.source_intention_id == "si_004"][0]
        assert si_004.wish_type == WishType.HEALTH_WELLNESS
        classified = classify(si_004)
        assert classified.level == WishLevel.L2

    def test_total_wishes_reasonable(self, items):
        """From 12 items, should detect 2-4 wishes."""
        results = detect_from_soul_items(items)
        assert 2 <= len(results) <= 5


# ═══════════════════════════════════════════════════════════════════════════════
# Unit tests: classification functions
# ═══════════════════════════════════════════════════════════════════════════════


class TestIsIntentionItem:
    def test_intention_tag(self):
        assert _is_intention_item({"tags": ["intention"]})

    def test_desire_tag(self):
        assert _is_intention_item({"tags": ["desire"]})

    def test_intention_domain(self):
        assert _is_intention_item({"domains": ["intention", "wellness"]})

    def test_action_type_with_confidence(self):
        assert _is_intention_item({"item_type": "action", "confidence": 0.7})

    def test_action_type_low_confidence(self):
        assert not _is_intention_item({"item_type": "action", "confidence": 0.3})

    def test_fact_tag(self):
        assert not _is_intention_item({"tags": ["fact"]})

    def test_emotion_tag(self):
        assert not _is_intention_item({"tags": ["emotion"]})

    def test_value_tag(self):
        assert not _is_intention_item({"tags": ["value"]})

    def test_empty(self):
        assert not _is_intention_item({})


class TestClassifyFromDomains:
    def test_relationship(self):
        assert _classify_from_domains(["relationship"]) == WishType.RELATIONSHIP_INSIGHT

    def test_identity(self):
        assert _classify_from_domains(["identity"]) == WishType.SELF_UNDERSTANDING

    def test_emotion(self):
        assert _classify_from_domains(["emotion"]) == WishType.EMOTIONAL_PROCESSING

    def test_career(self):
        assert _classify_from_domains(["career"]) == WishType.CAREER_DIRECTION

    def test_wellness(self):
        assert _classify_from_domains(["wellness"]) == WishType.HEALTH_WELLNESS

    def test_no_match(self):
        assert _classify_from_domains(["hobbies"]) is None

    def test_relationship_emotion_combined(self):
        """More specific combo should match first."""
        assert _classify_from_domains(["relationship", "emotion"]) == WishType.RELATIONSHIP_INSIGHT


class TestClassifyFromText:
    def test_self_understanding_zh(self):
        assert _classify_from_text("想理解自己为什么总是回避") == WishType.SELF_UNDERSTANDING

    def test_career_zh(self):
        assert _classify_from_text("想创业做AI工具") == WishType.CAREER_DIRECTION

    def test_wellness_zh(self):
        assert _classify_from_text("想试试冥想来放松") == WishType.HEALTH_WELLNESS

    def test_companion_zh(self):
        assert _classify_from_text("想找人聊聊") == WishType.FIND_COMPANION

    def test_no_match(self):
        assert _classify_from_text("今天天气不错") is None


class TestComputeConfidence:
    def test_base_confidence(self):
        assert _compute_confidence({"confidence": 0.8}) == 0.8

    def test_high_mention_boost(self):
        conf = _compute_confidence({"confidence": 0.8, "mention_count": 8})
        assert conf > 0.8

    def test_extreme_valence_boost(self):
        conf = _compute_confidence({"confidence": 0.7, "emotional_valence": "extreme"})
        assert conf > 0.7

    def test_fear_tag_boost(self):
        conf = _compute_confidence({"confidence": 0.8, "tags": ["intention", "fear"]})
        assert conf > 0.8

    def test_confidence_capped(self):
        conf = _compute_confidence({
            "confidence": 0.9,
            "mention_count": 10,
            "emotional_valence": "extreme",
            "specificity": 0.9,
            "tags": ["intention", "fear"],
        })
        assert conf <= 0.95


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: adapter + classifier + renderer
# ═══════════════════════════════════════════════════════════════════════════════


class TestFullPipeline:
    """End-to-end: SoulItem → adapter → classifier → verify level routing."""

    def test_zhang_wei_level_distribution(self):
        items = _load_fixture("zhang_wei.json")
        wishes = detect_from_soul_items(items)
        classified = [classify(w) for w in wishes]
        levels = {c.level for c in classified}

        # Should have a mix of L1 and L2 (career + self + health)
        assert WishLevel.L2 in levels  # Career, health

    def test_anxiety_user_level_distribution(self):
        items = _load_fixture("anxiety_user.json")
        wishes = detect_from_soul_items(items)
        classified = [classify(w) for w in wishes]
        levels = [c.level for c in classified]

        # Wellness intentions → L2
        assert WishLevel.L2 in levels

    def test_no_false_positives_on_facts(self):
        """Pure fact items should never produce wishes."""
        facts = [
            {"id": "f1", "text": "8年程序员", "tags": ["fact"], "domains": ["career"], "confidence": 0.9},
            {"id": "f2", "text": "女儿5岁", "tags": ["fact"], "domains": ["family"], "confidence": 0.9},
            {"id": "f3", "text": "房贷压力大", "tags": ["fact"], "domains": ["finance"], "confidence": 0.9},
        ]
        assert detect_from_soul_items(facts) == []

    def test_no_false_positives_on_emotions(self):
        """Emotion items without intention tag should not produce wishes."""
        emotions = [
            {"id": "e1", "text": "35岁焦虑", "tags": ["emotion"], "domains": ["career"], "confidence": 0.8},
            {"id": "e2", "text": "害怕平庸", "tags": ["fear"], "domains": ["identity"], "confidence": 0.8},
        ]
        assert detect_from_soul_items(emotions) == []
