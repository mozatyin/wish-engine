"""Tests for CravingAlternativeFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_craving_alternatives import CravingAlternativeFulfiller, CRAVING_CATALOG


class TestCravingCatalog:
    def test_catalog_has_12_entries(self):
        assert len(CRAVING_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in CRAVING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestCravingAlternativeFulfiller:
    def _make_wish(self, text="I have a craving right now") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="craving_alternatives",
        )

    def test_returns_l2_result(self):
        f = CravingAlternativeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = CravingAlternativeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_craving_keyword(self):
        f = CravingAlternativeFulfiller()
        result = f.fulfill(self._make_wish("craving alcohol"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("craving" in t for t in tags)

    def test_chinese_keyword(self):
        f = CravingAlternativeFulfiller()
        result = f.fulfill(self._make_wish("想喝酒"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = CravingAlternativeFulfiller()
        result = f.fulfill(self._make_wish("رغبة شديدة"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_urge_keyword(self):
        f = CravingAlternativeFulfiller()
        result = f.fulfill(self._make_wish("I have an urge"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = CravingAlternativeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
