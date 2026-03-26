"""Tests for CareerFulfiller — career direction with values + MBTI matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_career import CareerFulfiller, CAREER_CATALOG


class TestCareerCatalog:
    def test_catalog_not_empty(self):
        assert len(CAREER_CATALOG) >= 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in CAREER_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestCareerFulfiller:
    def _make_wish(self, text="想换个工作") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.CAREER_DIRECTION,
            level=WishLevel.L2, fulfillment_strategy="career_guidance",
        )

    def test_returns_l2_result(self):
        f = CareerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_self_direction_values(self):
        f = CareerFulfiller()
        det = DetectorResults(values={"top_values": ["self-direction", "stimulation"]})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("self-direction", "autonomous", "entrepreneurship") for t in tags)

    def test_benevolence_values(self):
        f = CareerFulfiller()
        det = DetectorResults(values={"top_values": ["benevolence", "universalism"]})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("helping", "social-impact", "benevolence") for t in tags)

    def test_max_3(self):
        f = CareerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = CareerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
