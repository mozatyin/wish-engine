"""Tests for SleepEnvFulfiller — sleep environment optimization."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_sleep_env import SleepEnvFulfiller, SLEEP_CATALOG


class TestSleepCatalog:
    def test_catalog_has_15_entries(self):
        assert len(SLEEP_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in SLEEP_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestSleepEnvFulfiller:
    def _make_wish(self, text="最近失眠严重") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="sleep_recommendation",
        )

    def test_returns_l2_result(self):
        f = SleepEnvFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = SleepEnvFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_anxiety_gets_meditation(self):
        f = SleepEnvFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.7}})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("meditation", "breathing", "guided") for t in tags)

    def test_anger_gets_exercise_or_cool(self):
        f = SleepEnvFulfiller()
        det = DetectorResults(emotion={"emotions": {"anger": 0.6}})
        result = f.fulfill(self._make_wish("can't sleep, too agitated, need exercise"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("exercise", "cool", "routine") for t in tags)

    def test_meditation_keyword(self):
        f = SleepEnvFulfiller()
        result = f.fulfill(self._make_wish("sleep meditation help"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "meditation" in tags

    def test_has_reminder(self):
        f = SleepEnvFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = SleepEnvFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
