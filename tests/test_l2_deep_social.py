"""Tests for DeepSocialFulfiller — deep connection format recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_deep_social import DeepSocialFulfiller, DEEP_SOCIAL_CATALOG


class TestDeepSocialCatalog:
    def test_catalog_has_15_entries(self):
        assert len(DEEP_SOCIAL_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in DEEP_SOCIAL_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestDeepSocialFulfiller:
    def _make_wish(self, text="想要深度社交") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="deep_social_recommendation",
        )

    def test_returns_l2_result(self):
        f = DeepSocialFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = DeepSocialFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_infj_gets_depth_formats(self):
        f = DeepSocialFulfiller()
        det = DetectorResults(mbti={"type": "INFJ"})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("one_on_one", "small_group", "vulnerability", "emotional") for t in tags)

    def test_intj_gets_depth_formats(self):
        """INTJ maps to small_group + analytical + structured — results should reflect depth."""
        f = DeepSocialFulfiller()
        det = DetectorResults(mbti={"type": "INTJ"})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        # INTJ introvert gets quiet/reflective/one_on_one/small_group depth formats
        assert any(t in ("one_on_one", "small_group", "quiet", "reflective", "analytical", "structured") for t in tags)

    def test_philosophy_keyword(self):
        f = DeepSocialFulfiller()
        result = f.fulfill(self._make_wish("philosophical discussion"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "philosophical" in tags

    def test_has_reminder(self):
        f = DeepSocialFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = DeepSocialFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
