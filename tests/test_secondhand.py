"""Tests for SecondhandFulfiller — personality-based secondhand item exchange."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_secondhand import SecondhandFulfiller, SECONDHAND_CATALOG, _match_candidates


class TestSecondhandCatalog:
    def test_catalog_has_20_entries(self):
        assert len(SECONDHAND_CATALOG) >= 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags", "values_match"}
        for item in SECONDHAND_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestSecondhandFulfiller:
    def _make_wish(self, text="想找二手书") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="secondhand",
        )

    def test_returns_l2_result(self):
        f = SecondhandFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = SecondhandFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_universalism_boosts_eco(self):
        f = SecondhandFulfiller()
        det = DetectorResults(values={"top_values": ["universalism"]})
        result = f.fulfill(self._make_wish("二手交换"), det)
        assert len(result.recommendations) >= 1

    def test_book_keyword_boost(self):
        candidates = _match_candidates("二手book exchange", DetectorResults())
        boosted = [c for c in candidates if c.get("_emotion_boost", 0) > 0]
        assert len(boosted) >= 1

    def test_no_map_data(self):
        f = SecondhandFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_has_reminder(self):
        f = SecondhandFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_security_values_match(self):
        det = DetectorResults(values={"top_values": ["security"]})
        candidates = _match_candidates("闲置", det)
        boosted = [c for c in candidates if c.get("_emotion_boost", 0) > 0]
        assert len(boosted) >= 1

    def test_all_categories_present(self):
        categories = {item["category"] for item in SECONDHAND_CATALOG}
        expected = {"books", "electronics", "clothing", "furniture", "plants", "bicycles"}
        assert expected.issubset(categories)
