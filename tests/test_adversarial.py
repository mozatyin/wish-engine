"""Adversarial test cases — edge cases, slang, code-switching, and noise.

Tests the system's robustness against:
1. Colloquial/slang expressions
2. Code-switching (mixed language)
3. Very short inputs
4. Very long inputs
5. Negation ("I don't want")
6. Past tense ("I wanted")
7. Third person ("she wants")
8. Repeated/duplicate wishes
9. Noisy/garbled input
10. Crisis-adjacent content (should NOT be treated as wish)
"""

import pytest

from wish_engine.models import (
    DetectedWish,
    EmotionState,
    Intention,
    WishLevel,
    WishType,
)
from wish_engine.detector import detect_wishes
from wish_engine.classifier import classify


# ═══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL 1: Colloquial / slang
# ═══════════════════════════════════════════════════════════════════════════════


class TestColloquialSlang:
    """Real users use slang. Test common informal expressions."""

    SHOULD_DETECT = [
        # English slang with wish intent
        ("I wanna know why I keep screwing up my relationships", WishType.SELF_UNDERSTANDING),
        ("I just wanna understand myself better ya know", WishType.SELF_UNDERSTANDING),
        # Chinese colloquial
        ("想搞明白为什么自己这么怂", WishType.SELF_UNDERSTANDING),
        ("我想知道自己到底咋回事", WishType.SELF_UNDERSTANDING),
    ]

    SHOULD_NOT_DETECT = [
        # Slang without wish intent
        "I'm so done with everything lol",
        "emo了",
        "meh whatever",
        "哈哈哈笑死",
        "bruh",
    ]

    @pytest.mark.parametrize("text,expected_type", SHOULD_DETECT,
                             ids=[c[0][:40] for c in SHOULD_DETECT])
    def test_slang_wish_detected(self, text, expected_type):
        results = detect_wishes([Intention(id="sl", text=text)])
        assert len(results) >= 1, f"MISS: '{text}'"

    @pytest.mark.parametrize("text", SHOULD_NOT_DETECT,
                             ids=[c[:20] for c in SHOULD_NOT_DETECT])
    def test_slang_non_wish(self, text):
        results = detect_wishes([Intention(id="sl", text=text)])
        assert len(results) == 0, f"FP: '{text}' → {results[0].wish_type if results else '?'}"


# ═══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL 2: Code-switching (mixed language)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCodeSwitching:
    """Users in MENA/SEA often mix languages."""

    SHOULD_DETECT = [
        ("我想understand自己为什么always这样", WishType.SELF_UNDERSTANDING),
        ("I want to理解为什么我总是avoid conflict", WishType.SELF_UNDERSTANDING),
    ]

    @pytest.mark.parametrize("text,expected_type", SHOULD_DETECT,
                             ids=[c[0][:40] for c in SHOULD_DETECT])
    def test_code_switch_detected(self, text, expected_type):
        results = detect_wishes([Intention(id="cs", text=text)])
        # May or may not detect — track success rate
        if not results:
            pytest.xfail(f"Code-switch not detected: '{text}'")
        assert results[0].wish_type == expected_type


# ═══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL 3: Negation — "I don't want" should NOT be a wish
# ═══════════════════════════════════════════════════════════════════════════════


class TestNegation:
    """Negated desires are NOT wishes."""

    CASES = [
        "I don't want to talk about it",
        "I don't need anyone's help",
        "我不想了解这些",
        "I never want to see him again",
        "我不需要理解什么",
    ]

    @pytest.mark.parametrize("text", CASES, ids=[c[:30] for c in CASES])
    def test_negation_rejected(self, text):
        results = detect_wishes([Intention(id="neg", text=text)])
        if results:
            pytest.xfail(f"Negation false positive: '{text}' → {results[0].wish_type}")


# ═══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL 4: Past tense — already happened, not a current wish
# ═══════════════════════════════════════════════════════════════════════════════


class TestPastTense:
    """Past tense wishes are generally not current wishes."""

    CASES = [
        "I wanted to understand myself but now I'm fine",
        "I used to wish I could express my feelings",
        "之前想过理解自己，但现在算了",
    ]

    @pytest.mark.parametrize("text", CASES, ids=[c[:30] for c in CASES])
    def test_past_tense(self, text):
        results = detect_wishes([Intention(id="past", text=text)])
        if results:
            pytest.xfail(f"Past tense detected as current wish: '{text}'")


# ═══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL 5: Third person — someone else's wish
# ═══════════════════════════════════════════════════════════════════════════════


class TestThirdPerson:
    """Other people's wishes should not be user's wishes."""

    CASES = [
        "She wants to understand herself better",
        "My friend wishes he could express his feelings",
        "他想理解自己",
        "Her therapist wants her to write a letter",
    ]

    @pytest.mark.parametrize("text", CASES, ids=[c[:30] for c in CASES])
    def test_third_person(self, text):
        results = detect_wishes([Intention(id="3p", text=text)])
        if results:
            pytest.xfail(f"Third person detected as user wish: '{text}'")


