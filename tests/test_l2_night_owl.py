"""Tests for NightOwlFulfiller — night owl activity recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_night_owl import (
    NightOwlFulfiller,
    NIGHT_OWL_CATALOG,
    _match_candidates,
    is_night_owl_hour,
)


class TestNightOwlCatalog:
    def test_catalog_has_12_entries(self):
        assert len(NIGHT_OWL_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in NIGHT_OWL_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestIsNightOwlHour:
    def test_midnight_is_active(self):
        assert is_night_owl_hour(0) is True

    def test_3am_is_active(self):
        assert is_night_owl_hour(3) is True

    def test_11pm_is_active(self):
        assert is_night_owl_hour(23) is True

    def test_noon_is_not_active(self):
        assert is_night_owl_hour(12) is False

    def test_9am_is_not_active(self):
        assert is_night_owl_hour(9) is False


class TestNightOwlFulfiller:
    def _make_wish(self, text="night owl looking for things to do") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="night_owl",
        )

    def test_returns_l2_result(self):
        f = NightOwlFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = NightOwlFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_late_hour_boosts_all(self):
        late = _match_candidates("night owl", DetectorResults(), current_hour=2)
        day = _match_candidates("night owl", DetectorResults(), current_hour=14)
        late_avg = sum(c["_emotion_boost"] for c in late) / len(late)
        day_avg = sum(c["_emotion_boost"] for c in day) / len(day)
        assert late_avg > day_avg

    def test_insomnia_boosts_calming(self):
        candidates = _match_candidates("insomnia can't sleep", DetectorResults(), current_hour=2)
        calming = [c for c in candidates if "calming" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in calming)

    def test_has_reminder(self):
        f = NightOwlFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
