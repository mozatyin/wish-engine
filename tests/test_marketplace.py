"""Tests for Agent Marketplace — stock exchange model.

Simulates full lifecycle: agent registration → need posting → response →
matching → bilateral verification → mutual match.
"""

import time
import pytest

from wish_engine.models import WishType
from wish_engine.marketplace import (
    Marketplace,
    RequestType,
    RequestState,
    MatchState,
    AgentTrustLevel,
    _compute_capability_overlap,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Capability overlap
# ═══════════════════════════════════════════════════════════════════════════════


class TestCapabilityOverlap:
    def test_full_overlap(self):
        assert _compute_capability_overlap(["a", "b"], ["a", "b"]) == 1.0

    def test_partial_overlap(self):
        assert _compute_capability_overlap(["a", "b"], ["a", "c"]) == 0.5

    def test_no_overlap(self):
        assert _compute_capability_overlap(["a"], ["b"]) == 0.0

    def test_empty(self):
        assert _compute_capability_overlap([], ["a"]) == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Agent registration
# ═══════════════════════════════════════════════════════════════════════════════


class TestRegistration:
    def test_register(self):
        m = Marketplace()
        rec = m.register_agent("a1", language="zh")
        assert rec.agent_id == "a1"
        assert rec.trust_level == AgentTrustLevel.PROBATION

    def test_duplicate_register(self):
        m = Marketplace()
        m.register_agent("a1")
        rec = m.register_agent("a1")  # idempotent
        assert rec.agent_id == "a1"

    def test_unregistered_cannot_post(self):
        m = Marketplace()
        with pytest.raises(ValueError, match="not registered"):
            m.post_need("unknown", WishType.FIND_COMPANION, ["test"])


# ═══════════════════════════════════════════════════════════════════════════════
# Need posting — privacy: no host info
# ═══════════════════════════════════════════════════════════════════════════════


class TestPostNeed:
    def test_post_need(self):
        m = Marketplace()
        m.register_agent("a1")
        need = m.post_need("a1", WishType.FIND_COMPANION,
                           seeking=["entrepreneurial_experience", "willing_to_listen"])
        assert need.request_type == RequestType.NEED
        assert need.state == RequestState.OPEN
        assert "entrepreneurial_experience" in need.seeking
        # NO host profile in the need
        assert not hasattr(need, "profile") or need.model_fields.get("profile") is None

    def test_rate_limit(self):
        m = Marketplace()
        m.register_agent("a1")
        for _ in range(m.MAX_ACTIVE_NEEDS_PER_AGENT):
            m.post_need("a1", WishType.FIND_COMPANION, seeking=["test"])
        with pytest.raises(ValueError, match="too many"):
            m.post_need("a1", WishType.FIND_COMPANION, seeking=["test"])


# ═══════════════════════════════════════════════════════════════════════════════
# Response posting
# ═══════════════════════════════════════════════════════════════════════════════


class TestPostResponse:
    def test_respond_to_need(self):
        m = Marketplace()
        m.register_agent("a1")
        m.register_agent("b1")
        need = m.post_need("a1", WishType.FIND_COMPANION, seeking=["empathy"])
        resp = m.post_response("b1", in_response_to=need.request_id,
                               offering=["empathy", "good_listener"])
        assert resp.request_type == RequestType.RESPONSE
        assert resp.in_response_to == need.request_id

    def test_cannot_respond_to_self(self):
        m = Marketplace()
        m.register_agent("a1")
        need = m.post_need("a1", WishType.FIND_COMPANION, seeking=["test"])
        with pytest.raises(ValueError, match="own need"):
            m.post_response("a1", in_response_to=need.request_id, offering=["test"])


# ═══════════════════════════════════════════════════════════════════════════════
# Full matching lifecycle
# ═══════════════════════════════════════════════════════════════════════════════


class TestFullLifecycle:
    """Simulates the complete exchange cycle."""

    def test_entrepreneurship_match(self):
        """Two agents: A wants to discuss startup loneliness, B has experience."""
        m = Marketplace()
        m.register_agent("agent_A", language="zh")
        m.register_agent("agent_B", language="zh")

        # A posts need
        need = m.post_need(
            "agent_A",
            WishType.FIND_COMPANION,
            seeking=["entrepreneurial_experience", "willing_to_listen", "understands_loneliness"],
        )

        # B sees the need (polls open needs)
        open_needs = m.get_open_needs(language="zh")
        assert len(open_needs) == 1
        assert open_needs[0].request_id == need.request_id

        # B decides locally it can help, posts response
        resp = m.post_response(
            "agent_B",
            in_response_to=need.request_id,
            offering=["entrepreneurial_experience", "high_benevolence", "willing_to_listen"],
        )

        # Exchange creates match (capability overlap only)
        matches = m.create_matches()
        assert len(matches) == 1
        match = matches[0]
        assert match.agent_a_id == "agent_A"
        assert match.agent_b_id == "agent_B"
        assert match.capability_overlap > 0.5  # 2/3 overlap
        assert match.state == MatchState.PROPOSED

        # Both agents verify locally (check host safety)
        m.verify(match.match_id, "agent_A", approved=True)
        assert m._matches[match.match_id].state == MatchState.A_VERIFIED

        m.verify(match.match_id, "agent_B", approved=True)
        assert m._matches[match.match_id].state == MatchState.MUTUAL

        # Mutual → ready for human notification
        mutual = m.get_mutual_matches()
        assert len(mutual) == 1

    def test_agent_b_declines(self):
        """B's agent decides match is unsafe for host → declines."""
        m = Marketplace()
        m.register_agent("a1")
        m.register_agent("b1")

        need = m.post_need("a1", WishType.EMOTIONAL_SUPPORT, seeking=["empathy"])
        m.post_response("b1", in_response_to=need.request_id, offering=["empathy"])
        matches = m.create_matches()

        # B declines (maybe host is in distress this week)
        m.verify(matches[0].match_id, "b1", approved=False)
        assert m._matches[matches[0].match_id].state == MatchState.B_DECLINED

        # No mutual matches
        assert len(m.get_mutual_matches()) == 0

    def test_multiple_responses_to_one_need(self):
        """Multiple agents can respond to one need."""
        m = Marketplace()
        m.register_agent("a1")
        for i in range(3):
            m.register_agent(f"b{i}")

        need = m.post_need("a1", WishType.FIND_COMPANION, seeking=["empathy"])

        for i in range(3):
            m.post_response(f"b{i}", in_response_to=need.request_id,
                            offering=["empathy"])

        matches = m.create_matches()
        # All 3 should match (all have full overlap)
        assert len(matches) >= 1


class TestMutualWish:
    """Both agents have complementary needs — strongest chocolate moment."""

    def test_mutual_needs(self):
        """A wants to chat about loneliness, B wants someone to listen to their story."""
        m = Marketplace()
        m.register_agent("a1")
        m.register_agent("b1")

        # A posts need
        need_a = m.post_need("a1", WishType.FIND_COMPANION,
                             seeking=["willing_to_listen", "understands_loneliness"])

        # B also has a need
        need_b = m.post_need("b1", WishType.EMOTIONAL_SUPPORT,
                             seeking=["good_listener", "non_judgmental"])

        # A responds to B's need
        m.post_response("a1", in_response_to=need_b.request_id,
                        offering=["good_listener", "empathetic"])

        # B responds to A's need
        m.post_response("b1", in_response_to=need_a.request_id,
                        offering=["willing_to_listen", "understands_loneliness"])

        # Create matches — should get 2 matches (A→B and B→A)
        matches = m.create_matches()
        assert len(matches) == 2

        # Verify all
        for match in matches:
            m.verify(match.match_id, match.agent_a_id, approved=True)
            m.verify(match.match_id, match.agent_b_id, approved=True)

        mutual = m.get_mutual_matches()
        assert len(mutual) == 2  # Both directions matched


# ═══════════════════════════════════════════════════════════════════════════════
# Privacy guarantees
# ═══════════════════════════════════════════════════════════════════════════════


class TestPrivacy:
    """Verify that no personal information leaks through the exchange."""

    def test_need_contains_no_profile(self):
        m = Marketplace()
        m.register_agent("a1")
        need = m.post_need("a1", WishType.FIND_COMPANION, seeking=["empathy"])
        data = need.model_dump()
        # Should not contain any profile fields
        forbidden = ["soul_type", "mbti", "attachment", "distress", "eq_score",
                     "conflict_style", "fragility", "values"]
        for field in forbidden:
            assert field not in data, f"Need contains profile field: {field}"

    def test_agent_record_contains_no_profile(self):
        m = Marketplace()
        rec = m.register_agent("a1")
        data = rec.model_dump()
        forbidden = ["soul_type", "mbti", "attachment", "distress", "eq_score"]
        for field in forbidden:
            assert field not in data, f"Agent record contains: {field}"

    def test_match_contains_no_profile(self):
        m = Marketplace()
        m.register_agent("a1")
        m.register_agent("b1")
        need = m.post_need("a1", WishType.FIND_COMPANION, seeking=["empathy"])
        m.post_response("b1", in_response_to=need.request_id, offering=["empathy"])
        matches = m.create_matches()
        data = matches[0].model_dump()
        forbidden = ["soul_type", "mbti", "attachment", "distress", "eq_score", "profile"]
        for field in forbidden:
            assert field not in data, f"Match contains profile field: {field}"


# ═══════════════════════════════════════════════════════════════════════════════
# Trust management
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrust:
    def test_new_agent_on_probation(self):
        m = Marketplace()
        rec = m.register_agent("a1")
        assert rec.trust_level == AgentTrustLevel.PROBATION

    def test_promotion_after_good_behavior(self):
        m = Marketplace()
        rec = m.register_agent("a1")
        rec.total_matches = 3
        rec.declined_count = 0
        m.promote_agent("a1")
        assert m._agents["a1"].trust_level == AgentTrustLevel.TRUSTED

    def test_suspended_cannot_post(self):
        m = Marketplace()
        m.register_agent("a1")
        m.suspend_agent("a1")
        with pytest.raises(ValueError, match="suspended"):
            m.post_need("a1", WishType.FIND_COMPANION, seeking=["test"])


# ═══════════════════════════════════════════════════════════════════════════════
# Stats
# ═══════════════════════════════════════════════════════════════════════════════


class TestStats:
    def test_stats(self):
        m = Marketplace()
        m.register_agent("a1")
        m.register_agent("b1")
        m.post_need("a1", WishType.FIND_COMPANION, seeking=["test"])
        stats = m.get_stats()
        assert stats["agents"] == 2
        assert stats["open_needs"] == 1
        assert stats["total_matches"] == 0
