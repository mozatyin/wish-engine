"""Tests for BirthdayPlannerFulfiller — MBTI-aware birthday planning."""

import pytest
from wish_engine.models import (
    ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType,
)
from wish_engine.l2_birthday_planning import BirthdayPlannerFulfiller, BIRTHDAY_CATALOG


class TestBirthdayCatalog:
    def test_catalog_has_12_entries(self):
        assert len(BIRTHDAY_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in BIRTHDAY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestBirthdayPlannerFulfiller:
    def _make_wish(self, text="plan my birthday") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="resource_recommendation",
        )

    def test_returns_l2_result(self):
        f = BirthdayPlannerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = BirthdayPlannerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_intimate(self):
        f = BirthdayPlannerFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish("birthday celebration ideas"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in categories for c in ("intimate_dinner", "solo_treat", "cooking_party", "cultural_outing"))

    def test_surprise_keyword(self):
        f = BirthdayPlannerFulfiller()
        result = f.fulfill(self._make_wish("surprise birthday party"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "surprise_party" in categories

    def test_chinese_birthday_keyword(self):
        f = BirthdayPlannerFulfiller()
        result = f.fulfill(self._make_wish("生日怎么过"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = BirthdayPlannerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = BirthdayPlannerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_spa_birthday_keyword(self):
        f = BirthdayPlannerFulfiller()
        result = f.fulfill(self._make_wish("spa birthday treat"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "spa_birthday" in categories
