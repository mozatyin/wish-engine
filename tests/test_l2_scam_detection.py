"""Tests for ScamDetectionFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_scam_detection import ScamDetectionFulfiller, SCAM_CATALOG


class TestScamCatalog:
    def test_catalog_has_10_entries(self):
        assert len(SCAM_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in SCAM_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestScamDetectionFulfiller:
    def _make_wish(self, text="I think I got scammed") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="scam_detection",
        )

    def test_returns_l2_result(self):
        f = ScamDetectionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = ScamDetectionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_phishing_keyword(self):
        f = ScamDetectionFulfiller()
        result = f.fulfill(self._make_wish("phishing email detection"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "phishing" in tags or "email" in tags

    def test_deepfake_keyword(self):
        f = ScamDetectionFulfiller()
        result = f.fulfill(self._make_wish("is this a deepfake"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "deepfake" in tags or "ai" in tags

    def test_has_reminder(self):
        f = ScamDetectionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = ScamDetectionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_chinese_keyword(self):
        f = ScamDetectionFulfiller()
        result = f.fulfill(self._make_wish("这是不是诈骗"), DetectorResults())
        assert len(result.recommendations) >= 1
