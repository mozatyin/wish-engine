"""Tests for L3 semantic text alignment."""
import pytest

from wish_engine.l3_matcher import _text_alignment, L3Matcher, L3MatchScore, MATCH_THRESHOLD
from wish_engine.models import AgentProfile, WishType


class TestTextAlignment:
    def test_identical_texts(self):
        score = _text_alignment("hungry want food restaurant", "hungry want food restaurant")
        assert score == 1.0

    def test_completely_different(self):
        score = _text_alignment("hungry food restaurant", "lonely friend connection")
        assert score == 0.0

    def test_partial_overlap(self):
        score = _text_alignment("hungry want food", "hungry tired exhausted")
        assert 0.0 < score < 1.0

    def test_empty_a(self):
        assert _text_alignment("", "hungry food") == 0.0

    def test_empty_b(self):
        assert _text_alignment("hungry food", "") == 0.0

    def test_both_empty(self):
        assert _text_alignment("", "") == 0.0

    def test_stopwords_only(self):
        # Only stopwords → filtered to empty → 0.0
        assert _text_alignment("i am the", "you and me") == 0.0

    def test_case_insensitive(self):
        score_lower = _text_alignment("food restaurant hungry", "food restaurant hungry")
        score_mixed = _text_alignment("Food Restaurant Hungry", "food restaurant hungry")
        assert score_lower == score_mixed == 1.0

    def test_symmetry(self):
        a, b = "learn grow career", "grow career change learn"
        assert _text_alignment(a, b) == _text_alignment(b, a)


class TestAgentProfileWishText:
    def test_wish_text_default_empty(self):
        p = AgentProfile(agent_id="a1", user_id="u1")
        assert p.wish_text == ""

    def test_wish_text_set(self):
        p = AgentProfile(agent_id="a1", user_id="u1", wish_text="find mentor career growth")
        assert p.wish_text == "find mentor career growth"


class TestL3MatchScoreTextAlignment:
    def test_has_text_alignment_field(self):
        score = L3MatchScore(
            wish_alignment=0.8,
            soul_compatibility=0.7,
            emotional_safety=0.9,
            availability=1.0,
            novelty=0.5,
            text_alignment=0.6,
        )
        assert score.text_alignment == 0.6

    def test_default_text_alignment_zero(self):
        score = L3MatchScore(
            wish_alignment=0.8,
            soul_compatibility=0.7,
            emotional_safety=0.9,
            availability=1.0,
            novelty=0.5,
        )
        assert score.text_alignment == 0.0

    def test_to_dict_includes_text_alignment(self):
        score = L3MatchScore(
            wish_alignment=0.8,
            soul_compatibility=0.7,
            emotional_safety=0.9,
            availability=1.0,
            novelty=0.5,
            text_alignment=0.6,
        )
        d = score.to_dict()
        assert "text_alignment" in d
        assert d["text_alignment"] == pytest.approx(0.6, abs=0.001)

    def test_text_alignment_does_not_affect_total(self):
        base = L3MatchScore(0.8, 0.7, 0.9, 1.0, 0.5, text_alignment=0.0)
        high = L3MatchScore(0.8, 0.7, 0.9, 1.0, 0.5, text_alignment=1.0)
        # text_alignment is informational only — total unchanged
        assert base.total == pytest.approx(high.total, abs=0.001)


class TestL3MatcherComputesTextAlignment:
    def _profile(self, agent_id: str, user_id: str, wish_text: str = "") -> AgentProfile:
        return AgentProfile(
            agent_id=agent_id,
            user_id=user_id,
            attachment_style="secure",
            wish_text=wish_text,
        )

    def test_text_alignment_computed(self):
        matcher = L3Matcher()
        a = self._profile("a1", "u1", wish_text="learn mentor career growth")
        b = self._profile("a2", "u2", wish_text="mentor career learning")
        score = matcher.score(
            a, b,
            wish_type=WishType.FIND_MENTOR,
            seeking=["mentorship"],
            offering=["mentorship"],
        )
        assert score is not None
        assert score.text_alignment > 0.0

    def test_text_alignment_zero_when_no_wish_text(self):
        matcher = L3Matcher()
        a = self._profile("a1", "u1")
        b = self._profile("a2", "u2")
        score = matcher.score(
            a, b,
            wish_type=WishType.FIND_COMPANION,
            seeking=["empathy"],
            offering=["empathy"],
        )
        assert score is not None
        assert score.text_alignment == 0.0
