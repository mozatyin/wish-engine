"""Tests for PhotoSpotFulfiller — time/weather-aware photo spot recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_photo_spots import PhotoSpotFulfiller, PHOTO_SPOT_CATALOG


class TestPhotoSpotCatalog:
    def test_catalog_has_15_entries(self):
        assert len(PHOTO_SPOT_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in PHOTO_SPOT_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestPhotoSpotFulfiller:
    def _make_wish(self, text="想去拍照") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="place_search",
        )

    def test_returns_l2_result(self):
        f = PhotoSpotFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = PhotoSpotFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_cherry_blossom_keyword(self):
        f = PhotoSpotFulfiller()
        result = f.fulfill(self._make_wish("想拍樱花"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "cherry_blossom" in categories

    def test_golden_hour_keyword(self):
        f = PhotoSpotFulfiller()
        result = f.fulfill(self._make_wish("golden hour photography"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "golden_hour_spot" in categories

    def test_neon_keyword(self):
        f = PhotoSpotFulfiller()
        result = f.fulfill(self._make_wish("neon night photography"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "neon_night" in categories

    def test_has_reminder(self):
        f = PhotoSpotFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = PhotoSpotFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_instagram_keyword(self):
        f = PhotoSpotFulfiller()
        result = f.fulfill(self._make_wish("instagram worthy spots"), DetectorResults())
        assert len(result.recommendations) >= 1
