"""Tests for PlaceFulfiller — place search with personality filtering."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_places import PlaceFulfiller, PLACE_CATALOG


class TestPlaceCatalog:
    def test_catalog_not_empty(self):
        assert len(PLACE_CATALOG) >= 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags"}
        for place in PLACE_CATALOG:
            missing = required - set(place.keys())
            assert not missing, f"{place['title']} missing: {missing}"

    def test_noise_values_valid(self):
        for place in PLACE_CATALOG:
            assert place["noise"] in ("quiet", "moderate", "loud"), place["title"]

    def test_social_values_valid(self):
        for place in PLACE_CATALOG:
            assert place["social"] in ("low", "medium", "high"), place["title"]


class TestPlaceFulfiller:
    def _make_wish(self, text="想找个安静的地方") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_PLACE,
            level=WishLevel.L2, fulfillment_strategy="place_search",
        )

    def test_returns_l2_result(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1
        assert len(result.recommendations) <= 3

    def test_has_map_data(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None
        assert result.map_data.radius_km > 0

    def test_has_reminder(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_introvert_no_noisy_places(self):
        f = PlaceFulfiller()
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            assert "noisy" not in rec.tags
            assert "loud" not in rec.tags

    def test_anxiety_no_intense_places(self):
        f = PlaceFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            assert "intense" not in rec.tags

    def test_meditation_wish_finds_meditation(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish("想学冥想"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert any("meditation" in c for c in categories)

    def test_exercise_wish_finds_fitness(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish("想多运动"), DetectorResults())
        categories = [r.category for r in result.recommendations]
        assert any(c in ("gym", "fitness_studio", "park", "swimming_pool", "yoga_studio") for c in categories)

    def test_quiet_wish_finds_quiet_places(self):
        f = PlaceFulfiller()
        result = f.fulfill(self._make_wish("想找个安静地方待会儿"), DetectorResults())
        for rec in result.recommendations:
            assert any(t in rec.tags for t in ["quiet", "peaceful", "calming"])
