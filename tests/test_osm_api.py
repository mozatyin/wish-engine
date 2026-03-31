"""Tests for OSM Overpass API -- dynamic place search."""

import json

import pytest
from unittest.mock import patch, MagicMock

from wish_engine.apis.osm_api import (
    nearby_places,
    nearby_events_venues,
    _osm_to_personality,
    search_and_enrich,
    is_open_now,
)


# ── is_open_now ──────────────────────────────────────────────────────────────


class TestIsOpenNow:
    def test_always_open(self):
        assert is_open_now("24/7") is True

    def test_none_returns_none(self):
        assert is_open_now(None) is None

    def test_empty_string_returns_none(self):
        assert is_open_now("") is None

    def test_unparseable_returns_none(self):
        assert is_open_now("by appointment only") is None

    def test_simple_range_open(self):
        from unittest.mock import patch
        from datetime import datetime
        # 14:00 on a Wednesday
        with patch("wish_engine.apis.osm_api.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 3, 14, 0)  # Wednesday
            result = is_open_now("09:00-20:00")
        assert result is True

    def test_simple_range_closed(self):
        from unittest.mock import patch
        from datetime import datetime
        # 22:00 — after closing
        with patch("wish_engine.apis.osm_api.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 3, 22, 0)
            result = is_open_now("09:00-20:00")
        assert result is False

    def test_lunch_break_open_before(self):
        """09:00-13:00,15:00-19:00 — at 11:00 should be open (first range)."""
        from unittest.mock import patch
        from datetime import datetime
        with patch("wish_engine.apis.osm_api.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 3, 11, 0)
            result = is_open_now("09:00-13:00,15:00-19:00")
        assert result is True

    def test_lunch_break_closed_during_break(self):
        """09:00-13:00,15:00-19:00 — at 14:00 (lunch break) should be closed."""
        from unittest.mock import patch
        from datetime import datetime
        with patch("wish_engine.apis.osm_api.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 3, 14, 0)
            result = is_open_now("09:00-13:00,15:00-19:00")
        assert result is False

    def test_lunch_break_open_after(self):
        """09:00-13:00,15:00-19:00 — at 16:00 should be open (second range)."""
        from unittest.mock import patch
        from datetime import datetime
        with patch("wish_engine.apis.osm_api.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 3, 16, 0)
            result = is_open_now("09:00-13:00,15:00-19:00")
        assert result is True

    def test_overnight_span_open(self):
        """22:00-03:00 — at 23:30 should be open."""
        from unittest.mock import patch
        from datetime import datetime
        with patch("wish_engine.apis.osm_api.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 3, 23, 30)
            result = is_open_now("22:00-03:00")
        assert result is True

    def test_overnight_span_open_after_midnight(self):
        """22:00-03:00 — at 01:00 should be open (after midnight)."""
        from unittest.mock import patch
        from datetime import datetime
        with patch("wish_engine.apis.osm_api.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 4, 1, 0)
            result = is_open_now("22:00-03:00")
        assert result is True

    def test_weekday_only_closed_on_weekend(self):
        """Mo-Fr 09:00-18:00 — on Saturday should be closed."""
        from unittest.mock import patch
        from datetime import datetime
        # Saturday = weekday 5
        with patch("wish_engine.apis.osm_api.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 6, 12, 0)  # Saturday
            result = is_open_now("Mo-Fr 09:00-18:00")
        assert result is False

    def test_weekday_only_open_on_weekday(self):
        """Mo-Fr 09:00-18:00 — on Wednesday at noon should be open."""
        from unittest.mock import patch
        from datetime import datetime
        # Wednesday = weekday 2
        with patch("wish_engine.apis.osm_api.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 3, 12, 0)  # Wednesday
            result = is_open_now("Mo-Fr 09:00-18:00")
        assert result is True


# ── _osm_to_personality mapping ──────────────────────────────────────────────


class TestOsmToPersonality:
    def test_cafe(self):
        place = {"name": "Test Cafe", "category": "cafe", "lat": 25.0, "lng": 55.0}
        result = _osm_to_personality(place)
        assert result["title"] == "Test Cafe"
        assert result["noise"] == "moderate"
        assert "coffee" in result["tags"]

    def test_library(self):
        place = {"name": "City Library", "category": "library"}
        result = _osm_to_personality(place)
        assert result["noise"] == "quiet"
        assert "reading" in result["tags"]

    def test_gym(self):
        place = {"name": "Iron Gym", "category": "gym"}
        result = _osm_to_personality(place)
        assert result["noise"] == "loud"
        assert "exercise" in result["tags"]

    def test_unknown_category(self):
        place = {"name": "Mystery", "category": "unknown_thing"}
        result = _osm_to_personality(place)
        assert result["noise"] == "moderate"  # default
        assert result["social"] == "medium"

    def test_mosque(self):
        place = {"name": "Grand Mosque", "category": "place_of_worship"}
        result = _osm_to_personality(place)
        assert result["noise"] == "quiet"
        assert "spiritual" in result["tags"]

    def test_park(self):
        place = {"name": "Central Park", "category": "park"}
        result = _osm_to_personality(place)
        assert result["noise"] == "quiet"
        assert "nature" in result["tags"]
        assert "outdoor" in result["tags"]

    def test_nightclub(self):
        place = {"name": "Club X", "category": "nightclub"}
        result = _osm_to_personality(place)
        assert result["noise"] == "loud"
        assert result["social"] == "high"

    def test_museum(self):
        place = {"name": "Art Museum", "category": "museum"}
        result = _osm_to_personality(place)
        assert result["noise"] == "quiet"
        assert "culture" in result["tags"]

    def test_description_uses_address_when_available(self):
        place = {"name": "Cafe Z", "category": "cafe", "address": "123 Main St"}
        result = _osm_to_personality(place)
        assert "123 Main St" in result["description"]

    def test_description_falls_back_to_category(self):
        place = {"name": "Cafe Z", "category": "cafe"}
        result = _osm_to_personality(place)
        assert "cafe" in result["description"]


# ── nearby_places ────────────────────────────────────────────────────────────


class TestNearbyPlaces:
    def test_returns_empty_on_timeout(self):
        with patch("wish_engine.apis.osm_api.urlopen", side_effect=TimeoutError):
            result = nearby_places(25.0, 55.0)
            assert result == []

    def test_returns_empty_on_url_error(self):
        from urllib.error import URLError
        with patch("wish_engine.apis.osm_api.urlopen", side_effect=URLError("fail")):
            result = nearby_places(25.0, 55.0)
            assert result == []

    def test_returns_empty_on_json_error(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("wish_engine.apis.osm_api.urlopen", return_value=mock_resp):
            result = nearby_places(25.0, 55.0)
            assert result == []

    @patch("wish_engine.apis.osm_api.urlopen")
    def test_parses_response(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "elements": [
                {"type": "node", "lat": 25.1, "lon": 55.2, "tags": {"name": "Test Cafe", "amenity": "cafe"}},
                {"type": "node", "lat": 25.2, "lon": 55.3, "tags": {"name": "Nice Park", "leisure": "park"}},
            ]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = nearby_places(25.0, 55.0)
        assert len(result) == 2
        assert result[0]["name"] == "Test Cafe"
        assert result[0]["category"] == "cafe"
        assert result[1]["name"] == "Nice Park"
        assert result[1]["category"] == "park"

    @patch("wish_engine.apis.osm_api.urlopen")
    def test_skips_elements_without_name(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "elements": [
                {"type": "node", "lat": 25.1, "lon": 55.2, "tags": {"amenity": "cafe"}},
                {"type": "node", "lat": 25.2, "lon": 55.3, "tags": {"name": "Named Place", "amenity": "library"}},
            ]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = nearby_places(25.0, 55.0)
        assert len(result) == 1
        assert result[0]["name"] == "Named Place"

    @patch("wish_engine.apis.osm_api.urlopen")
    def test_custom_place_types(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"elements": []}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        nearby_places(25.0, 55.0, place_types=["theatre"])
        # Verify the query was sent (urlopen was called)
        assert mock_urlopen.called

    @patch("wish_engine.apis.osm_api.urlopen")
    def test_extracts_optional_fields(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "elements": [{
                "type": "node", "lat": 25.1, "lon": 55.2,
                "tags": {
                    "name": "Fancy Cafe",
                    "amenity": "cafe",
                    "addr:street": "123 Main St",
                    "opening_hours": "Mo-Fr 08:00-20:00",
                    "website": "https://fancy.cafe",
                    "phone": "+1234567890",
                },
            }]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = nearby_places(25.0, 55.0)
        assert result[0]["address"] == "123 Main St"
        assert result[0]["opening_hours"] == "Mo-Fr 08:00-20:00"
        assert result[0]["website"] == "https://fancy.cafe"
        assert result[0]["phone"] == "+1234567890"


# ── search_and_enrich ────────────────────────────────────────────────────────


class TestSearchAndEnrich:
    @patch("wish_engine.apis.osm_api.urlopen")
    def test_enriches_results(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "elements": [
                {"type": "node", "lat": 25.1, "lon": 55.2, "tags": {"name": "Quiet Library", "amenity": "library"}},
            ]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = search_and_enrich(25.0, 55.0)
        assert len(result) == 1
        assert result[0]["noise"] == "quiet"
        assert "reading" in result[0]["tags"]
        assert result[0]["title"] == "Quiet Library"

    @patch("wish_engine.apis.osm_api.urlopen")
    def test_empty_on_no_results(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"elements": []}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = search_and_enrich(25.0, 55.0)
        assert result == []


# ── nearby_events_venues ─────────────────────────────────────────────────────


class TestNearbyEventsVenues:
    @patch("wish_engine.apis.osm_api.urlopen")
    def test_returns_venue_places(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "elements": [
                {"type": "node", "lat": 25.1, "lon": 55.2, "tags": {"name": "City Theatre", "amenity": "theatre"}},
            ]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = nearby_events_venues(25.0, 55.0)
        assert len(result) == 1
        assert result[0]["name"] == "City Theatre"
