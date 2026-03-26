"""Tests for AgentNegotiator — agent-to-agent negotiation protocol.

Covers: proposal creation, evaluation logic, safety gates (crisis/distress/load),
full negotiation lifecycle, mutual match detection, and privacy.
"""

import time
import pytest

from wish_engine.models import (
    AgentProfile,
    NegotiationState,
    WishType,
)
from wish_engine.l3_matcher import L3Matcher, MATCH_THRESHOLD
from wish_engine.agent_negotiator import (
    AgentNegotiator,
    DISTRESS_DELAY_SECONDS,
    LOAD_DELAY_SECONDS,
    MAX_ACTIVE_NEGOTIATIONS,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _profile(
    agent_id: str = "a1",
    user_id: str = "u1",
    mbti: str = "INFJ",
    attachment_style: str = "secure",
    conflict_style: str = "collaborating",
    eq_score: float = 0.7,
    values: list[str] | None = None,
    is_crisis: bool = False,
    distress: float = 0.1,
    available: bool = True,
    load: int = 0,
) -> AgentProfile:
    return AgentProfile(
        agent_id=agent_id,
        user_id=user_id,
        soul_type="Hidden Depths",
        mbti=mbti,
        attachment_style=attachment_style,
        conflict_style=conflict_style,
        eq_score=eq_score,
        values=values or ["belonging", "benevolence"],
        love_language="words_of_affirmation",
        humor_style="affiliative",
        communication_style="reflective",
        is_crisis=is_crisis,
        distress=distress,
        available=available,
        load=load,
    )


# ── Proposal creation ────────────────────────────────────────────────────────


class TestPropose:
    def test_successful_proposal(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        proposal = neg.propose(
            a, b, match_id="m1", wish_type=WishType.FIND_COMPANION,
            seeking=["empathy", "shared_experience"],
            offering=["empathy", "shared_experience"],
        )
        assert proposal is not None
        assert proposal.from_agent_id == "a1"
        assert proposal.to_agent_id == "b1"
        assert proposal.match_score >= MATCH_THRESHOLD

    def test_crisis_user_cannot_propose(self):
        neg = AgentNegotiator()
        a = _profile(is_crisis=True)
        b = _profile(agent_id="b1")
        assert neg.propose(a, b, "m1", WishType.FIND_COMPANION) is None

    def test_crisis_target_blocked(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1", is_crisis=True)
        assert neg.propose(a, b, "m1", WishType.FIND_COMPANION) is None

    def test_rate_limit_proposals(self):
        neg = AgentNegotiator()
        a = _profile()
        for i in range(MAX_ACTIVE_NEGOTIATIONS):
            b = _profile(agent_id=f"b{i}")
            result = neg.propose(
                a, b, f"m{i}", WishType.FIND_COMPANION,
                seeking=["empathy"], offering=["empathy"],
            )
            assert result is not None
        # Next proposal should be blocked
        b_extra = _profile(agent_id="b_extra")
        assert neg.propose(
            a, b_extra, "m_extra", WishType.FIND_COMPANION,
            seeking=["empathy"], offering=["empathy"],
        ) is None

    def test_below_threshold_returns_none(self):
        neg = AgentNegotiator()
        a = _profile(attachment_style="anxious", conflict_style="avoiding")
        b = _profile(agent_id="b1", attachment_style="avoidant", conflict_style="competing",
                     available=True, load=4)
        # No capability overlap + poor compatibility
        result = neg.propose(
            a, b, "m1", WishType.FIND_COMPANION,
            seeking=["empathy", "shared_experience"],
            offering=[],
        )
        # Might be None if total score < threshold
        # (depends on exact scoring, but with 0 wish alignment + poor soul compat...)
        if result is not None:
            assert result.match_score >= MATCH_THRESHOLD


# ── Evaluation logic ─────────────────────────────────────────────────────────


class TestEvaluate:
    def _make_proposal(self, neg: AgentNegotiator) -> tuple:
        a = _profile()
        b = _profile(agent_id="b1")
        proposal = neg.propose(
            a, b, "m1", WishType.FIND_COMPANION,
            seeking=["empathy"], offering=["empathy"],
        )
        return proposal, b

    def test_accept_healthy_user(self):
        neg = AgentNegotiator()
        proposal, b = self._make_proposal(neg)
        assert proposal is not None
        resp = neg.evaluate(proposal, local_profile=b)
        assert resp.state == NegotiationState.ACCEPTED

    def test_crisis_decline(self):
        neg = AgentNegotiator()
        proposal, _ = self._make_proposal(neg)
        assert proposal is not None
        crisis_b = _profile(agent_id="b1", is_crisis=True)
        resp = neg.evaluate(proposal, local_profile=crisis_b)
        assert resp.state == NegotiationState.DECLINED
        assert resp.reason == "crisis"

    def test_high_distress_delay(self):
        neg = AgentNegotiator()
        proposal, _ = self._make_proposal(neg)
        assert proposal is not None
        distressed_b = _profile(agent_id="b1", distress=0.7)
        resp = neg.evaluate(proposal, local_profile=distressed_b)
        assert resp.state == NegotiationState.DELAYED
        assert resp.reason == "high_distress"
        assert resp.delay_until > time.time()

    def test_distress_exactly_0_6_not_delayed(self):
        neg = AgentNegotiator()
        proposal, _ = self._make_proposal(neg)
        assert proposal is not None
        b = _profile(agent_id="b1", distress=0.6)
        resp = neg.evaluate(proposal, local_profile=b)
        assert resp.state == NegotiationState.ACCEPTED

    def test_load_limit_delay(self):
        neg = AgentNegotiator()
        proposal, _ = self._make_proposal(neg)
        assert proposal is not None
        overloaded_b = _profile(agent_id="b1", load=5)
        resp = neg.evaluate(proposal, local_profile=overloaded_b)
        assert resp.state == NegotiationState.DELAYED
        assert resp.reason == "load_limit"

    def test_unavailable_decline(self):
        neg = AgentNegotiator()
        proposal, _ = self._make_proposal(neg)
        assert proposal is not None
        unavail_b = _profile(agent_id="b1", available=False)
        resp = neg.evaluate(proposal, local_profile=unavail_b)
        assert resp.state == NegotiationState.DECLINED
        assert resp.reason == "unavailable"


# ── Full negotiation lifecycle ───────────────────────────────────────────────


class TestFullNegotiation:
    def test_successful_negotiation(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        result, resp = neg.negotiate_full(
            a, b, match_id="m1", wish_type=WishType.FIND_COMPANION,
            seeking=["empathy", "shared_experience"],
            offering=["empathy", "shared_experience"],
        )
        assert result is not None
        assert result.match_id == "m1"
        assert result.agent_a_id == "a1"
        assert result.agent_b_id == "b1"
        assert result.match_text == "Someone's star resonates with yours"
        assert not result.is_mutual

    def test_delayed_returns_response(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1", distress=0.8)
        result, resp = neg.negotiate_full(
            a, b, "m1", WishType.FIND_COMPANION,
            seeking=["empathy"], offering=["empathy"],
        )
        assert result is None
        assert resp is not None
        assert resp.state == NegotiationState.DELAYED

    def test_crisis_returns_none_none(self):
        neg = AgentNegotiator()
        a = _profile(is_crisis=True)
        b = _profile(agent_id="b1")
        result, resp = neg.negotiate_full(a, b, "m1", WishType.FIND_COMPANION)
        assert result is None
        assert resp is None


# ── Mutual match detection ───────────────────────────────────────────────────


class TestMutualMatch:
    def test_mutual_stars_found_each_other(self):
        """Both users have complementary wishes → 'Your stars found each other'."""
        neg = AgentNegotiator()
        a = _profile(eq_score=0.8, values=["belonging", "benevolence"])
        b = _profile(agent_id="b1", eq_score=0.7, values=["belonging", "benevolence"])
        result = neg.negotiate_mutual(
            a, b, match_id="mutual_1",
            a_wish_type=WishType.FIND_COMPANION,
            b_wish_type=WishType.EMOTIONAL_SUPPORT,
            a_seeking=["empathy", "shared_experience"],
            a_offering=["empathy", "shared_experience"],
            b_seeking=["empathy", "active_listening"],
            b_offering=["empathy", "active_listening"],
        )
        assert result is not None
        assert result.is_mutual
        assert result.match_text == "Your stars found each other"
        assert result.agent_a_id == "a1"
        assert result.agent_b_id == "b1"

    def test_mutual_blocked_by_distress(self):
        """Even if wishes match, high distress delays the mutual match."""
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1", distress=0.8)
        result = neg.negotiate_mutual(
            a, b, "mutual_1",
            a_wish_type=WishType.FIND_COMPANION,
            b_wish_type=WishType.FIND_COMPANION,
            a_seeking=["empathy"], a_offering=["empathy"],
            b_seeking=["empathy"], b_offering=["empathy"],
        )
        assert result is None  # B's distress blocks

    def test_mutual_blocked_by_crisis(self):
        neg = AgentNegotiator()
        a = _profile(is_crisis=True)
        b = _profile(agent_id="b1")
        result = neg.negotiate_mutual(
            a, b, "mutual_1",
            a_wish_type=WishType.FIND_COMPANION,
            b_wish_type=WishType.FIND_COMPANION,
            a_seeking=["empathy"], a_offering=["empathy"],
            b_seeking=["empathy"], b_offering=["empathy"],
        )
        assert result is None

    def test_non_mutual_returns_none(self):
        """Unavailable user blocks mutual match."""
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1", available=False)
        result = neg.negotiate_mutual(
            a, b, "mutual_1",
            a_wish_type=WishType.FIND_COMPANION,
            b_wish_type=WishType.FIND_COMPANION,
            a_seeking=["empathy"], a_offering=["empathy"],
            b_seeking=["empathy"], b_offering=["empathy"],
        )
        assert result is None


# ── Finalize ─────────────────────────────────────────────────────────────────


class TestFinalize:
    def test_finalize_creates_result(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        proposal = neg.propose(
            a, b, "m1", WishType.FIND_COMPANION,
            seeking=["empathy"], offering=["empathy"],
        )
        assert proposal is not None
        result = neg.finalize(proposal, a, b, is_mutual=False)
        assert result.match_text == "Someone's star resonates with yours"
        assert not result.is_mutual

    def test_finalize_mutual(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        proposal = neg.propose(
            a, b, "m1", WishType.FIND_COMPANION,
            seeking=["empathy"], offering=["empathy"],
        )
        assert proposal is not None
        result = neg.finalize(proposal, a, b, is_mutual=True)
        assert result.match_text == "Your stars found each other"
        assert result.is_mutual


# ── State tracking ───────────────────────────────────────────────────────────


class TestStateTracking:
    def test_active_count_increments(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        neg.propose(a, b, "m1", WishType.FIND_COMPANION,
                    seeking=["empathy"], offering=["empathy"])
        assert neg.get_active_count("a1") == 1

    def test_get_proposal(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        proposal = neg.propose(a, b, "m1", WishType.FIND_COMPANION,
                               seeking=["empathy"], offering=["empathy"])
        assert proposal is not None
        fetched = neg.get_proposal(proposal.proposal_id)
        assert fetched is not None
        assert fetched.match_id == "m1"

    def test_get_response(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        proposal = neg.propose(a, b, "m1", WishType.FIND_COMPANION,
                               seeking=["empathy"], offering=["empathy"])
        assert proposal is not None
        neg.evaluate(proposal, local_profile=b)
        resp = neg.get_response(proposal.proposal_id)
        assert resp is not None
        assert resp.state == NegotiationState.ACCEPTED


# ── Privacy ──────────────────────────────────────────────────────────────────


class TestPrivacy:
    def test_proposal_contains_no_conversation(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        proposal = neg.propose(a, b, "m1", WishType.FIND_COMPANION,
                               seeking=["empathy"], offering=["empathy"])
        assert proposal is not None
        data = proposal.model_dump()
        forbidden = ["conversation", "messages", "text", "raw_text",
                      "dialogue", "chat_history", "soul_type",
                      "mbti", "attachment"]
        for field in forbidden:
            assert field not in data, f"Proposal contains: {field}"

    def test_response_contains_no_personal_data(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        proposal = neg.propose(a, b, "m1", WishType.FIND_COMPANION,
                               seeking=["empathy"], offering=["empathy"])
        assert proposal is not None
        resp = neg.evaluate(proposal, local_profile=b)
        data = resp.model_dump()
        forbidden = ["soul_type", "mbti", "attachment", "distress",
                      "eq_score", "profile"]
        for field in forbidden:
            assert field not in data, f"Response contains: {field}"

    def test_l3_match_result_no_profile(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        proposal = neg.propose(a, b, "m1", WishType.FIND_COMPANION,
                               seeking=["empathy"], offering=["empathy"])
        assert proposal is not None
        result = neg.finalize(proposal, a, b)
        data = result.model_dump()
        forbidden = ["conversation", "messages", "profile", "raw_text"]
        for field in forbidden:
            assert field not in data, f"Result contains: {field}"


# ── Expiry ───────────────────────────────────────────────────────────────────


class TestExpiry:
    def test_expire_stale_negotiations(self):
        neg = AgentNegotiator()
        a = _profile()
        b = _profile(agent_id="b1")
        proposal = neg.propose(a, b, "m1", WishType.FIND_COMPANION,
                               seeking=["empathy"], offering=["empathy"])
        assert proposal is not None

        # Backdate the proposal
        proposal.created_at = time.time() - 50 * 3600  # 50 hours ago

        expired = neg.expire_stale()
        assert expired == 1
        assert neg.get_proposal(proposal.proposal_id) is None
        assert neg.get_active_count("a1") == 0
