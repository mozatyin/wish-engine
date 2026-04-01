"""Tests for wish_engine.api_server (FastAPI HTTP layer)."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from wish_engine.api_server import app

client = TestClient(app)

_DUMMY_RESULT = {
    "api":      "wish_engine.apis.joke_api",
    "fn":       "get_joke",
    "cat":      "healing",
    "star":     "meteor",
    "rendered": "😄 A joke",
    "raw":      {"joke": "A joke"},
}


# ── /health ───────────────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_has_status_ok(self):
        assert client.get("/health").json()["status"] == "ok"

    def test_has_signal_count(self):
        data = client.get("/health").json()
        assert data["signals"] >= 92


# ── /signals ──────────────────────────────────────────────────────────────────

class TestSignals:
    def test_returns_200(self):
        assert client.get("/signals").status_code == 200

    def test_count_matches_list(self):
        data = client.get("/signals").json()
        assert data["count"] == len(data["signals"])

    def test_known_signals_present(self):
        signals = client.get("/signals").json()["signals"]
        for s in ("sad", "lonely", "bored", "want_learn"):
            assert s in signals

    def test_signals_sorted(self):
        signals = client.get("/signals").json()["signals"]
        assert signals == sorted(signals)


# ── POST /recommend ───────────────────────────────────────────────────────────

class TestRecommend:
    @patch("wish_engine.executor._call_action", return_value=_DUMMY_RESULT)
    def test_returns_200_for_known_signal(self, _):
        resp = client.post("/recommend", json={"signal": "sad"})
        assert resp.status_code == 200

    @patch("wish_engine.executor._call_action", return_value=_DUMMY_RESULT)
    def test_response_has_signal_and_results(self, _):
        data = client.post("/recommend", json={"signal": "sad"}).json()
        assert data["signal"] == "sad"
        assert "results" in data
        assert isinstance(data["results"], list)

    @patch("wish_engine.executor._call_action", return_value=_DUMMY_RESULT)
    def test_result_items_have_required_keys(self, _):
        data = client.post("/recommend", json={"signal": "sad", "limit": 1}).json()
        if data["results"]:
            item = data["results"][0]
            for key in ("api", "fn", "cat", "star", "rendered", "raw"):
                assert key in item

    def test_unknown_signal_returns_404(self):
        resp = client.post("/recommend", json={"signal": "__nonexistent__"})
        assert resp.status_code == 404

    @patch("wish_engine.executor._call_action", return_value=_DUMMY_RESULT)
    def test_limit_respected(self, _):
        data = client.post("/recommend", json={"signal": "sad", "limit": 2}).json()
        assert len(data["results"]) <= 2

    @patch("wish_engine.executor._call_action", return_value=_DUMMY_RESULT)
    def test_with_location(self, _):
        resp = client.post("/recommend", json={
            "signal": "want_outdoor",
            "lat": 25.2048,
            "lng": 55.2708,
        })
        assert resp.status_code == 200

    def test_limit_above_10_rejected(self):
        resp = client.post("/recommend", json={"signal": "sad", "limit": 99})
        assert resp.status_code == 422

    def test_missing_signal_returns_422(self):
        resp = client.post("/recommend", json={"limit": 2})
        assert resp.status_code == 422


# ── POST /pipeline ────────────────────────────────────────────────────────────

class TestPipeline:
    @patch("wish_engine.executor._call_action", return_value=_DUMMY_RESULT)
    def test_returns_200(self, _):
        resp = client.post("/pipeline", json={"utterances": ["I feel sad"]})
        assert resp.status_code == 200

    @patch("wish_engine.executor._call_action", return_value=_DUMMY_RESULT)
    def test_response_structure(self, _):
        data = client.post("/pipeline", json={"utterances": ["I feel sad"]}).json()
        assert "signals" in data
        assert "results" in data
        assert isinstance(data["signals"], list)
        assert isinstance(data["results"], dict)

    @patch("wish_engine.soul_recommender.detect_surface_attention", return_value=["sad", "lonely"])
    @patch("wish_engine.executor._call_action", return_value=_DUMMY_RESULT)
    def test_detected_signals_in_results(self, _call, _detect):
        data = client.post("/pipeline", json={"utterances": ["test"]}).json()
        assert "sad" in data["results"]
        assert "lonely" in data["results"]

    @patch("wish_engine.executor._call_action", return_value=_DUMMY_RESULT)
    def test_with_location(self, _):
        resp = client.post("/pipeline", json={
            "utterances": ["feeling lonely"],
            "lat": 25.2,
            "lng": 55.3,
        })
        assert resp.status_code == 200

    @patch("wish_engine.soul_recommender.detect_surface_attention", return_value=["a", "b", "c", "d"])
    @patch("wish_engine.executor._call_action", return_value=_DUMMY_RESULT)
    def test_max_signals_respected(self, _call, _detect):
        data = client.post("/pipeline", json={
            "utterances": ["test"],
            "max_signals": 2,
        }).json()
        assert len(data["signals"]) <= 2

    def test_empty_utterances_rejected(self):
        resp = client.post("/pipeline", json={"utterances": []})
        assert resp.status_code == 422
