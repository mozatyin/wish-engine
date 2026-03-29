import pytest, json
from unittest.mock import patch, MagicMock
from wish_engine.apis.google_books_api import search_books as google_search, is_available as google_avail
from wish_engine.apis.open_library_api import search_books as ol_search, is_available as ol_avail

class TestGoogleBooks:
    def test_always_available(self):
        assert google_avail() == True

    @patch("wish_engine.apis.google_books_api.urlopen")
    def test_parses_response(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"items": [
            {"volumeInfo": {"title": "Attached", "authors": ["Amir Levine"], "description": "Attachment theory", "averageRating": 4.2}}
        ]}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        results = google_search("attachment theory")
        assert len(results) == 1
        assert results[0]["title"] == "Attached"
        assert results[0]["rating"] == 4.2

    def test_timeout_returns_empty(self):
        with patch("wish_engine.apis.google_books_api.urlopen", side_effect=TimeoutError):
            assert google_search("test") == []

class TestOpenLibrary:
    def test_always_available(self):
        assert ol_avail() == True

    @patch("wish_engine.apis.open_library_api.urlopen")
    def test_parses_response(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"docs": [
            {"title": "Mindfulness", "author_name": ["Jon Kabat-Zinn"], "cover_i": 12345, "ratings_average": 4.0, "subject": ["meditation"]}
        ]}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        results = ol_search("mindfulness meditation")
        assert len(results) == 1
        assert results[0]["title"] == "Mindfulness"
        assert "meditation" in results[0]["subjects"]

    def test_timeout_returns_empty(self):
        with patch("wish_engine.apis.open_library_api.urlopen", side_effect=TimeoutError):
            assert ol_search("test") == []
