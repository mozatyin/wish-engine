"""Tests for NatureHealingFulfiller — emotion-matched nature healing routes."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_nature_healing import NatureHealingFulfiller, NATURE_CATALOG


class TestNatureCatalog:
    def test_catalog_has_15_entries(self):
        assert len(NATURE_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in NATURE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestNatureHealingFulfiller:
    def _make_wish(self, text="想去自然疗愈") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="place_search",
        )

    def test_returns_l2_result(self):
        f = NatureHealingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = NatureHealingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_anxiety_matches_forest(self):
        f = NatureHealingFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        result = f.fulfill(self._make_wish("nature healing"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in ("forest_bathing", "garden_meditation", "bamboo_forest", "ancient_tree") for c in categories)

    def test_sadness_matches_beach(self):
        f = NatureHealingFulfiller()
        det = DetectorResults(emotion={"emotions": {"sadness": 0.7}})
        result = f.fulfill(self._make_wish("go to nature"), det)
        categories = [r.category for r in result.recommendations]
        assert any(c in ("beach_walk", "lake", "riverside", "coastal_cliff") for c in categories)

    def test_forest_keyword_match(self):
        f = NatureHealingFulfiller()
        result = f.fulfill(self._make_wish("想去森林"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "forest_bathing" in categories

    def test_beach_keyword_match(self):
        f = NatureHealingFulfiller()
        result = f.fulfill(self._make_wish("想去海边"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert "beach_walk" in categories

    def test_has_reminder(self):
        f = NatureHealingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = NatureHealingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
