"""Tests for DomesticViolenceFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_domestic_violence import DomesticViolenceFulfiller, DV_CATALOG


class TestDVCatalog:
    def test_catalog_has_10_entries(self):
        assert len(DV_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in DV_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_hotline_exists(self):
        hotline = [i for i in DV_CATALOG if "hotline" in i["category"]]
        assert len(hotline) >= 1


class TestDomesticViolenceFulfiller:
    def _make_wish(self, text="He keeps hitting me") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.EMOTIONAL_SUPPORT,
            level=WishLevel.L2, fulfillment_strategy="domestic_violence",
        )

    def test_returns_l2_result(self):
        f = DomesticViolenceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = DomesticViolenceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_prioritizes_safety(self):
        f = DomesticViolenceFulfiller()
        result = f.fulfill(self._make_wish("domestic violence help"), DetectorResults())
        first = result.recommendations[0]
        assert any(t in ("priority", "immediate", "dv") for t in first.tags)

    def test_chinese_keyword(self):
        f = DomesticViolenceFulfiller()
        result = f.fulfill(self._make_wish("家暴"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = DomesticViolenceFulfiller()
        result = f.fulfill(self._make_wish("عنف أسري"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = DomesticViolenceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = DomesticViolenceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
