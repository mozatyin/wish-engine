"""Tests for wish_engine.executor — the runtime execution layer."""
from unittest.mock import MagicMock, patch

import pytest

from wish_engine.executor import (
    _build_kwargs,
    _call_action,
    _render,
    execute,
    execute_pipeline,
)


# ── helpers ───────────────────────────────────────────────────────────────────

_DUMMY = {
    "api":      "wish_engine.apis.joke_api",
    "fn":       "get_joke",
    "cat":      "fun",
    "star":     "meteor",
    "rendered": "😄 A joke",
    "raw":      {"joke": "A joke"},
}

def _action(fn="get_joke", params=None, cat="fun", template="😄 {joke}"):
    return {
        "api":      "wish_engine.apis.joke_api",
        "fn":       fn,
        "params":   params or {},
        "template": template,
        "star":     "meteor",
        "cat":      cat,
    }


# ── _build_kwargs ─────────────────────────────────────────────────────────────

class TestBuildKwargs:
    def test_injects_lat_lng_when_in_signature(self):
        def fn(lat, lng, query="x"):
            pass
        result = _build_kwargs(fn, {"query": "hello"}, lat=10.0, lng=20.0)
        assert result == {"query": "hello", "lat": 10.0, "lng": 20.0}

    def test_does_not_inject_when_not_in_signature(self):
        def fn(query="x"):
            pass
        result = _build_kwargs(fn, {"query": "hello"}, lat=10.0, lng=20.0)
        assert "lat" not in result
        assert "lng" not in result

    def test_does_not_inject_none_values(self):
        def fn(lat, lng):
            pass
        result = _build_kwargs(fn, {}, lat=None, lng=None)
        assert result == {}

    def test_only_lat_injected_when_lng_none(self):
        def fn(lat, lng):
            pass
        result = _build_kwargs(fn, {}, lat=5.0, lng=None)
        assert result == {"lat": 5.0}
        assert "lng" not in result

    def test_static_params_preserved(self):
        def fn(place_types=None):
            pass
        result = _build_kwargs(fn, {"place_types": ["park"]}, lat=None, lng=None)
        assert result == {"place_types": ["park"]}

    def test_runtime_lat_lng_override_static_params(self):
        def fn(lat, lng):
            pass
        result = _build_kwargs(fn, {"lat": 0.0, "lng": 0.0}, lat=10.0, lng=20.0)
        assert result["lat"] == 10.0
        assert result["lng"] == 20.0

    def test_mixed_static_and_injected(self):
        def fn(lat, lng, radius_m=500, place_types=None):
            pass
        result = _build_kwargs(fn, {"radius_m": 1000, "place_types": ["park"]}, lat=1.0, lng=2.0)
        assert result == {"radius_m": 1000, "place_types": ["park"], "lat": 1.0, "lng": 2.0}


# ── _render ───────────────────────────────────────────────────────────────────

class TestRender:
    def test_simple_dict(self):
        assert _render("Hello {name}", {"name": "World"}) == "Hello World"

    def test_list_uses_first_item(self):
        raw = [{"title": "Central Park"}, {"title": "Other Park"}]
        assert _render("Place: {title}", raw) == "Place: Central Park"

    def test_string_bound_to_result(self):
        assert _render("Tip: {result}", "Drink water") == "Tip: Drink water"

    def test_missing_key_renders_empty(self):
        result = _render("Hello {missing}", {"name": "World"})
        assert result == "Hello "

    def test_empty_template_returns_empty(self):
        assert _render("", {"name": "World"}) == ""

    def test_truncation_format_spec(self):
        assert _render("{text:.5}", {"text": "Hello World"}) == "Hello"

    def test_returns_template_on_failure(self):
        # Non-iterable raw that can't be rendered
        result = _render("{a[0][b]}", "not-indexable")
        assert isinstance(result, str)

    def test_non_dict_list_item(self):
        # list of strings — first item becomes {result}
        result = _render("{result}", ["item1", "item2"])
        assert result == "item1"

    def test_dict_result_key_fallback(self):
        # dict without template key falls back to _SafeDict empty
        result = _render("val={missing_key}", {"other": 1})
        assert result == "val="

    def test_numeric_raw_becomes_result(self):
        result = _render("Number: {result}", 42)
        assert result == "Number: 42"


# ── _call_action ──────────────────────────────────────────────────────────────

