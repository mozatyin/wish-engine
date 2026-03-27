"""Tests for VirtualCompanionFulfiller — AI companion mode recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_virtual_companion import (
    VirtualCompanionFulfiller,
    COMPANION_CATALOG,
    _match_companions,
)


class TestCompanionCatalog:
    def test_catalog_has_15_entries(self):
        assert len(COMPANION_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "companion_style", "noise", "social", "mood", "tags", "emotion_match"}
        for item in COMPANION_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_catalog_has_diverse_styles(self):
        styles = {item["companion_style"] for item in COMPANION_CATALOG}
        assert len(styles) >= 3  # soothing, chatty, focused, energetic


class TestVirtualCompanionFulfiller:
    def _make_wish(self, text="想要有人陪伴") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_COMPANION,
            level=WishLevel.L2, fulfillment_strategy="virtual_companion",
        )

    def test_returns_l2_result(self):
        f = VirtualCompanionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_anxiety_boosts_calming_companions(self):
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        candidates = _match_companions("陪我", det)
        anxiety_matches = [c for c in candidates if "anxiety" in c.get("emotion_match", [])]
        non_matches = [c for c in candidates if "anxiety" not in c.get("emotion_match", [])]
        # Anxiety-matched companions should have higher emotion boost
        if anxiety_matches and non_matches:
            assert anxiety_matches[0]["_emotion_boost"] > non_matches[0]["_emotion_boost"]

    def test_max_3(self):
        f = VirtualCompanionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = VirtualCompanionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_introvert_prefers_quiet_companion(self):
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        candidates = _match_companions("陪我", det)
        soothing = [c for c in candidates if c["companion_style"] in ("soothing", "focused")]
        chatty = [c for c in candidates if c["companion_style"] in ("chatty", "energetic")]
        # Soothing/focused should have higher boost than chatty for introvert
        if soothing and chatty:
            assert soothing[0]["_emotion_boost"] >= chatty[0]["_emotion_boost"]

    def test_no_map_data(self):
        """Virtual companions don't need map data."""
        f = VirtualCompanionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_loneliness_boosts_social_companions(self):
        det = DetectorResults(emotion={"emotions": {"loneliness": 0.7}})
        candidates = _match_companions("陪我", det)
        lonely_matches = [c for c in candidates if "loneliness" in c.get("emotion_match", [])]
        assert any(c["_emotion_boost"] > 0 for c in lonely_matches)