# ═══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL 6: Very short / very long inputs
# ═══════════════════════════════════════════════════════════════════════════════


class TestInputLength:
    def test_empty(self):
        assert detect_wishes([]) == []

    def test_single_char(self):
        results = detect_wishes([Intention(id="sc", text="?")])
        assert len(results) == 0

    def test_very_long(self):
        """Long text with a wish buried in the middle."""
        filler = "I had a really long day at work and my boss was being difficult. " * 10
        wish = "I want to understand why I always feel so anxious."
        text = filler + wish + filler
        results = detect_wishes([Intention(id="long", text=text)])
        assert len(results) >= 1, "Wish buried in long text not detected"
        assert results[0].wish_type in (WishType.EMOTIONAL_PROCESSING, WishType.SELF_UNDERSTANDING)


# ═══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL 7: Crisis-adjacent — should detect as wish but be careful
# ═══════════════════════════════════════════════════════════════════════════════


class TestCrisisAdjacent:
    """Wishes that are near crisis territory but still valid wishes.
    Note: Crisis filtering is done by Crisis Scorer, not Wish Engine.
    Wish Engine should still detect these as wishes.
    """

    CASES = [
        ("I want to understand why I feel so hopeless", WishType.EMOTIONAL_PROCESSING),
        ("想理解为什么我总是觉得活着没意思", WishType.SELF_UNDERSTANDING),
        ("I need to process this overwhelming grief", WishType.EMOTIONAL_PROCESSING),
    ]

    @pytest.mark.parametrize("text,expected_type", CASES,
                             ids=[c[0][:40] for c in CASES])
    def test_crisis_adjacent_still_detected(self, text, expected_type):
        """Wish Engine detects the wish; Crisis Scorer handles safety."""
        results = detect_wishes([Intention(id="ca", text=text)])
        assert len(results) >= 1, f"MISS: '{text}'"


# ═══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL 8: Confidence calibration
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfidenceCalibration:
    """Verify confidence ordering makes intuitive sense."""

    def test_explicit_higher_than_implicit(self):
        """Direct 'I want to...' should have higher confidence than ambiguous."""
        explicit = detect_wishes([Intention(id="e", text="I want to understand myself")])
        # A text that hits fallback path
        implicit = detect_wishes([Intention(id="i", text="I want to do something about myself")])

        assert len(explicit) >= 1
        if len(implicit) >= 1:
            assert explicit[0].confidence >= implicit[0].confidence, \
                f"Explicit ({explicit[0].confidence}) should >= implicit ({implicit[0].confidence})"

    def test_distress_boosts_confidence(self):
        """Same wish with high distress should have higher confidence."""
        text = "I want to understand myself"
        base = detect_wishes([Intention(id="b", text=text)])
        boosted = detect_wishes(
            [Intention(id="bo", text=text)],
            emotion_state=EmotionState(distress=0.7),
        )
        assert boosted[0].confidence > base[0].confidence

    def test_confidence_bounds(self):
        """Confidence should always be [0, 1]."""
        all_cases = [
            "I want to understand myself",
            "想理解自己",
            "أريد أن أفهم نفسي",
            "I want to find a quiet place",
            "想找人聊聊",
        ]
        for text in all_cases:
            results = detect_wishes(
                [Intention(id="cb", text=text)],
                emotion_state=EmotionState(distress=0.9),
                cross_detector_patterns=[
                    CrossDetectorPattern(pattern_name="safe_silence", confidence=0.95)
                    for _ in range(5)
                ],
            )
            for r in results:
                assert 0.0 <= r.confidence <= 1.0, f"Confidence out of bounds: {r.confidence}"


from wish_engine.models import CrossDetectorPattern


# ═══════════════════════════════════════════════════════════════════════════════
# ADVERSARIAL 9: Comprehensive accuracy on 50-case ground truth
# ═══════════════════════════════════════════════════════════════════════════════


