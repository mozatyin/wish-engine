"""Tests for DebtCrisisFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_debt_crisis import DebtCrisisFulfiller, DEBT_CRISIS_CATALOG


class TestDebtCrisisCatalog:
    def test_catalog_has_10_entries(self):
        assert len(DEBT_CRISIS_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in DEBT_CRISIS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestDebtCrisisFulfiller:
    def _make_wish(self, text="I am drowning in debt") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="debt_crisis",
        )

    def test_returns_l2_result(self):
        f = DebtCrisisFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = DebtCrisisFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_debt_keyword(self):
        f = DebtCrisisFulfiller()
        result = f.fulfill(self._make_wish("debt counseling"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("debt" in t for t in tags)

    def test_bankruptcy_keyword(self):
        f = DebtCrisisFulfiller()
        result = f.fulfill(self._make_wish("considering bankruptcy"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("bankruptcy" in t or "debt" in t for t in tags)

    def test_chinese_keyword(self):
        f = DebtCrisisFulfiller()
        result = f.fulfill(self._make_wish("债务危机"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = DebtCrisisFulfiller()
        result = f.fulfill(self._make_wish("ديون كثيرة"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = DebtCrisisFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
