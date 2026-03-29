import json
from unittest.mock import MagicMock, patch

import pytest

from wish_engine.apis.events_free import discover_events_free
from wish_engine.apis.events_free import is_available as ef_avail
from wish_engine.apis.nominatim_api import geocode, reverse_geocode
from wish_engine.apis.nominatim_api import is_available as nom_avail


class TestNominatim:
    def test_always_available(self):
        assert nom_avail() is True

    @patch("wish_engine.apis.nominatim_api.urlopen")
    def test_geocode(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([
            {"lat": "25.2048", "lon": "55.2708", "display_name": "Dubai, UAE"},
        ]).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp

        result = geocode("Dubai")
        assert result is not None
        assert abs(result["lat"] - 25.2048) < 0.01

    @patch("wish_engine.apis.nominatim_api.urlopen")
    def test_reverse_geocode(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "display_name": "Dubai, UAE",
            "address": {"city": "Dubai", "country": "UAE", "country_code": "ae"},
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp

        result = reverse_geocode(25.2048, 55.2708)
        assert result is not None
        assert result["city"] == "Dubai"

    def test_timeout_returns_none(self):
        with patch("wish_engine.apis.nominatim_api.urlopen", side_effect=TimeoutError):
            assert geocode("test") is None
            assert reverse_geocode(0, 0) is None


class TestEventsFree:
    def test_always_available(self):
        assert ef_avail() is True

    @patch("wish_engine.apis.events_free.nearby_places")
    def test_discovers_venues(self, mock):
        mock.return_value = [
            {"name": "City Theatre", "category": "theatre", "lat": 25.1, "lng": 55.2},
            {"name": "Art Gallery", "category": "arts_centre", "lat": 25.1, "lng": 55.3},
        ]
        events = discover_events_free(25.0, 55.0, day_of_week=5)  # Saturday
        assert len(events) == 2
        assert events[0]["venue_name"] == "City Theatre"
        assert "Saturday" in events[0]["event_hint"] or "show" in events[0]["event_hint"]

    @patch("wish_engine.apis.events_free.nearby_places")
    def test_empty_when_no_venues(self, mock):
        mock.return_value = []
        assert discover_events_free(0, 0) == []
