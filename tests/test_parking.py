"""Tests for ParkingFulfiller — parking spot finder."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_parking import ParkingFulfiller, PARKING_CATALOG, _match_candidates


class TestParkingCatalog:
    def test_catalog_has_10_entries(self):
        assert len(PARKING_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in PARKING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestParkingFulfiller:
    def _make_wish(self, text="I need parking") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="parking",
        )

    def test_returns_l2_result(self):
        f = ParkingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = ParkingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = ParkingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "parking"

    def test_has_reminder(self):
        f = ParkingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_free_keyword_boosts_free_parking(self):
        candidates = _match_candidates("free parking nearby", DetectorResults())
        free = [c for c in candidates if c["category"] == "free_parking"]
        assert len(free) >= 1
        assert free[0]["_emotion_boost"] > 0

    def test_ev_keyword_boosts_ev_parking(self):
        candidates = _match_candidates("EV charging parking", DetectorResults())
        ev = [c for c in candidates if c["category"] == "ev_charging_parking"]
        assert len(ev) >= 1
        assert ev[0]["_emotion_boost"] > 0

    def test_accessible_keyword_boosts_handicap(self):
        candidates = _match_candidates("accessible parking for disability", DetectorResults())
        accessible = [c for c in candidates if c["category"] == "handicap_parking"]
        assert len(accessible) >= 1
        assert accessible[0]["_emotion_boost"] > 0
