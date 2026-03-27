"""Tests for Event Discovery — API client, personality mapping, and EventFulfiller."""

import pytest
from unittest.mock import patch
from wish_engine.apis.events_api import search_all, is_available, _normalize_eventbrite, _normalize_ticketmaster
from wish_engine.apis.events_personality import enrich_event, enrich_events, _infer_category
from wish_engine.l2_events import EventFulfiller, EVENT_CATALOG, _match_categories
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType


class TestEventsApiAvailability:
    def test_not_available_without_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            assert not is_available()

    def test_available_with_eventbrite(self):
        with patch.dict("os.environ", {"EVENTBRITE_API_KEY": "test"}):
            assert is_available()

    def test_available_with_ticketmaster(self):
        with patch.dict("os.environ", {"TICKETMASTER_API_KEY": "test"}):
            assert is_available()

    def test_search_all_empty_without_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            assert search_all(25.0, 55.0) == []


class TestEventNormalization:
    def test_normalize_eventbrite(self):
        raw = {
            "name": {"text": "Jazz Night"},
            "description": {"text": "Live jazz at the Blue Note"},
            "url": "https://example.com/jazz",
            "start": {"local": "2026-03-28T20:00"},
            "end": {"local": "2026-03-28T23:00"},
            "venue": {"name": "Blue Note", "latitude": 25.1, "longitude": 55.2,
                      "address": {"localized_address_display": "123 Music St"}},
            "category": {"name": "Music"},
            "is_free": False,
        }
        norm = _normalize_eventbrite(raw)
        assert norm["name"] == "Jazz Night"
        assert norm["source"] == "eventbrite"
        assert norm["lat"] == 25.1

    def test_normalize_eventbrite_missing_venue(self):
        raw = {
            "name": {"text": "No Venue Event"},
            "description": {"text": "An event"},
            "url": "",
            "start": {"local": ""},
            "end": {"local": ""},
            "venue": None,
            "category": None,
            "is_free": True,
        }
        norm = _normalize_eventbrite(raw)
        assert norm["name"] == "No Venue Event"
        assert norm["lat"] == 0
        assert norm["is_free"] is True

    def test_normalize_ticketmaster(self):
        raw = {
            "name": "Rock Concert",
            "info": "Amazing rock show",
            "url": "https://example.com/rock",
            "dates": {"start": {"localDate": "2026-03-28", "localTime": "19:00"}},
            "_embedded": {"venues": [{"name": "Arena", "location": {"latitude": "25.1", "longitude": "55.2"},
                                       "city": {"name": "Dubai"}, "country": {"name": "UAE"}}]},
            "classifications": [{"genre": {"name": "Rock"}}],
        }
        norm = _normalize_ticketmaster(raw)
        assert norm["name"] == "Rock Concert"
        assert norm["source"] == "ticketmaster"
        assert norm["category"] == "Rock"

    def test_normalize_ticketmaster_no_venues(self):
        raw = {
            "name": "Minimal Event",
            "info": "Info text",
            "url": "",
            "dates": {"start": {"localDate": "2026-04-01", "localTime": ""}},
            "_embedded": {"venues": []},
            "classifications": [],
        }
        norm = _normalize_ticketmaster(raw)
        assert norm["name"] == "Minimal Event"
        assert norm["lat"] == 0


class TestEventsPersonality:
    def test_opera_is_quiet(self):
        event = {"name": "红楼梦 Opera", "description": "Classic Chinese opera", "category": ""}
        enriched = enrich_event(event)
        assert enriched["noise"] == "quiet"
        assert "traditional" in enriched["tags"]

    def test_rock_concert_is_loud(self):
        event = {"name": "Rock Night", "description": "Live rock music", "category": "rock"}
        enriched = enrich_event(event)
        assert enriched["noise"] == "loud"
        assert "intense" in enriched["tags"]

    def test_infer_from_chinese_keywords(self):
        assert _infer_category({"name": "京剧表演", "description": "", "category": ""}) == "opera"
        assert _infer_category({"name": "读书会", "description": "", "category": ""}) == "book_signing"
        assert _infer_category({"name": "瑜伽课", "description": "", "category": ""}) == "yoga"

    def test_infer_from_arabic_keywords(self):
        assert _infer_category({"name": "ورشة فنية", "description": "", "category": ""}) == "workshop"

    def test_infer_from_english_keywords(self):
        assert _infer_category({"name": "Jazz Festival", "description": "", "category": ""}) == "jazz"

    def test_free_event_tagged(self):
        event = {"name": "Free Concert", "category": "classical", "is_free": True}
        enriched = enrich_event(event)
        assert "free" in enriched["tags"]

    def test_unknown_category_gets_default(self):
        event = {"name": "Unknown Thing", "description": "No category match", "category": ""}
        enriched = enrich_event(event)
        assert enriched["noise"] == "moderate"
        assert enriched["category"] == "event"

    def test_enrich_multiple(self):
        events = [{"name": "A", "category": "jazz"}, {"name": "B", "category": "yoga"}]
        enriched = enrich_events(events)
        assert len(enriched) == 2
        assert enriched[0]["category"] == "jazz"
        assert enriched[1]["category"] == "yoga"

    def test_source_category_takes_priority(self):
        event = {"name": "Some Event", "description": "", "category": "ballet"}
        assert _infer_category(event) == "ballet"


