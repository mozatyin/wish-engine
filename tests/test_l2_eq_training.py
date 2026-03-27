"""Tests for EQTrainingFulfiller — EQ exercises by weak dimensions."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_eq_training import EQTrainingFulfiller, EQ_CATALOG


class TestEQCatalog:
    def test_catalog_has_12_entries(self):
        assert len(EQ_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty", "eq_dimension"}
        for item in EQ_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_12_categories(self):
        cats = {item["category"] for item in EQ_CATALOG}
        assert len(cats) == 12


class TestEQTrainingFulfiller:
    def _make_wish(self, text="提高我的情商") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="eq_training",
        )

    def test_returns_l2_result(self):
        f = EQTrainingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = EQTrainingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_low_eq_targets_all_areas(self):
        f = EQTrainingFulfiller()
        det = DetectorResults(eq={"score": 0.2})
        result = f.fulfill(self._make_wish(), det)
        assert len(result.recommendations) >= 1

    def test_low_empathy_targets_empathy(self):
        f = EQTrainingFulfiller()
        det = DetectorResults(eq={"score": 0.5, "dimensions": {"empathy": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        empathy_cats = {"perspective_taking", "active_listening_drill", "empathy_mapping"}
        assert any(c in empathy_cats for c in cats)

    def test_has_reminder(self):
        f = EQTrainingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_fragile_prefers_gentle(self):
        f = EQTrainingFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"}, eq={"score": 0.3})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        gentle_cats = {"emotion_labeling", "empathy_mapping", "emotional_vocabulary", "nonverbal_reading"}
        assert any(c in gentle_cats for c in cats)

    def test_relevance_reason_mentions_eq(self):
        f = EQTrainingFulfiller()
        det = DetectorResults(eq={"score": 0.2})
        result = f.fulfill(self._make_wish(), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("eq" in r.lower() or "growth" in r.lower() for r in reasons)
