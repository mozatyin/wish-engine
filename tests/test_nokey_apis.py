import pytest, json
from unittest.mock import patch, MagicMock

class TestOpenMeteo:
    @patch("wish_engine.apis.open_meteo_api.urlopen")
    def test_get_weather(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"current_weather": {"temperature": 28, "windspeed": 15, "weathercode": 0, "is_day": 1}}).encode()
        mock_resp.__enter__ = lambda s: s; mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        from wish_engine.apis.open_meteo_api import get_weather
        w = get_weather(25.2, 55.3)
        assert w["temperature_c"] == 28
        assert w["condition"] == "clear"

    def test_should_stay_indoors_rain(self):
        from wish_engine.apis.open_meteo_api import should_stay_indoors
        assert should_stay_indoors({"condition": "rain"}) == True
        assert should_stay_indoors({"condition": "clear"}) == False

    def test_always_available(self):
        from wish_engine.apis.open_meteo_api import is_available
        assert is_available() == True

class TestAladhan:
    @patch("wish_engine.apis.aladhan_api.urlopen")
    def test_prayer_times(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"data": {"timings": {"Fajr": "05:11", "Dhuhr": "12:23", "Asr": "15:41", "Maghrib": "18:23", "Isha": "19:41", "Sunrise": "06:14"}, "date": {"readable": "29 Mar 2026"}}}).encode()
        mock_resp.__enter__ = lambda s: s; mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        from wish_engine.apis.aladhan_api import get_prayer_times
        pt = get_prayer_times(25.2, 55.3)
        assert pt["fajr"] == "05:11"
        assert pt["maghrib"] == "18:23"

class TestWikipedia:
    @patch("wish_engine.apis.wikipedia_api.urlopen")
    def test_summary(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"title": "Dubai", "extract": "Dubai is a city in the UAE", "description": "City in UAE"}).encode()
        mock_resp.__enter__ = lambda s: s; mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        from wish_engine.apis.wikipedia_api import get_summary
        s = get_summary("Dubai")
        assert s["title"] == "Dubai"
        assert "UAE" in s["extract"]

class TestPoetryDB:
    @patch("wish_engine.apis.poetry_api.urlopen")
    def test_random_poem(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([{"title": "Sonnet 18", "author": "Shakespeare", "lines": ["Shall I compare thee"], "linecount": "14"}]).encode()
        mock_resp.__enter__ = lambda s: s; mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        from wish_engine.apis.poetry_api import random_poem
        p = random_poem()
        assert p["author"] == "Shakespeare"

class TestHolidays:
    @patch("wish_engine.apis.holidays_api.urlopen")
    def test_uae_holidays(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([{"date": "2026-12-02", "localName": "اليوم الوطني", "name": "National Day", "types": ["Public"]}]).encode()
        mock_resp.__enter__ = lambda s: s; mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        from wish_engine.apis.holidays_api import get_holidays
        h = get_holidays("AE")
        assert len(h) >= 1
        assert "National" in h[0]["name_en"]

class TestCountries:
    @patch("wish_engine.apis.countries_api.urlopen")
    def test_uae(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([{"name": {"common": "United Arab Emirates", "official": "UAE"}, "capital": ["Abu Dhabi"], "languages": {"ara": "Arabic"}, "currencies": {"AED": {"name": "UAE Dirham"}}, "timezones": ["UTC+04:00"], "population": 9890000, "flag": "\ud83c\udde6\ud83c\uddea", "region": "Asia"}]).encode()
        mock_resp.__enter__ = lambda s: s; mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        from wish_engine.apis.countries_api import get_country
        c = get_country("AE")
        assert c["name"] == "United Arab Emirates"
        assert "Arabic" in c["languages"]

class TestDatamuse:
    @patch("wish_engine.apis.datamuse_api.urlopen")
    def test_related_words(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps([{"word": "phobia", "score": 1674}, {"word": "stress", "score": 1200}]).encode()
        mock_resp.__enter__ = lambda s: s; mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        from wish_engine.apis.datamuse_api import related_words
        words = related_words("anxiety")
        assert "phobia" in words

class TestFoodFacts:
    @patch("wish_engine.apis.food_facts_api.urlopen")
    def test_product(self, mock):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"product": {"product_name": "Nutella", "brands": "Ferrero", "nutriscore_grade": "e", "allergens_tags": ["en:milk", "en:nuts"]}}).encode()
        mock_resp.__enter__ = lambda s: s; mock_resp.__exit__ = MagicMock(return_value=False)
        mock.return_value = mock_resp
        from wish_engine.apis.food_facts_api import get_product
        p = get_product("3017620422003")
        assert p["name"] == "Nutella"
        assert "en:nuts" in p["allergens"]

class TestAllAvailable:
    def test_all_free_apis_available(self):
        from wish_engine.apis.open_meteo_api import is_available as a1
        from wish_engine.apis.aladhan_api import is_available as a2
        from wish_engine.apis.wikipedia_api import is_available as a3
        from wish_engine.apis.poetry_api import is_available as a4
        from wish_engine.apis.holidays_api import is_available as a5
        from wish_engine.apis.countries_api import is_available as a6
        from wish_engine.apis.datamuse_api import is_available as a7
        from wish_engine.apis.food_facts_api import is_available as a8
        assert all([a1(), a2(), a3(), a4(), a5(), a6(), a7(), a8()])
