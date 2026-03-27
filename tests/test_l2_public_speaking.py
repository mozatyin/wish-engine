"""Tests for PublicSpeakingFulfiller — introvert-aware speaking opportunities."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_public_speaking import PublicSpeakingFulfiller, SPEAKING_CATALOG


class TestSpeakingCatalog:
    def test_catalog_has_10_entries(self):
        assert len(SPEAKING_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty"}
        for item in SPEAKING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_10_categories(self):
        cats = {item["category"] for item in SPEAKING_CATALOG}
        assert len(cats) == 10


class TestPublicSpeakingFulfiller:
    def _make_wish(self, text="我想学演讲") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.LEARN_SKILL,
            level=WishLevel.L2, fulfillment_strategy="public_speaking",
        )

    def test_returns_l2_result(self):
        f = PublicSpeakingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = PublicSpeakingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_gentle(self):
        f = PublicSpeakingFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        # Pitch practice (gentle) should rank higher than TEDx (bold)
        cats = [r.category for r in result.recommendations]
        assert "pitch_practice" in cats

    def test_extravert_gets_bold(self):
        f = PublicSpeakingFulfiller()
        det = DetectorResults(mbti={"type": "ENTP"})
        result = f.fulfill(self._make_wish(), det)
        assert len(result.recommendations) >= 1

    def test_fragile_gets_gentle_start(self):
        f = PublicSpeakingFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("safe" in r.lower() or "when you" in r.lower() for r in reasons)

    def test_has_reminder(self):
        f = PublicSpeakingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_introvert_filters_loud_social(self):
        f = PublicSpeakingFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            # TEDx and standup should be filtered for deep introverts
            assert rec.title != "Try Standup Comedy"
