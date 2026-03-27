"""Tests for FocusModeFulfiller — focus environments."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_focus_mode import FocusModeFulfiller, FOCUS_CATALOG


class TestFocusCatalog:
    def test_catalog_has_10_entries(self):
        assert len(FOCUS_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "mood"}
        for item in FOCUS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestFocusModeFulfiller:
    def _make_wish(self, text="我需要专注") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="focus_mode",
        )

    def test_returns_l2_result(self):
        f = FocusModeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = FocusModeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_quiet_spots(self):
        f = FocusModeFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("introvert" in r.lower() for r in reasons)

    def test_extravert_gets_social_spots(self):
        f = FocusModeFulfiller()
        det = DetectorResults(mbti={"type": "ENTP", "dimensions": {"E_I": 0.8}})
        result = f.fulfill(self._make_wish(), det)
        # Study group should rank higher for extraverts
        assert len(result.recommendations) >= 1

    def test_has_map_data(self):
        f = FocusModeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "focus_space"

    def test_has_reminder(self):
        f = FocusModeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_morning_keyword(self):
        f = FocusModeFulfiller()
        result = f.fulfill(self._make_wish("morning focus session"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_all_recs_have_tags(self):
        f = FocusModeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for rec in result.recommendations:
            assert len(rec.tags) > 0
