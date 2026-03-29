"""Tests for wave 2 APIs (25-50). All use mocks — no real network calls."""
from __future__ import annotations
import json
from unittest.mock import patch, MagicMock
import pytest


# ── helpers ──────────────────────────────────────────────────────────
def _mock_urlopen(payload: bytes):
    """Return a context-manager mock that yields a response with .read()."""
    resp = MagicMock()
    resp.read.return_value = payload
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ── sunrise_sunset_api ───────────────────────────────────────────────
class TestSunriseSunset:
    def test_get_sun_times(self):
        from wish_engine.apis.sunrise_sunset_api import get_sun_times
        body = json.dumps({"results": {"sunrise": "2026-03-26T06:00:00+00:00", "sunset": "2026-03-26T18:00:00+00:00", "day_length": 43200, "solar_noon": "2026-03-26T12:00:00+00:00", "civil_twilight_begin": "2026-03-26T05:30:00+00:00", "civil_twilight_end": "2026-03-26T18:30:00+00:00"}, "status": "OK"}).encode()
        with patch("wish_engine.apis.sunrise_sunset_api.urlopen", return_value=_mock_urlopen(body)):
            result = get_sun_times(25.2, 55.3)
            assert result is not None
            assert "sunrise" in result
            assert "sunset" in result
            assert result["day_length"] == 43200

    def test_is_available(self):
        from wish_engine.apis.sunrise_sunset_api import is_available
        assert is_available() is True

    def test_network_error_returns_none(self):
        from wish_engine.apis.sunrise_sunset_api import get_sun_times
        with patch("wish_engine.apis.sunrise_sunset_api.urlopen", side_effect=Exception("timeout")):
            assert get_sun_times(0, 0) is None


# ── ip_geolocation_api ──────────────────────────────────────────────
class TestIPGeolocation:
    def test_get_location(self):
        from wish_engine.apis.ip_geolocation_api import get_location_from_ip
        body = json.dumps({"status": "success", "city": "Dubai", "country": "UAE", "countryCode": "AE", "lat": 25.2, "lon": 55.3, "timezone": "Asia/Dubai", "isp": "Etisalat"}).encode()
        with patch("wish_engine.apis.ip_geolocation_api.urlopen", return_value=_mock_urlopen(body)):
            result = get_location_from_ip("8.8.8.8")
            assert result is not None
            assert result["city"] == "Dubai"
            assert result["country_code"] == "AE"

    def test_failed_status(self):
        from wish_engine.apis.ip_geolocation_api import get_location_from_ip
        body = json.dumps({"status": "fail", "message": "reserved"}).encode()
        with patch("wish_engine.apis.ip_geolocation_api.urlopen", return_value=_mock_urlopen(body)):
            assert get_location_from_ip("127.0.0.1") is None

    def test_is_available(self):
        from wish_engine.apis.ip_geolocation_api import is_available
        assert is_available() is True


# ── qr_code_api ──────────────────────────────────────────────────────
class TestQRCode:
    def test_returns_url(self):
        from wish_engine.apis.qr_code_api import get_qr_url
        url = get_qr_url("hello world")
        assert url.startswith("https://api.qrserver.com/")
        assert "hello" in url

    def test_custom_size(self):
        from wish_engine.apis.qr_code_api import get_qr_url
        url = get_qr_url("test", size=400)
        assert "400x400" in url

    def test_is_available(self):
        from wish_engine.apis.qr_code_api import is_available
        assert is_available() is True


# ── dictionary_api ───────────────────────────────────────────────────
class TestDictionary:
    def test_define(self):
        from wish_engine.apis.dictionary_api import define
        body = json.dumps([{"word": "hello", "phonetic": "/həˈloʊ/", "meanings": [{"partOfSpeech": "noun", "definitions": [{"definition": "A greeting", "example": "She said hello"}]}]}]).encode()
        with patch("wish_engine.apis.dictionary_api.urlopen", return_value=_mock_urlopen(body)):
            result = define("hello")
            assert result is not None
            assert result["word"] == "hello"
            assert len(result["definitions"]) == 1
            assert result["definitions"][0]["partOfSpeech"] == "noun"

    def test_not_found(self):
        from wish_engine.apis.dictionary_api import define
        with patch("wish_engine.apis.dictionary_api.urlopen", side_effect=Exception("404")):
            assert define("xyznotaword") is None

    def test_is_available(self):
        from wish_engine.apis.dictionary_api import is_available
        assert is_available() is True


