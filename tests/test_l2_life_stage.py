"""Tests for LifeStageFulfiller — life stage transition recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_life_stage import (
    LifeStageFulfiller,
    LIFE_STAGE_CATALOG,
    _match_candidates,
)


class TestLifeStageCatalog:
    def test_catalog_has_15_entries(self):
        assert len(LIFE_STAGE_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in LIFE_STAGE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_have_tags(self):
        for item in LIFE_STAGE_CATALOG:
            assert len(item["tags"]) >= 2, f"{item['title']} needs more tags"


class TestLifeStageFulfiller:
    def _make_wish(self, text="graduation planning next steps") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="life_stage",
        )

    def test_returns_l2_result(self):
        f = LifeStageFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = LifeStageFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_graduation_keyword_boosts(self):
        candidates = _match_candidates("graduation planning", DetectorResults())
        grad = [c for c in candidates if c["category"] == "graduation_planning"]
        assert len(grad) >= 1
        assert grad[0]["_emotion_boost"] > 0

    def test_retirement_keyword_boosts(self):
        candidates = _match_candidates("retirement planning community", DetectorResults())
        ret = [c for c in candidates if "retirement" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in ret)

    def test_career_pivot_keyword(self):
        candidates = _match_candidates("career change pivot new direction", DetectorResults())
        pivot = [c for c in candidates if c["category"] == "career_pivot"]
        assert len(pivot) >= 1
        assert pivot[0]["_emotion_boost"] > 0

    def test_planning_boosts_planning_tags(self):
        candidates = _match_candidates("planning prepare next step", DetectorResults())
        planning = [c for c in candidates if "planning" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in planning)

    def test_no_map_data(self):
        f = LifeStageFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        # Life stage is informational, no map needed
        assert result.map_data is None

    def test_has_reminder(self):
        f = LifeStageFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
