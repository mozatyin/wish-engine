"""Tests for adzuna_api."""
import json
from unittest.mock import MagicMock, patch

import pytest

from wish_engine.apis.adzuna_api import is_available, search_jobs, search_visa_jobs


class TestIsAvailable:
    def test_returns_false_without_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            assert is_available() is False

    def test_returns_false_with_only_app_id(self):
        with patch.dict("os.environ", {"ADZUNA_APP_ID": "abc"}, clear=True):
            assert is_available() is False

    def test_returns_false_with_only_api_key(self):
        with patch.dict("os.environ", {"ADZUNA_API_KEY": "xyz"}, clear=True):
            assert is_available() is False

    def test_returns_true_with_both_keys(self):
        env = {"ADZUNA_APP_ID": "abc", "ADZUNA_API_KEY": "xyz"}
        with patch.dict("os.environ", env):
            assert is_available() is True


class TestSearchJobs:
    def test_returns_empty_without_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            result = search_jobs()
        assert result == []

    def test_returns_empty_on_url_error(self):
        env = {"ADZUNA_APP_ID": "abc", "ADZUNA_API_KEY": "xyz"}
        with patch.dict("os.environ", env):
            with patch("wish_engine.apis.adzuna_api.urlopen", side_effect=URLError("fail")):
                result = search_jobs()
        assert result == []

    @patch("wish_engine.apis.adzuna_api.urlopen")
    def test_parses_response(self, mock_urlopen):
        payload = {
            "results": [{
                "title": "Python Developer",
                "company": {"display_name": "Acme Corp"},
                "location": {"display_name": "London"},
                "redirect_url": "https://adzuna.com/job/123",
                "salary_min": 50000,
                "salary_max": 70000,
                "description": "Build things.",
            }]
        }
        _mock_response(mock_urlopen, payload)
        with patch.dict("os.environ", {"ADZUNA_APP_ID": "a", "ADZUNA_API_KEY": "b"}):
            results = search_jobs(query="python")
        assert len(results) == 1
        job = results[0]
        assert job["title"] == "Python Developer"
        assert job["company"] == "Acme Corp"
        assert job["location"] == "London"
        assert job["url"] == "https://adzuna.com/job/123"
        assert "50,000" in job["salary"]

    @patch("wish_engine.apis.adzuna_api.urlopen")
    def test_required_fields_always_present(self, mock_urlopen):
        payload = {
            "results": [{
                "title": "Data Engineer",
                "company": {"display_name": "TechCo"},
                "location": {"display_name": "Manchester"},
                "redirect_url": "https://adzuna.com/job/456",
                "description": "Work with pipelines.",
            }]
        }
        _mock_response(mock_urlopen, payload)
        with patch.dict("os.environ", {"ADZUNA_APP_ID": "a", "ADZUNA_API_KEY": "b"}):
            results = search_jobs()
        required = {"title", "company", "location", "url", "salary", "description"}
        assert required.issubset(results[0].keys())

    @patch("wish_engine.apis.adzuna_api.urlopen")
    def test_empty_salary_when_missing(self, mock_urlopen):
        payload = {"results": [{"title": "Dev", "company": {}, "location": {}, "redirect_url": "", "description": ""}]}
        _mock_response(mock_urlopen, payload)
        with patch.dict("os.environ", {"ADZUNA_APP_ID": "a", "ADZUNA_API_KEY": "b"}):
            results = search_jobs()
        assert results[0]["salary"] == ""

    @patch("wish_engine.apis.adzuna_api.urlopen")
    def test_max_results_respected(self, mock_urlopen):
        jobs = [{"title": f"Job {i}", "company": {}, "location": {}, "redirect_url": "", "description": ""} for i in range(20)]
        _mock_response(mock_urlopen, {"results": jobs})
        with patch.dict("os.environ", {"ADZUNA_APP_ID": "a", "ADZUNA_API_KEY": "b"}):
            results = search_jobs(max_results=5)
        assert len(results) <= 5


class TestSearchVisaJobs:
    def test_returns_empty_without_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            result = search_visa_jobs()
        assert result == []

    @patch("wish_engine.apis.adzuna_api.urlopen")
    def test_queries_visa_sponsorship(self, mock_urlopen):
        _mock_response(mock_urlopen, {"results": []})
        with patch.dict("os.environ", {"ADZUNA_APP_ID": "a", "ADZUNA_API_KEY": "b"}):
            result = search_visa_jobs(location="London")
        assert isinstance(result, list)
        # Check the URL passed to urlopen contains "visa"
        request_obj = mock_urlopen.call_args[0][0]
        assert "visa" in request_obj.full_url.lower()


# ── helpers ──────────────────────────────────────────────────────────────────

def _mock_response(mock_urlopen: MagicMock, payload: dict) -> None:
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp


from urllib.error import URLError  # noqa: E402 — needed for test_returns_empty_on_url_error