# ── iss_api ──────────────────────────────────────────────────────────
class TestISS:
    def test_location(self):
        from wish_engine.apis.iss_api import iss_location
        body = json.dumps({"iss_position": {"latitude": "25.0", "longitude": "55.0"}, "timestamp": 1711400000}).encode()
        with patch("wish_engine.apis.iss_api.urlopen", return_value=_mock_urlopen(body)):
            result = iss_location()
            assert result is not None
            assert result["lat"] == 25.0
            assert result["lng"] == 55.0

    def test_people_in_space(self):
        from wish_engine.apis.iss_api import people_in_space
        body = json.dumps({"people": [{"name": "Sultan AlNeyadi", "craft": "ISS"}], "number": 1}).encode()
        with patch("wish_engine.apis.iss_api.urlopen", return_value=_mock_urlopen(body)):
            result = people_in_space()
            assert len(result) == 1
            assert result[0]["name"] == "Sultan AlNeyadi"

    def test_is_available(self):
        from wish_engine.apis.iss_api import is_available
        assert is_available() is True


# ── cat_api ──────────────────────────────────────────────────────────
class TestCat:
    def test_random_image(self):
        from wish_engine.apis.cat_api import random_cat_image
        body = json.dumps([{"url": "https://cdn2.thecatapi.com/images/abc.jpg"}]).encode()
        with patch("wish_engine.apis.cat_api.urlopen", return_value=_mock_urlopen(body)):
            url = random_cat_image()
            assert url.endswith(".jpg")

    def test_cat_fact(self):
        from wish_engine.apis.cat_api import cat_fact
        body = json.dumps({"fact": "Cats sleep 16 hours a day."}).encode()
        with patch("wish_engine.apis.cat_api.urlopen", return_value=_mock_urlopen(body)):
            assert "Cats" in cat_fact()

    def test_is_available(self):
        from wish_engine.apis.cat_api import is_available
        assert is_available() is True


# ── fox_api ──────────────────────────────────────────────────────────
class TestFox:
    def test_random_image(self):
        from wish_engine.apis.fox_api import random_fox_image
        body = json.dumps({"image": "https://randomfox.ca/images/42.jpg"}).encode()
        with patch("wish_engine.apis.fox_api.urlopen", return_value=_mock_urlopen(body)):
            url = random_fox_image()
            assert "randomfox" in url

    def test_is_available(self):
        from wish_engine.apis.fox_api import is_available
        assert is_available() is True


# ── usgs_earthquake_api ──────────────────────────────────────────────
class TestEarthquake:
    def test_recent(self):
        from wish_engine.apis.usgs_earthquake_api import recent_earthquakes
        body = json.dumps({"features": [{"properties": {"place": "10km NE of Tokyo", "mag": 5.2, "time": 1711400000, "url": "https://earthquake.usgs.gov/event/1"}}]}).encode()
        with patch("wish_engine.apis.usgs_earthquake_api.urlopen", return_value=_mock_urlopen(body)):
            result = recent_earthquakes()
            assert len(result) == 1
            assert result[0]["magnitude"] == 5.2
            assert "Tokyo" in result[0]["place"]

    def test_nearby(self):
        from wish_engine.apis.usgs_earthquake_api import nearby_earthquakes
        body = json.dumps({"features": [{"properties": {"place": "5km S of Muscat", "mag": 3.0}}]}).encode()
        with patch("wish_engine.apis.usgs_earthquake_api.urlopen", return_value=_mock_urlopen(body)):
            result = nearby_earthquakes(23.6, 58.5)
            assert len(result) == 1

    def test_is_available(self):
        from wish_engine.apis.usgs_earthquake_api import is_available
        assert is_available() is True


# ── github_trending_api ──────────────────────────────────────────────
class TestGitHubTrending:
    def test_trending(self):
        from wish_engine.apis.github_trending_api import trending_repos
        body = json.dumps([{"name": "awesome-project", "author": "dev", "description": "Cool stuff", "stars": 1000, "language": "Python", "url": "https://github.com/dev/awesome-project"}]).encode()
        with patch("wish_engine.apis.github_trending_api.urlopen", return_value=_mock_urlopen(body)):
            result = trending_repos()
            assert len(result) == 1
            assert result[0]["name"] == "awesome-project"

    def test_is_available(self):
        from wish_engine.apis.github_trending_api import is_available
        assert is_available() is True


# ── timezone_api ─────────────────────────────────────────────────────
class TestTimezone:
    def test_get_timezone(self):
        from wish_engine.apis.timezone_api import get_timezone
        body = json.dumps({"datetime": "2026-03-26T12:00:00+04:00", "timezone": "Asia/Dubai", "utc_offset": "+04:00", "day_of_week": 4}).encode()
        with patch("wish_engine.apis.timezone_api.urlopen", return_value=_mock_urlopen(body)):
            result = get_timezone("Asia/Dubai")
            assert result is not None
            assert result["timezone"] == "Asia/Dubai"
            assert result["utc_offset"] == "+04:00"

    def test_is_available(self):
        from wish_engine.apis.timezone_api import is_available
        assert is_available() is True


