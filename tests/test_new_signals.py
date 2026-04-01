"""Tests for the 7 new signals + enriched thin signals + newly wired APIs."""
import pytest

from wish_engine.soul_api_bridge import SOUL_API_MAP, get_api_actions, count_api_connections
from wish_engine.soul_recommender import detect_surface_attention


# ── Coverage sanity ──────────────────────────────────────────────────────────

class TestCoverageSanity:
    def test_total_attentions_at_least_92(self):
        assert len(SOUL_API_MAP) >= 92

    def test_no_thin_signals(self):
        """Every signal must have at least 2 API actions."""
        thin = [(k, len(v)) for k, v in SOUL_API_MAP.items() if len(v) < 2]
        assert thin == [], f"Thin signals found: {thin}"

    def test_total_connections_at_least_260(self):
        stats = count_api_connections()
        assert stats["total_connections"] >= 260


# ── 7 new signals exist and have sufficient actions ──────────────────────────

class TestNewSignalsExist:
    @pytest.mark.parametrize("signal,min_actions", [
        ("procrastinating",  4),
        ("want_romance",     4),
        ("poor_sleep",       4),
        ("entertainment",    4),
        ("want_travel",      4),
        ("want_invest",      4),
        ("want_volunteer",   3),
    ])
    def test_signal_has_enough_actions(self, signal, min_actions):
        actions = get_api_actions(signal)
        assert len(actions) >= min_actions, f"{signal} has only {len(actions)} actions"

    def test_procrastinating_has_pomodoro(self):
        apis = [a["api"] for a in get_api_actions("procrastinating")]
        assert any("productivity" in a for a in apis)

    def test_procrastinating_has_joke(self):
        apis = [a["api"] for a in get_api_actions("procrastinating")]
        assert any("joke" in a for a in apis)

    def test_want_romance_has_sufi_quote(self):
        actions = get_api_actions("want_romance")
        sufi = [a for a in actions if "philosophy_quotes" in a["api"]]
        assert sufi, "want_romance should have Sufi quotes"
        assert sufi[0]["params"].get("tradition") == "Sufi"

    def test_poor_sleep_has_sleep_times(self):
        apis = [a["api"] for a in get_api_actions("poor_sleep")]
        assert any("health_apis" in a for a in apis)

    def test_poor_sleep_has_breathing(self):
        apis = [a["api"] for a in get_api_actions("poor_sleep")]
        assert any("wellness" in a for a in apis)

    def test_entertainment_has_joke(self):
        apis = [a["api"] for a in get_api_actions("entertainment")]
        assert any("joke" in a for a in apis)

    def test_want_travel_has_teleport(self):
        apis = [a["api"] for a in get_api_actions("want_travel")]
        assert any("teleport" in a for a in apis)

    def test_want_invest_has_currency(self):
        apis = [a["api"] for a in get_api_actions("want_invest")]
        assert any("currency" in a for a in apis)

    def test_want_volunteer_has_osm_community(self):
        actions = get_api_actions("want_volunteer")
        osm_acts = [a for a in actions if "osm_api" in a["api"]]
        assert osm_acts
        place_types = osm_acts[0]["params"].get("place_types", [])
        assert "community_centre" in place_types or "social_facility" in place_types


# ── Previously thin signals now have ≥3 actions ──────────────────────────────

class TestEnrichedThinSignals:
    @pytest.mark.parametrize("signal", ["need_medicine", "need_wifi", "need_quiet", "need_vet"])
    def test_no_longer_thin(self, signal):
        assert len(get_api_actions(signal)) >= 3

    def test_need_medicine_has_breathing(self):
        apis = [a["api"] for a in get_api_actions("need_medicine")]
        assert any("wellness" in a for a in apis)

    def test_need_wifi_has_knowledge(self):
        apis = [a["api"] for a in get_api_actions("need_wifi")]
        assert any("knowledge" in a for a in apis)

    def test_need_quiet_has_spiritual(self):
        apis = [a["api"] for a in get_api_actions("need_quiet")]
        assert any("spiritual" in a or "wellness" in a for a in apis)

    def test_need_vet_has_comfort(self):
        apis = [a["api"] for a in get_api_actions("need_vet")]
        assert any("wellness" in a or "advice" in a for a in apis)


