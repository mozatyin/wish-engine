import pytest, json
from unittest.mock import patch, MagicMock
from wish_engine.apis.air_quality_api import get_air_quality, air_quality_advice, is_available as aqi_avail
from wish_engine.apis.foursquare_api import search_places, is_available as fsq_avail
from wish_engine.apis.podcast_api import search_podcasts, is_available as pod_avail

class TestAirQuality:
    def test_not_available_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert not aqi_avail()
    def test_advice_good(self):
        assert "good" in air_quality_advice(30).lower()
    def test_advice_hazardous(self):
        assert "indoors" in air_quality_advice(350).lower()
    def test_returns_none_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert get_air_quality(25.0, 55.0) is None

class TestFoursquare:
    def test_not_available_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert not fsq_avail()
    def test_returns_empty_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert search_places(25.0, 55.0) == []
    @patch("wish_engine.apis.foursquare_api.urlopen")
    def test_parses_response(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"results": [
            {"name": "Dubai Cafe", "location": {"latitude": 25.1, "longitude": 55.2, "formatted_address": "JBR"}, "distance": 500, "categories": [{"name": "Café", "id": 13000}]}
        ]}).encode()
        mock_resp.__enter__ = lambda s: s; mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        with patch.dict("os.environ", {"FOURSQUARE_API_KEY": "test"}):
            results = search_places(25.0, 55.0, query="cafe")
        assert len(results) == 1
        assert results[0]["name"] == "Dubai Cafe"

class TestPodcast:
    def test_not_available_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert not pod_avail()
    def test_returns_empty_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert search_podcasts("meditation") == []
