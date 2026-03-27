"""Tests for Calendar-Aware Filter — time-appropriate recommendations."""

from wish_engine.apis.calendar_filter import (
    is_good_time,
    get_time_context,
    filter_by_time,
)


class TestIsGoodTime:
    def test_no_gym_at_2am(self):
        assert is_good_time(hour=2, day_of_week=1, recommendation_type="gym") is False

    def test_no_lecture_on_sunday_morning(self):
        # Sunday early morning — lecture is unsuitable
        assert is_good_time(hour=6, day_of_week=6, recommendation_type="lecture") is False

    def test_no_nightclub_weekday_morning(self):
        assert is_good_time(hour=10, day_of_week=2, recommendation_type="nightclub") is False

    def test_gym_ok_at_noon(self):
        assert is_good_time(hour=12, day_of_week=1, recommendation_type="gym") is True

    def test_bar_ok_in_evening(self):
        assert is_good_time(hour=20, day_of_week=4, recommendation_type="bar") is True

    def test_unknown_type_always_allowed(self):
        assert is_good_time(hour=3, day_of_week=0, recommendation_type="meditation") is True


class TestGetTimeContext:
    def test_late_night_period(self):
        ctx = get_time_context(hour=2, day_of_week=1)
        assert ctx["period"] == "late_night"
        assert ctx["is_weekend"] is False

    def test_weekend_flag(self):
        ctx = get_time_context(hour=10, day_of_week=5)  # Saturday
        assert ctx["is_weekend"] is True

    def test_activity_window_not_empty(self):
        ctx = get_time_context(hour=14, day_of_week=3)
        assert len(ctx["activity_window"]) > 0
        assert "shopping" in ctx["activity_window"]

    def test_valid_periods(self):
        valid = {"early_morning", "morning", "afternoon", "evening", "late_night"}
        for hour in range(24):
            ctx = get_time_context(hour=hour, day_of_week=0)
            assert ctx["period"] in valid


class TestFilterByTime:
    def test_2am_filters_gyms_and_lectures(self):
        candidates = [
            {"name": "24h Gym", "type": "gym"},
            {"name": "Online Course", "type": "lecture"},
            {"name": "Late Night Bar", "type": "bar"},
        ]
        result = filter_by_time(candidates, hour=2, day_of_week=1)
        names = [c["name"] for c in result]
        assert "24h Gym" not in names
        assert "Online Course" not in names
        assert "Late Night Bar" in names

    def test_afternoon_allows_most(self):
        candidates = [
            {"name": "City Library", "type": "library"},
            {"name": "Central Park", "type": "park"},
            {"name": "Night Club", "type": "nightclub"},
        ]
        result = filter_by_time(candidates, hour=14, day_of_week=3)
        names = [c["name"] for c in result]
        assert "City Library" in names
        assert "Central Park" in names
        assert "Night Club" not in names

    def test_late_night_allows_bars_not_libraries(self):
        candidates = [
            {"name": "Rooftop Bar", "type": "bar"},
            {"name": "Public Library", "type": "library"},
        ]
        result = filter_by_time(candidates, hour=23, day_of_week=4)
        names = [c["name"] for c in result]
        assert "Rooftop Bar" in names
        assert "Public Library" not in names

    def test_filter_by_tags(self):
        candidates = [
            {"name": "Hiking Trail", "tags": ["outdoor", "hiking"]},
            {"name": "Jazz Bar", "tags": ["bar", "social"]},
        ]
        result = filter_by_time(candidates, hour=1, day_of_week=2)
        names = [c["name"] for c in result]
        assert "Hiking Trail" not in names
        # bar at 1am (late_night) — bars have no late_night restriction
        assert "Jazz Bar" in names
