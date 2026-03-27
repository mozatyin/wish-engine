"""Tests for PostpartumFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_postpartum import PostpartumFulfiller, POSTPARTUM_CATALOG


class TestPostpartumCatalog:
    def test_catalog_has_10_entries(self):
        assert len(POSTPARTUM_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in POSTPARTUM_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestPostpartumFulfiller:
    def _make_wish(self, text="postpartum support") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="postpartum",
        )

    def test_returns_l2_result(self):
        f = PostpartumFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = PostpartumFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_depression_keyword(self):
        f = PostpartumFulfiller()
        result = f.fulfill(self._make_wish("postpartum depression help"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "depression" in tags or "professional" in tags

    def test_has_reminder(self):
        f = PostpartumFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = PostpartumFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_chinese_keyword(self):
        f = PostpartumFulfiller()
        result = f.fulfill(self._make_wish("产后抑郁"), DetectorResults())
        assert len(result.recommendations) >= 1
