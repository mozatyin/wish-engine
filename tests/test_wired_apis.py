"""Tests for the 8 newly wired API modules (nature, ISS, github_trending, dictionary, numbers, podcast, events)."""
import pytest

from wish_engine.soul_api_bridge import get_api_actions


class TestNatureApisWired:
    def test_lonely_has_shiba(self):
        apis = [a["api"] for a in get_api_actions("lonely")]
        assert any("nature_apis" in a for a in apis)

    def test_lonely_shiba_is_random_shiba_image(self):
        acts = [a for a in get_api_actions("lonely") if "nature_apis" in a["api"]]
        assert acts and acts[0]["fn"] == "random_shiba_image"

    def test_grieving_has_bird(self):
        apis = [a["api"] for a in get_api_actions("grieving")]
        assert any("nature_apis" in a for a in apis)

    def test_grieving_bird_is_random_bird_image(self):
        acts = [a for a in get_api_actions("grieving") if "nature_apis" in a["api"]]
        assert acts and acts[0]["fn"] == "random_bird_image"

    def test_want_outdoor_has_bird(self):
        acts = [a for a in get_api_actions("want_outdoor") if "nature_apis" in a["api"]]
        assert acts and acts[0]["fn"] == "random_bird_image"


class TestISSApiWired:
    def test_want_outdoor_has_iss_location(self):
        acts = [a for a in get_api_actions("want_outdoor") if "iss_api" in a["api"]]
        assert acts and acts[0]["fn"] == "iss_location"

    def test_morning_has_people_in_space(self):
        acts = [a for a in get_api_actions("morning") if "iss_api" in a["api"]]
        assert acts and acts[0]["fn"] == "people_in_space"


class TestGithubTrendingWired:
    def test_want_work_has_github_trending(self):
        apis = [a["api"] for a in get_api_actions("want_work")]
        assert any("github_trending_api" in a for a in apis)

    def test_want_learn_has_github_trending(self):
        apis = [a["api"] for a in get_api_actions("want_learn")]
        assert any("github_trending_api" in a for a in apis)


class TestDictionaryApiWired:
    def test_want_learn_has_dictionary(self):
        apis = [a["api"] for a in get_api_actions("want_learn")]
        assert any("dictionary_api" in a for a in apis)

    def test_want_learn_dictionary_fn_is_define(self):
        acts = [a for a in get_api_actions("want_learn") if "dictionary_api" in a["api"]]
        assert acts and acts[0]["fn"] == "define"


class TestNumbersApiWired:
    def test_want_learn_has_numbers(self):
        apis = [a["api"] for a in get_api_actions("want_learn")]
        assert any("numbers_api" in a for a in apis)

    def test_bored_has_numbers(self):
        apis = [a["api"] for a in get_api_actions("bored")]
        assert any("numbers_api" in a for a in apis)


class TestPodcastApiWired:
    def test_want_learn_has_podcast(self):
        apis = [a["api"] for a in get_api_actions("want_learn")]
        assert any("podcast_api" in a for a in apis)

    def test_entertainment_has_podcast(self):
        apis = [a["api"] for a in get_api_actions("entertainment")]
        assert any("podcast_api" in a for a in apis)


class TestEventsApiWired:
    def test_bored_has_events_api(self):
        apis = [a["api"] for a in get_api_actions("bored")]
        assert any("events_api" in a for a in apis)

    def test_weekend_has_events_api(self):
        apis = [a["api"] for a in get_api_actions("weekend")]
        assert any("events_api" in a for a in apis)

    def test_bored_events_api_has_keyword(self):
        acts = [a for a in get_api_actions("bored") if "events_api" in a["api"]]
        assert acts
        assert "keyword" in acts[0]["params"]

    def test_weekend_events_api_larger_radius(self):
        bored_acts = [a for a in get_api_actions("bored") if "events_api" in a["api"]]
        weekend_acts = [a for a in get_api_actions("weekend") if "events_api" in a["api"]]
        assert bored_acts and weekend_acts
        assert weekend_acts[0]["params"]["radius_km"] >= bored_acts[0]["params"]["radius_km"]


class TestCoverageSanityAfterWiring:
    def test_total_connections_at_least_270(self):
        from wish_engine.soul_api_bridge import count_api_connections
        stats = count_api_connections()
        assert stats["total_connections"] >= 270

    def test_no_thin_signals(self):
        from wish_engine.soul_api_bridge import SOUL_API_MAP
        thin = [(k, len(v)) for k, v in SOUL_API_MAP.items() if len(v) < 2]
        assert thin == []
