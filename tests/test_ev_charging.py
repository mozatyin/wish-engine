"""Tests for EVChargingFulfiller — EV charging and gas station finder."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_ev_charging import EVChargingFulfiller, EV_CATALOG, _match_candidates


class TestEVCatalog:
    def test_catalog_has_10_entries(self):
        assert len(EV_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in EV_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestEVChargingFulfiller:
    def _make_wish(self, text="I need to charge my EV") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="ev_charging",
        )

    def test_returns_l2_result(self):
        f = EVChargingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = EVChargingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = EVChargingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "ev_charging"

    def test_has_reminder(self):
        f = EVChargingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_ev_keyword_deprioritizes_gas(self):
        candidates = _match_candidates("I need to charge my electric car", DetectorResults())
        gas = [c for c in candidates if c["category"] == "gas_station"]
        ev = [c for c in candidates if c["category"] == "fast_charger"]
        assert gas[0]["_emotion_boost"] < ev[0]["_emotion_boost"]

    def test_gas_keyword_deprioritizes_ev(self):
        candidates = _match_candidates("I need to refuel gas", DetectorResults())
        gas = [c for c in candidates if c["category"] == "gas_station"]
        ev_slow = [c for c in candidates if c["category"] == "slow_charger"]
        assert gas[0]["_emotion_boost"] > ev_slow[0]["_emotion_boost"]

    def test_cafe_keyword_boosts_charging_cafe(self):
        candidates = _match_candidates("charge my car at a cafe", DetectorResults())
        cafe = [c for c in candidates if c["category"] == "charging_cafe"]
        assert len(cafe) >= 1
        assert cafe[0]["_emotion_boost"] > 0
