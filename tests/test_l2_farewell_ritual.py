"""Tests for FarewellRitualFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_farewell_ritual import FarewellRitualFulfiller, FAREWELL_RITUAL_CATALOG


class TestFarewellRitualCatalog:
    def test_catalog_has_10_entries(self):
        assert len(FAREWELL_RITUAL_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in FAREWELL_RITUAL_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestFarewellRitualFulfiller:
    def _make_wish(self, text="I need to plan a farewell") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="farewell_ritual",
        )

    def test_returns_l2_result(self):
        f = FarewellRitualFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = FarewellRitualFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_farewell_keyword(self):
        f = FarewellRitualFulfiller()
        result = f.fulfill(self._make_wish("farewell ceremony"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("ritual" in t for t in tags)

    def test_chinese_keyword(self):
        f = FarewellRitualFulfiller()
        result = f.fulfill(self._make_wish("告别仪式"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = FarewellRitualFulfiller()
        result = f.fulfill(self._make_wish("وداع"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_memorial_keyword(self):
        f = FarewellRitualFulfiller()
        result = f.fulfill(self._make_wish("memorial service"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("memorial" in t or "ritual" in t for t in tags)

    def test_has_reminder(self):
        f = FarewellRitualFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
