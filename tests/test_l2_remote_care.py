"""Tests for RemoteCareFulfiller — remote monitoring and care tools."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_remote_care import RemoteCareFulfiller, REMOTE_CARE_CATALOG


class TestRemoteCareCatalog:
    def test_catalog_has_10_entries(self):
        assert len(REMOTE_CARE_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in REMOTE_CARE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_are_quiet(self):
        for item in REMOTE_CARE_CATALOG:
            assert item["noise"] == "quiet", f"{item['title']} should be quiet"


class TestRemoteCareFulfiller:
    def _make_wish(self, text="远程看护老人的工具") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="remote_care",
        )

    def test_returns_l2_result(self):
        f = RemoteCareFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = RemoteCareFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_fall_detection_keyword(self):
        f = RemoteCareFulfiller()
        result = f.fulfill(self._make_wish("fall detection for my mother"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "fall_detection" in categories

    def test_has_reminder(self):
        f = RemoteCareFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = RemoteCareFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = RemoteCareFulfiller()
        result = f.fulfill(self._make_wish("مراقبة المسنين عن بعد"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_gps_keyword(self):
        f = RemoteCareFulfiller()
        result = f.fulfill(self._make_wish("gps tracker for elderly parent"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "gps_tracker" in categories

    def test_medication_keyword(self):
        f = RemoteCareFulfiller()
        result = f.fulfill(self._make_wish("medication reminder for dad"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "medication_reminder" in categories
