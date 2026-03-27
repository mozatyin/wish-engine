"""Tests for ReviewsFulfiller — personality-filtered review aggregation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_reviews import ReviewsFulfiller, REVIEWS_CATALOG


class TestReviewsCatalog:
    def test_catalog_has_15_entries(self):
        assert len(REVIEWS_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in REVIEWS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestReviewsFulfiller:
    def _make_wish(self, text="想看评价") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = ReviewsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = ReviewsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_quiet_places(self):
        f = ReviewsFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish("review"), det)
        # Introvert filter should exclude loud/high-social
        for r in result.recommendations:
            assert r.category != "gym"  # gym is loud + high social

    def test_restaurant_keyword_match(self):
        f = ReviewsFulfiller()
        result = f.fulfill(self._make_wish("餐厅评价"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "restaurant" in categories

    def test_cafe_keyword_match(self):
        f = ReviewsFulfiller()
        result = f.fulfill(self._make_wish("cafe review"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "cafe" in categories

    def test_has_reminder(self):
        f = ReviewsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_no_map_data(self):
        f = ReviewsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_relevance_reason_not_empty(self):
        f = ReviewsFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