# ── Newly wired APIs ──────────────────────────────────────────────────────────

class TestNewlyWiredAPIs:
    def test_joke_api_in_sad(self):
        apis = [a["api"] for a in get_api_actions("sad")]
        assert any("joke" in a for a in apis)

    def test_joke_api_in_lonely(self):
        apis = [a["api"] for a in get_api_actions("lonely")]
        assert any("joke" in a for a in apis)

    def test_joke_api_in_bored(self):
        apis = [a["api"] for a in get_api_actions("bored")]
        assert any("joke" in a for a in apis)

    def test_open_library_in_want_read(self):
        apis = [a["api"] for a in get_api_actions("want_read")]
        assert any("open_library" in a for a in apis)

    def test_tarot_in_reflection(self):
        apis = [a["api"] for a in get_api_actions("reflection")]
        assert any("tarot" in a for a in apis)

    def test_tarot_in_need_meaning(self):
        apis = [a["api"] for a in get_api_actions("need_meaning")]
        assert any("tarot" in a for a in apis)

    def test_air_quality_in_want_outdoor(self):
        apis = [a["api"] for a in get_api_actions("want_outdoor")]
        assert any("air_quality" in a for a in apis)

    def test_air_quality_in_need_exercise(self):
        apis = [a["api"] for a in get_api_actions("need_exercise")]
        assert any("air_quality" in a for a in apis)

    def test_air_quality_in_headache(self):
        apis = [a["api"] for a in get_api_actions("headache")]
        assert any("air_quality" in a for a in apis)

    def test_music_api_in_want_music(self):
        apis = [a["api"] for a in get_api_actions("want_music")]
        assert any("music_api" in a for a in apis)

    def test_music_api_in_morning(self):
        apis = [a["api"] for a in get_api_actions("morning")]
        assert any("music_api" in a for a in apis)


# ── Keyword detection for new signals ────────────────────────────────────────

class TestNewSignalKeywords:
    def test_procrastinating_detected(self):
        signals = detect_surface_attention(["I keep putting it off, can't get started"])
        assert "procrastinating" in signals

    def test_procrastinating_detected_indirect(self):
        signals = detect_surface_attention(["been meaning to do it but haven't started yet"])
        assert "procrastinating" in signals

    def test_want_romance_detected(self):
        signals = detect_surface_attention(["I'm so single, I want a relationship"])
        assert "want_romance" in signals

    def test_poor_sleep_detected(self):
        signals = detect_surface_attention(["wake up exhausted even after sleeping 8 hours"])
        assert "poor_sleep" in signals

    def test_entertainment_detected(self):
        signals = detect_surface_attention(["staying in tonight, what to watch"])
        assert "entertainment" in signals

    def test_want_travel_detected(self):
        signals = detect_surface_attention(["I want to travel, planning a trip"])
        assert "want_travel" in signals

    def test_want_invest_detected(self):
        signals = detect_surface_attention(["want to invest, where should I put my money"])
        assert "want_invest" in signals

    def test_want_volunteer_detected(self):
        signals = detect_surface_attention(["want to volunteer and give back to the community"])
        assert "want_volunteer" in signals

    def test_procrastinating_not_triggered_by_negation(self):
        # "I'm not procrastinating" should not trigger (single-word negation)
        signals = detect_surface_attention(["I'm not procrastinating at all"])
        assert "procrastinating" not in signals

    def test_chinese_romance_detected(self):
        signals = detect_surface_attention(["我想恋爱，想找对象"])
        assert "want_romance" in signals

    def test_chinese_invest_detected(self):
        signals = detect_surface_attention(["我想投资，不知道从哪里开始"])
        assert "want_invest" in signals