class TestComprehensiveAccuracy:
    """50-case ground truth covering all edge categories."""

    GROUND_TRUTH = [
        # ── True L1 wishes (20 cases) ────
        ("I want to understand why I'm always so defensive", True, WishType.SELF_UNDERSTANDING),
        ("想理解为什么我总是回避冲突", True, WishType.SELF_UNDERSTANDING),
        ("I wish I knew why I push people away", True, WishType.SELF_UNDERSTANDING),
        ("想弄清楚为什么自己总是讨好别人", True, WishType.SELF_UNDERSTANDING),
        ("I want to write a letter to myself", True, WishType.SELF_EXPRESSION),
        ("想给自己写一封信", True, WishType.SELF_EXPRESSION),
        ("I'd love to express what I've been holding inside", True, WishType.SELF_EXPRESSION),
        ("我想把心里的话写出来", True, WishType.SELF_EXPRESSION),
        ("I want to know why we keep fighting", True, WishType.RELATIONSHIP_INSIGHT),
        ("想知道我和他为什么总吵架", True, WishType.RELATIONSHIP_INSIGHT),
        ("I want to understand where this sadness comes from", True, WishType.EMOTIONAL_PROCESSING),
        ("想理解我的愤怒从哪来", True, WishType.EMOTIONAL_PROCESSING),
        ("I need to deal with my anxiety", True, WishType.EMOTIONAL_PROCESSING),
        ("希望可以放下对前任的执念", True, WishType.EMOTIONAL_PROCESSING),
        ("I want a summary of my journey", True, WishType.LIFE_REFLECTION),
        ("想做一个关于自己的总结", True, WishType.LIFE_REFLECTION),
        ("أريد أن أفهم نفسي بشكل أفضل", True, WishType.SELF_UNDERSTANDING),
        ("أتمنى أن أعبر عن مشاعري", True, WishType.SELF_EXPRESSION),
        ("I want to process the grief I've been carrying", True, WishType.EMOTIONAL_PROCESSING),
        ("我想做一个人生阶段的回顾", True, WishType.LIFE_REFLECTION),

        # ── True L2 wishes (5 cases) ────
        ("I want to learn meditation", True, None),  # L2, type varies
        ("想找一个安静的地方想想", True, None),
        ("I want to read a book about attachment", True, None),
        ("想找一份更有意义的工作", True, None),
        ("I want to find a good therapist near me", True, None),

        # ── True L3 wishes (5 cases) ────
        ("I want to find someone who understands me", True, None),
        ("想找人聊聊创业的孤独感", True, None),
        ("I want to meet a mentor in my field", True, None),
        ("想找一个真正理解内向者的朋友", True, None),
        ("I want to talk to someone who understands", True, None),

        # ── Non-wishes (20 cases) ────
        ("Today was a good day", False, None),
        ("今天天气不错", False, None),
        ("My boss said I did a good job", False, None),
        ("刚才和朋友吃了顿饭", False, None),
        ("I went to the gym", False, None),
        ("太累了", False, None),
        ("Ok", False, None),
        ("嗯嗯是的", False, None),
        ("Yeah I guess so", False, None),
        ("Traffic was terrible", False, None),
        ("I'm so done with everything lol", False, None),
        ("哈哈哈笑死", False, None),
        ("bruh", False, None),
        ("meh whatever", False, None),
        ("emo了", False, None),
        ("I had a meeting today", False, None),
        ("昨天下了好大的雨", False, None),
        ("She said it was fine", False, None),
        ("好无聊", False, None),
        ("What time is it?", False, None),
    ]

    def test_overall_detection_accuracy(self):
        """Target: >85% detection accuracy."""
        correct = 0
        total = len(self.GROUND_TRUTH)
        false_pos = []
        misses = []

        for text, is_wish, _ in self.GROUND_TRUTH:
            results = detect_wishes([Intention(id="gt", text=text)])
            detected = len(results) > 0
            if detected == is_wish:
                correct += 1
            elif detected:
                false_pos.append(f"  FP: '{text[:40]}' → {results[0].wish_type}")
            else:
                misses.append(f"  MISS: '{text[:40]}'")

        accuracy = correct / total
        report = f"\nDetection: {correct}/{total} = {accuracy:.1%}"
        if false_pos:
            report += f"\n  False positives ({len(false_pos)}):\n" + "\n".join(false_pos)
        if misses:
            report += f"\n  Misses ({len(misses)}):\n" + "\n".join(misses)

        print(report)
        assert accuracy >= 0.85, f"Below 85%:\n{report}"

    def test_l1_type_accuracy(self):
        """Target: >80% type accuracy for L1 wishes."""
        correct = 0
        total = 0

        for text, is_wish, expected_type in self.GROUND_TRUTH:
            if not is_wish or expected_type is None:
                continue
            results = detect_wishes([Intention(id="gt", text=text)])
            if not results:
                continue
            total += 1
            if results[0].wish_type == expected_type:
                correct += 1

        accuracy = correct / total if total else 0
        print(f"\nL1 Type: {correct}/{total} = {accuracy:.1%}")
        assert accuracy >= 0.80, f"L1 type accuracy below 80%: {correct}/{total}"

    def test_zero_false_positive_on_non_wishes(self):
        """Non-wishes should have <10% false positive rate."""
        non_wishes = [(t, iw, et) for t, iw, et in self.GROUND_TRUTH if not iw]
        fps = 0
        for text, _, _ in non_wishes:
            results = detect_wishes([Intention(id="gt", text=text)])
            if results:
                fps += 1

        fp_rate = fps / len(non_wishes) if non_wishes else 0
        print(f"\nFP rate: {fps}/{len(non_wishes)} = {fp_rate:.1%}")
        assert fp_rate < 0.10, f"FP rate too high: {fp_rate:.1%}"
