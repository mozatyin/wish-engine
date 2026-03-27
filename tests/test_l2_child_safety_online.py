"""Tests for ChildSafetyOnlineFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_child_safety_online import ChildSafetyOnlineFulfiller, CHILD_SAFETY_CATALOG


class TestChildSafetyCatalog:
    def test_catalog_has_10_entries(self):
        assert len(CHILD_SAFETY_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in CHILD_SAFETY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestChildSafetyOnlineFulfiller:
    def _make_wish(self, text="child safety online") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="child_safety_online",
        )

    def test_returns_l2_result(self):
        f = ChildSafetyOnlineFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = ChildSafetyOnlineFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_parental_control_keyword(self):
        f = ChildSafetyOnlineFulfiller()
        result = f.fulfill(self._make_wish("parental control setup"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "controls" in tags or "setup" in tags

    def test_screen_time_keyword(self):
        f = ChildSafetyOnlineFulfiller()
        result = f.fulfill(self._make_wish("screen time management"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "screen_time" in tags or "management" in tags

    def test_has_reminder(self):
        f = ChildSafetyOnlineFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = ChildSafetyOnlineFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
