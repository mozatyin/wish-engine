"""Tests for CollectiveTraumaFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_collective_trauma import CollectiveTraumaFulfiller, COLLECTIVE_TRAUMA_CATALOG


class TestCollectiveTraumaCatalog:
    def test_catalog_has_10_entries(self):
        assert len(COLLECTIVE_TRAUMA_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in COLLECTIVE_TRAUMA_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestCollectiveTraumaFulfiller:
    def _make_wish(self, text="disaster trauma support") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="collective_trauma",
        )

    def test_returns_l2_result(self):
        f = CollectiveTraumaFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = CollectiveTraumaFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_trauma_keyword(self):
        f = CollectiveTraumaFulfiller()
        result = f.fulfill(self._make_wish("trauma counseling"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("trauma" in t for t in tags)

    def test_ptsd_keyword(self):
        f = CollectiveTraumaFulfiller()
        result = f.fulfill(self._make_wish("PTSD group therapy"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("ptsd" in t or "trauma" in t for t in tags)

    def test_chinese_keyword(self):
        f = CollectiveTraumaFulfiller()
        result = f.fulfill(self._make_wish("灾后心理支持"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = CollectiveTraumaFulfiller()
        result = f.fulfill(self._make_wish("صدمة جماعية"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_war_keyword(self):
        f = CollectiveTraumaFulfiller()
        result = f.fulfill(self._make_wish("war trauma"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("war" in t or "trauma" in t for t in tags)

    def test_has_reminder(self):
        f = CollectiveTraumaFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
