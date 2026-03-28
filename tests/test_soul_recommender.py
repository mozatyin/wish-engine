"""Tests for Soul Recommender — TriSoul layers drive real place recommendations."""

import pytest
from unittest.mock import patch
from wish_engine.soul_recommender import (
    detect_surface_attention,
    detect_middle_history,
    recommend_from_soul,
    SoulRecommendation,
)


class TestSurfaceDetection:
    def test_hungry(self):
        assert "hungry" in detect_surface_attention(["I'm so hungry I could die"])

    def test_anxious(self):
        assert "anxious" in detect_surface_attention(["I feel so anxious and nervous"])

    def test_lonely_chinese(self):
        assert "lonely" in detect_surface_attention(["我觉得好孤独"])

    def test_angry(self):
        assert "angry" in detect_surface_attention(["I hate everything, I'm furious"])

    def test_need_pray_arabic(self):
        assert "need_pray" in detect_surface_attention(["وقت صلاة المغرب"])

    def test_multiple_attentions(self):
        atts = detect_surface_attention(["I'm hungry and lonely and scared"])
        assert "hungry" in atts
        assert "lonely" in atts
        assert "scared" in atts

    def test_no_attention_neutral(self):
        atts = detect_surface_attention(["The weather is nice today"])
        assert len(atts) == 0

    def test_scarlett_phase4(self):
        """Scarlett Phase 4: mother dead, starving."""
        texts = [
            "Mother is dead. She died before I could get home.",
            "I'm so hungry. The Yankees took everything.",
            "I swear I'll never be hungry again.",
        ]
        atts = detect_surface_attention(texts)
        assert "grieving" in atts  # "died", "dead"
        assert "hungry" in atts    # "hungry"

    def test_anna_crisis(self):
        """Anna in crisis: suicidal, panicking."""
        texts = [
            "I can't breathe. I don't want to live anymore.",
            "Nobody understands. I'm completely alone.",
        ]
        atts = detect_surface_attention(texts)
        assert "panicking" in atts or "anxious" in atts
        assert "lonely" in atts


class TestMiddleHistory:
    def test_recurring_yoga(self):
        history = {"yoga": 12, "weather": 2, "food": 1}
        atts = detect_middle_history(history)
        assert "need_exercise" in atts

    def test_recurring_coffee(self):
        history = {"coffee": 15}
        atts = detect_middle_history(history)
        assert "hungry" in atts

    def test_low_count_ignored(self):
        history = {"yoga": 1, "art": 2}
        atts = detect_middle_history(history)
        assert len(atts) == 0


class TestRecommendFromSoul:
    @patch("wish_engine.soul_recommender.search_and_enrich")
    def test_hungry_gets_restaurant(self, mock_search):
        mock_search.return_value = [
            {"title": "Corner Cafe", "category": "cafe", "description": "Corner Cafe",
             "noise": "quiet", "social": "low", "mood": "calming", "tags": ["cafe"],
             "_lat": 25.2, "_lng": 55.3, "_opening_hours": "7am-11pm"},
        ]
        recs = recommend_from_soul(
            recent_texts=["I'm so hungry"],
            lat=25.2, lng=55.3,
        )
        assert len(recs) >= 1
        assert recs[0].attention == "hungry"
        assert recs[0].layer == "surface"
        assert "Corner Cafe" in recs[0].why

    @patch("wish_engine.soul_recommender.search_and_enrich")
    def test_anxious_gets_park(self, mock_search):
        mock_search.return_value = [
            {"title": "Green Park", "category": "park", "description": "Green Park",
             "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature"],
             "_lat": 25.2, "_lng": 55.3},
        ]
        recs = recommend_from_soul(
            recent_texts=["I feel so anxious I can't think"],
            lat=25.2, lng=55.3,
        )
        assert len(recs) >= 1
        assert recs[0].attention == "anxious"
        assert "Green Park" in recs[0].why

    @patch("wish_engine.soul_recommender.search_and_enrich")
    def test_middle_layer_yoga(self, mock_search):
        mock_search.return_value = [
            {"title": "Sunrise Gym", "category": "gym", "description": "Sunrise Gym",
             "noise": "loud", "social": "high", "mood": "intense", "tags": ["exercise"],
             "_lat": 25.2, "_lng": 55.3},
        ]
        recs = recommend_from_soul(
            recent_texts=["just thinking about stuff"],
            lat=25.2, lng=55.3,
            topic_history={"yoga": 10},
        )
        # Should get middle layer rec from yoga history
        middle_recs = [r for r in recs if r.layer == "middle"]
        assert len(middle_recs) >= 1

    @patch("wish_engine.soul_recommender.search_and_enrich")
    def test_surface_before_middle(self, mock_search):
        """Surface (current) needs should come before middle (historical)."""
        mock_search.return_value = [
            {"title": "Place A", "category": "cafe", "description": "A",
             "noise": "quiet", "social": "low", "mood": "calming", "tags": ["cafe"],
             "_lat": 25.2, "_lng": 55.3},
        ]
        recs = recommend_from_soul(
            recent_texts=["I'm so hungry"],
            lat=25.2, lng=55.3,
            topic_history={"yoga": 10},
        )
        if len(recs) >= 1:
            assert recs[0].layer == "surface"

    @patch("wish_engine.soul_recommender.search_and_enrich")
    def test_no_osm_returns_empty(self, mock_search):
        mock_search.return_value = []
        recs = recommend_from_soul(["I'm hungry"], 0.0, 0.0)
        assert recs == []

    @patch("wish_engine.soul_recommender.search_and_enrich")
    def test_dedup_places(self, mock_search):
        """Same place shouldn't appear twice even for different attentions."""
        mock_search.return_value = [
            {"title": "Only Place", "category": "cafe", "description": "Only",
             "noise": "quiet", "social": "low", "mood": "calming", "tags": ["cafe"],
             "_lat": 25.2, "_lng": 55.3},
        ]
        recs = recommend_from_soul(
            recent_texts=["I'm hungry and lonely and tired"],
            lat=25.2, lng=55.3,
        )
        names = [r.place_name for r in recs]
        assert len(names) == len(set(names))  # no duplicates
