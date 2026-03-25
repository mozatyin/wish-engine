"""End-to-end integration tests for WishEngine facade.

Tests the full pipeline: SoulItem → detect → dedup → classify → route →
fulfill/marketplace → queue → render.
"""

import json
import pytest
from pathlib import Path

from wish_engine.models import (
    CardType, ClassifiedWish, CrossDetectorPattern, DetectedWish,
    DetectorResults, EmotionState, Intention, L1FulfillmentResult,
    RenderOutput, WishLevel, WishState, WishType,
)
from wish_engine.engine import WishEngine, WishEngineResult, _count_profile_dimensions
from wish_engine.marketplace import Marketplace
from wish_engine.queue import WishQueue, WishPriority


FIXTURES_DIR = Path.home() / "soulgraph" / "fixtures"


def _load_fixture(name: str) -> list[dict]:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f).get("items", [])


RICH_PROFILE = DetectorResults(
    emotion={"emotions": {"anxiety": 0.6, "frustration": 0.4}, "distress": 0.45},
    conflict={"style": "avoiding"},
    mbti={"type": "INFJ"},
    attachment={"style": "anxious-preoccupied"},
    values={"top_values": ["belonging", "benevolence"]},
    fragility={"pattern": "approval-seeking"},
    eq={"overall": 0.65},
    communication_dna={"dominant_style": "reflective-cautious"},
)

SPARSE_PROFILE = DetectorResults(
    emotion={"emotions": {"sadness": 0.5}},
)


# ═══════════════════════════════════════════════════════════════════════════════
# Profile sufficiency gate
# ═══════════════════════════════════════════════════════════════════════════════


class TestProfileSufficiency:
    def test_rich_profile(self):
        assert _count_profile_dimensions(RICH_PROFILE) >= 3

    def test_sparse_profile(self):
        assert _count_profile_dimensions(SPARSE_PROFILE) < 3

    def test_empty_profile(self):
        assert _count_profile_dimensions(DetectorResults()) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Engine with Path A (SoulItem structured detection)
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnginePathA:
    """Process SoulGraph fixtures through the engine."""

    def test_zhang_wei_session(self):
        """Career changer → detects wishes, routes to L1/L2."""
        items = _load_fixture("zhang_wei.json")
        engine = WishEngine(fulfill_l1=False)  # No API call
        result = engine.process(
            soul_items=items,
            detector_results=RICH_PROFILE,
            user_id="zhang_wei",
            session_id="s1",
        )
        assert result.total_wishes >= 3
        assert len(result.l2_wishes) >= 1  # Career wishes
        assert len(result.renders) >= 1

    def test_anxiety_user_session(self):
        """Anxiety user → wellness wishes."""
        items = _load_fixture("anxiety_user.json")
        engine = WishEngine(fulfill_l1=False)
        result = engine.process(
            soul_items=items,
            detector_results=RICH_PROFILE,
            user_id="anxiety",
            session_id="s1",
        )
        assert result.total_wishes >= 2
        # Wellness wishes → L2
        assert len(result.l2_wishes) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# Engine with Path B (raw text wishes)
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnginePathB:
    """Process raw wish text through the engine."""

    def test_single_l1_wish_no_api(self):
        engine = WishEngine(fulfill_l1=False)
        result = engine.process(
            raw_wishes=["想理解为什么我总是回避冲突"],
            detector_results=RICH_PROFILE,
            user_id="u1",
        )
        assert result.total_wishes == 1
        assert len(result.l1_wishes) == 1
        assert result.l1_wishes[0].wish_type == WishType.SELF_UNDERSTANDING

    def test_multiple_wishes_mixed_levels(self):
        engine = WishEngine(fulfill_l1=False)
        result = engine.process(
            raw_wishes=[
                "想理解为什么我总是回避冲突",  # L1
                "想找一个安静的地方想想",      # L2
                "想找人聊聊创业的孤独感",      # L3
            ],
            detector_results=RICH_PROFILE,
            user_id="u1",
        )
        assert len(result.l1_wishes) >= 1
        assert len(result.l2_wishes) >= 1
        assert len(result.l3_wishes) >= 1

    def test_non_wishes_filtered(self):
        engine = WishEngine(fulfill_l1=False)
        result = engine.process(
            raw_wishes=["今天天气不错", "好无聊"],
            user_id="u1",
        )
        assert result.total_wishes == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Profile sufficiency gate in engine
# ═══════════════════════════════════════════════════════════════════════════════


class TestSufficiencyGate:
    def test_sparse_profile_stays_born(self):
        """With sparse profile, L1 wishes stay in BORN (no fulfillment)."""
        engine = WishEngine(fulfill_l1=True)  # would fulfill if enough data
        result = engine.process(
            raw_wishes=["I want to understand myself"],
            detector_results=SPARSE_PROFILE,
            user_id="u1",
        )
        assert len(result.l1_wishes) == 1
        assert len(result.fulfillments) == 0  # Not fulfilled
        assert result.renders[0].star_state == WishState.BORN

    def test_rich_profile_reaches_found(self):
        """With rich profile but no API key, reaches SEARCHING."""
        engine = WishEngine(api_key="", fulfill_l1=True)
        result = engine.process(
            raw_wishes=["I want to understand myself"],
            detector_results=RICH_PROFILE,
            user_id="u1",
        )
        assert len(result.l1_wishes) == 1
        # No API key → searching (can't fulfill)
        assert result.renders[0].star_state == WishState.SEARCHING


