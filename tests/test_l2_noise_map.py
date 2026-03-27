"""Tests for NoiseMapFulfiller — noise-level zone recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_noise_map import (
    NoiseMapFulfiller,
    NOISE_CATALOG,
    _match_candidates,
)


class TestNoiseCatalog:
    def test_catalog_has_10_entries(self):
        assert len(NOISE_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in NOISE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_have_tags(self):
        for item in NOISE_CATALOG:
            assert len(item["tags"]) >= 2, f"{item['title']} needs more tags"


class TestNoiseMapFulfiller:
    def _make_wish(self, text="I want a quiet place") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="noise_map",
        )

    def test_returns_l2_result(self):
        f = NoiseMapFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = NoiseMapFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = NoiseMapFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "noise_zone"

    def test_quiet_preference_boosts_quiet_zones(self):
        candidates = _match_candidates("I need quiet peaceful space", DetectorResults())
        quiet_zones = [c for c in candidates if "quiet" in c.get("tags", [])]
        assert all(c["_emotion_boost"] > 0 for c in quiet_zones)

    def test_loud_preference_boosts_loud_zones(self):
        candidates = _match_candidates("I want a lively loud place", DetectorResults())
        loud_zones = [c for c in candidates if "loud" in c.get("tags", [])]
        assert all(c["_emotion_boost"] > 0 for c in loud_zones)

    def test_introvert_mbti_boosts_quiet(self):
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        candidates = _match_candidates("find a place", det)
        quiet_zones = [c for c in candidates if "quiet" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in quiet_zones)

    def test_has_reminder(self):
        f = NoiseMapFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
