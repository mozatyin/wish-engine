import pytest
from wish_engine.apis.city_data import get_city_places, get_city_events, detect_city, get_supported_cities


class TestCityData:
    def test_dubai_has_places(self):
        places = get_city_places("dubai")
        assert len(places) >= 5

    def test_each_place_has_coords(self):
        for city in get_supported_cities():
            for p in get_city_places(city):
                assert "lat" in p, f"{p['title']} missing lat"
                assert "lng" in p, f"{p['title']} missing lng"

    def test_detect_city_dubai(self):
        assert detect_city("I'm in Dubai Marina") == "dubai"

    def test_detect_city_shanghai(self):
        assert detect_city("\u6211\u5728\u4e0a\u6d77\u6d66\u4e1c") == "shanghai"

    def test_detect_city_arabic(self):
        assert detect_city("\u0623\u0646\u0627 \u0641\u064a \u062f\u0628\u064a") == "dubai"

    def test_dubai_has_events(self):
        events = get_city_events("dubai")
        assert len(events) >= 3

    def test_unknown_city_empty(self):
        assert get_city_places("atlantis") == []

    def test_supported_cities_count(self):
        cities = get_supported_cities()
        assert len(cities) >= 5

    def test_each_place_has_required_fields(self):
        for city in get_supported_cities():
            for p in get_city_places(city):
                assert "title" in p, f"Place missing title in {city}"
                assert "category" in p, f"{p['title']} missing category"
                assert "tags" in p, f"{p['title']} missing tags"

    def test_detect_city_riyadh(self):
        assert detect_city("\u0627\u0644\u0631\u064a\u0627\u0636") == "riyadh"

    def test_detect_city_cairo(self):
        assert detect_city("I live in Cairo") == "cairo"

    def test_detect_city_barcelona(self):
        assert detect_city("visiting barcelona") == "barcelona"

    def test_unknown_text_empty(self):
        assert detect_city("hello world") == ""

    def test_events_have_required_fields(self):
        for city in get_supported_cities():
            for e in get_city_events(city):
                assert "title" in e, f"Event missing title in {city}"
                assert "tags" in e, f"{e['title']} missing tags"
