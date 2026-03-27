"""Tests for InterestCircleFulfiller — niche hobby interest circle matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_interest_circles import (
    InterestCircleFulfiller,
    INTEREST_CATALOG,
    _mbti_group_filter,
)


class TestInterestCatalog:
    def test_catalog_has_20_entries(self):
        assert len(INTEREST_CATALOG) == 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "group_size", "noise", "social", "mood", "tags"}
        for item in INTEREST_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_catalog_has_diverse_tags(self):
        all_tags = set()
        for item in INTEREST_CATALOG:
            all_tags.update(item.get("tags", []))
        for expected in ["quiet", "social", "creative", "outdoor", "intellectual", "physical", "traditional", "modern"]:
            assert expected in all_tags, f"Missing tag: {expected}"


class TestInterestCircleFulfiller:
    def _make_wish(self, text="想找兴趣圈子") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="interest_circle",
        )

    def test_returns_l2_result(self):
        f = InterestCircleFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_introvert_gets_small_groups(self):
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        filtered = _mbti_group_filter([dict(i) for i in INTEREST_CATALOG], det)
        for item in filtered:
            assert item["group_size"] in ("small", "medium")

    def test_extravert_gets_larger_groups(self):
        det = DetectorResults(mbti={"type": "ENFP", "dimensions": {"E_I": 0.8}})
        filtered = _mbti_group_filter([dict(i) for i in INTEREST_CATALOG], det)
        for item in filtered:
            assert item["group_size"] in ("medium", "large")

    def test_max_3(self):
        f = InterestCircleFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = InterestCircleFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_has_map_data(self):
        f = InterestCircleFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "community_center"

    def test_no_mbti_returns_all(self):
        det = DetectorResults()
        filtered = _mbti_group_filter([dict(i) for i in INTEREST_CATALOG], det)
        assert len(filtered) == len(INTEREST_CATALOG)
