"""Tests for SuicidePreventionFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_suicide_prevention import SuicidePreventionFulfiller, SUICIDE_PREVENTION_CATALOG


class TestSuicidePreventionCatalog:
    def test_catalog_has_10_entries(self):
        assert len(SUICIDE_PREVENTION_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in SUICIDE_PREVENTION_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_crisis_hotline_exists(self):
        hotline = [i for i in SUICIDE_PREVENTION_CATALOG if "hotline" in i["category"]]
        assert len(hotline) >= 1


class TestSuicidePreventionFulfiller:
    def _make_wish(self, text="I feel like ending it all") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.EMOTIONAL_SUPPORT,
            level=WishLevel.L2, fulfillment_strategy="suicide_prevention",
        )

    def test_returns_l2_result(self):
        f = SuicidePreventionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = SuicidePreventionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_prioritizes_immediate_resources(self):
        f = SuicidePreventionFulfiller()
        result = f.fulfill(self._make_wish("suicide"), DetectorResults())
        # First recommendation should be priority/immediate
        first = result.recommendations[0]
        assert any(t in ("crisis", "immediate", "priority") for t in first.tags)

    def test_chinese_keyword(self):
        f = SuicidePreventionFulfiller()
        result = f.fulfill(self._make_wish("不想活了"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = SuicidePreventionFulfiller()
        result = f.fulfill(self._make_wish("انتحار"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = SuicidePreventionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = SuicidePreventionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
