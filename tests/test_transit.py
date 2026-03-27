"""Tests for Transit API and Transit Filter."""

import os

from wish_engine.apis.transit_api import (
    is_available,
    haversine_km,
    estimate_transit,
    _haversine_estimate,
)
from wish_engine.apis.transit_filter import filter_by_transit


class TestTransitAPIAvailability:
    def test_not_available_without_key(self):
        # Ensure no key is set
        old = os.environ.pop("GOOGLE_DIRECTIONS_API_KEY", None)
        try:
            assert is_available() is False
        finally:
            if old is not None:
                os.environ["GOOGLE_DIRECTIONS_API_KEY"] = old

    def test_available_with_key(self):
        os.environ["GOOGLE_DIRECTIONS_API_KEY"] = "test_key"
        try:
            assert is_available() is True
        finally:
            del os.environ["GOOGLE_DIRECTIONS_API_KEY"]


class TestHaversine:
    def test_same_point_zero_distance(self):
        d = haversine_km(40.0, -74.0, 40.0, -74.0)
        assert d == 0.0

    def test_known_distance_nyc_to_la(self):
        # NYC (40.7128, -74.0060) to LA (34.0522, -118.2437)
        # Actual ~3944 km
        d = haversine_km(40.7128, -74.0060, 34.0522, -118.2437)
        assert 3900 < d < 4000

    def test_short_distance(self):
        # Two points ~1km apart (roughly 0.009 degrees lat)
        d = haversine_km(40.0, -74.0, 40.009, -74.0)
        assert 0.5 < d < 1.5


class TestEstimateTransit:
    def test_fallback_walking(self):
        """Without API key, uses haversine fallback."""
        old = os.environ.pop("GOOGLE_DIRECTIONS_API_KEY", None)
        try:
            result = estimate_transit(40.0, -74.0, 40.01, -74.0, mode="walking")
            assert result["mode"] == "walking"
            assert result["duration_minutes"] >= 1
            assert result["distance_km"] > 0
            assert "walk" in result["summary"]
            assert "estimated" in result["summary"]
        finally:
            if old is not None:
                os.environ["GOOGLE_DIRECTIONS_API_KEY"] = old

    def test_fallback_transit(self):
        old = os.environ.pop("GOOGLE_DIRECTIONS_API_KEY", None)
        try:
            result = estimate_transit(40.0, -74.0, 40.1, -74.0, mode="transit")
            assert result["mode"] == "transit"
            assert result["duration_minutes"] >= 1
            assert result["duration_minutes"] < 1000  # Not absurd
        finally:
            if old is not None:
                os.environ["GOOGLE_DIRECTIONS_API_KEY"] = old

    def test_walking_slower_than_driving(self):
        old = os.environ.pop("GOOGLE_DIRECTIONS_API_KEY", None)
        try:
            walk = estimate_transit(40.0, -74.0, 40.05, -74.0, mode="walking")
            drive = estimate_transit(40.0, -74.0, 40.05, -74.0, mode="driving")
            assert walk["duration_minutes"] >= drive["duration_minutes"]
        finally:
            if old is not None:
                os.environ["GOOGLE_DIRECTIONS_API_KEY"] = old

    def test_duration_not_negative(self):
        result = _haversine_estimate(0.0, 0.0, 0.0, 0.0, "transit")
        assert result["duration_minutes"] >= 1


class TestTransitFilter:
    def test_filters_far_places(self):
        candidates = [
            {"name": "Nearby Cafe", "lat": 40.001, "lng": -74.0},
            {"name": "Far Away Park", "lat": 41.0, "lng": -74.0},  # ~111 km away
        ]
        old = os.environ.pop("GOOGLE_DIRECTIONS_API_KEY", None)
        try:
            result = filter_by_transit(
                candidates, origin=(40.0, -74.0), max_minutes=30, mode="transit"
            )
            names = [c["name"] for c in result]
            assert "Nearby Cafe" in names
            assert "Far Away Park" not in names
        finally:
            if old is not None:
                os.environ["GOOGLE_DIRECTIONS_API_KEY"] = old

    def test_walking_shorter_radius(self):
        candidates = [
            {"name": "Close Place", "lat": 40.001, "lng": -74.0},
            {"name": "Medium Place", "lat": 40.03, "lng": -74.0},  # ~3.3 km
        ]
        old = os.environ.pop("GOOGLE_DIRECTIONS_API_KEY", None)
        try:
            walk_result = filter_by_transit(
                candidates, origin=(40.0, -74.0), max_minutes=15, mode="walking"
            )
            transit_result = filter_by_transit(
                candidates, origin=(40.0, -74.0), max_minutes=15, mode="transit"
            )
            # Walking should accept fewer or equal candidates
            assert len(walk_result) <= len(transit_result)
        finally:
            if old is not None:
                os.environ["GOOGLE_DIRECTIONS_API_KEY"] = old

    def test_transit_annotations_added(self):
        candidates = [{"name": "Cafe", "lat": 40.001, "lng": -74.0}]
        old = os.environ.pop("GOOGLE_DIRECTIONS_API_KEY", None)
        try:
            result = filter_by_transit(candidates, origin=(40.0, -74.0), max_minutes=60)
            assert len(result) == 1
            assert "_transit_time" in result[0]
            assert "_transit_summary" in result[0]
        finally:
            if old is not None:
                os.environ["GOOGLE_DIRECTIONS_API_KEY"] = old

    def test_candidates_without_coords_kept(self):
        candidates = [{"name": "Virtual Event"}]
        result = filter_by_transit(candidates, origin=(40.0, -74.0), max_minutes=30)
        assert len(result) == 1
        assert result[0]["name"] == "Virtual Event"
