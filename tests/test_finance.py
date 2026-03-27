"""Tests for FinanceFulfiller — values-based financial direction recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_finance import FinanceFulfiller, FINANCE_CATALOG, _match_candidates


class TestFinanceCatalog:
    def test_catalog_has_15_entries(self):
        assert len(FINANCE_CATALOG) >= 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags", "values_match"}
        for item in FINANCE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestFinanceFulfiller:
    def _make_wish(self, text="想学理财") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.LEARN_SKILL,
            level=WishLevel.L2, fulfillment_strategy="finance",
        )

    def test_returns_l2_result(self):
        f = FinanceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = FinanceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_security_values_boost(self):
        det = DetectorResults(values={"top_values": ["security"]})
        candidates = _match_candidates("理财", det)
        boosted = [c for c in candidates if c.get("_emotion_boost", 0) > 0]
        assert len(boosted) >= 1

    def test_debt_keyword_boost(self):
        candidates = _match_candidates("how to manage debt", DetectorResults())
        debt_item = [c for c in candidates if c["category"] == "debt_management"]
        assert len(debt_item) == 1
        assert debt_item[0].get("_emotion_boost", 0) > 0

    def test_no_map_data(self):
        f = FinanceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_has_reminder(self):
        f = FinanceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_invest_keyword_boost(self):
        candidates = _match_candidates("想学投资", DetectorResults())
        boosted = [c for c in candidates if c.get("_emotion_boost", 0) > 0]
        assert len(boosted) >= 1

    def test_stimulation_values_get_growth(self):
        f = FinanceFulfiller()
        det = DetectorResults(values={"top_values": ["stimulation"]})
        result = f.fulfill(self._make_wish("finance tips"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("growth", "entrepreneurial", "creative") for t in tags)
