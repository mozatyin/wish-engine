"""Tests for Google Places API integration."""

import pytest
from unittest.mock import patch, MagicMock
from wish_engine.apis.places_api import nearby_search, place_details, is_available
from wish_engine.apis.places_personality import (
    enrich_place,
    enrich_places,
    wish_to_search_params,
)


class TestPlacesApiAvailability:
    def test_not_available_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert not is_available()

    def test_available_with_key(self):
        with patch.dict("os.environ", {"GOOGLE_PLACES_API_KEY": "test-key"}):
            assert is_available()

    def test_nearby_search_returns_empty_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            results = nearby_search(25.0, 55.0)
            assert results == []

    def test_place_details_returns_none_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            result = place_details("some_place_id")
            assert result is None


class TestPlacesPersonality:
    def test_enrich_park(self):
        place = {"name": "City Park", "types": ["park"], "vicinity": "123 Main St", "rating": 4.5}
        enriched = enrich_place(place)
        assert enriched["noise"] == "quiet"
        assert enriched["social"] == "low"
        assert enriched["mood"] == "calming"
        assert "nature" in enriched["tags"]
        assert "highly-rated" in enriched["tags"]

    def test_enrich_gym(self):
        place = {"name": "Iron Gym", "types": ["gym"], "rating": 3.8}
        enriched = enrich_place(place)
        assert enriched["noise"] == "loud"
        assert enriched["social"] == "high"
        assert "exercise" in enriched["tags"]

    def test_enrich_cafe(self):
        place = {"name": "Quiet Beans", "types": ["cafe", "food"], "rating": 4.2}
        enriched = enrich_place(place)
        assert enriched["noise"] == "moderate"
        assert "coffee" in enriched["tags"]
        assert "well-rated" in enriched["tags"]

    def test_enrich_unknown_type(self):
        place = {"name": "Mystery", "types": ["unknown_type"], "rating": 3.0}
        enriched = enrich_place(place)
        assert enriched["noise"] == "moderate"  # default
        assert enriched["social"] == "medium"  # default
        assert enriched["category"] == "unknown_type"  # first type used

    def test_enrich_preserves_place_id(self):
        place = {"name": "X", "types": ["park"], "place_id": "abc123"}
        enriched = enrich_place(place)
        assert enriched["_place_id"] == "abc123"

    def test_enrich_preserves_geometry(self):
        place = {"name": "X", "types": ["park"], "geometry": {"location": {"lat": 25.1, "lng": 55.2}}}
        enriched = enrich_place(place)
        assert enriched["_lat"] == 25.1
        assert enriched["_lng"] == 55.2

    def test_enrich_multiple(self):
        places = [
            {"name": "Park", "types": ["park"]},
            {"name": "Gym", "types": ["gym"]},
        ]
        enriched = enrich_places(places)
        assert len(enriched) == 2
        assert enriched[0]["noise"] == "quiet"
        assert enriched[1]["noise"] == "loud"

    def test_mosque_mapping(self):
        place = {"name": "Grand Mosque", "types": ["mosque"], "rating": 4.8}
        enriched = enrich_place(place)
        assert enriched["noise"] == "quiet"
        assert "spiritual" in enriched["tags"]
        assert "traditional" in enriched["tags"]
        assert "highly-rated" in enriched["tags"]

    def test_empty_types(self):
        place = {"name": "NoType", "types": []}
        enriched = enrich_place(place)
        assert enriched["category"] == "place"

    def test_no_vicinity(self):
        place = {"name": "Solo", "types": ["park"]}
        enriched = enrich_place(place)
        assert enriched["description"] == "Solo"

    def test_with_vicinity(self):
        place = {"name": "Solo", "types": ["park"], "vicinity": "Main St"}
        enriched = enrich_place(place)
        assert "Main St" in enriched["description"]


