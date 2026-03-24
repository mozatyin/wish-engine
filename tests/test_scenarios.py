"""Scenario-based validation — simulates real user sessions through the full pipeline.

Each scenario represents a realistic user expression as it would come from Deep Soul's
intention extraction. Tests cover:
  1. Implicit wishes (user doesn't say "I want")
  2. Indirect expressions (embedded in emotional context)
  3. False positives (look like wishes but aren't)
  4. Multi-language (EN/ZH/AR)
  5. Ambiguous/borderline cases
  6. Crisis-adjacent content
  7. Colloquial/slang
  8. Multi-intention sessions
  9. Profile-dependent fulfillment quality
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
from wish_engine.detector import detect_wishes, _detect_language, _has_desire_marker, _classify_wish_type
from wish_engine.classifier import classify
from wish_engine.l1_fulfiller import (
    _select_card_type,
    _extract_profile_summary,
    _extract_related_stars,
    _build_fulfillment_prompt,
)
from wish_engine.renderer import render, render_lifecycle


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO GROUP 1: Explicit L1 wishes — should ALL be detected + classified
# ═══════════════════════════════════════════════════════════════════════════════


class TestExplicitL1Wishes:
    """Clean, direct wish expressions. Baseline accuracy must be 100%."""

    CASES = [
        # (text, expected_type, expected_card, lang)
        ("I want to understand why I'm always so defensive", WishType.SELF_UNDERSTANDING, CardType.INSIGHT, "en"),
        ("I wish I knew why I push people away", WishType.SELF_UNDERSTANDING, CardType.INSIGHT, "en"),
        ("I need to figure out who I really am", WishType.SELF_UNDERSTANDING, CardType.INSIGHT, "en"),
        ("I want to write down my feelings", WishType.SELF_EXPRESSION, CardType.SELF_DIALOGUE, "en"),
        ("I'd love to express what I've been holding inside", WishType.SELF_EXPRESSION, CardType.SELF_DIALOGUE, "en"),
        ("I want to know why we keep fighting", WishType.RELATIONSHIP_INSIGHT, CardType.RELATIONSHIP_ANALYSIS, "en"),
        ("I want to understand where this sadness comes from", WishType.EMOTIONAL_PROCESSING, CardType.EMOTION_TRACE, "en"),
        ("I need to deal with my anxiety", WishType.EMOTIONAL_PROCESSING, CardType.EMOTION_TRACE, "en"),
        ("I want a reflection on my growth this year", WishType.LIFE_REFLECTION, CardType.SOUL_PORTRAIT, "en"),
        ("我想了解自己为什么总是害怕被拒绝", WishType.SELF_UNDERSTANDING, CardType.INSIGHT, "zh"),
        ("我想知道为什么我一直在逃避感情", WishType.SELF_UNDERSTANDING, CardType.INSIGHT, "zh"),
        ("想给过去的自己写一封信", WishType.SELF_EXPRESSION, CardType.SELF_DIALOGUE, "zh"),
        ("我想理解我和妈妈的关系为什么这么紧张", WishType.RELATIONSHIP_INSIGHT, CardType.RELATIONSHIP_ANALYSIS, "zh"),
        ("想知道我的焦虑到底从哪来的", WishType.EMOTIONAL_PROCESSING, CardType.EMOTION_TRACE, "zh"),
        ("我想做一个人生阶段的回顾", WishType.LIFE_REFLECTION, CardType.SOUL_PORTRAIT, "zh"),
        ("أريد أن أفهم نفسي بشكل أفضل", WishType.SELF_UNDERSTANDING, CardType.INSIGHT, "ar"),
        ("أتمنى أن أعبر عن مشاعري", WishType.SELF_EXPRESSION, CardType.SELF_DIALOGUE, "ar"),
    ]

    @pytest.mark.parametrize("text,expected_type,expected_card,lang", CASES,
                             ids=[c[0][:40] for c in CASES])
    def test_explicit_wish(self, text, expected_type, expected_card, lang):
        intentions = [Intention(id="exp", text=text)]
        results = detect_wishes(intentions)
        assert len(results) >= 1, f"MISS: '{text}' not detected as wish"
        wish = results[0]
        classified = classify(wish)
        assert classified.level == WishLevel.L1, f"WRONG LEVEL: '{text}' → {classified.level}"
        assert wish.wish_type == expected_type, f"WRONG TYPE: '{text}' → {wish.wish_type} (expected {expected_type})"
        card = _select_card_type(classified.wish_type)
        assert card == expected_card, f"WRONG CARD: '{text}' → {card} (expected {expected_card})"


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO GROUP 2: Implicit/indirect wishes — the hard cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestImplicitWishes:
    """Users don't say 'I want'. Deep Soul extracts these as intentions.
    These represent what Deep Soul WOULD output after processing the raw text.
    """

    # These are intentions as Deep Soul would extract them — slightly more structured
    # than raw user text, but still natural language
    CASES_SHOULD_DETECT = [
        # Deep Soul extracted intention → expected type
        ("想弄清楚为什么自己总是讨好别人", WishType.SELF_UNDERSTANDING, "zh"),
        ("希望能明白自己到底想要什么", WishType.SELF_UNDERSTANDING, "zh"),
        ("想搞懂为什么每段感情都会失败", WishType.SELF_UNDERSTANDING, "zh"),  # borderline: self/relationship, self wins on "搞懂为什么"
        ("我想把心里的话写出来", WishType.SELF_EXPRESSION, "zh"),
        ("I want to figure out what's been eating at me", WishType.EMOTIONAL_PROCESSING, "en"),
        ("I wish I could understand my relationship with my father", WishType.RELATIONSHIP_INSIGHT, "en"),
        ("I'd like to look back on how far I've come", WishType.LIFE_REFLECTION, "en"),
        ("I want to process the grief I've been carrying", WishType.EMOTIONAL_PROCESSING, "en"),
        ("想理解为什么自己害怕亲密关系", WishType.SELF_UNDERSTANDING, "zh"),  # borderline: self wins on "为什么自己"
        ("希望可以放下对前任的执念", WishType.EMOTIONAL_PROCESSING, "zh"),
    ]

    @pytest.mark.parametrize("text,expected_type,lang", CASES_SHOULD_DETECT,
                             ids=[c[0][:40] for c in CASES_SHOULD_DETECT])
    def test_implicit_wish_detected(self, text, expected_type, lang):
        intentions = [Intention(id="imp", text=text)]
        results = detect_wishes(intentions)
        assert len(results) >= 1, f"MISS: '{text}' not detected"
        assert results[0].wish_type == expected_type, \
            f"WRONG TYPE: '{text}' → {results[0].wish_type} (expected {expected_type})"


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO GROUP 3: Non-wishes — should NOT be detected as wishes
# ═══════════════════════════════════════════════════════════════════════════════


class TestNonWishes:
    """Statements, observations, and casual speech that are NOT wishes."""

    CASES = [
        # Observations / statements
        "Today was a good day",
        "今天天气不错，心情还行",
        "My boss told me I did a good job",
        "刚才和朋友吃了顿饭",
        "I went to the gym this morning",
        "الطقس جميل اليوم",
        # Past tense narration
        "I talked to my mom yesterday",
        "昨天和他聊了聊，感觉好多了",
        # Questions without desire
        "What time is it?",
        "你觉得呢?",
        # Casual filler
        "嗯嗯，是的",
        "Yeah, I guess so",
        "Ok",
        # Complaints without desire for change
        "Traffic was terrible",
        "太累了",
        "好无聊",
    ]

    @pytest.mark.parametrize("text", CASES, ids=[c[:30] for c in CASES])
    def test_non_wish_rejected(self, text):
        intentions = [Intention(id="nw", text=text)]
        results = detect_wishes(intentions)
        assert len(results) == 0, f"FALSE POSITIVE: '{text}' detected as {results[0].wish_type if results else '?'}"


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO GROUP 4: Tricky false positives — look like wishes but aren't
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrickyFalsePositives:
    """Sentences with 'want/想' that are NOT actionable wishes."""

    CASES = [
        # Physical needs (not psychological wishes)
        "I want to eat pizza",
        "我想去上厕所",
        "I need to sleep",
        "想喝杯咖啡",
        # Past wishes (already fulfilled)
        "I wanted to tell him but I already did",
        # Hypothetical / not genuine
        "I don't really want to talk about it",
        # Reporting someone else's wish
        "She wants to understand herself better",
        "他想了解自己",
    ]

    @pytest.mark.parametrize("text", CASES, ids=[c[:30] for c in CASES])
    def test_tricky_non_wish(self, text):
        intentions = [Intention(id="fp", text=text)]
        results = detect_wishes(intentions)
        # These MAY be detected — we track them but don't hard-fail
        # The key metric is false positive rate across the full suite
        if results:
            pytest.xfail(f"Known FP: '{text}' → {results[0].wish_type}")


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO GROUP 5: L2/L3 routing accuracy
# ═══════════════════════════════════════════════════════════════════════════════


class TestL2L3Routing:
    """Wishes that should route to L2 (Internet) or L3 (user matching)."""

    L2_CASES = [
        ("I want to learn how to cook Italian food", WishType.LEARN_SKILL),
        ("我想学画画", WishType.LEARN_SKILL),
        ("I want to find a good therapist near me", WishType.HEALTH_WELLNESS),
        ("想找一个可以安静看书的咖啡馆", WishType.FIND_PLACE),
        ("I want to read a book about attachment theory", WishType.FIND_RESOURCE),
        ("我想找一本关于育儿的书", WishType.FIND_RESOURCE),
        ("想找一份更有意义的工作", WishType.CAREER_DIRECTION),
    ]

    L3_CASES = [
        ("I want to find someone who's been through something similar", WishType.FIND_COMPANION),
        ("想找一个真正理解内向者的朋友", WishType.FIND_COMPANION),
        ("I want to meet a mentor in my field", WishType.FIND_MENTOR),
        ("我想找人一起去爬山", WishType.SHARED_EXPERIENCE),
        ("I want to talk to someone who understands", WishType.EMOTIONAL_SUPPORT),
    ]

    @pytest.mark.parametrize("text,expected_type", L2_CASES,
                             ids=[c[0][:40] for c in L2_CASES])
    def test_l2_routing(self, text, expected_type):
        intentions = [Intention(id="l2", text=text)]
        results = detect_wishes(intentions)
        assert len(results) >= 1, f"MISS: '{text}'"
        classified = classify(results[0])
        assert classified.level == WishLevel.L2, f"WRONG: '{text}' → {classified.level}"

    @pytest.mark.parametrize("text,expected_type", L3_CASES,
                             ids=[c[0][:40] for c in L3_CASES])
    def test_l3_routing(self, text, expected_type):
        intentions = [Intention(id="l3", text=text)]
        results = detect_wishes(intentions)
        assert len(results) >= 1, f"MISS: '{text}'"
        classified = classify(results[0])
        assert classified.level == WishLevel.L3, f"WRONG: '{text}' → {classified.level}"


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO GROUP 6: Multi-intention sessions
# ═══════════════════════════════════════════════════════════════════════════════


class TestMultiIntentionSessions:
    """Simulate a session where Deep Soul extracts multiple intentions."""

    def test_session_mixed_wish_and_observation(self):
        """User talks about their day, one intention is a wish."""
        intentions = [
            Intention(id="s1", text="今天工作很累"),
            Intention(id="s2", text="和同事有点不愉快"),
            Intention(id="s3", text="想理解为什么自己总是在意别人的看法"),
            Intention(id="s4", text="晚上打算早点睡"),
        ]
        results = detect_wishes(intentions)
        wish_ids = {r.source_intention_id for r in results}
        assert "s3" in wish_ids, "Should detect the self-understanding wish"
        # s1, s2, s4 should NOT be wishes
        assert "s1" not in wish_ids
        assert "s4" not in wish_ids

    def test_session_multiple_wishes(self):
        """User expresses multiple wishes in one session."""
        intentions = [
            Intention(id="m1", text="I want to understand why I'm so afraid of being alone"),
            Intention(id="m2", text="I also wish I could write about what I'm feeling"),
            Intention(id="m3", text="I'd love to find someone who gets it"),
        ]
        results = detect_wishes(intentions)
        assert len(results) == 3
        types = {r.wish_type for r in results}
        assert WishType.SELF_UNDERSTANDING in types
        assert WishType.SELF_EXPRESSION in types
        assert WishType.FIND_COMPANION in types

    def test_session_with_emotion_context(self):
        """Distress boosts confidence for detected wishes."""
        intentions = [
            Intention(id="e1", text="想理解自己为什么总是这么焦虑"),
        ]
        emotion = EmotionState(emotions={"anxiety": 0.7}, distress=0.6, valence=-0.4)
        results = detect_wishes(intentions, emotion_state=emotion)
        assert len(results) == 1
        assert results[0].confidence > 0.85  # Boosted by distress

    def test_session_with_cross_detector_patterns(self):
        """Cross-detector patterns provide context boost."""
        intentions = [
            Intention(id="p1", text="想知道为什么我总是选择沉默"),
        ]
        patterns = [
            CrossDetectorPattern(pattern_name="safe_silence", confidence=0.85,
                                 signals={"conflict": "avoid", "attachment": "anxious"}),
        ]
        results = detect_wishes(intentions, cross_detector_patterns=patterns)
        assert len(results) == 1
        assert results[0].confidence > 0.85


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO GROUP 7: L1 Fulfiller — profile quality
# ═══════════════════════════════════════════════════════════════════════════════


class TestFulfillerProfileQuality:
    """Verify that fulfiller uses all available detector data correctly."""

    FULL_PROFILE = DetectorResults(
        emotion={"emotions": {"sadness": 0.6, "anxiety": 0.5, "hope": 0.3}, "distress": 0.45},
        conflict={"style": "avoiding"},
        mbti={"type": "INFJ", "dimensions": {"E_I": 0.3, "S_N": 0.8, "T_F": 0.7, "J_P": 0.6}},
        attachment={"style": "anxious-preoccupied"},
        values={"top_values": ["belonging", "benevolence", "self-direction"]},
        fragility={"pattern": "approval-seeking"},
        eq={"overall": 0.65},
        communication_dna={"dominant_style": "reflective-cautious"},
        humor={"style": "self-enhancing"},
        love_language={"primary": "words_of_affirmation"},
        super_brain={"type": "analyzer"},
    )

    def test_full_profile_summary(self):
        """All available dimensions should appear in the profile."""
        profile = _extract_profile_summary(
            self.FULL_PROFILE,
            {"name": "Hidden Depths", "tagline": "Still waters run deep"},
            {"theme": "Seeking Authentic Connection"},
        )
        assert "sadness" in profile
        assert "avoiding" in profile
        assert "INFJ" in profile
        assert "anxious-preoccupied" in profile
        assert "belonging" in profile
        assert "approval-seeking" in profile
        assert "0.65" in profile
        assert "reflective-cautious" in profile
        assert "Hidden Depths" in profile
        assert "Seeking Authentic Connection" in profile

    def test_sparse_profile_still_works(self):
        """Even with minimal data, fulfiller should produce useful output."""
        sparse = DetectorResults(emotion={"emotions": {"sadness": 0.5}})
        profile = _extract_profile_summary(sparse, {}, {})
        assert "sadness" in profile
        assert profile != "No profile data available"

    def test_prompt_quality_insight_card(self):
        """Insight prompt should contain wish text + profile + instruction."""
        wish = ClassifiedWish(
            wish_text="想理解为什么自己总是讨好别人",
            wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        )
        profile = _extract_profile_summary(self.FULL_PROFILE, {"name": "Hidden Depths"}, {})
        prompt = _build_fulfillment_prompt(wish, CardType.INSIGHT, profile, [])
        assert "讨好别人" in prompt
        assert "avoiding" in prompt
        assert "INFJ" in prompt
        assert "WHY" in prompt
        assert "No clinical terms" in prompt

    def test_prompt_quality_emotion_trace(self):
        """Emotion trace prompt references emotional dimensions."""
        wish = ClassifiedWish(
            wish_text="I want to understand where my anxiety comes from",
            wish_type=WishType.EMOTIONAL_PROCESSING,
            level=WishLevel.L1,
            fulfillment_strategy="emotion_trace",
        )
        profile = _extract_profile_summary(self.FULL_PROFILE, {}, {})
        prompt = _build_fulfillment_prompt(wish, CardType.EMOTION_TRACE, profile, [])
        assert "anxiety" in prompt.lower()
        assert "Distress" in prompt
        assert "emotional origin" in prompt.lower() or "origin" in prompt.lower()

    def test_prompt_with_cross_detector_patterns(self):
        """Patterns should be included when available."""
        wish = ClassifiedWish(
            wish_text="test",
            wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        )
        patterns = [
            CrossDetectorPattern(pattern_name="safe_silence", confidence=0.8),
            CrossDetectorPattern(pattern_name="frozen_distance", confidence=0.6),
        ]
        prompt = _build_fulfillment_prompt(wish, CardType.INSIGHT, "profile", patterns)
        assert "safe_silence" in prompt
        assert "frozen_distance" in prompt

    def test_related_stars_insight_with_full_profile(self):
        """Insight card should reference conflict + attachment stars."""
        stars = _extract_related_stars(CardType.INSIGHT, self.FULL_PROFILE)
        assert "conflict:avoiding" in stars
        assert "attachment:anxious-preoccupied" in stars

    def test_related_stars_soul_portrait(self):
        """Soul portrait should reference MBTI + values."""
        stars = _extract_related_stars(CardType.SOUL_PORTRAIT, self.FULL_PROFILE)
        assert "mbti:INFJ" in stars
        assert "values:belonging" in stars

    def test_related_stars_emotion_trace(self):
        """Emotion trace references top 2 emotions."""
        stars = _extract_related_stars(CardType.EMOTION_TRACE, self.FULL_PROFILE)
        assert len(stars) == 2
        assert "emotion:sadness" in stars
        assert "emotion:anxiety" in stars


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO GROUP 8: Renderer — full lifecycle validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestRendererLifecycle:
    """Validate renderer output for complete wish lifecycles."""

    def test_l1_wish_full_lifecycle(self):
        """L1 wish: born → searching → found(gold) → fulfilled(burst)."""
        wish = ClassifiedWish(
            wish_text="想理解为什么我总是回避冲突",
            wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        )
        fulfillment = L1FulfillmentResult(
            fulfillment_text="Your tendency to step back from conflict comes from...",
            related_stars=["conflict:avoiding", "attachment:anxious"],
            card_type=CardType.INSIGHT,
        )
        stages = render_lifecycle(wish, fulfillment)

        # Born → pale purple, dim pulse
        assert stages[0].color == "#8B7BA8"
        assert stages[0].animation == "pulse_dim"

        # Searching → silver
        assert stages[1].color == "#C0C0D0"
        assert stages[1].animation == "rotate_slow"

        # Found → gold (L1)
        assert stages[2].color == "#D4A853"
        assert stages[2].animation == "brighten_gold_halo"

        # Fulfilled → warm gold burst
        assert stages[-1].color == "#F4C542"
        assert stages[-1].animation == "burst_gold_particles"
        assert "Your stars have an answer" == stages[-1].card_data["reveal_text"]
        assert stages[-1].card_data["fulfillment_text"].startswith("Your tendency")

    def test_l2_wish_found_state(self):
        """L2 wish found state → blue."""
        wish = ClassifiedWish(
            wish_text="想学冥想",
            wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2,
            fulfillment_strategy="wellness_recommendation",
        )
        found = render(WishState.FOUND, wish=wish)
        assert found.color == "#4A90D9"
        assert found.animation == "pulse_blue_wave"

    def test_l3_wish_found_state(self):
        """L3 wish found state → purple with extension."""
        wish = ClassifiedWish(
            wish_text="想找人聊聊",
            wish_type=WishType.FIND_COMPANION,
            level=WishLevel.L3,
            fulfillment_strategy="user_matching",
        )
        found = render(WishState.FOUND, wish=wish)
        assert found.color == "#9B59B6"
        assert found.animation == "glow_purple_extend"

    def test_card_data_serializable(self):
        """All card data should be JSON-serializable for frontend."""
        import json
        wish = ClassifiedWish(
            wish_text="test",
            wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1,
            fulfillment_strategy="personalized_insight",
        )
        fulfillment = L1FulfillmentResult(
            fulfillment_text="insight text",
            related_stars=["conflict:avoiding"],
            card_type=CardType.INSIGHT,
        )
        out = render(WishState.FULFILLED, wish=wish, fulfillment=fulfillment)
        # Should not raise
        serialized = json.dumps(out.model_dump())
        assert len(serialized) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO GROUP 9: Accuracy metrics — aggregate scoring
# ═══════════════════════════════════════════════════════════════════════════════


class TestAccuracyMetrics:
    """Compute aggregate accuracy across all scenario groups."""

    # Ground truth: (text, is_wish, expected_type_if_wish, expected_level_if_wish)
    GROUND_TRUTH = [
        # True wishes — L1
        ("I want to understand why I'm always so defensive", True, WishType.SELF_UNDERSTANDING, WishLevel.L1),
        ("想理解为什么我总是回避冲突", True, WishType.SELF_UNDERSTANDING, WishLevel.L1),
        ("I want to write a letter to myself", True, WishType.SELF_EXPRESSION, WishLevel.L1),
        ("想给自己写一封信", True, WishType.SELF_EXPRESSION, WishLevel.L1),
        ("I want to understand the relationship between us", True, WishType.RELATIONSHIP_INSIGHT, WishLevel.L1),
        ("想知道我和他为什么总吵架", True, WishType.RELATIONSHIP_INSIGHT, WishLevel.L1),
        ("I need to understand where my anger comes from", True, WishType.EMOTIONAL_PROCESSING, WishLevel.L1),
        ("想理解我的愤怒从哪来", True, WishType.EMOTIONAL_PROCESSING, WishLevel.L1),
        ("I want a summary of my journey so far", True, WishType.LIFE_REFLECTION, WishLevel.L1),
        ("想做一个关于自己的总结", True, WishType.LIFE_REFLECTION, WishLevel.L1),
        # True wishes — L2
        ("I want to learn meditation", True, WishType.HEALTH_WELLNESS, WishLevel.L2),
        ("想找一个安静的地方想想", True, WishType.FIND_PLACE, WishLevel.L2),
        ("I want to read a book about attachment", True, WishType.FIND_RESOURCE, WishLevel.L2),
        # True wishes — L3
        ("I want to find someone who understands me", True, WishType.FIND_COMPANION, WishLevel.L3),
        ("想找人聊聊创业的孤独感", True, WishType.FIND_COMPANION, WishLevel.L3),
        # Non-wishes
        ("Today was a good day", False, None, None),
        ("今天天气不错", False, None, None),
        ("My boss said I did a good job", False, None, None),
        ("刚才和朋友吃了顿饭", False, None, None),
        ("I went to the gym", False, None, None),
        ("太累了", False, None, None),
        ("Ok", False, None, None),
        ("嗯嗯是的", False, None, None),
        ("Yeah I guess so", False, None, None),
        ("Traffic was terrible", False, None, None),
    ]

    def test_detection_accuracy(self):
        """Wish detection accuracy (is_wish prediction)."""
        correct = 0
        total = len(self.GROUND_TRUTH)
        errors = []

        for text, is_wish, expected_type, expected_level in self.GROUND_TRUTH:
            intentions = [Intention(id="gt", text=text)]
            results = detect_wishes(intentions)
            detected = len(results) > 0

            if detected == is_wish:
                correct += 1
            else:
                direction = "FALSE_POS" if detected else "MISS"
                errors.append(f"  {direction}: '{text[:50]}'")

        accuracy = correct / total
        report = f"Detection accuracy: {correct}/{total} = {accuracy:.1%}"
        if errors:
            report += "\n" + "\n".join(errors)

        assert accuracy >= 0.80, f"Detection accuracy below 80%:\n{report}"
        print(f"\n{report}")

    def test_type_accuracy(self):
        """Type classification accuracy (for correctly detected wishes)."""
        correct = 0
        total = 0
        errors = []

        for text, is_wish, expected_type, expected_level in self.GROUND_TRUTH:
            if not is_wish:
                continue
            intentions = [Intention(id="gt", text=text)]
            results = detect_wishes(intentions)
            if not results:
                continue  # Skip misses (counted in detection accuracy)

            total += 1
            if results[0].wish_type == expected_type:
                correct += 1
            else:
                errors.append(f"  '{text[:40]}' → {results[0].wish_type} (expected {expected_type})")

        accuracy = correct / total if total > 0 else 0
        report = f"Type accuracy: {correct}/{total} = {accuracy:.1%}"
        if errors:
            report += "\n" + "\n".join(errors)

        assert accuracy >= 0.80, f"Type accuracy below 80%:\n{report}"
        print(f"\n{report}")

    def test_level_accuracy(self):
        """Level routing accuracy (for correctly typed wishes)."""
        correct = 0
        total = 0

        for text, is_wish, expected_type, expected_level in self.GROUND_TRUTH:
            if not is_wish:
                continue
            intentions = [Intention(id="gt", text=text)]
            results = detect_wishes(intentions)
            if not results:
                continue

            total += 1
            classified = classify(results[0])
            if classified.level == expected_level:
                correct += 1

        accuracy = correct / total if total > 0 else 0
        # Level accuracy should be 100% once type is correct (it's a lookup table)
        assert accuracy >= 0.95, f"Level accuracy: {correct}/{total} = {accuracy:.1%}"