class TestCallAction:
    @patch("wish_engine.executor.importlib.import_module")
    def test_returns_structured_result_on_success(self, mock_import):
        mock_mod = MagicMock()
        mock_mod.get_joke.return_value = {"joke": "Why did..."}
        mock_import.return_value = mock_mod

        result = _call_action(_action(), lat=None, lng=None)

        assert result is not None
        assert result["raw"] == {"joke": "Why did..."}
        assert result["api"] == "wish_engine.apis.joke_api"
        assert result["fn"] == "get_joke"
        assert result["cat"] == "fun"
        assert result["star"] == "meteor"
        assert "rendered" in result

    @patch("wish_engine.executor.importlib.import_module")
    def test_result_has_all_required_keys(self, mock_import):
        mock_mod = MagicMock()
        mock_mod.get_joke.return_value = {"joke": "test"}
        mock_import.return_value = mock_mod

        result = _call_action(_action(), lat=None, lng=None)
        for key in ("api", "fn", "cat", "star", "rendered", "raw"):
            assert key in result

    @patch("wish_engine.executor.importlib.import_module")
    def test_returns_none_on_api_exception(self, mock_import):
        mock_mod = MagicMock()
        mock_mod.get_joke.side_effect = Exception("network error")
        mock_import.return_value = mock_mod

        assert _call_action(_action(), lat=None, lng=None) is None

    @patch("wish_engine.executor.importlib.import_module")
    def test_returns_none_when_api_returns_none(self, mock_import):
        mock_mod = MagicMock()
        mock_mod.get_joke.return_value = None
        mock_import.return_value = mock_mod

        assert _call_action(_action(), lat=None, lng=None) is None

    @patch("wish_engine.executor.importlib.import_module")
    def test_returns_none_when_api_returns_empty_list(self, mock_import):
        mock_mod = MagicMock()
        mock_mod.search.return_value = []
        mock_import.return_value = mock_mod

        assert _call_action({**_action(), "fn": "search"}, lat=None, lng=None) is None

    @patch("wish_engine.executor.importlib.import_module")
    def test_returns_none_when_api_returns_empty_string(self, mock_import):
        mock_mod = MagicMock()
        mock_mod.random_fact.return_value = ""
        mock_import.return_value = mock_mod

        assert _call_action({**_action(), "fn": "random_fact"}, lat=None, lng=None) is None

    @patch("wish_engine.executor.importlib.import_module")
    def test_injects_lat_lng_for_location_api(self, mock_import):
        captured = {}

        def fake_search(lat, lng, place_types=None):
            captured["lat"] = lat
            captured["lng"] = lng
            return [{"title": "Park"}]

        mock_mod = MagicMock()
        mock_mod.search_and_enrich = fake_search
        mock_import.return_value = mock_mod

        action = {
            "api":      "wish_engine.apis.osm_api",
            "fn":       "search_and_enrich",
            "params":   {"place_types": ["park"]},
            "template": "{title}",
            "star":     "meteor",
            "cat":      "place",
        }
        result = _call_action(action, lat=25.2, lng=55.3)

        assert result is not None
        assert captured["lat"] == 25.2
        assert captured["lng"] == 55.3

    @patch("wish_engine.executor.importlib.import_module")
    def test_does_not_inject_lat_lng_for_non_location_api(self, mock_import):
        captured = {}

        def fake_joke(category="Any", lang="en"):
            captured["kwargs"] = {"category": category, "lang": lang}
            return {"joke": "test"}

        mock_mod = MagicMock()
        mock_mod.get_joke = fake_joke
        mock_import.return_value = mock_mod

        _call_action(_action(), lat=25.2, lng=55.3)
        assert "lat" not in captured.get("kwargs", {})

    @patch("wish_engine.executor.importlib.import_module")
    def test_list_raw_accepted(self, mock_import):
        mock_mod = MagicMock()
        mock_mod.search.return_value = [{"title": "Place A"}]
        mock_import.return_value = mock_mod

        result = _call_action({**_action(), "fn": "search", "template": "{title}"}, lat=None, lng=None)
        assert result is not None
        assert result["raw"] == [{"title": "Place A"}]

    def test_returns_none_on_import_error(self):
        action = {
            "api":      "wish_engine.apis.__nonexistent_module__",
            "fn":       "fn",
            "params":   {},
            "template": "",
            "star":     "meteor",
            "cat":      "x",
        }
        assert _call_action(action, lat=None, lng=None) is None


# ── execute ───────────────────────────────────────────────────────────────────

