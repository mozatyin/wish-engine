"""Tests for Soul Recommender — TriSoul layers drive real place recommendations."""

import pytest
from unittest.mock import patch
from wish_engine.soul_recommender import (
    detect_surface_attention,
    detect_middle_history,
    update_topic_history,
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


# ── P1A: Expanded emotional vocabulary ───────────────────────────────────────

class TestExpandedEmotionalVocabulary:
    """Real-data gaps: indirect/softer expressions of emotional states."""

    def test_numb_maps_to_sad(self):
        assert "sad" in detect_surface_attention(["I feel completely numb inside"])

    def test_hopeless_maps_to_sad(self):
        assert "sad" in detect_surface_attention(["Everything feels hopeless right now"])

    def test_feel_low_maps_to_sad(self):
        assert "sad" in detect_surface_attention(["I've been feeling low all week"])

    def test_drained_maps_to_tired(self):
        assert "tired" in detect_surface_attention(["I feel so drained I can barely function"])

    def test_burnt_out_maps_to_tired(self):
        assert "tired" in detect_surface_attention(["I'm completely burnt out from work"])

    def test_isolated_maps_to_lonely(self):
        assert "lonely" in detect_surface_attention(["I feel so isolated, like nobody is there"])

    def test_disconnected_maps_to_lonely(self):
        assert "lonely" in detect_surface_attention(["I've been feeling disconnected from everyone"])

    def test_cant_cope_maps_to_overwhelmed(self):
        assert "overwhelmed" in detect_surface_attention(["I just can't cope with all of this"])

    def test_not_good_enough_maps_to_confidence(self):
        assert "confidence" in detect_surface_attention(["I never feel not good enough"])

    def test_useless_maps_to_confidence(self):
        assert "confidence" in detect_surface_attention(["I feel so useless, completely worthless"])

    def test_confused_about_maps_to_need_talk(self):
        assert "need_talk" in detect_surface_attention(["I'm so confused about my situation"])

    def test_dont_know_what_to_do_maps_to_need_talk(self):
        assert "need_talk" in detect_surface_attention(["I just don't know what to do anymore"])

    def test_restless_maps_to_anxious(self):
        assert "anxious" in detect_surface_attention(["I've been so restless, can't settle"])

    def test_on_edge_maps_to_anxious(self):
        assert "anxious" in detect_surface_attention(["I've been on edge all day"])


# ── P2: update_topic_history ──────────────────────────────────────────────────

class TestUpdateTopicHistory:
    """Middle layer accumulator — App uses this to build topic_history per session."""

    def test_starts_empty(self):
        h = update_topic_history("Hello how are you", None)
        assert isinstance(h, dict)

    def test_detects_yoga(self):
        h = update_topic_history("I did yoga this morning", {})
        assert h.get("yoga", 0) >= 1

    def test_detects_cooking(self):
        h = update_topic_history("I love cooking new recipes", {})
        assert h.get("cooking", 0) >= 1

    def test_accumulates_across_turns(self):
        h = {}
        for _ in range(4):
            h = update_topic_history("I went running today", h)
        assert h.get("running", 0) >= 4

    def test_decay_reduces_old_counts(self):
        h = {"yoga": 100}
        h = update_topic_history("nothing relevant", h, decay=0.5)
        assert h.get("yoga", 0) < 60  # 100 * 0.5 = 50

    def test_decay_below_threshold_drops_topic(self):
        h = {"yoga": 1}
        # With decay=0.5, 1 * 0.5 = 0.5, rounds to 0 → drops out
        h = update_topic_history("nothing", h, decay=0.5)
        assert "yoga" not in h

    def test_multiple_topics_one_message(self):
        h = update_topic_history("I went running and then did some cooking", {})
        assert h.get("running", 0) >= 1
        assert h.get("cooking", 0) >= 1

    def test_feeds_detect_middle_history(self):
        """After enough turns, update_topic_history output drives detect_middle_history."""
        h = {}
        for _ in range(5):
            h = update_topic_history("I love hiking in nature", h)
        attentions = detect_middle_history(h)
        assert "want_outdoor" in attentions

    def test_feeds_detect_middle_yoga(self):
        h = {}
        for _ in range(5):
            h = update_topic_history("yoga class was great today", h)
        attentions = detect_middle_history(h)
        assert "need_exercise" in attentions

    def test_one_match_per_topic_per_message(self):
        """'yoga yoga yoga' should only add 1, not 3."""
        h = update_topic_history("yoga yoga yoga", {})
        assert h.get("yoga", 0) == 1

    def test_preserves_unrelated_history(self):
        h = {"books": 10, "music": 7}
        h = update_topic_history("I went running today", h)
        assert h.get("books", 0) >= 9   # decayed but present
        assert h.get("music", 0) >= 6
        assert h.get("running", 0) >= 1
