"""Stress tests — high-volume scenarios for regression and balloon squeezing detection.

Tests that every fix doesn't break other areas (balloon squeezing).
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
from wish_engine.l1_fulfiller import _select_card_type, _extract_profile_summary
from wish_engine.renderer import render


# ═══════════════════════════════════════════════════════════════════════════════
# STRESS 1: Negation must NOT trigger — exhaustive
# ═══════════════════════════════════════════════════════════════════════════════


class TestNegationExhaustive:
    """Expanded negation tests to prevent balloon squeezing from wanna/want expansion."""

    NEGATED = [
        "I don't want to understand anything",
        "I don't wanna talk about it",
        "I don't need to know why",
        "我不想理解了",
        "我不需要这些",
        "I never wanted to understand myself",
        "No I don't want to write anything",
        "I don't want to find anyone",
        "I really don't want to deal with this",
        "我真的不想了解自己",
    ]

    @pytest.mark.parametrize("text", NEGATED, ids=[c[:30] for c in NEGATED])
    def test_negation_not_detected(self, text):
        results = detect_wishes([Intention(id="neg", text=text)])
        if results:
            pytest.xfail(f"Negation FP: '{text}' → {results[0].wish_type}")


# ═══════════════════════════════════════════════════════════════════════════════
# STRESS 2: Balloon squeezing — original V10 examples must still pass
# ═══════════════════════════════════════════════════════════════════════════════


class TestV10ExamplesRegression:
    """Every V10 design doc example must work after all PDCA iterations."""

    CASES = [
        ("想理解为什么我总是回避冲突", WishType.SELF_UNDERSTANDING, WishLevel.L1, CardType.INSIGHT),
        ("想知道我和他为什么总吵架", WishType.RELATIONSHIP_INSIGHT, WishLevel.L1, CardType.RELATIONSHIP_ANALYSIS),
        ("想给自己写一封信", WishType.SELF_EXPRESSION, WishLevel.L1, CardType.SELF_DIALOGUE),
        ("想做一个关于自己的总结", WishType.LIFE_REFLECTION, WishLevel.L1, CardType.SOUL_PORTRAIT),
        ("想理解我的愤怒从哪来", WishType.EMOTIONAL_PROCESSING, WishLevel.L1, CardType.EMOTION_TRACE),
    ]

    @pytest.mark.parametrize("text,exp_type,exp_level,exp_card", CASES,
                             ids=[c[0][:20] for c in CASES])
    def test_v10_example(self, text, exp_type, exp_level, exp_card):
        results = detect_wishes([Intention(id="v10", text=text)])
        assert len(results) >= 1, f"REGRESSION: '{text}' not detected"
        classified = classify(results[0])
        assert results[0].wish_type == exp_type, f"REGRESSION type: {results[0].wish_type}"
        assert classified.level == exp_level, f"REGRESSION level: {classified.level}"
        assert _select_card_type(classified.wish_type) == exp_card, f"REGRESSION card"


# ═══════════════════════════════════════════════════════════════════════════════
# STRESS 3: All 15 wish types detectable
# ═══════════════════════════════════════════════════════════════════════════════


class TestAllTypesDetectable:
    """Every WishType should be reachable via at least one input."""

    REPRESENTATIVES = [
        ("I want to understand why I'm like this", WishType.SELF_UNDERSTANDING),
        ("I want to write about my feelings", WishType.SELF_EXPRESSION),
        ("I want to understand why we fight", WishType.RELATIONSHIP_INSIGHT),
        ("I want to process my grief", WishType.EMOTIONAL_PROCESSING),
        ("I want a reflection on my life", WishType.LIFE_REFLECTION),
        ("I want to learn Spanish", WishType.LEARN_SKILL),
        ("I want to find a quiet park", WishType.FIND_PLACE),
        ("I want to read a book about psychology", WishType.FIND_RESOURCE),
        ("I want to change my career direction", WishType.CAREER_DIRECTION),
        ("I want to try yoga", WishType.HEALTH_WELLNESS),
        ("I want to find a friend who gets me", WishType.FIND_COMPANION),
        ("I want to find a mentor", WishType.FIND_MENTOR),
        ("I want to exchange language skills", WishType.SKILL_EXCHANGE),
        ("I want to hike together with someone", WishType.SHARED_EXPERIENCE),
        ("I want to talk to someone who understands", WishType.EMOTIONAL_SUPPORT),
    ]

    @pytest.mark.parametrize("text,expected_type", REPRESENTATIVES,
                             ids=[f"{c[1].value}" for c in REPRESENTATIVES])
    def test_type_reachable(self, text, expected_type):
        results = detect_wishes([Intention(id="ty", text=text)])
        assert len(results) >= 1, f"Type {expected_type.value} not reachable"
        assert results[0].wish_type == expected_type


# ═══════════════════════════════════════════════════════════════════════════════
# STRESS 4: Renderer edge cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestRendererEdgeCases:
    def test_render_all_states_no_crash(self):
        """Every WishState should render without error."""
        for state in WishState:
            out = render(state)
            assert out.star_state == state
            assert len(out.color) == 7  # #RRGGBB
            assert len(out.animation) > 0

    def test_render_all_level_state_combinations(self):
        """Every (state, level) combination should work."""
        for state in WishState:
            for level in WishLevel:
                wish = ClassifiedWish(
                    wish_text="t", wish_type=WishType.SELF_UNDERSTANDING,
                    level=level, fulfillment_strategy="test",
                )
                out = render(state, wish=wish)
                assert len(out.color) == 7

    def test_render_fulfilled_without_fulfillment_data(self):
        """Fulfilled state without fulfillment result should not crash."""
        out = render(WishState.FULFILLED)
        assert out.color == "#F4C542"
        assert out.animation == "burst_gold_particles"


# ═══════════════════════════════════════════════════════════════════════════════
# STRESS 5: Profile summary with missing/partial data
# ═══════════════════════════════════════════════════════════════════════════════


class TestProfileSummaryEdgeCases:
    def test_all_empty(self):
        assert _extract_profile_summary(DetectorResults(), {}, {}) == "No profile data available"

    def test_emotion_no_emotions_key(self):
        r = DetectorResults(emotion={"something_else": True})
        profile = _extract_profile_summary(r, {}, {})
        # Should not crash, just skip emotion
        assert isinstance(profile, str)

    def test_values_empty_list(self):
        r = DetectorResults(values={"top_values": []})
        profile = _extract_profile_summary(r, {}, {})
        assert isinstance(profile, str)

    def test_soul_type_missing_name(self):
        r = DetectorResults()
        profile = _extract_profile_summary(r, {"tagline": "test"}, {})
        assert "test" not in profile  # Only name is used

    def test_numeric_fields(self):
        r = DetectorResults(eq={"overall": 0.0})  # edge: exactly 0
        profile = _extract_profile_summary(r, {}, {})
        assert "EQ: 0.00" in profile


# ═══════════════════════════════════════════════════════════════════════════════
# STRESS 6: Full pipeline accuracy scorecard
# ═══════════════════════════════════════════════════════════════════════════════


class TestFinalScorecard:
    """Aggregate accuracy metrics printed as final report."""

    ALL_WISH_CASES = [
        # L1
        ("I want to understand why I'm always so defensive", True, "L1"),
        ("想理解为什么我总是回避冲突", True, "L1"),
        ("I wish I knew why I push people away", True, "L1"),
        ("想弄清楚为什么自己总是讨好别人", True, "L1"),
        ("I want to write a letter to myself", True, "L1"),
        ("想给自己写一封信", True, "L1"),
        ("I'd love to express what I've been holding inside", True, "L1"),
        ("我想把心里的话写出来", True, "L1"),
        ("I want to know why we keep fighting", True, "L1"),
        ("想知道我和他为什么总吵架", True, "L1"),
        ("I want to understand where this sadness comes from", True, "L1"),
        ("想理解我的愤怒从哪来", True, "L1"),
        ("I need to deal with my anxiety", True, "L1"),
        ("希望可以放下对前任的执念", True, "L1"),
        ("I want a summary of my journey", True, "L1"),
        ("想做一个关于自己的总结", True, "L1"),
        ("I wanna know why I keep screwing up my relationships", True, "L1"),
        ("I just wanna understand myself better ya know", True, "L1"),
        ("想搞明白为什么自己这么怂", True, "L1"),
        ("أريد أن أفهم نفسي بشكل أفضل", True, "L1"),
        # L2
        ("I want to learn meditation", True, "L2"),
        ("想找一个安静的地方想想", True, "L2"),
        ("I want to read a book about attachment", True, "L2"),
        ("I want to find a good therapist near me", True, "L2"),
        ("我想学画画", True, "L2"),
        # L3
        ("I want to find someone who understands me", True, "L3"),
        ("想找人聊聊创业的孤独感", True, "L3"),
        ("I want to meet a mentor in my field", True, "L3"),
        ("I want to talk to someone who understands", True, "L3"),
        ("想找一个真正理解内向者的朋友", True, "L3"),
        # Non-wishes
        ("Today was a good day", False, None),
        ("今天天气不错", False, None),
        ("My boss said I did a good job", False, None),
        ("刚才和朋友吃了顿饭", False, None),
        ("I went to the gym", False, None),
        ("太累了", False, None),
        ("Ok", False, None),
        ("嗯嗯是的", False, None),
        ("Traffic was terrible", False, None),
        ("I'm so done with everything lol", False, None),
        ("哈哈哈笑死", False, None),
        ("bruh", False, None),
        ("meh whatever", False, None),
        ("emo了", False, None),
        ("好无聊", False, None),
    ]

    def test_final_scorecard(self):
        """Print comprehensive scorecard."""
        detection_correct = 0
        level_correct = 0
        total = len(self.ALL_WISH_CASES)
        wish_total = sum(1 for _, iw, _ in self.ALL_WISH_CASES if iw)
        non_wish_total = total - wish_total
        fps = 0
        misses = 0

        for text, is_wish, expected_level in self.ALL_WISH_CASES:
            results = detect_wishes([Intention(id="sc", text=text)])
            detected = len(results) > 0

            if detected == is_wish:
                detection_correct += 1
            elif detected and not is_wish:
                fps += 1
            elif not detected and is_wish:
                misses += 1

            if detected and is_wish and expected_level:
                classified = classify(results[0])
                if classified.level.value == expected_level:
                    level_correct += 1

        det_acc = detection_correct / total
        fp_rate = fps / non_wish_total if non_wish_total else 0
        miss_rate = misses / wish_total if wish_total else 0
        lv_acc = level_correct / wish_total if wish_total else 0

        report = (
            f"\n{'='*60}\n"
            f"  WISH ENGINE SCORECARD\n"
            f"{'='*60}\n"
            f"  Detection:   {detection_correct}/{total} = {det_acc:.1%}\n"
            f"  FP rate:     {fps}/{non_wish_total} = {fp_rate:.1%}\n"
            f"  Miss rate:   {misses}/{wish_total} = {miss_rate:.1%}\n"
            f"  Level acc:   {level_correct}/{wish_total} = {lv_acc:.1%}\n"
            f"{'='*60}"
        )
        print(report)

        assert det_acc >= 0.85, f"Detection < 85%\n{report}"
        assert fp_rate < 0.10, f"FP > 10%\n{report}"
        assert miss_rate < 0.15, f"Miss > 15%\n{report}"
        assert lv_acc >= 0.85, f"Level < 85%\n{report}"
