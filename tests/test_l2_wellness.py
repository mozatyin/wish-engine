"""Tests for WellnessFulfiller — wellness with emotion + fragility matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_wellness import WellnessFulfiller, WELLNESS_CATALOG


class TestWellnessCatalog:
    def test_catalog_not_empty(self):
        assert len(WELLNESS_CATALOG) >= 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "mood"}
        for item in WELLNESS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestWellnessFulfiller:
    def _make_wish(self, text="最近总失眠") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="wellness_recommendation",
        )

    def test_returns_l2_result(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_anxiety_gets_calming(self):
        f = WellnessFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        result = f.fulfill(self._make_wish("想减轻焦虑"), det)
        for rec in result.recommendations:
            assert "intense" not in rec.tags

    def test_sleep_wish_finds_sleep_items(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish("最近总失眠"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("sleep", "relaxation", "calming") for t in tags)

    def test_exercise_wish(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish("想多运动"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("exercise", "movement", "fitness") for t in tags)

    def test_max_3(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = WellnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