class TestWishToSearchParams:
    def test_meditation_maps_to_spa(self):
        params = wish_to_search_params("想学冥想")
        assert params.get("place_type") == "spa"

    def test_exercise_maps_to_gym(self):
        params = wish_to_search_params("想多运动")
        assert params.get("place_type") == "gym"

    def test_quiet_maps_to_park(self):
        params = wish_to_search_params("想找个安静的地方")
        assert params.get("place_type") == "park"

    def test_arabic_mosque(self):
        params = wish_to_search_params("أريد الذهاب إلى مسجد")
        assert params.get("place_type") == "mosque"

    def test_english_library(self):
        params = wish_to_search_params("I want to find a library")
        assert params.get("place_type") == "library"

    def test_unknown_returns_empty(self):
        params = wish_to_search_params("hello world")
        assert params == {}

    def test_case_insensitive(self):
        params = wish_to_search_params("I need a GYM")
        assert params.get("place_type") == "gym"


class TestPlaceFulfillerWithApi:
    """Test PlaceFulfiller uses API when available."""

    def test_falls_back_to_catalog_without_api(self):
        """Without API key, should use static catalog."""
        from wish_engine.l2_places import PlaceFulfiller
        from wish_engine.models import ClassifiedWish, DetectorResults, WishLevel, WishType
        f = PlaceFulfiller()
        wish = ClassifiedWish(
            wish_text="想找个安静地方", wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="place_search",
        )
        with patch.dict("os.environ", {}, clear=True):
            result = f.fulfill(wish, DetectorResults())
        assert len(result.recommendations) >= 1

    def test_falls_back_without_location(self):
        """With API key but no location, should use static catalog."""
        from wish_engine.l2_places import PlaceFulfiller
        from wish_engine.models import ClassifiedWish, DetectorResults, WishLevel, WishType
        f = PlaceFulfiller()
        wish = ClassifiedWish(
            wish_text="想找个安静地方", wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="place_search",
        )
        with patch.dict("os.environ", {"GOOGLE_PLACES_API_KEY": "test-key"}):
            result = f.fulfill(wish, DetectorResults())
        assert len(result.recommendations) >= 1

    @patch("wish_engine.apis.places_api.nearby_search")
    @patch("wish_engine.apis.places_api.is_available", return_value=True)
    def test_uses_api_when_available(self, mock_avail, mock_search):
        """With API key + location, should use Google Places."""
        mock_search.return_value = [
            {"name": "Zen Garden", "types": ["spa"], "vicinity": "123 Peace St", "rating": 4.7, "place_id": "p1",
             "geometry": {"location": {"lat": 25.1, "lng": 55.2}}},
            {"name": "Loud Gym", "types": ["gym"], "vicinity": "456 Iron St", "rating": 4.0, "place_id": "p2",
             "geometry": {"location": {"lat": 25.1, "lng": 55.2}}},
        ]
        from wish_engine.l2_places import PlaceFulfiller
        from wish_engine.models import ClassifiedWish, DetectorResults, WishLevel, WishType
        f = PlaceFulfiller()
        wish = ClassifiedWish(
            wish_text="想学冥想", wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="place_search",
        )
        result = f.fulfill(wish, DetectorResults(), location=(25.0, 55.0))
        assert len(result.recommendations) >= 1
        mock_search.assert_called_once()

    @patch("wish_engine.apis.places_api.nearby_search")
    @patch("wish_engine.apis.places_api.is_available", return_value=True)
    def test_falls_back_when_api_returns_empty(self, mock_avail, mock_search):
        """If API returns empty results, fall back to static catalog."""
        mock_search.return_value = []
        from wish_engine.l2_places import PlaceFulfiller
        from wish_engine.models import ClassifiedWish, DetectorResults, WishLevel, WishType
        f = PlaceFulfiller()
        wish = ClassifiedWish(
            wish_text="想找个安静地方", wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="place_search",
        )
        result = f.fulfill(wish, DetectorResults(), location=(25.0, 55.0))
        assert len(result.recommendations) >= 1
        # Should have tried the API
        mock_search.assert_called_once()
