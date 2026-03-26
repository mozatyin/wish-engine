"""Integration tests — L2 wishes flow through the full engine pipeline."""

import pytest
from wish_engine.models import (
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishState,
)
from wish_engine.engine import WishEngine


class TestL2EngineIntegration:
    def test_l2_wish_gets_fulfilled(self):
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想找个安静的地方"],
            detector_results=DetectorResults(
                mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}},
            ),
            session_id="s1",
            user_id="u1",
        )
        assert len(result.l2_wishes) >= 1
        assert len(result.l2_fulfillments) >= 1

    def test_l2_render_blue_star(self):
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想学冥想"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        l2_renders = [
            r for r in result.renders
            if r.star_state == WishState.FOUND and r.color == "#4A90D9"
        ]
        assert len(l2_renders) >= 1
        assert l2_renders[0].animation == "pulse_blue_wave"

    def test_l2_card_data_has_recommendations(self):
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想读一本关于心理学的书"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        found_renders = [r for r in result.renders if r.star_state == WishState.FOUND]
        if found_renders:
            card = found_renders[0].card_data
            assert "recommendations" in card
            assert len(card["recommendations"]) >= 1

    def test_l2_queue_state_found(self):
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想学画画"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        l2_queued = [q for q in result.queued if q.wish.level == WishLevel.L2]
        assert len(l2_queued) >= 1
        assert l2_queued[0].state == WishState.FOUND

    def test_l2_with_personality_filtering(self):
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想找个地方运动"],
            detector_results=DetectorResults(
                mbti={"type": "INFP", "dimensions": {"E_I": 0.15}},
            ),
            session_id="s1",
            user_id="u1",
        )
        if result.l2_fulfillments:
            for key, ful in result.l2_fulfillments.items():
                for rec in ful.recommendations:
                    assert "noisy" not in rec.tags

    def test_l2_summary_counts(self):
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想找个安静地方"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        summary = result.summary()
        assert summary["l2"] >= 1
        assert summary["l2_fulfilled"] >= 1

    def test_l2_chocolate_moment_timing(self):
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想找个安静地方"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        l2_queued = [q for q in result.queued if q.wish.level == WishLevel.L2]
        if l2_queued:
            assert l2_queued[0].reveal_after > 0
