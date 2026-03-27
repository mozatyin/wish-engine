"""Tests for FreeActivityFulfiller — free and low-cost activity recommendations."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_free_activities import (
    FreeActivityFulfiller,
    FREE_ACTIVITY_CATALOG,
    _match_candidates,
)


class TestFreeActivityCatalog:
    def test_catalog_has_20_entries(self):
        assert len(FREE_ACTIVITY_CATALOG) >= 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in FREE_ACTIVITY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_tagged_free(self):
        for item in FREE_ACTIVITY_CATALOG:
            assert "free" in item["tags"], f"{item['title']} missing 'free' tag"


class TestFreeActivityFulfiller:
    def _make_wish(self, text="想找免费活动") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="free_activity",
        )

    def test_returns_l2_result(self):
        f = FreeActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = FreeActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_quiet(self):
        f = FreeActivityFulfiller()
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "free" in tags

    def test_all_results_are_free(self):
        f = FreeActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert "free" in r.tags

    def test_has_map_data(self):
        f = FreeActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None

    def test_has_reminder(self):
        f = FreeActivityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_outdoor_keyword_boost(self):
        candidates = _match_candidates("free outdoor activity", DetectorResults())
        boosted = [c for c in candidates if c.get("_emotion_boost", 0) > 0]
        assert len(boosted) >= 1

    def test_volunteer_keyword_boost(self):
        candidates = _match_candidates("free volunteer", DetectorResults())
        boosted = [c for c in candidates if c.get("_emotion_boost", 0) > 0]
        assert len(boosted) >= 1
