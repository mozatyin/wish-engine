"""Tests for PoetryFulfiller — emotion & culture-matched poetry recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_poetry import PoetryFulfiller, POETRY_CATALOG


class TestPoetryCatalog:
    def test_catalog_has_20_entries(self):
        assert len(POETRY_CATALOG) == 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in POETRY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestPoetryFulfiller:
    def _make_wish(self, text="想读一首诗") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = PoetryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = PoetryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_sadness_matches_grief_or_hope(self):
        f = PoetryFulfiller()
        det = DetectorResults(emotion={"emotions": {"sadness": 0.7}})
        result = f.fulfill(self._make_wish("I need poetry"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in ("grief_poetry", "hope_poetry") for c in categories)

    def test_arab_culture_matches_arabic_classical(self):
        f = PoetryFulfiller()
        det = DetectorResults(values={"culture": "arab"})
        result = f.fulfill(self._make_wish("أريد شعر"), det)
        categories = [r.category for r in result.recommendations]
        assert "arabic_classical" in categories

    def test_chinese_culture_matches_tang(self):
        f = PoetryFulfiller()
        det = DetectorResults(values={"culture": "chinese"})
        result = f.fulfill(self._make_wish("想读唐诗"), det)
        categories = [r.category for r in result.recommendations]
        assert "chinese_tang" in categories

    def test_has_reminder(self):
        f = PoetryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_no_map_data(self):
        f = PoetryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_relevance_reason_not_empty(self):
        f = PoetryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
