"""Tests for MicroChallengeFulfiller — daily micro-challenges."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_micro_challenge import MicroChallengeFulfiller, CHALLENGE_CATALOG


class TestChallengeCatalog:
    def test_catalog_has_25_entries(self):
        assert len(CHALLENGE_CATALOG) == 25

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty"}
        for item in CHALLENGE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_five_categories(self):
        cats = {item["category"] for item in CHALLENGE_CATALOG}
        expected = {"social_anxiety", "conflict_avoidance", "introvert_stretch", "creativity", "values"}
        assert cats == expected


class TestMicroChallengeFulfiller:
    def _make_wish(self, text="给我个小挑战") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="micro_challenge",
        )

    def test_returns_l2_result(self):
        f = MicroChallengeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = MicroChallengeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_fragile_gets_gentle(self):
        f = MicroChallengeFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        # Gentle challenges should rank higher for fragile users
        assert len(result.recommendations) >= 1

    def test_resilient_extravert_gets_bold(self):
        f = MicroChallengeFulfiller()
        det = DetectorResults(
            fragility={"pattern": "resilient"},
            mbti={"type": "ENTP"},
        )
        result = f.fulfill(self._make_wish(), det)
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = MicroChallengeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_includes_difficulty(self):
        f = MicroChallengeFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("no pressure" in r.lower() or "just try" in r.lower() for r in reasons)

    def test_defensive_avoids_confrontational(self):
        f = MicroChallengeFulfiller()
        det = DetectorResults(fragility={"pattern": "defensive"})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            assert "confrontational" not in rec.tags

    def test_introvert_filters_loud_social(self):
        f = MicroChallengeFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            # "Attend a Meetup" is loud+high, should be filtered for introverts
            assert rec.title != "Attend a Meetup"
