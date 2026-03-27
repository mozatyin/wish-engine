"""Tests for BereavementFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_bereavement import BereavementFulfiller, BEREAVEMENT_CATALOG


class TestBereavementCatalog:
    def test_catalog_has_12_entries(self):
        assert len(BEREAVEMENT_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in BEREAVEMENT_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestBereavementFulfiller:
    def _make_wish(self, text="I lost my father") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="bereavement",
        )

    def test_returns_l2_result(self):
        f = BereavementFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = BereavementFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_grief_keyword_matches(self):
        f = BereavementFulfiller()
        result = f.fulfill(self._make_wish("I need grief support"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("grief" in t for t in tags)

    def test_chinese_keyword_matches(self):
        f = BereavementFulfiller()
        result = f.fulfill(self._make_wish("丧亲之痛"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword_matches(self):
        f = BereavementFulfiller()
        result = f.fulfill(self._make_wish("فقدان أحد الأحباء"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = BereavementFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = BereavementFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
