"""Tests for GameFulfiller — MBTI-aware game recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_games import GameFulfiller, GAME_CATALOG


class TestGameCatalog:
    def test_catalog_has_15_entries(self):
        assert len(GAME_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in GAME_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestGameFulfiller:
    def _make_wish(self, text="想玩游戏") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = GameFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = GameFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_solo_games(self):
        f = GameFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish("I want to play puzzle games"), det)
        # Introverts should not get loud/high-social items
        for r in result.recommendations:
            assert not (r.category in ("party_game", "trivia_night", "vr_arcade")
                        and r.score > 0.7)

    def test_chess_keyword_match(self):
        f = GameFulfiller()
        result = f.fulfill(self._make_wish("I want to play chess"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "chess_club" in categories

    def test_mahjong_keyword_match(self):
        f = GameFulfiller()
        result = f.fulfill(self._make_wish("想打麻将"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "mahjong" in categories

    def test_has_reminder(self):
        f = GameFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = GameFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
