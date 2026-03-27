"""Tests for ProgressGroupFulfiller — accountability group matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_progress_groups import (
    ProgressGroupFulfiller,
    PROGRESS_CATALOG,
    _mbti_group_size_filter,
)


class TestProgressCatalog:
    def test_catalog_has_20_entries(self):
        assert len(PROGRESS_CATALOG) == 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "group_size", "noise", "social", "mood", "tags"}
        for item in PROGRESS_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_catalog_has_group_sizes(self):
        sizes = {item["group_size"] for item in PROGRESS_CATALOG}
        assert "small" in sizes
        assert "medium" in sizes or "large" in sizes


class TestProgressGroupFulfiller:
    def _make_wish(self, text="想加入打卡小组") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_COMPANION,
            level=WishLevel.L2, fulfillment_strategy="progress_group",
        )

    def test_returns_l2_result(self):
        f = ProgressGroupFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_introvert_gets_small_groups(self):
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        filtered = _mbti_group_size_filter([dict(i) for i in PROGRESS_CATALOG], det)
        for item in filtered:
            assert item["group_size"] == "small"

    def test_extravert_gets_larger_groups(self):
        det = DetectorResults(mbti={"type": "ENFJ", "dimensions": {"E_I": 0.8}})
        filtered = _mbti_group_size_filter([dict(i) for i in PROGRESS_CATALOG], det)
        for item in filtered:
            assert item["group_size"] in ("medium", "large")

    def test_max_3(self):
        f = ProgressGroupFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = ProgressGroupFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_no_map_data(self):
        """Progress groups are virtual — no map data needed."""
        f = ProgressGroupFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_no_mbti_returns_all(self):
        det = DetectorResults()
        filtered = _mbti_group_size_filter([dict(i) for i in PROGRESS_CATALOG], det)
        assert len(filtered) == len(PROGRESS_CATALOG)
