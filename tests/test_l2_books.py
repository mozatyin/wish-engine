"""Tests for BookFulfiller — book recommendations with personality matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_books import BookFulfiller, BOOK_CATALOG


class TestBookCatalog:
    def test_catalog_not_empty(self):
        assert len(BOOK_CATALOG) >= 30

    def test_each_entry_has_required_fields(self):
        required = {"title", "author", "description", "category", "topic", "tags"}
        for book in BOOK_CATALOG:
            missing = required - set(book.keys())
            assert not missing, f"{book['title']} missing: {missing}"


class TestBookFulfiller:
    def _make_wish(self, text="想读一本关于心理学的书") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_no_map_data(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_attachment_wish_finds_attachment_books(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish("想了解依恋理论"), DetectorResults())
        topics = []
        for r in result.recommendations:
            topics.extend(r.tags)
        assert any("attachment" in t for t in topics)

    def test_meditation_wish_finds_mindfulness_books(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish("想学冥想"), DetectorResults())
        topics = []
        for r in result.recommendations:
            topics.extend(r.tags)
        assert any(t in ("meditation", "mindfulness") for t in topics)

    def test_tradition_values_boost_traditional_books(self):
        f = BookFulfiller()
        det = DetectorResults(values={"top_values": ["tradition"]})
        result = f.fulfill(self._make_wish("想了解冥想"), det)
        assert any("traditional" in r.tags for r in result.recommendations)

    def test_max_3_recommendations(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = BookFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_mentions_profile(self):
        f = BookFulfiller()
        det = DetectorResults(attachment={"style": "anxious"})
        result = f.fulfill(self._make_wish("想了解依恋"), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any(len(r) > 10 for r in reasons)
