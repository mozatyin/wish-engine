"""Tests for DocumentaryFulfiller — emotion-matched documentary recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_documentaries import DocumentaryFulfiller, DOCUMENTARY_CATALOG


class TestDocumentaryCatalog:
    def test_catalog_has_15_entries(self):
        assert len(DOCUMENTARY_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in DOCUMENTARY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestDocumentaryFulfiller:
    def _make_wish(self, text="recommend a documentary") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = DocumentaryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = DocumentaryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_curious_emotion_gets_science(self):
        f = DocumentaryFulfiller()
        det = DetectorResults(emotion={"emotions": {"curious": 0.8, "joy": 0.2}})
        result = f.fulfill(self._make_wish("纪录片推荐"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in categories for c in ("science", "technology", "space", "psychology"))

    def test_anxious_emotion_gets_nature(self):
        f = DocumentaryFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxious": 0.7, "sad": 0.2}})
        result = f.fulfill(self._make_wish("documentary"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in categories for c in ("nature", "art", "food"))

    def test_space_keyword(self):
        f = DocumentaryFulfiller()
        result = f.fulfill(self._make_wish("space documentary"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "space" in categories

    def test_has_reminder(self):
        f = DocumentaryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = DocumentaryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_true_crime_keyword(self):
        f = DocumentaryFulfiller()
        result = f.fulfill(self._make_wish("true crime documentary"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "true_crime" in categories
