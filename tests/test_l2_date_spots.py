"""Tests for DateSpotFulfiller — date spot recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_date_spots import DateSpotFulfiller, DATE_CATALOG


class TestDateCatalog:
    def test_catalog_has_15_entries(self):
        assert len(DATE_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in DATE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestDateSpotFulfiller:
    def _make_wish(self, text="想找个约会的地方") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="date_recommendation",
        )

    def test_returns_l2_result(self):
        f = DateSpotFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = DateSpotFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_quiet_dates(self):
        f = DateSpotFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("quiet", "quiet_dinner", "bookstore_cafe", "stargazing") for t in tags)

    def test_extrovert_gets_social_dates(self):
        f = DateSpotFulfiller()
        det = DetectorResults(mbti={"type": "ENFP", "dimensions": {"E_I": 0.8}})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("social", "rooftop_bar", "live_music", "comedy_show") for t in tags)

    def test_dinner_keyword(self):
        f = DateSpotFulfiller()
        result = f.fulfill(self._make_wish("want a nice dinner date"), DetectorResults())
        cats = [r.category for r in result.recommendations]
        assert "quiet_dinner" in cats

    def test_has_reminder(self):
        f = DateSpotFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = DateSpotFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
