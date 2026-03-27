"""Tests for CulturalRecoveryFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_cultural_recovery import CulturalRecoveryFulfiller, CULTURAL_RECOVERY_CATALOG


class TestCulturalRecoveryCatalog:
    def test_catalog_has_10_entries(self):
        assert len(CULTURAL_RECOVERY_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in CULTURAL_RECOVERY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestCulturalRecoveryFulfiller:
    def _make_wish(self, text="cultural recovery and traditions") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="cultural_recovery",
        )

    def test_returns_l2_result(self):
        f = CulturalRecoveryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = CulturalRecoveryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_ceremony_keyword(self):
        f = CulturalRecoveryFulfiller()
        result = f.fulfill(self._make_wish("traditional ceremony"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "ceremony" in tags or "spiritual" in tags

    def test_revival_keyword(self):
        f = CulturalRecoveryFulfiller()
        result = f.fulfill(self._make_wish("cultural revival movement"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "revival" in tags or "movement" in tags

    def test_has_reminder(self):
        f = CulturalRecoveryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = CulturalRecoveryFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_chinese_keyword(self):
        f = CulturalRecoveryFulfiller()
        result = f.fulfill(self._make_wish("传统文化复兴"), DetectorResults())
        assert len(result.recommendations) >= 1
