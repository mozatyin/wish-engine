"""Tests for live API modules: jobs_api, teleport_api, translation_api.

All tests use mocks — no real network calls.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from wish_engine.apis.jobs_api import remoteok_jobs, arbeitnow_jobs, search_jobs
from wish_engine.apis.teleport_api import get_urban_area, get_city_salaries
from wish_engine.apis.translation_api import translate_text, get_translation_resources


# ── Helpers ──────────────────────────────────────────────────────────────────

def _mock_urlopen(data):
    """Return a context-manager mock that yields the given JSON data."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ── RemoteOK Jobs ─────────────────────────────────────────────────────────────

class TestRemoteokJobs:
    def test_returns_empty_on_network_error(self):
        with patch("wish_engine.apis.jobs_api.urlopen", side_effect=TimeoutError):
            assert remoteok_jobs() == []

    def test_parses_jobs(self):
        fake_data = [
            {"legal": "disclaimer"},  # first element is always skipped
            {"position": "Python Developer", "company": "Acme", "tags": ["python", "remote"],
             "url": "https://remoteok.com/jobs/1", "salary": "$100k"},
            {"position": "Data Scientist", "company": "Beta", "tags": ["data", "ml"],
             "url": "https://remoteok.com/jobs/2", "salary": ""},
        ]
        with patch("wish_engine.apis.jobs_api.urlopen", return_value=_mock_urlopen(fake_data)):
            result = remoteok_jobs(max_results=5)
        assert len(result) == 2
        assert result[0]["title"] == "Python Developer"
        assert result[0]["company"] == "Acme"
        assert result[0]["location"] == "Remote"

    def test_keyword_filter(self):
        fake_data = [
            {"legal": "disclaimer"},
            {"position": "Python Developer", "company": "Acme", "tags": ["python"]},
            {"position": "Java Developer", "company": "Beta", "tags": ["java"]},
        ]
        with patch("wish_engine.apis.jobs_api.urlopen", return_value=_mock_urlopen(fake_data)):
            result = remoteok_jobs(keywords=["python"], max_results=5)
        assert len(result) == 1
        assert "Python" in result[0]["title"]

    def test_keyword_no_match_returns_all(self):
        """If no keyword matches, return all jobs as fallback."""
        fake_data = [
            {"legal": "disclaimer"},
            {"position": "Python Developer", "company": "Acme", "tags": ["python"]},
        ]
        with patch("wish_engine.apis.jobs_api.urlopen", return_value=_mock_urlopen(fake_data)):
            result = remoteok_jobs(keywords=["rust"], max_results=5)
        # Falls back to all jobs
        assert len(result) == 1

    def test_respects_max_results(self):
        fake_data = [{"legal": "x"}] + [
            {"position": f"Job {i}", "company": "Co", "tags": []} for i in range(10)
        ]
        with patch("wish_engine.apis.jobs_api.urlopen", return_value=_mock_urlopen(fake_data)):
            result = remoteok_jobs(max_results=3)
        assert len(result) == 3

    def test_skips_non_job_entries(self):
        fake_data = [
            {"legal": "disclaimer"},  # no "position" key
            {},                        # empty
            {"position": "Real Job", "company": "Co", "tags": []},
        ]
        with patch("wish_engine.apis.jobs_api.urlopen", return_value=_mock_urlopen(fake_data)):
            result = remoteok_jobs()
        assert len(result) == 1


# ── Arbeitnow Jobs ────────────────────────────────────────────────────────────

class TestArbeitnowJobs:
    def test_returns_empty_on_error(self):
        with patch("wish_engine.apis.jobs_api.urlopen", side_effect=TimeoutError):
            assert arbeitnow_jobs() == []

    def test_parses_jobs(self):
        fake_data = {
            "data": [
                {"title": "Backend Engineer", "company_name": "StartupXYZ",
                 "location": "Berlin, Germany", "url": "https://arbeitnow.com/jobs/1",
                 "tags": ["python"], "remote": False, "visa_sponsorship": True},
            ]
        }
        with patch("wish_engine.apis.jobs_api.urlopen", return_value=_mock_urlopen(fake_data)):
            result = arbeitnow_jobs(max_results=5)
        assert len(result) == 1
        assert result[0]["title"] == "Backend Engineer"
        assert result[0]["visa"] is True
        assert result[0]["location"] == "Berlin, Germany"

    def test_empty_data_returns_empty_list(self):
        fake_data = {"data": []}
        with patch("wish_engine.apis.jobs_api.urlopen", return_value=_mock_urlopen(fake_data)):
            result = arbeitnow_jobs()
        assert result == []

    def test_visa_sponsorship_flag_included_in_url(self):
        """When visa_sponsorship=True, urlopen should be called with visa param in URL."""
        fake_data = {"data": []}
        mock_resp = _mock_urlopen(fake_data)
        with patch("wish_engine.apis.jobs_api.urlopen", return_value=mock_resp) as mock_open:
            arbeitnow_jobs(visa_sponsorship=True)
        called_url = mock_open.call_args[0][0].get_full_url()
        assert "visa_sponsorship=true" in called_url


