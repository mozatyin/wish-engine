"""Tests for HousingFulfiller — personality-matched housing neighborhoods."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_housing import HousingFulfiller, HOUSING_CATALOG, _match_candidates


class TestHousingCatalog:
    def test_catalog_has_15_entries(self):
        assert len(HOUSING_CATALOG) >= 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags", "values_match"}
        for item in HOUSING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestHousingFulfiller:
    def _make_wish(self, text="想租房") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="housing",
        )

    def test_returns_l2_result(self):
        f = HousingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = HousingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_quiet(self):
        f = HousingFulfiller()
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("quiet", "calming") for t in tags)

    def test_extrovert_gets_social(self):
        f = HousingFulfiller()
        det = DetectorResults(mbti={"type": "ENFP", "dimensions": {"E_I": 0.8}})
        result = f.fulfill(self._make_wish(), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("social", "creative") for t in tags)

    def test_has_map_data(self):
        f = HousingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "neighborhood"

    def test_has_reminder(self):
        f = HousingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_quiet_keyword_boost(self):
        candidates = _match_candidates("quiet neighborhood", DetectorResults())
        boosted = [c for c in candidates if c.get("_emotion_boost", 0) > 0]
        assert len(boosted) >= 1

    def test_family_keyword_boost(self):
        candidates = _match_candidates("family friendly housing", DetectorResults())
        boosted = [c for c in candidates if c.get("_emotion_boost", 0) > 0]
        assert len(boosted) >= 1