class TestEventCatalog:
    def test_catalog_not_empty(self):
        assert len(EVENT_CATALOG) >= 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for event in EVENT_CATALOG:
            missing = required - set(event.keys())
            assert not missing, f"{event['title']} missing: {missing}"

    def test_catalog_categories_are_diverse(self):
        categories = {e["category"] for e in EVENT_CATALOG}
        assert len(categories) >= 10


class TestEventKeywordMatching:
    def test_opera_keywords(self):
        assert "opera" in _match_categories("想去看红楼梦")
        assert "opera" in _match_categories("想去听歌剧")

    def test_exhibition_keywords(self):
        assert "exhibition" in _match_categories("想去看展览")

    def test_comedy_keywords(self):
        assert "comedy" in _match_categories("想去看脱口秀")

    def test_english_keywords(self):
        assert "theatre" in _match_categories("I want to see a theater play")

    def test_no_match_returns_empty(self):
        assert _match_categories("想学编程") == []

    def test_multiple_matches(self):
        cats = _match_categories("想去看演出和展览")
        assert "theatre" in cats
        assert "exhibition" in cats


class TestEventFulfiller:
    def _make_wish(self, text="想去看演出") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.LEARN_SKILL,
            level=WishLevel.L2, fulfillment_strategy="course_recommendation",
        )

    def test_returns_l2_result(self):
        f = EventFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_opera_wish_finds_opera(self):
        f = EventFulfiller()
        result = f.fulfill(self._make_wish("想去看歌剧"), DetectorResults())
        cats = [r.category for r in result.recommendations]
        assert any(c in ("opera", "theatre", "classical") for c in cats)

    def test_introvert_no_loud_events(self):
        f = EventFulfiller()
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish("想去看演出"), det)
        for rec in result.recommendations:
            assert "noisy" not in rec.tags

    def test_has_map_data(self):
        f = EventFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "event_venue"

    def test_has_reminder(self):
        f = EventFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_max_3(self):
        f = EventFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_tradition_values_boost(self):
        f = EventFulfiller()
        det = DetectorResults(values={"top_values": ["tradition"]})
        result = f.fulfill(self._make_wish("想去看演出"), det)
        assert any("traditional" in r.tags for r in result.recommendations)

    def test_generic_wish_uses_full_catalog(self):
        f = EventFulfiller()
        result = f.fulfill(self._make_wish("想参加活动"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1


class TestEventRouting:
    """Test that event-related wishes route to EventFulfiller."""

    def test_event_keyword_routes_to_events(self):
        from wish_engine.l2_fulfiller import fulfill_l2
        wish = ClassifiedWish(
            wish_text="想去看演出", wish_type=WishType.LEARN_SKILL,
            level=WishLevel.L2, fulfillment_strategy="course_recommendation",
        )
        result = fulfill_l2(wish, DetectorResults())
        # Should get event-type recommendations, not courses
        cats = [r.category for r in result.recommendations]
        assert any(c in ("theatre", "opera", "ballet", "comedy", "classical", "jazz",
                         "exhibition", "workshop", "meetup", "film") for c in cats)

    def test_non_event_still_routes_normally(self):
        from wish_engine.l2_fulfiller import fulfill_l2
        wish = ClassifiedWish(
            wish_text="想学编程", wish_type=WishType.LEARN_SKILL,
            level=WishLevel.L2, fulfillment_strategy="course_recommendation",
        )
        result = fulfill_l2(wish, DetectorResults())
        # Should get course recommendations, not events
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("programming", "coding", "tech") for t in tags)

    def test_exhibition_routes_to_events(self):
        from wish_engine.l2_fulfiller import fulfill_l2
        wish = ClassifiedWish(
            wish_text="想去看exhibition", wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="place_search",
        )
        result = fulfill_l2(wish, DetectorResults())
        cats = [r.category for r in result.recommendations]
        assert any(c in ("exhibition", "photography", "gallery") for c in cats)
