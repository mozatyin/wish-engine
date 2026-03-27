"""Tests for ConfidenceFulfiller — fragility-aware confidence builders."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_confidence import ConfidenceFulfiller, CONFIDENCE_CATALOG


class TestConfidenceCatalog:
    def test_catalog_has_15_entries(self):
        assert len(CONFIDENCE_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty"}
        for item in CONFIDENCE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_15_categories(self):
        cats = {item["category"] for item in CONFIDENCE_CATALOG}
        assert len(cats) == 15


class TestConfidenceFulfiller:
    def _make_wish(self, text="我想变得更自信") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="confidence",
        )

    def test_returns_l2_result(self):
        f = ConfidenceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = ConfidenceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_fragile_gets_gentle(self):
        f = ConfidenceFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        gentle_cats = {"daily_affirmation", "achievement_log", "power_pose", "positive_self_talk",
                       "visualization", "past_wins_review", "compliment_practice", "body_language", "success_journal"}
        assert all(c in gentle_cats for c in cats)

    def test_fragile_avoids_rejection_therapy(self):
        f = ConfidenceFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        assert "rejection_therapy" not in cats

    def test_resilient_extravert_gets_bold(self):
        f = ConfidenceFulfiller()
        det = DetectorResults(
            fragility={"pattern": "resilient"},
            mbti={"type": "ENTP"},
        )
        result = f.fulfill(self._make_wish(), det)
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = ConfidenceFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_includes_gentle(self):
        f = ConfidenceFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("gentle" in r.lower() or "safe" in r.lower() for r in reasons)
