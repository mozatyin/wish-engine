"""Tests for free_transit_api (OSM Overpass + OSRM)."""
import json
from unittest.mock import MagicMock, patch

import pytest

from wish_engine.apis.free_transit_api import (
    find_nearest_stops,
    route_summary,
    _haversine_km,
)


def _mock_response(mock_urlopen: MagicMock, payload: dict) -> None:
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp


class TestHaversine:
    def test_same_point_is_zero(self):
        assert _haversine_km(51.5, -0.1, 51.5, -0.1) == pytest.approx(0.0)

    def test_known_distance_london_paris(self):
        # London → Paris ≈ 341 km
        d = _haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
        assert 330 < d < 360

    def test_symmetric(self):
        a = _haversine_km(51.0, 0.0, 52.0, 1.0)
        b = _haversine_km(52.0, 1.0, 51.0, 0.0)
        assert a == pytest.approx(b, rel=1e-6)


class TestFindNearestStops:
    def test_returns_empty_on_network_error(self):
        with patch("wish_engine.apis.free_transit_api.urlopen", side_effect=Exception("fail")):
            result = find_nearest_stops(51.5, -0.1)
        assert result == []

    def test_returns_empty_on_missing_elements_key(self):
        with patch("wish_engine.apis.free_transit_api.urlopen") as mock_u:
            _mock_response(mock_u, {})
            result = find_nearest_stops(51.5, -0.1)
        assert result == []

    @patch("wish_engine.apis.free_transit_api.urlopen")
    def test_parses_bus_stop(self, mock_urlopen):
        payload = {"elements": [{
            "type": "node",
            "id": 1,
            "lat": 51.501,
            "lon": -0.130,
            "tags": {"highway": "bus_stop", "name": "Victoria"},
        }]}
        _mock_response(mock_urlopen, payload)
        results = find_nearest_stops(51.5, -0.1)
        assert len(results) == 1
        stop = results[0]
        assert stop["name"] == "Victoria"
        assert stop["type"] == "bus_stop"
        assert stop["distance_m"] > 0
        assert "lat" in stop and "lng" in stop

    @patch("wish_engine.apis.free_transit_api.urlopen")
    def test_sorted_by_distance(self, mock_urlopen):
        payload = {"elements": [
            {"type": "node", "id": 1, "lat": 51.600, "lon": -0.100,
             "tags": {"highway": "bus_stop", "name": "Far Stop"}},
            {"type": "node", "id": 2, "lat": 51.501, "lon": -0.101,
             "tags": {"highway": "bus_stop", "name": "Near Stop"}},
        ]}
        _mock_response(mock_urlopen, payload)
        results = find_nearest_stops(51.5, -0.1)
        assert results[0]["name"] == "Near Stop"

    @patch("wish_engine.apis.free_transit_api.urlopen")
    def test_max_results_respected(self, mock_urlopen):
        payload = {"elements": [
            {"type": "node", "id": i, "lat": 51.5 + i * 0.001, "lon": -0.1,
             "tags": {"highway": "bus_stop", "name": f"Stop {i}"}}
            for i in range(10)
        ]}
        _mock_response(mock_urlopen, payload)
        results = find_nearest_stops(51.5, -0.1, max_results=3)
        assert len(results) <= 3

    @patch("wish_engine.apis.free_transit_api.urlopen")
    def test_skips_non_node_elements(self, mock_urlopen):
        payload = {"elements": [
            {"type": "way", "id": 1, "tags": {"name": "Should be skipped"}},
            {"type": "node", "id": 2, "lat": 51.501, "lon": -0.101,
             "tags": {"highway": "bus_stop", "name": "Real Stop"}},
        ]}
        _mock_response(mock_urlopen, payload)
        results = find_nearest_stops(51.5, -0.1)
        assert len(results) == 1
        assert results[0]["name"] == "Real Stop"

    @patch("wish_engine.apis.free_transit_api.urlopen")
    def test_stop_without_name_uses_fallback(self, mock_urlopen):
        payload = {"elements": [{
            "type": "node", "id": 1, "lat": 51.501, "lon": -0.101,
            "tags": {"highway": "bus_stop"},   # no name tag
        }]}
        _mock_response(mock_urlopen, payload)
        results = find_nearest_stops(51.5, -0.1)
        assert len(results) == 1
        assert results[0]["name"]  # non-empty fallback


class TestRouteSummary:
    @patch("wish_engine.apis.free_transit_api.urlopen")
    def test_uses_osrm_when_available(self, mock_urlopen):
        payload = {
            "code": "Ok",
            "routes": [{"distance": 8300, "duration": 6000}],
        }
        _mock_response(mock_urlopen, payload)
        result = route_summary(51.5074, -0.1278, 51.515, -0.085)
        assert result["source"] == "osrm"
        assert result["distance_km"] == pytest.approx(8.3, rel=1e-3)
        assert result["duration_min"] == pytest.approx(100, rel=1e-3)
        assert result["mode"] == "foot-walking"

    def test_falls_back_to_haversine_on_error(self):
        with patch("wish_engine.apis.free_transit_api.urlopen", side_effect=Exception("fail")):
            result = route_summary(51.5074, -0.1278, 51.515, -0.085, mode="foot-walking")
        assert result["source"] == "haversine"
        assert result["distance_km"] > 0
        assert result["duration_min"] > 0

    def test_haversine_walking_speed_reasonable(self):
        with patch("wish_engine.apis.free_transit_api.urlopen", side_effect=Exception("fail")):
            result = route_summary(51.0, 0.0, 51.0, 0.1, mode="foot-walking")
        # ~7.7 km at 5 km/h → ~92 min; allow generous range
        assert 50 < result["duration_min"] < 200

    @patch("wish_engine.apis.free_transit_api.urlopen")
    def test_mode_cycling_uses_bike_profile(self, mock_urlopen):
        _mock_response(mock_urlopen, {"code": "Ok", "routes": [{"distance": 5000, "duration": 1200}]})
        result = route_summary(51.5, -0.1, 51.51, -0.09, mode="cycling")
        assert result["mode"] == "cycling"
        # Verify URL contained "bike"
        url_called = mock_urlopen.call_args[0][0].full_url
        assert "bike" in url_called

    @patch("wish_engine.apis.free_transit_api.urlopen")
    def test_result_has_required_keys(self, mock_urlopen):
        _mock_response(mock_urlopen, {"code": "Ok", "routes": [{"distance": 1000, "duration": 600}]})
        result = route_summary(51.5, -0.1, 51.51, -0.09)
        for key in ("distance_km", "duration_min", "mode", "source"):
            assert key in result