# ── Search Jobs (combined) ────────────────────────────────────────────────────

class TestSearchJobs:
    def test_returns_empty_when_both_fail(self):
        with patch("wish_engine.apis.jobs_api.urlopen", side_effect=TimeoutError):
            assert search_jobs() == {}

    def test_deduplicates_results(self):
        """Same job from both APIs should appear only once."""
        fake_remoteok = [
            {"legal": "x"},
            {"position": "Python Dev", "company": "Acme", "tags": [], "url": "", "salary": ""},
        ]
        fake_arbeitnow = {
            "data": [
                {"title": "Python Dev", "company_name": "Acme", "location": "",
                 "url": "", "tags": [], "remote": True, "visa_sponsorship": False},
            ]
        }

        call_count = {"n": 0}
        def alternating_mock(*args, **kwargs):
            resp = fake_remoteok if call_count["n"] == 0 else fake_arbeitnow
            call_count["n"] += 1
            return _mock_urlopen(resp)

        with patch("wish_engine.apis.jobs_api.urlopen", side_effect=alternating_mock):
            result = search_jobs()
        # Should have a result (not empty)
        assert result != {}
        assert result.get("title") == "Python Dev"

    def test_returns_best_result_dict(self):
        fake_data = [
            {"legal": "x"},
            {"position": "ML Engineer", "company": "DataCo", "tags": ["ml"],
             "url": "https://example.com", "salary": "$120k"},
        ]
        with patch("wish_engine.apis.jobs_api.remoteok_jobs",
                   return_value=[{"title": "ML Engineer", "company": "DataCo",
                                  "location": "Remote", "url": "https://example.com", "tags": ["ml"]}]):
            with patch("wish_engine.apis.jobs_api.arbeitnow_jobs", return_value=[]):
                result = search_jobs()
        assert result["title"] == "ML Engineer"
        assert "result" in result


# ── Teleport API ──────────────────────────────────────────────────────────────

