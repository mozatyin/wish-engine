"""Tests for PregnancyLossFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_pregnancy_loss import PregnancyLossFulfiller, PREGNANCY_LOSS_CATALOG


class TestPregnancyLossCatalog:
    def test_catalog_has_10_entries(self):
        assert len(PREGNANCY_LOSS_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in PREGNANCY_LOSS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestPregnancyLossFulfiller:
    def _make_wish(self, text="I had a miscarriage") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="pregnancy_loss",
        )

    def test_returns_l2_result(self):
        f = PregnancyLossFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = PregnancyLossFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_miscarriage_keyword(self):
        f = PregnancyLossFulfiller()
        result = f.fulfill(self._make_wish("miscarriage support"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("miscarriage" in t or "loss" in t for t in tags)

    def test_chinese_keyword(self):
        f = PregnancyLossFulfiller()
        result = f.fulfill(self._make_wish("流产后很难过"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = PregnancyLossFulfiller()
        result = f.fulfill(self._make_wish("إجهاض"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = PregnancyLossFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = PregnancyLossFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
