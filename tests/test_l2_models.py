"""Tests for L2 output models."""

import pytest
from wish_engine.models import (
    L2FulfillmentResult,
    Recommendation,
    MapData,
    ReminderOption,
)


class TestRecommendation:
    def test_create_minimal(self):
        r = Recommendation(
            title="Calm Yoga Studio",
            description="Quiet yoga studio with small classes",
            category="yoga_studio",
            relevance_reason="Matches your introversion preference",
            score=0.85,
        )
        assert r.title == "Calm Yoga Studio"
        assert r.score == 0.85
        assert r.action_url is None
        assert r.tags == []

    def test_create_full(self):
        r = Recommendation(
            title="Mindfulness in Plain English",
            description="Classic meditation guide",
            category="book",
            relevance_reason="Aligns with your values: tradition",
            score=0.92,
            action_url="https://example.com/book/123",
            tags=["meditation", "beginner", "tradition"],
        )
        assert r.action_url == "https://example.com/book/123"
        assert len(r.tags) == 3

    def test_score_bounds(self):
        with pytest.raises(Exception):
            Recommendation(
                title="Bad", description="x", category="x",
                relevance_reason="x", score=1.5,
            )
        with pytest.raises(Exception):
            Recommendation(
                title="Bad", description="x", category="x",
                relevance_reason="x", score=-0.1,
            )


class TestMapData:
    def test_create(self):
        m = MapData(place_type="meditation_center", radius_km=5.0)
        assert m.place_type == "meditation_center"
        assert m.radius_km == 5.0


class TestReminderOption:
    def test_create(self):
        r = ReminderOption(text="Want a reminder this Saturday?", delay_hours=72)
        assert r.delay_hours == 72


class TestL2FulfillmentResult:
    def test_minimal(self):
        rec = Recommendation(
            title="Park", description="Quiet park",
            category="park", relevance_reason="calm", score=0.8,
        )
        result = L2FulfillmentResult(recommendations=[rec])
        assert len(result.recommendations) == 1
        assert result.map_data is None
        assert result.reminder_option is None

    def test_full_with_map_and_reminder(self):
        rec = Recommendation(
            title="Zen Garden", description="Traditional meditation space",
            category="meditation_center", relevance_reason="values: tradition",
            score=0.9, tags=["meditation", "quiet"],
        )
        result = L2FulfillmentResult(
            recommendations=[rec],
            map_data=MapData(place_type="meditation_center", radius_km=3.0),
            reminder_option=ReminderOption(
                text="Want a reminder this Saturday?", delay_hours=48,
            ),
        )
        assert result.map_data.radius_km == 3.0
        assert result.reminder_option.delay_hours == 48

    def test_empty_recommendations_rejected(self):
        with pytest.raises(Exception):
            L2FulfillmentResult(recommendations=[])
