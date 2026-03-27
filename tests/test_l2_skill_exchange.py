"""Tests for SkillExchangeFulfiller — skill exchange map."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_skill_exchange import SkillExchangeFulfiller, SKILL_CATALOG


class TestSkillCatalog:
    def test_catalog_has_20_entries(self):
        assert len(SKILL_CATALOG) == 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "skills"}
        for item in SKILL_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_each_has_two_skills(self):
        for item in SKILL_CATALOG:
            assert len(item["skills"]) == 2, f"{item['title']} should have 2 skills"


class TestSkillExchangeFulfiller:
    def _make_wish(self, text="技能交换") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.SKILL_EXCHANGE,
            level=WishLevel.L2, fulfillment_strategy="skill_exchange",
        )

    def test_returns_l2_result(self):
        f = SkillExchangeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = SkillExchangeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_guitar_keyword_boosts_music(self):
        f = SkillExchangeFulfiller()
        result = f.fulfill(self._make_wish("I want to learn guitar"), DetectorResults())
        cats = [r.category for r in result.recommendations]
        assert "music" in cats

    def test_coding_keyword_boosts_tech(self):
        f = SkillExchangeFulfiller()
        result = f.fulfill(self._make_wish("swap coding skills"), DetectorResults())
        cats = [r.category for r in result.recommendations]
        assert "tech" in cats

    def test_has_reminder(self):
        f = SkillExchangeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_introvert_filters_loud_social(self):
        f = SkillExchangeFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            # Dance/Fitness and Basketball/Soccer are loud+high — should be filtered
            assert rec.category not in ("fitness", "sports")

    def test_relevance_reason_for_match(self):
        f = SkillExchangeFulfiller()
        result = f.fulfill(self._make_wish("I know chess"), DetectorResults())
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("chess" in r.lower() for r in reasons)
