"""Tests for PregnancyFulfiller — pregnancy and maternity recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_pregnancy import (
    PregnancyFulfiller,
    PREGNANCY_CATALOG,
    _match_candidates,
)


class TestPregnancyCatalog:
    def test_catalog_has_12_entries(self):
        assert len(PREGNANCY_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in PREGNANCY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_calming_mood(self):
        for item in PREGNANCY_CATALOG:
            assert item["mood"] == "calming", f"{item['title']} should be calming"


class TestPregnancyFulfiller:
    def _make_wish(self, text="pregnancy prenatal resources") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="pregnancy",
        )

    def test_returns_l2_result(self):
        f = PregnancyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = PregnancyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = PregnancyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "pregnancy_friendly"

    def test_yoga_keyword_boosts(self):
        candidates = _match_candidates("prenatal yoga class", DetectorResults())
        yoga = [c for c in candidates if c["category"] == "prenatal_yoga"]
        assert len(yoga) >= 1
        assert yoga[0]["_emotion_boost"] > 0

    def test_health_keyword_boosts(self):
        candidates = _match_candidates("pregnancy health safe", DetectorResults())
        health = [c for c in candidates if "health" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in health)

    def test_social_keyword_boosts(self):
        candidates = _match_candidates("mommy group connect", DetectorResults())
        groups = [c for c in candidates if c["category"] == "mommy_group"]
        assert len(groups) >= 1
        assert groups[0]["_emotion_boost"] > 0

    def test_has_reminder(self):
        f = PregnancyFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