# ── cocktail_api ─────────────────────────────────────────────────────
class TestCocktail:
    def test_search(self):
        from wish_engine.apis.cocktail_api import search_cocktail
        body = json.dumps({"drinks": [{"strDrink": "Mojito", "strCategory": "Cocktail", "strInstructions": "Mix everything", "strDrinkThumb": "https://img.com/mojito.jpg", "strAlcoholic": "Alcoholic"}]}).encode()
        with patch("wish_engine.apis.cocktail_api.urlopen", return_value=_mock_urlopen(body)):
            result = search_cocktail("mojito")
            assert len(result) == 1
            assert result[0]["name"] == "Mojito"

    def test_random(self):
        from wish_engine.apis.cocktail_api import random_cocktail
        body = json.dumps({"drinks": [{"strDrink": "Daiquiri", "strInstructions": "Shake with ice", "strDrinkThumb": "https://img.com/daiquiri.jpg"}]}).encode()
        with patch("wish_engine.apis.cocktail_api.urlopen", return_value=_mock_urlopen(body)):
            result = random_cocktail()
            assert result is not None
            assert result["name"] == "Daiquiri"

    def test_is_available(self):
        from wish_engine.apis.cocktail_api import is_available
        assert is_available() is True


# ── micro_apis ───────────────────────────────────────────────────────
class TestMicroAPIs:
    def test_kanye_quote(self):
        from wish_engine.apis.micro_apis import kanye_quote
        body = json.dumps({"quote": "I am a god"}).encode()
        with patch("wish_engine.apis.micro_apis.urlopen", return_value=_mock_urlopen(body)):
            assert kanye_quote() == "I am a god"

    def test_chuck_norris(self):
        from wish_engine.apis.micro_apis import chuck_norris_joke
        body = json.dumps({"value": "Chuck Norris counted to infinity. Twice."}).encode()
        with patch("wish_engine.apis.micro_apis.urlopen", return_value=_mock_urlopen(body)):
            assert "Chuck" in chuck_norris_joke()

    def test_trivia(self):
        from wish_engine.apis.micro_apis import random_trivia
        body = json.dumps({"results": [{"question": "What is 2+2?", "correct_answer": "4", "category": "Math"}]}).encode()
        with patch("wish_engine.apis.micro_apis.urlopen", return_value=_mock_urlopen(body)):
            result = random_trivia()
            assert result is not None
            assert result["answer"] == "4"

    def test_spacex(self):
        from wish_engine.apis.micro_apis import spacex_latest_launch
        body = json.dumps({"name": "Starship Test 5", "date_utc": "2026-03-01T00:00:00Z", "success": True, "details": "Test flight"}).encode()
        with patch("wish_engine.apis.micro_apis.urlopen", return_value=_mock_urlopen(body)):
            result = spacex_latest_launch()
            assert result is not None
            assert result["name"] == "Starship Test 5"

    def test_zen_quote(self):
        from wish_engine.apis.micro_apis import zen_quote
        body = json.dumps([{"q": "Be present", "a": "Lao Tzu"}]).encode()
        with patch("wish_engine.apis.micro_apis.urlopen", return_value=_mock_urlopen(body)):
            result = zen_quote()
            assert "Be present" in result
            assert "Lao Tzu" in result

    def test_public_ip(self):
        from wish_engine.apis.micro_apis import my_public_ip
        body = json.dumps({"ip": "1.2.3.4"}).encode()
        with patch("wish_engine.apis.micro_apis.urlopen", return_value=_mock_urlopen(body)):
            assert my_public_ip() == "1.2.3.4"

    def test_placeholder_image(self):
        from wish_engine.apis.micro_apis import placeholder_image
        url = placeholder_image(300, 400)
        assert url == "https://picsum.photos/300/400"

    def test_estimate_age(self):
        from wish_engine.apis.micro_apis import estimate_age
        body = json.dumps({"name": "michael", "age": 35}).encode()
        with patch("wish_engine.apis.micro_apis.urlopen", return_value=_mock_urlopen(body)):
            assert estimate_age("michael") == 35

    def test_http_cat(self):
        from wish_engine.apis.micro_apis import http_cat
        assert http_cat(404) == "https://http.cat/404"

    def test_is_available(self):
        from wish_engine.apis.micro_apis import is_available
        assert is_available() is True

    def test_network_errors(self):
        from wish_engine.apis.micro_apis import kanye_quote, chuck_norris_joke, zen_quote, my_public_ip, estimate_age
        with patch("wish_engine.apis.micro_apis.urlopen", side_effect=Exception("offline")):
            assert kanye_quote() == ""
            assert chuck_norris_joke() == ""
            assert zen_quote() == ""
            assert my_public_ip() == ""
            assert estimate_age("test") == 0
