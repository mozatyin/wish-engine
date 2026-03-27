"""Tests for BehavioralAddictionFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_behavioral_addiction import BehavioralAddictionFulfiller, BEHAVIORAL_ADDICTION_CATALOG


class TestBehavioralAddictionCatalog:
    def test_catalog_has_10_entries(self):
        assert len(BEHAVIORAL_ADDICTION_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in BEHAVIORAL_ADDICTION_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestBehavioralAddictionFulfiller:
    def _make_wish(self, text="I think I have a gambling problem") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="behavioral_addiction",
        )

    def test_returns_l2_result(self):
        f = BehavioralAddictionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = BehavioralAddictionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_gambling_keyword(self):
        f = BehavioralAddictionFulfiller()
        result = f.fulfill(self._make_wish("gambling addiction"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("gambling" in t or "behavioral" in t for t in tags)

    def test_gaming_keyword(self):
        f = BehavioralAddictionFulfiller()
        result = f.fulfill(self._make_wish("gaming addiction help"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("gaming" in t or "behavioral" in t for t in tags)

    def test_chinese_keyword(self):
        f = BehavioralAddictionFulfiller()
        result = f.fulfill(self._make_wish("赌博成瘾"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = BehavioralAddictionFulfiller()
        result = f.fulfill(self._make_wish("قمار"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = BehavioralAddictionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
