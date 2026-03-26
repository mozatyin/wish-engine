"""Tests for L3Matcher — multi-dimensional match scoring.

Covers: score computation, safety gates, privacy, compatibility tables,
ranking, mutual detection, and edge cases.
"""

from __future__ import annotations

import pytest

from wish_engine.models import AgentProfile, WishType
from wish_engine.l3_matcher import (
    L3Matcher,
    L3MatchScore,
    MATCH_THRESHOLD,
    _wish_alignment,
    _values_overlap,
    _soul_compatibility,
    _emotional_safety,
    _availability,
    _novelty,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _profile(
    agent_id: str = "a1",
    user_id: str = "u1",
    soul_type: str = "Hidden Depths",
    mbti: str = "INFJ",
    attachment_style: str = "secure",
    conflict_style: str = "collaborating",
    eq_score: float = 0.7,
    values: list[str] | None = None,
    love_language: str = "words_of_affirmation",
    humor_style: str = "affiliative",
    communication_style: str = "reflective",
    fragility_pattern: str = "",
    is_crisis: bool = False,
    distress: float = 0.1,
    available: bool = True,
    load: int = 0,
    language: str = "en",
) -> AgentProfile:
    return AgentProfile(
        agent_id=agent_id,
        user_id=user_id,
        soul_type=soul_type,
        mbti=mbti,
        attachment_style=attachment_style,
        conflict_style=conflict_style,
        eq_score=eq_score,
        values=values or ["belonging", "benevolence"],
        love_language=love_language,
        humor_style=humor_style,
        communication_style=communication_style,
        fragility_pattern=fragility_pattern,
        is_crisis=is_crisis,
        distress=distress,
        available=available,
        load=load,
        language=language,
    )


# ── Component score tests ────────────────────────────────────────────────────


class TestWishAlignment:
    def test_full_overlap(self):
        assert _wish_alignment(WishType.FIND_COMPANION, ["a", "b"], ["a", "b"]) == 1.0

    def test_partial_overlap(self):
        assert _wish_alignment(WishType.FIND_COMPANION, ["a", "b"], ["a", "c"]) == 0.5

    def test_no_overlap(self):
        assert _wish_alignment(WishType.FIND_COMPANION, ["a"], ["b"]) == 0.0

    def test_empty_seeking(self):
        assert _wish_alignment(WishType.FIND_COMPANION, [], ["a"]) == 0.0


class TestValuesOverlap:
    def test_full_overlap(self):
        assert _values_overlap(["belonging", "justice"], ["belonging", "justice"]) == 1.0

    def test_partial(self):
        score = _values_overlap(["belonging", "justice"], ["belonging", "power"])
        assert 0.3 < score < 0.5

    def test_empty_returns_neutral(self):
        assert _values_overlap([], ["a"]) == 0.5

    def test_case_insensitive(self):
        assert _values_overlap(["Belonging"], ["belonging"]) == 1.0


class TestSoulCompatibility:
    def test_secure_secure_high(self):
        a = _profile(attachment_style="secure", conflict_style="collaborating", mbti="INFJ")
        b = _profile(agent_id="b1", attachment_style="secure", conflict_style="collaborating", mbti="ENFP")
        score = _soul_compatibility(a, b, WishType.FIND_COMPANION)
        assert score > 0.7

    def test_anxious_avoidant_low(self):
        a = _profile(attachment_style="anxious", conflict_style="avoiding")
        b = _profile(agent_id="b1", attachment_style="avoidant", conflict_style="competing")
        score = _soul_compatibility(a, b, WishType.FIND_COMPANION)
        assert score < 0.5

    def test_unknown_dimensions_neutral(self):
        a = _profile(attachment_style="", conflict_style="", mbti="")
        b = _profile(agent_id="b1", attachment_style="", conflict_style="", mbti="")
        score = _soul_compatibility(a, b, WishType.FIND_COMPANION)
        assert 0.4 <= score <= 0.7  # neutral-ish (values overlap can push up)


class TestEmotionalSafety:
    def test_low_distress_high_safety(self):
        a = _profile(distress=0.1)
        b = _profile(agent_id="b1", distress=0.1)
        assert _emotional_safety(a, b) > 0.9

    def test_high_distress_reduces_safety(self):
        a = _profile(distress=0.8)
        b = _profile(agent_id="b1", distress=0.1)
        score = _emotional_safety(a, b)
        assert score < 1.0

    def test_anxious_avoidant_penalty(self):
        a = _profile(attachment_style="anxious", distress=0.1)
        b = _profile(agent_id="b1", attachment_style="avoidant", distress=0.1)
        score = _emotional_safety(a, b)
        assert score < 0.9  # has penalty

    def test_never_negative(self):
        a = _profile(distress=1.0, attachment_style="anxious", eq_score=0.2)
        b = _profile(agent_id="b1", distress=1.0, attachment_style="avoidant", eq_score=0.2)
        assert _emotional_safety(a, b) >= 0.0


class TestAvailability:
    def test_both_available_no_load(self):
        a = _profile(available=True, load=0)
        b = _profile(agent_id="b1", available=True, load=0)
        assert _availability(a, b) == 1.0

    def test_one_unavailable(self):
        a = _profile(available=True)
        b = _profile(agent_id="b1", available=False)
        assert _availability(a, b) == 0.0

    def test_high_load_reduces(self):
        a = _profile(load=4)
        b = _profile(agent_id="b1", load=4)
        score = _availability(a, b)
        assert score < 0.5


class TestNovelty:
    def test_new_connection(self):
        a = _profile()
        b = _profile(agent_id="b1")
        assert _novelty(a, b) == 1.0

    def test_repeated_connection(self):
        a = _profile()
        b = _profile(agent_id="b1")
        assert _novelty(a, b, past_matches=["b1"]) == 0.2


# ── Safety gates ─────────────────────────────────────────────────────────────


class TestSafetyGates:
    def test_crisis_excluded_from_pool(self):
        matcher = L3Matcher()
        p = _profile(is_crisis=True)
        safe, reason = matcher.is_safe_for_pool(p)
        assert not safe
        assert reason == "crisis"

    def test_unavailable_excluded(self):
        matcher = L3Matcher()
        p = _profile(available=False)
        safe, reason = matcher.is_safe_for_pool(p)
        assert not safe
        assert reason == "unavailable"

    def test_healthy_user_safe(self):
        matcher = L3Matcher()
        p = _profile()
        safe, reason = matcher.is_safe_for_pool(p)
        assert safe
        assert reason == ""

    def test_distress_delay(self):
        matcher = L3Matcher()
        p = _profile(distress=0.7)
        should_delay, reason = matcher.should_delay(p)
        assert should_delay
        assert reason == "high_distress"

    def test_load_delay(self):
        matcher = L3Matcher()
        p = _profile(load=5)
        should_delay, reason = matcher.should_delay(p)
        assert should_delay
        assert reason == "load_limit"

    def test_crisis_returns_none_score(self):
        matcher = L3Matcher()
        a = _profile(is_crisis=True)
        b = _profile(agent_id="b1")
        assert matcher.score(a, b, WishType.FIND_COMPANION) is None

    def test_crisis_b_returns_none(self):
        matcher = L3Matcher()
        a = _profile()
        b = _profile(agent_id="b1", is_crisis=True)
        assert matcher.score(a, b, WishType.FIND_COMPANION) is None


# ── Full scoring ─────────────────────────────────────────────────────────────


class TestFullScoring:
    def test_good_match_above_threshold(self):
        matcher = L3Matcher()
        a = _profile(
            attachment_style="secure", conflict_style="collaborating",
            mbti="INFJ", values=["belonging", "benevolence"],
        )
        b = _profile(
            agent_id="b1", attachment_style="secure",
            conflict_style="collaborating", mbti="ENFP",
            values=["belonging", "benevolence"],
        )
        score = matcher.score(
            a, b, WishType.FIND_COMPANION,
            seeking=["empathy", "shared_experience"],
            offering=["empathy", "shared_experience"],
        )
        assert score is not None
        assert score.total >= MATCH_THRESHOLD
        assert score.wish_alignment == 1.0

    def test_poor_match_below_threshold(self):
        matcher = L3Matcher()
        a = _profile(
            attachment_style="anxious", conflict_style="avoiding",
            mbti="INFJ", values=["power"],
        )
        b = _profile(
            agent_id="b1", attachment_style="avoidant",
            conflict_style="competing", mbti="ESTP",
            values=["tradition"], available=True, load=4,
        )
        score = matcher.score(
            a, b, WishType.FIND_COMPANION,
            seeking=["empathy", "shared_experience"],
            offering=[],  # no overlap
        )
        assert score is not None
        assert score.total < MATCH_THRESHOLD

    def test_score_breakdown_has_all_components(self):
        matcher = L3Matcher()
        a = _profile()
        b = _profile(agent_id="b1")
        score = matcher.score(a, b, WishType.FIND_COMPANION,
                              seeking=["empathy"], offering=["empathy"])
        assert score is not None
        d = score.to_dict()
        assert "wish_alignment" in d
        assert "soul_compatibility" in d
        assert "emotional_safety" in d
        assert "availability" in d
        assert "novelty" in d
        assert "total" in d

    def test_emotional_support_weights_eq_higher(self):
        """EMOTIONAL_SUPPORT should weight EQ and attachment more."""
        matcher = L3Matcher()
        # B has high EQ + secure attachment
        a = _profile(eq_score=0.3, attachment_style="anxious")
        b = _profile(agent_id="b1", eq_score=0.9, attachment_style="secure")
        score_support = matcher.score(a, b, WishType.EMOTIONAL_SUPPORT,
                                      seeking=["empathy"], offering=["empathy"])
        # Same profiles but for skill exchange
        score_skill = matcher.score(a, b, WishType.SKILL_EXCHANGE,
                                    seeking=["empathy"], offering=["empathy"])
        assert score_support is not None
        assert score_skill is not None
        # EQ matters more for emotional support
        assert score_support.soul_compatibility > score_skill.soul_compatibility


# ── Ranking ──────────────────────────────────────────────────────────────────


class TestRanking:
    def test_rank_returns_sorted(self):
        matcher = L3Matcher()
        seeker = _profile()
        # Good candidate
        c1 = _profile(
            agent_id="c1", attachment_style="secure",
            conflict_style="collaborating", mbti="ENFP",
            values=["belonging", "benevolence"],
        )
        # Poor candidate
        c2 = _profile(
            agent_id="c2", attachment_style="avoidant",
            conflict_style="competing", mbti="ESTP",
            values=["power"],
        )
        results = matcher.rank_candidates(
            seeker, [c1, c2], WishType.FIND_COMPANION,
            seeking=["empathy", "shared_experience"],
            offerings={
                "c1": ["empathy", "shared_experience"],
                "c2": ["empathy"],
            },
        )
        assert len(results) >= 1
        # c1 should rank higher
        if len(results) >= 2:
            assert results[0][0].agent_id == "c1"

    def test_rank_excludes_self(self):
        matcher = L3Matcher()
        seeker = _profile(agent_id="self")
        same = _profile(agent_id="self", user_id="u2")
        results = matcher.rank_candidates(
            seeker, [same], WishType.FIND_COMPANION,
        )
        assert len(results) == 0

    def test_rank_excludes_crisis(self):
        matcher = L3Matcher()
        seeker = _profile()
        crisis = _profile(agent_id="crisis", is_crisis=True)
        results = matcher.rank_candidates(
            seeker, [crisis], WishType.FIND_COMPANION,
            seeking=["empathy"],
            offerings={"crisis": ["empathy"]},
        )
        assert len(results) == 0


# ── Mutual detection ─────────────────────────────────────────────────────────


class TestMutualDetection:
    def test_mutual_complementary_wishes(self):
        """A wants companion, B wants emotional support — both can fulfill each other."""
        matcher = L3Matcher()
        a = _profile(
            attachment_style="secure", eq_score=0.8,
            values=["belonging", "benevolence"],
        )
        b = _profile(
            agent_id="b1", attachment_style="secure", eq_score=0.7,
            values=["belonging", "benevolence"],
        )
        is_mutual = matcher.detect_mutual(
            a, b,
            a_wish_type=WishType.FIND_COMPANION,
            b_wish_type=WishType.EMOTIONAL_SUPPORT,
            a_seeking=["empathy", "shared_experience"],
            a_offering=["empathy", "shared_experience"],
            b_seeking=["empathy", "active_listening"],
            b_offering=["empathy", "active_listening"],
        )
        assert is_mutual

    def test_non_mutual_one_direction_fails(self):
        """One direction has crisis user → blocks mutual."""
        matcher = L3Matcher()
        a = _profile()
        b = _profile(agent_id="b1", available=False)  # B unavailable
        is_mutual = matcher.detect_mutual(
            a, b,
            a_wish_type=WishType.FIND_COMPANION,
            b_wish_type=WishType.SKILL_EXCHANGE,
            a_seeking=["empathy"],
            a_offering=["empathy"],
            b_seeking=["skill_teaching"],
            b_offering=["empathy"],
        )
        assert not is_mutual

    def test_crisis_blocks_mutual(self):
        matcher = L3Matcher()
        a = _profile(is_crisis=True)
        b = _profile(agent_id="b1")
        is_mutual = matcher.detect_mutual(
            a, b,
            a_wish_type=WishType.FIND_COMPANION,
            b_wish_type=WishType.FIND_COMPANION,
            a_seeking=["empathy"], a_offering=["empathy"],
            b_seeking=["empathy"], b_offering=["empathy"],
        )
        assert not is_mutual


# ── Privacy ──────────────────────────────────────────────────────────────────


class TestPrivacy:
    def test_profile_has_no_conversation_fields(self):
        """AgentProfile should never contain raw conversation text."""
        p = _profile()
        data = p.model_dump()
        forbidden = ["conversation", "messages", "text", "raw_text",
                      "dialogue", "chat_history"]
        for field in forbidden:
            assert field not in data, f"Profile contains: {field}"

    def test_score_breakdown_has_no_personal_data(self):
        matcher = L3Matcher()
        a = _profile()
        b = _profile(agent_id="b1")
        score = matcher.score(a, b, WishType.FIND_COMPANION,
                              seeking=["empathy"], offering=["empathy"])
        assert score is not None
        d = score.to_dict()
        for key in d:
            assert isinstance(d[key], float), f"Non-float in breakdown: {key}"


# ── Edge cases ───────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_all_unknown_dimensions(self):
        """Should return a score even if all dimensions are unknown."""
        matcher = L3Matcher()
        a = AgentProfile(agent_id="a1", user_id="u1")
        b = AgentProfile(agent_id="b1", user_id="u2")
        score = matcher.score(a, b, WishType.FIND_COMPANION,
                              seeking=["empathy"], offering=["empathy"])
        assert score is not None
        assert 0.0 <= score.total <= 1.0

    def test_same_profile_different_agents(self):
        """Two identical profiles should have high compatibility."""
        matcher = L3Matcher()
        a = _profile()
        b = _profile(agent_id="b1", user_id="u2")
        score = matcher.score(a, b, WishType.FIND_COMPANION,
                              seeking=["empathy"], offering=["empathy"])
        assert score is not None
        assert score.soul_compatibility > 0.5

    def test_custom_threshold(self):
        matcher = L3Matcher(threshold=0.9)
        assert matcher.threshold == 0.9

    def test_all_wish_types_have_weights(self):
        """Every L3 wish type should produce a valid score."""
        matcher = L3Matcher()
        a = _profile()
        b = _profile(agent_id="b1")
        l3_types = [
            WishType.FIND_COMPANION, WishType.FIND_MENTOR,
            WishType.SKILL_EXCHANGE, WishType.SHARED_EXPERIENCE,
            WishType.EMOTIONAL_SUPPORT,
        ]
        for wt in l3_types:
            score = matcher.score(a, b, wt, seeking=["empathy"], offering=["empathy"])
            assert score is not None, f"No score for {wt}"
            assert 0.0 <= score.total <= 1.0, f"Invalid score for {wt}: {score.total}"
