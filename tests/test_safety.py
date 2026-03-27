"""Tests for Safety Scorer and SafeRouteFulfiller."""

import pytest

from wish_engine.apis.safety_scorer import (
    score_safety,
    suggest_safe_places,
    get_safety_tags,
    is_available,
)
from wish_engine.l2_safety import SafeRouteFulfiller, SAFE_CATALOG
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)


class TestSafetyScorer:
    def test_is_available_always_true(self):
        assert is_available() is True

    def test_late_night_low_score(self):
        score = score_safety(2)
        assert score <= 0.4

    def test_daytime_high_score(self):
        score = score_safety(14)
        assert score >= 0.8

    def test_female_late_night_lower(self):
        male_score = score_safety(1, is_female=False)
        female_score = score_safety(1, is_female=True)
        assert female_score < male_score

    def test_police_station_boosts(self):
        base = score_safety(2)
        boosted = score_safety(2, place_types_nearby=["police_station"])
        assert boosted > base

    def test_hospital_boosts(self):
        base = score_safety(2)
        boosted = score_safety(2, place_types_nearby=["hospital"])
        assert boosted > base

    def test_score_clamped_0_1(self):
        # Even with multiple boosts, should not exceed 1.0
        score = score_safety(12, place_types_nearby=["police_station", "hospital", "24h_store"])
        assert 0.0 <= score <= 1.0
        # Even with heavy penalties, should not go below 0.0
        score = score_safety(2, is_female=True)
        assert 0.0 <= score <= 1.0


class TestSafePlaceSuggestions:
    def test_midnight_includes_24h_places(self):
        places = suggest_safe_places(25.0, 55.0, 2)
        assert any("24h" in p for p in places)

    def test_midnight_includes_police(self):
        places = suggest_safe_places(25.0, 55.0, 2)
        assert "police_station" in places


class TestSafetyTags:
    def test_late_night_tags(self):
        tags = get_safety_tags(2)
        assert "late-night" in tags
        assert "caution" in tags

    def test_daytime_safe(self):
        tags = get_safety_tags(14)
        assert "daytime-safe" in tags

    def test_female_late_night_extra_caution(self):
        tags = get_safety_tags(2, is_female=True)
        assert "extra-caution" in tags


class TestSafeCatalog:
    def test_catalog_has_entries(self):
        assert len(SAFE_CATALOG) >= 15

    def test_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in SAFE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestSafeRouteFulfiller:
    def _make_wish(self, text="晚上回家不安全") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="safe_route",
        )

    def test_returns_l2_result(self):
        f = SafeRouteFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = SafeRouteFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None

    def test_has_reminder(self):
        f = SafeRouteFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
