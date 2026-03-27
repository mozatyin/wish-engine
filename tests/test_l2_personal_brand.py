"""Tests for PersonalBrandFulfiller — MBTI-matched brand building."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_personal_brand import PersonalBrandFulfiller, BRAND_CATALOG


class TestBrandCatalog:
    def test_catalog_has_12_entries(self):
        assert len(BRAND_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty"}
        for item in BRAND_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_12_categories(self):
        cats = {item["category"] for item in BRAND_CATALOG}
        assert len(cats) == 12


class TestPersonalBrandFulfiller:
    def _make_wish(self, text="我想建立个人品牌") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.CAREER_DIRECTION,
            level=WishLevel.L2, fulfillment_strategy="personal_brand",
        )

    def test_returns_l2_result(self):
        f = PersonalBrandFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = PersonalBrandFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_written(self):
        f = PersonalBrandFulfiller()
        det = DetectorResults(mbti={"type": "INFP"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        written_cats = {"portfolio_creation", "blog_start", "design_portfolio", "github_profile", "writing_samples", "photography_portfolio"}
        assert any(c in written_cats for c in cats)

    def test_extravert_gets_speaking(self):
        f = PersonalBrandFulfiller()
        det = DetectorResults(mbti={"type": "ENTP"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        speaking_cats = {"youtube_channel", "podcast_launch", "speaking_profile"}
        assert any(c in speaking_cats for c in cats)

    def test_has_reminder(self):
        f = PersonalBrandFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_introvert(self):
        f = PersonalBrandFulfiller()
        det = DetectorResults(mbti={"type": "INFP"})
        result = f.fulfill(self._make_wish(), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("introvert" in r.lower() for r in reasons)

    def test_no_mbti_still_works(self):
        f = PersonalBrandFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) >= 1
