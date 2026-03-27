"""Tests for LateNightFulfiller — late-night / 24-hour service finder."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_late_night import (
    LateNightFulfiller,
    LATE_NIGHT_CATALOG,
    _match_candidates,
    is_late_night,
)


class TestLateNightCatalog:
    def test_catalog_has_15_entries(self):
        assert len(LATE_NIGHT_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in LATE_NIGHT_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestIsLateNight:
    def test_midnight_is_late(self):
        assert is_late_night(0) is True

    def test_3am_is_late(self):
        assert is_late_night(3) is True

    def test_11pm_is_late(self):
        assert is_late_night(23) is True

    def test_noon_is_not_late(self):
        assert is_late_night(12) is False

    def test_6am_is_not_late(self):
        assert is_late_night(6) is False


class TestLateNightFulfiller:
    def _make_wish(self, text="I need a 24h pharmacy") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="late_night",
        )

    def test_returns_l2_result(self):
        f = LateNightFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = LateNightFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = LateNightFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "late_night_service"

    def test_pharmacy_keyword_boosts_pharmacy(self):
        candidates = _match_candidates("I need pharmacy medicine", DetectorResults(), current_hour=2)
        pharmacy = [c for c in candidates if c["category"] == "pharmacy_24h"]
        assert len(pharmacy) >= 1
        assert pharmacy[0]["_emotion_boost"] > 0

    def test_late_hour_boosts_24h_items(self):
        late_candidates = _match_candidates("need something open", DetectorResults(), current_hour=2)
        day_candidates = _match_candidates("need something open", DetectorResults(), current_hour=14)
        # At 2am, 24h items should get a time boost
        late_24h = [c for c in late_candidates if "24h" in c.get("tags", [])]
        day_24h = [c for c in day_candidates if "24h" in c.get("tags", [])]
        assert late_24h[0]["_emotion_boost"] >= day_24h[0]["_emotion_boost"]

    def test_emergency_keyword_boosts_emergency(self):
        candidates = _match_candidates("emergency hospital", DetectorResults(), current_hour=1)
        er = [c for c in candidates if c["category"] == "hospital_emergency"]
        assert len(er) >= 1
        assert er[0]["_emotion_boost"] > 0
