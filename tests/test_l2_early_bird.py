"""Tests for EarlyBirdFulfiller — early morning activity recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_early_bird import (
    EarlyBirdFulfiller,
    EARLY_BIRD_CATALOG,
    _match_candidates,
    is_early_bird_hour,
)


class TestEarlyBirdCatalog:
    def test_catalog_has_12_entries(self):
        assert len(EARLY_BIRD_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in EARLY_BIRD_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestIsEarlyBirdHour:
    def test_5am_is_active(self):
        assert is_early_bird_hour(5) is True

    def test_7am_is_active(self):
        assert is_early_bird_hour(7) is True

    def test_9am_is_not_active(self):
        assert is_early_bird_hour(9) is False

    def test_midnight_is_not_active(self):
        assert is_early_bird_hour(0) is False

    def test_noon_is_not_active(self):
        assert is_early_bird_hour(12) is False


class TestEarlyBirdFulfiller:
    def _make_wish(self, text="early bird sunrise activities") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="early_bird",
        )

    def test_returns_l2_result(self):
        f = EarlyBirdFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = EarlyBirdFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_early_hour_boosts_all(self):
        early = _match_candidates("morning", DetectorResults(), current_hour=6)
        late = _match_candidates("morning", DetectorResults(), current_hour=14)
        early_avg = sum(c["_emotion_boost"] for c in early) / len(early)
        late_avg = sum(c["_emotion_boost"] for c in late) / len(late)
        assert early_avg > late_avg

    def test_exercise_keyword_boosts(self):
        candidates = _match_candidates("morning exercise workout", DetectorResults(), current_hour=6)
        exercise = [c for c in candidates if "exercise" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in exercise)

    def test_has_reminder(self):
        f = EarlyBirdFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
