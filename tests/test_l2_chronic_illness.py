"""Tests for ChronicIllnessFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_chronic_illness import ChronicIllnessFulfiller, ILLNESS_CATALOG


class TestIllnessCatalog:
    def test_catalog_has_12_entries(self):
        assert len(ILLNESS_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in ILLNESS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestChronicIllnessFulfiller:
    def _make_wish(self, text="I need help managing my chronic illness") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="chronic_illness",
        )

    def test_returns_l2_result(self):
        f = ChronicIllnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = ChronicIllnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_diabetes_keyword(self):
        f = ChronicIllnessFulfiller()
        result = f.fulfill(self._make_wish("help with diabetes management"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "diabetes" in tags

    def test_chinese_keyword(self):
        f = ChronicIllnessFulfiller()
        result = f.fulfill(self._make_wish("我有糖尿病需要帮助"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "diabetes" in tags

    def test_has_reminder(self):
        f = ChronicIllnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = ChronicIllnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