class TestExecute:
    @patch("wish_engine.executor._call_action", return_value=_DUMMY)
    def test_returns_up_to_limit(self, _):
        results = execute("sad", limit=2)
        assert len(results) == 2

    @patch("wish_engine.executor._call_action", return_value=_DUMMY)
    def test_returns_at_most_limit_even_if_more_actions(self, _):
        results = execute("sad", limit=1)
        assert len(results) == 1

    @patch("wish_engine.executor._call_action", return_value=None)
    def test_skips_none_results(self, _):
        assert execute("sad", limit=3) == []

    @patch("wish_engine.executor._call_action")
    def test_cat_filter_restricts_actions(self, mock_call):
        # Return a result whose cat mirrors the action's cat
        mock_call.side_effect = lambda action, lat, lng: {**_DUMMY, "cat": action.get("cat", "")}
        results = execute("sad", cat="healing", limit=10)
        # Only actions with cat="healing" should have been processed
        for r in results:
            assert r["cat"] == "healing"

    def test_unknown_signal_returns_empty(self):
        assert execute("__not_a_real_signal__") == []

    @patch("wish_engine.executor._call_action", return_value=_DUMMY)
    def test_no_location_does_not_raise(self, _):
        results = execute("bored", limit=1)
        assert isinstance(results, list)

    @patch("wish_engine.executor._call_action", return_value=_DUMMY)
    def test_result_structure(self, _):
        results = execute("sad", limit=1)
        assert len(results) == 1
        r = results[0]
        for key in ("api", "fn", "cat", "star", "rendered", "raw"):
            assert key in r

    @patch("wish_engine.executor._call_action")
    def test_continues_after_failure(self, mock_call):
        # First call fails, second succeeds
        mock_call.side_effect = [None, _DUMMY, _DUMMY]
        results = execute("sad", limit=2)
        assert len(results) == 2

    @patch("wish_engine.executor._call_action", return_value=_DUMMY)
    def test_location_passed_through_to_call_action(self, mock_call):
        execute("sad", user_lat=10.0, user_lng=20.0, limit=1)
        _, call_kwargs = mock_call.call_args
        # _call_action(action, lat, lng) — check positional args
        args = mock_call.call_args[0]
        assert args[1] == 10.0  # lat
        assert args[2] == 20.0  # lng


# ── execute_pipeline ──────────────────────────────────────────────────────────

class TestExecutePipeline:
    def test_returns_required_keys(self):
        with patch("wish_engine.soul_recommender.detect_surface_attention", return_value=["sad"]):
            with patch("wish_engine.executor._call_action", return_value=_DUMMY):
                result = execute_pipeline(["I feel sad"])
        assert "signals" in result
        assert "results" in result

    def test_detected_signals_present_in_results(self):
        with patch("wish_engine.soul_recommender.detect_surface_attention", return_value=["sad", "lonely"]):
            with patch("wish_engine.executor._call_action", return_value=_DUMMY):
                result = execute_pipeline(["I feel sad and lonely"])
        assert "sad" in result["results"]
        assert "lonely" in result["results"]

    def test_empty_utterances_returns_empty(self):
        result = execute_pipeline([])
        assert result["signals"] == []
        assert result["results"] == {}

    def test_max_signals_respected(self):
        four_signals = ["sad", "lonely", "scared", "panicking"]
        with patch("wish_engine.soul_recommender.detect_surface_attention", return_value=four_signals):
            with patch("wish_engine.executor._call_action", return_value=_DUMMY):
                result = execute_pipeline(["test"], max_signals=2)
        assert len(result["signals"]) <= 2

    def test_limit_per_signal_respected(self):
        with patch("wish_engine.soul_recommender.detect_surface_attention", return_value=["sad"]):
            with patch("wish_engine.executor._call_action", return_value=_DUMMY):
                result = execute_pipeline(["test"], limit_per_signal=1)
        assert len(result["results"].get("sad", [])) <= 1

    def test_signals_list_is_list(self):
        with patch("wish_engine.soul_recommender.detect_surface_attention", return_value=["sad"]):
            with patch("wish_engine.executor._call_action", return_value=_DUMMY):
                result = execute_pipeline(["test"])
        assert isinstance(result["signals"], list)

    def test_with_real_location(self):
        with patch("wish_engine.soul_recommender.detect_surface_attention", return_value=["want_outdoor"]):
            with patch("wish_engine.executor._call_action", return_value=_DUMMY):
                result = execute_pipeline(["want to go outside"], user_lat=25.2, user_lng=55.3)
        assert "want_outdoor" in result["results"]
