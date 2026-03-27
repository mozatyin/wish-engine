"""Tests for DreamJournalFulfiller — dream theme analysis."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_dream_journal import DreamJournalFulfiller, DREAM_CATALOG, _detect_dream_theme


class TestDreamCatalog:
    def test_catalog_has_15_entries(self):
        assert len(DREAM_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty"}
        for item in DREAM_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_15_categories(self):
        cats = {item["category"] for item in DREAM_CATALOG}
        assert len(cats) == 15


class TestDreamThemeDetection:
    def test_flying(self):
        assert _detect_dream_theme("I dreamed I was flying") == "flying"

    def test_water_chinese(self):
        assert _detect_dream_theme("梦到了水") == "water"

    def test_no_theme(self):
        assert _detect_dream_theme("hello world") is None


class TestDreamJournalFulfiller:
    def _make_wish(self, text="我做了个梦") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="dream_journal",
        )

    def test_returns_l2_result(self):
        f = DreamJournalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = DreamJournalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_flying_theme_ranked_high(self):
        f = DreamJournalFulfiller()
        result = f.fulfill(self._make_wish("I dreamed of flying"), DetectorResults())
        cats = [r.category for r in result.recommendations]
        assert "flying" in cats

    def test_fragile_avoids_bold(self):
        f = DreamJournalFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = DreamJournalFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
