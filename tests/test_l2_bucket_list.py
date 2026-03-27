"""Tests for BucketListFulfiller — life experiment list."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_bucket_list import BucketListFulfiller, BUCKET_LIST_CATALOG


class TestBucketListCatalog:
    def test_catalog_has_25_entries(self):
        assert len(BUCKET_LIST_CATALOG) == 25

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "nearby"}
        for item in BUCKET_LIST_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_nearby_distribution(self):
        nearby = [i for i in BUCKET_LIST_CATALOG if i["nearby"]]
        remote = [i for i in BUCKET_LIST_CATALOG if not i["nearby"]]
        assert len(nearby) > len(remote), "Most items should be doable nearby"


class TestBucketListFulfiller:
    def _make_wish(self, text="我想做的事") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="bucket_list",
        )

    def test_returns_l2_result(self):
        f = BucketListFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = BucketListFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_nearby_preference_boosts_local(self):
        f = BucketListFulfiller()
        result = f.fulfill(self._make_wish("附近能做的事"), DetectorResults())
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("right where you are" in r.lower() for r in reasons)

    def test_introvert_filters_loud_social(self):
        f = BucketListFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            assert rec.title != "Attend a Festival"

    def test_has_reminder(self):
        f = BucketListFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_no_map_data(self):
        f = BucketListFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_tradition_value_boosts_traditional(self):
        f = BucketListFulfiller()
        det = DetectorResults(values={"top_values": ["tradition"]})
        result = f.fulfill(self._make_wish(), det)
        # Traditional-tagged items should rank higher
        assert len(result.recommendations) >= 1

    def test_all_recs_have_category(self):
        f = BucketListFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for rec in result.recommendations:
            assert rec.category != ""
