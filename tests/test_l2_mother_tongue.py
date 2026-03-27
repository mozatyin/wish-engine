"""Tests for MotherTongueFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_mother_tongue import MotherTongueFulfiller, MOTHER_TONGUE_CATALOG


class TestMotherTongueCatalog:
    def test_catalog_has_10_entries(self):
        assert len(MOTHER_TONGUE_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in MOTHER_TONGUE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestMotherTongueFulfiller:
    def _make_wish(self, text="learn my mother tongue") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.LEARN_SKILL,
            level=WishLevel.L2, fulfillment_strategy="mother_tongue",
        )

    def test_returns_l2_result(self):
        f = MotherTongueFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = MotherTongueFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_bilingual_keyword(self):
        f = MotherTongueFulfiller()
        result = f.fulfill(self._make_wish("bilingual school for kids"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "bilingual" in tags or "children" in tags

    def test_immersion_keyword(self):
        f = MotherTongueFulfiller()
        result = f.fulfill(self._make_wish("language immersion program"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "immersion" in tags or "intensive" in tags

    def test_has_reminder(self):
        f = MotherTongueFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = MotherTongueFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
