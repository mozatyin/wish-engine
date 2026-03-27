"""Tests for MindfulnessFulfiller — meditation/mindfulness calendar."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_mindfulness import MindfulnessFulfiller, MINDFULNESS_CATALOG


class TestMindfulnessCatalog:
    def test_catalog_has_15_entries(self):
        assert len(MINDFULNESS_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "mood", "durations"}
        for item in MINDFULNESS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_durations_are_valid(self):
        for item in MINDFULNESS_CATALOG:
            for d in item["durations"]:
                assert d in (5, 10, 20), f"{item['title']} has invalid duration {d}"


class TestMindfulnessFulfiller:
    def _make_wish(self, text="想冥想") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="mindfulness",
        )

    def test_returns_l2_result(self):
        f = MindfulnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = MindfulnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_anxiety_boosts_anxiety_practices(self):
        f = MindfulnessFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        result = f.fulfill(self._make_wish("help me calm down"), det)
        assert len(result.recommendations) >= 1

    def test_sleep_keyword_boosts_sleep_meditation(self):
        f = MindfulnessFulfiller()
        result = f.fulfill(self._make_wish("I can't sleep"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("sleep", "relaxation") for t in tags)

    def test_has_reminder(self):
        f = MindfulnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_for_sleep(self):
        f = MindfulnessFulfiller()
        result = f.fulfill(self._make_wish("失眠"), DetectorResults())
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("sleep" in r.lower() for r in reasons)

    def test_no_map_data(self):
        f = MindfulnessFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None
