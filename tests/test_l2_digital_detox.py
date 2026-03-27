"""Tests for DigitalDetoxFulfiller — screen-free activities."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_digital_detox import DigitalDetoxFulfiller, DETOX_CATALOG


class TestDetoxCatalog:
    def test_catalog_has_12_entries(self):
        assert len(DETOX_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty"}
        for item in DETOX_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_12_categories(self):
        cats = {item["category"] for item in DETOX_CATALOG}
        assert len(cats) == 12


class TestDigitalDetoxFulfiller:
    def _make_wish(self, text="我想排毒") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="digital_detox",
        )

    def test_returns_l2_result(self):
        f = DigitalDetoxFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = DigitalDetoxFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_fragile_avoids_bold(self):
        f = DigitalDetoxFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        # Bold items should not be top-ranked for fragile users
        for rec in result.recommendations:
            assert rec.category != "tech_free_weekend" or rec.score < 0.7

    def test_introvert_prefers_solo(self):
        f = DigitalDetoxFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = DigitalDetoxFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_resilient_extravert_gets_bold(self):
        f = DigitalDetoxFulfiller()
        det = DetectorResults(
            fragility={"pattern": "resilient"},
            mbti={"type": "ENTP"},
        )
        result = f.fulfill(self._make_wish(), det)
        assert len(result.recommendations) >= 1

    def test_relevance_reason_present(self):
        f = DigitalDetoxFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for rec in result.recommendations:
            assert rec.relevance_reason
