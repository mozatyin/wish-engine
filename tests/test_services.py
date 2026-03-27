"""Tests for LocalServiceFulfiller — local service finder."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_services import LocalServiceFulfiller, SERVICES_CATALOG, _match_candidates


class TestServicesCatalog:
    def test_catalog_has_15_entries(self):
        assert len(SERVICES_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in SERVICES_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestLocalServiceFulfiller:
    def _make_wish(self, text="I need to print something") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="local_service",
        )

    def test_returns_l2_result(self):
        f = LocalServiceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = LocalServiceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = LocalServiceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "local_service"

    def test_has_reminder(self):
        f = LocalServiceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_print_keyword_boosts_print_shop(self):
        candidates = _match_candidates("I need to print documents", DetectorResults())
        print_shops = [c for c in candidates if c["category"] == "print_shop"]
        assert len(print_shops) >= 1
        assert print_shops[0]["_emotion_boost"] > 0

    def test_urgent_keyword_boosts_urgent_services(self):
        candidates = _match_candidates("urgent phone repair", DetectorResults())
        repair = [c for c in candidates if c["category"] == "phone_repair"]
        assert len(repair) >= 1
        assert repair[0]["_emotion_boost"] > 0

    def test_laundry_keyword_matching(self):
        candidates = _match_candidates("我需要洗衣服", DetectorResults())
        laundry = [c for c in candidates if c["category"] == "laundry"]
        assert len(laundry) >= 1
        assert laundry[0]["_emotion_boost"] > 0