class TestTeleportAPI:
    def test_returns_empty_on_network_error(self):
        with patch("wish_engine.apis.teleport_api.urlopen", side_effect=TimeoutError):
            assert get_urban_area("London") == {}

    def test_returns_empty_when_no_results(self):
        fake_search = {"_embedded": {"city:search-results": []}}
        with patch("wish_engine.apis.teleport_api.urlopen", return_value=_mock_urlopen(fake_search)):
            assert get_urban_area("Nonexistent City XYZ") == {}

    def test_handles_city_without_urban_area(self):
        """City found but no urban area link — returns partial result."""
        fake_search = {
            "_embedded": {
                "city:search-results": [
                    {"matching_full_name": "Small Town, US",
                     "_embedded": {"city:item": {"_links": {}}}}
                ]
            }
        }
        with patch("wish_engine.apis.teleport_api.urlopen", return_value=_mock_urlopen(fake_search)):
            result = get_urban_area("Small Town")
        assert result.get("name") == "Small Town, US"
        assert result.get("scores") == {}

    def test_parses_scores(self):
        fake_search = {
            "_embedded": {
                "city:search-results": [
                    {
                        "_embedded": {
                            "city:item": {
                                "_links": {
                                    "city:urban_area": {
                                        "href": "https://api.teleport.org/api/urban_areas/slug:london/"
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        fake_scores = {
            "summary": "<p>London is a great city.</p>",
            "categories": [
                {"name": "Housing", "score_out_of_10": 4.2},
                {"name": "Safety", "score_out_of_10": 7.8},
                {"name": "Startups", "score_out_of_10": 9.1},
            ],
            "_links": {"ua:cities": {"name": "London"}},
        }

        call_count = {"n": 0}
        def two_calls(*args, **kwargs):
            resp = fake_search if call_count["n"] == 0 else fake_scores
            call_count["n"] += 1
            return _mock_urlopen(resp)

        with patch("wish_engine.apis.teleport_api.urlopen", side_effect=two_calls):
            result = get_urban_area("London")

        assert result["name"] == "London"
        assert result["scores"]["Safety"] == 7.8
        assert "Startups" in result["highlights"]
        assert "result" in result

    def test_returns_empty_on_second_call_failure(self):
        """First call succeeds, second (scores) call fails."""
        fake_search = {
            "_embedded": {
                "city:search-results": [
                    {
                        "_embedded": {
                            "city:item": {
                                "_links": {
                                    "city:urban_area": {
                                        "href": "https://api.teleport.org/api/urban_areas/slug:london/"
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }

        call_count = {"n": 0}
        def first_ok_then_fail(*args, **kwargs):
            if call_count["n"] == 0:
                call_count["n"] += 1
                return _mock_urlopen(fake_search)
            raise TimeoutError("scores API failed")

        with patch("wish_engine.apis.teleport_api.urlopen", side_effect=first_ok_then_fail):
            result = get_urban_area("London")
        assert result == {}


# ── Translation API ───────────────────────────────────────────────────────────

class TestTranslationAPI:
    def test_returns_empty_on_network_error(self):
        with patch("wish_engine.apis.translation_api.urlopen", side_effect=TimeoutError):
            assert translate_text("hello") == {}

    def test_returns_empty_for_empty_text(self):
        assert translate_text("") == {}
        assert translate_text("   ") == {}

    def test_parses_translation(self):
        fake_data = {
            "responseStatus": 200,
            "responseData": {
                "translatedText": "你好",
                "detectedLanguage": "en",
            }
        }
        with patch("wish_engine.apis.translation_api.urlopen", return_value=_mock_urlopen(fake_data)):
            result = translate_text("hello", source_lang="en", target_lang="zh")

        assert result["translated"] == "你好"
        assert result["source_lang"] == "en"
        assert result["target_lang"] == "zh"
        assert result["result"] == "你好"

    def test_returns_empty_on_non_200_status(self):
        fake_data = {"responseStatus": 429, "responseData": {}}
        with patch("wish_engine.apis.translation_api.urlopen", return_value=_mock_urlopen(fake_data)):
            assert translate_text("hello") == {}

    def test_truncates_long_text(self):
        """Very long text is truncated to 500 chars before sending."""
        long_text = "a" * 1000
        fake_data = {
            "responseStatus": 200,
            "responseData": {"translatedText": "截断文本", "detectedLanguage": "en"},
        }
        captured = {}

        def capture_url(*args, **kwargs):
            captured["url"] = args[0].get_full_url() if hasattr(args[0], "get_full_url") else str(args[0])
            return _mock_urlopen(fake_data)

        with patch("wish_engine.apis.translation_api.urlopen", side_effect=capture_url):
            translate_text(long_text)

        # URL should not have >500 'a' chars encoded
        assert "a" * 600 not in captured.get("url", "")

    def test_get_translation_resources_english(self):
        result = get_translation_resources("en")
        assert "Duolingo" in result["app"]
        assert result["language"] == "English"
        assert "result" in result

    def test_get_translation_resources_arabic(self):
        result = get_translation_resources("ar")
        assert result["language"] == "Arabic"
        assert "result" in result

    def test_get_translation_resources_unknown_lang(self):
        result = get_translation_resources("xx")
        # Falls back to Google Translate
        assert "Google" in result["app"]
        assert "result" in result


# ── Integration: bridge wires new APIs ───────────────────────────────────────

class TestBridgeIntegration:
    def test_job_seeking_includes_jobs_api(self):
        from wish_engine.soul_api_bridge import SOUL_API_MAP
        actions = SOUL_API_MAP.get("job_seeking", [])
        api_modules = [a["api"] for a in actions]
        assert "wish_engine.apis.jobs_api" in api_modules

    def test_career_change_includes_jobs_and_teleport(self):
        from wish_engine.soul_api_bridge import SOUL_API_MAP
        actions = SOUL_API_MAP.get("career_change", [])
        api_modules = [a["api"] for a in actions]
        assert "wish_engine.apis.jobs_api" in api_modules
        assert "wish_engine.apis.teleport_api" in api_modules

    def test_need_translation_includes_translation_api(self):
        from wish_engine.soul_api_bridge import SOUL_API_MAP
        actions = SOUL_API_MAP.get("need_translation", [])
        api_modules = [a["api"] for a in actions]
        assert "wish_engine.apis.translation_api" in api_modules

    def test_immigration_stress_includes_translation_and_visa_jobs(self):
        from wish_engine.soul_api_bridge import SOUL_API_MAP
        actions = SOUL_API_MAP.get("immigration_stress", [])
        api_modules = [a["api"] for a in actions]
        assert "wish_engine.apis.translation_api" in api_modules
        assert "wish_engine.apis.jobs_api" in api_modules
        # Should have visa sponsorship
        jobs_action = next(a for a in actions if a["api"] == "wish_engine.apis.jobs_api")
        assert jobs_action["params"].get("visa_sponsorship") is True

    def test_job_loss_includes_live_jobs(self):
        from wish_engine.soul_api_bridge import SOUL_API_MAP
        actions = SOUL_API_MAP.get("job_loss", [])
        api_modules = [a["api"] for a in actions]
        assert "wish_engine.apis.jobs_api" in api_modules

    def test_new_place_includes_teleport(self):
        from wish_engine.soul_api_bridge import SOUL_API_MAP
        actions = SOUL_API_MAP.get("new_place", [])
        api_modules = [a["api"] for a in actions]
        assert "wish_engine.apis.teleport_api" in api_modules