# ═══════════════════════════════════════════════════════════════════════════════
# L3 marketplace integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestL3Integration:
    def test_l3_wish_posted_to_marketplace(self):
        market = Marketplace()
        market.register_agent("agent_u1")
        engine = WishEngine(marketplace=market, fulfill_l1=False)

        result = engine.process(
            raw_wishes=["I want to find someone who understands me"],
            user_id="u1",
            agent_id="agent_u1",
        )
        assert len(result.l3_wishes) == 1
        assert result.marketplace_needs_posted == 1

        # Verify need is in marketplace
        needs = market.get_open_needs()
        assert len(needs) == 1
        assert needs[0].agent_id == "agent_u1"

    def test_l3_without_marketplace(self):
        """Without marketplace, L3 wishes still queue but don't post."""
        engine = WishEngine(marketplace=None, fulfill_l1=False)
        result = engine.process(
            raw_wishes=["I want to find a mentor"],
            user_id="u1",
        )
        assert len(result.l3_wishes) == 1
        assert result.marketplace_needs_posted == 0

    def test_full_l3_cycle(self):
        """Full cycle: A posts need → B responds → match → verify → mutual."""
        market = Marketplace()
        market.register_agent("agent_A", language="zh")
        market.register_agent("agent_B", language="zh")

        engine = WishEngine(marketplace=market, fulfill_l1=False)

        # A's session
        result_a = engine.process(
            raw_wishes=["想找人聊聊创业的孤独感"],
            user_id="user_A",
            agent_id="agent_A",
        )
        assert result_a.marketplace_needs_posted == 1

        # B sees the need
        needs = market.get_open_needs(language="zh")
        assert len(needs) == 1

        # B responds
        market.post_response(
            "agent_B",
            in_response_to=needs[0].request_id,
            offering=["entrepreneurial_experience", "willing_to_listen", "empathy"],
        )

        # Match engine runs
        matches = market.create_matches()
        assert len(matches) == 1

        # Both verify
        market.verify(matches[0].match_id, "agent_A", approved=True)
        market.verify(matches[0].match_id, "agent_B", approved=True)

        mutual = market.get_mutual_matches()
        assert len(mutual) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Queue integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestQueueIntegration:
    def test_wishes_enqueued(self):
        engine = WishEngine(fulfill_l1=False)
        result = engine.process(
            raw_wishes=["想理解自己"],
            detector_results=RICH_PROFILE,
            user_id="u1",
        )
        assert len(result.queued) >= 1

    def test_queue_persists_across_sessions(self):
        queue = WishQueue()
        engine = WishEngine(queue=queue, fulfill_l1=False)

        # Session 1
        engine.process(raw_wishes=["想理解自己"], user_id="u1", session_id="s1")

        # Session 2 — same queue
        engine.process(raw_wishes=["想知道我和她为什么总吵架"], user_id="u1", session_id="s2")

        assert queue.get_active_count("u1") == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Dedup integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestDedupIntegration:
    def test_duplicate_wishes_merged(self):
        engine = WishEngine(fulfill_l1=False)
        result = engine.process(
            raw_wishes=[
                "I want to understand why I avoid conflict",
                "I want to understand why I always withdraw from confrontation",
            ],
            user_id="u1",
        )
        # Should be deduped to 1
        assert result.total_wishes == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Render integration
# ═══════════════════════════════════════════════════════════════════════════════


class TestRenderIntegration:
    def test_renders_generated(self):
        engine = WishEngine(fulfill_l1=False)
        result = engine.process(
            raw_wishes=["想理解自己"],
            detector_results=RICH_PROFILE,
            user_id="u1",
        )
        assert len(result.renders) >= 1
        r = result.renders[0]
        assert r.star_state in (WishState.BORN, WishState.SEARCHING, WishState.FOUND)
        assert len(r.color) == 7  # #RRGGBB

    def test_chocolate_moment_check(self):
        engine = WishEngine(fulfill_l1=False)
        result = engine.process(raw_wishes=["想理解自己"], user_id="u1")
        assert not result.has_chocolate_moment  # No fulfillment without API


# ═══════════════════════════════════════════════════════════════════════════════
# Error handling
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    def test_empty_input(self):
        engine = WishEngine()
        result = engine.process(user_id="u1")
        assert result.total_wishes == 0
        assert len(result.errors) == 0

    def test_invalid_api_key_graceful(self):
        engine = WishEngine(api_key="invalid", fulfill_l1=True)
        result = engine.process(
            raw_wishes=["想理解自己"],
            detector_results=RICH_PROFILE,
            user_id="u1",
        )
        # Should error gracefully, not crash
        assert len(result.errors) >= 1 or result.renders[0].star_state in (
            WishState.BORN, WishState.SEARCHING
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Result summary
# ═══════════════════════════════════════════════════════════════════════════════


class TestResultSummary:
    def test_summary_structure(self):
        engine = WishEngine(fulfill_l1=False)
        result = engine.process(
            raw_wishes=["想理解自己", "想找人聊聊"],
            user_id="u1",
        )
        s = result.summary()
        assert "detected" in s
        assert "classified" in s
        assert "l1" in s
        assert "l2" in s
        assert "l3" in s
        assert "errors" in s
