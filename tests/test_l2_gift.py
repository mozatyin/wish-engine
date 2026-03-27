"""Tests for GiftFulfiller — love language + personality gift recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_gift import GiftFulfiller, GIFT_CATALOG


class TestGiftCatalog:
    def test_catalog_has_15_entries(self):
        assert len(GIFT_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in GIFT_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestGiftFulfiller:
    def _make_wish(self, text="想给朋友买礼物") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="gift_recommendation",
        )

    def test_returns_l2_result(self):
        f = GiftFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = GiftFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_words_of_affirmation_gets_letter(self):
        f = GiftFulfiller()
        det = DetectorResults(love_language={"primary": "words_of_affirmation"})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("letter", "poem", "card") for t in tags)

    def test_quality_time_gets_experience(self):
        f = GiftFulfiller()
        det = DetectorResults(love_language={"primary": "quality_time"})
        result = f.fulfill(self._make_wish("want an experience gift"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("experience", "shared_activity") for t in tags)

    def test_intj_gets_personal_or_meaningful(self):
        """INTJ personality matches personal/meaningful gifts via introvert+intuitive traits."""
        f = GiftFulfiller()
        det = DetectorResults(mbti={"type": "INTJ"})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("personal", "meaningful", "useful", "quiet") for t in tags)

    def test_has_reminder(self):
        f = GiftFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = GiftFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
