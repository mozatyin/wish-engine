"""Tests for AccessibilityFulfiller — accessible place recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_accessibility import (
    AccessibilityFulfiller,
    ACCESSIBILITY_CATALOG,
    _match_candidates,
)


class TestAccessibilityCatalog:
    def test_catalog_has_12_entries(self):
        assert len(ACCESSIBILITY_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for item in ACCESSIBILITY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_all_entries_have_tags(self):
        for item in ACCESSIBILITY_CATALOG:
            assert len(item["tags"]) >= 2, f"{item['title']} needs more tags"


class TestAccessibilityFulfiller:
    def _make_wish(self, text="I need wheelchair accessible places") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="accessibility",
        )

    def test_returns_l2_result(self):
        f = AccessibilityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = AccessibilityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = AccessibilityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.place_type == "accessible_place"

    def test_wheelchair_keyword_boosts(self):
        candidates = _match_candidates("wheelchair restaurant", DetectorResults())
        wheelchair = [c for c in candidates if c["category"] == "wheelchair_restaurant"]
        assert len(wheelchair) >= 1
        assert wheelchair[0]["_emotion_boost"] > 0

    def test_sensory_keyword_boosts(self):
        candidates = _match_candidates("sensory friendly autism", DetectorResults())
        sensory = [c for c in candidates if c["category"] == "sensory_friendly"]
        assert len(sensory) >= 1
        assert sensory[0]["_emotion_boost"] > 0

    def test_chinese_keyword(self):
        candidates = _match_candidates("无障碍 轮椅", DetectorResults())
        wheelchair = [c for c in candidates if "wheelchair" in c.get("tags", [])]
        assert any(c["_emotion_boost"] > 0 for c in wheelchair)

    def test_has_reminder(self):
        f = AccessibilityFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
