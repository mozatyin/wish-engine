"""Tests for Proactive Engine — Soul + Location + Time → real recommendations."""

import pytest
from unittest.mock import patch, MagicMock
from wish_engine.models import DetectorResults
from wish_engine.proactive_engine import (
    generate_daily_stars,
    _check_emotional_need,
    _check_time_based,
    _check_compass,
    _check_values_interests,
    DailyStar,
    ProactiveRecommendation,
)


class TestEmotionalTriggers:
    def test_high_anxiety_triggers(self):
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.7}})
        needs = _check_emotional_need(det)
        assert len(needs) >= 1
        assert any("anxiety" in n["trigger"].lower() or "mind" in n["trigger"].lower() for n in needs)

    def test_sadness_triggers(self):
        det = DetectorResults(emotion={"emotions": {"sadness": 0.6}})
        needs = _check_emotional_need(det)
        assert any("sadness" in n["trigger"].lower() or "scenery" in n["trigger"].lower() for n in needs)

    def test_loneliness_triggers(self):
        det = DetectorResults(emotion={"emotions": {"loneliness": 0.5}})
        needs = _check_emotional_need(det)
        assert any("alone" in n["trigger"].lower() for n in needs)

    def test_anger_triggers_physical(self):
        det = DetectorResults(emotion={"emotions": {"anger": 0.6}})
        needs = _check_emotional_need(det)
        assert any("gym" in n["osm_types"] or "fitness_centre" in n["osm_types"] for n in needs)

    def test_high_distress_urgent(self):
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.9}, "distress": 0.8})
        needs = _check_emotional_need(det)
        urgent = [n for n in needs if n["urgency"] == "urgent"]
        assert len(urgent) >= 1

    def test_low_emotion_no_trigger(self):
        det = DetectorResults(emotion={"emotions": {"joy": 0.3}})
        needs = _check_emotional_need(det)
        assert len(needs) == 0


class TestTimeTriggers:
    def test_morning(self):
        needs = _check_time_based(7, 1)
        assert any("morning" in n["trigger"].lower() for n in needs)

    def test_lunch(self):
        needs = _check_time_based(12, 2)
        assert any("lunch" in n["trigger"].lower() for n in needs)

    def test_evening(self):
        needs = _check_time_based(18, 3)
        assert any("evening" in n["trigger"].lower() or "decompress" in n["trigger"].lower() for n in needs)

    def test_weekend(self):
        needs = _check_time_based(10, 5)  # Saturday
        assert any("weekend" in n["trigger"].lower() for n in needs)


class TestCompassTriggers:
    def test_bud_shell_triggers(self):
        shells = [{"topic": "Rhett", "stage": "bud", "confidence": 0.6}]
        needs = _check_compass(shells)
        assert len(needs) >= 1
        assert "Rhett" in needs[0]["trigger"]

    def test_seed_shell_no_trigger(self):
        shells = [{"topic": "X", "stage": "seed", "confidence": 0.2}]
        needs = _check_compass(shells)
        assert len(needs) == 0


class TestValuesTriggers:
    def test_tradition_suggests_worship(self):
        det = DetectorResults(values={"top_values": ["tradition"]})
        needs = _check_values_interests(det)
        assert any("place_of_worship" in n["osm_types"] for n in needs)

    def test_aesthetics_suggests_art(self):
        det = DetectorResults(values={"top_values": ["aesthetics"]})
        needs = _check_values_interests(det)
        assert any("arts_centre" in n["osm_types"] or "gallery" in n["osm_types"] for n in needs)


class TestGenerateDailyStars:
    @patch("wish_engine.proactive_engine.search_and_enrich")
    def test_returns_daily_star(self, mock_search):
        mock_search.return_value = [
            {"title": "Quiet Park", "description": "A peaceful park", "category": "park",
             "noise": "quiet", "social": "low", "mood": "calming",
             "tags": ["nature", "quiet", "calming"], "_lat": 25.2, "_lng": 55.3},
        ]
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.7}})
        result = generate_daily_stars(det, 25.2, 55.3, hour=18, day_of_week=4)
        assert isinstance(result, DailyStar)
        assert len(result.stars) >= 1
        assert result.stars[0].recommendation.title == "Quiet Park"

    @patch("wish_engine.proactive_engine.search_and_enrich")
    def test_urgency_ordering(self, mock_search):
        mock_search.return_value = [
            {"title": "Safe Garden", "description": "Peaceful", "category": "garden",
             "noise": "quiet", "social": "low", "mood": "calming",
             "tags": ["quiet", "calming", "safe"], "_lat": 25.2, "_lng": 55.3},
        ]
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.9}, "distress": 0.85})
        result = generate_daily_stars(det, 25.2, 55.3, hour=15)
        if result.stars:
            assert result.stars[0].urgency == "urgent"

    @patch("wish_engine.proactive_engine.search_and_enrich")
    def test_dedup_history(self, mock_search):
        mock_search.return_value = [
            {"title": "Already Visited", "description": "x", "category": "cafe",
             "noise": "quiet", "social": "low", "mood": "calming", "tags": ["calming"]},
        ]
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.7}})
        result = generate_daily_stars(det, 25.2, 55.3, history={"Already Visited"})
        titles = [s.recommendation.title for s in result.stars]
        assert "Already Visited" not in titles

    @patch("wish_engine.proactive_engine.search_and_enrich")
    def test_compass_whisper(self, mock_search):
        mock_search.return_value = []
        det = DetectorResults()
        shells = [{"topic": "Hidden Love", "stage": "bud", "confidence": 0.6}]
        result = generate_daily_stars(det, 25.0, 55.0, compass_shells=shells)
        assert "Hidden Love" in result.compass_whisper

    def test_no_osm_returns_quiet(self):
        """When OSM returns nothing, should not crash."""
        with patch("wish_engine.proactive_engine.search_and_enrich", return_value=[]):
            det = DetectorResults(emotion={"emotions": {"anxiety": 0.7}})
            result = generate_daily_stars(det, 0.0, 0.0)
            assert isinstance(result, DailyStar)
            assert "quiet" in result.summary.lower() or len(result.stars) == 0
