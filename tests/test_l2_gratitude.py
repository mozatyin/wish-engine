"""Tests for GratitudeFulfiller — love-language-matched gratitude expressions."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_gratitude import GratitudeFulfiller, GRATITUDE_CATALOG


class TestGratitudeCatalog:
    def test_catalog_has_12_entries(self):
        assert len(GRATITUDE_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in GRATITUDE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestGratitudeFulfiller:
    def _make_wish(self, text="想表达感恩") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="gratitude",
        )

    def test_returns_l2_result(self):
        f = GratitudeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = GratitudeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_letter_keyword_match(self):
        f = GratitudeFulfiller()
        result = f.fulfill(self._make_wish("write a thank you letter"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "handwritten_letter" in categories

    def test_love_language_words_of_affirmation(self):
        f = GratitudeFulfiller()
        det = DetectorResults(love_language={"primary": "words_of_affirmation"})
        result = f.fulfill(self._make_wish("want to express gratitude"), det)
        # Should include word-based expressions
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = GratitudeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = GratitudeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_arabic_keyword(self):
        f = GratitudeFulfiller()
        result = f.fulfill(self._make_wish("شكر وتقدير"), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)

    def test_no_map_data(self):
        f = GratitudeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None
