"""Tests for ChronicPainFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_chronic_pain import ChronicPainFulfiller, PAIN_CATALOG


class TestPainCatalog:
    def test_catalog_has_10_entries(self):
        assert len(PAIN_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in PAIN_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_calming(self):
        for item in PAIN_CATALOG:
            assert item["mood"] == "calming", f"{item['title']} should be calming"


class TestChronicPainFulfiller:
    def _make_wish(self, text="I have chronic pain") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="chronic_pain",
        )

    def test_returns_l2_result(self):
        f = ChronicPainFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = ChronicPainFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_meditation_keyword(self):
        f = ChronicPainFulfiller()
        result = f.fulfill(self._make_wish("meditation for pain"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "meditation" in tags or "mindfulness" in tags

    def test_has_reminder(self):
        f = ChronicPainFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = ChronicPainFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_chinese_keyword(self):
        f = ChronicPainFulfiller()
        result = f.fulfill(self._make_wish("慢性疼痛怎么办"), DetectorResults())
        assert len(result.recommendations) >= 1
