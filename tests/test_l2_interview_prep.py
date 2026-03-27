"""Tests for InterviewPrepFulfiller — MBTI-matched interview strategies."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_interview_prep import InterviewPrepFulfiller, INTERVIEW_CATALOG


class TestInterviewCatalog:
    def test_catalog_has_12_entries(self):
        assert len(INTERVIEW_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty"}
        for item in INTERVIEW_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_12_categories(self):
        cats = {item["category"] for item in INTERVIEW_CATALOG}
        assert len(cats) == 12


class TestInterviewPrepFulfiller:
    def _make_wish(self, text="帮我准备面试") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.CAREER_DIRECTION,
            level=WishLevel.L2, fulfillment_strategy="interview_prep",
        )

    def test_returns_l2_result(self):
        f = InterviewPrepFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = InterviewPrepFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_introvert_gets_preparation(self):
        f = InterviewPrepFulfiller()
        det = DetectorResults(mbti={"type": "INTJ"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        prep_cats = {"behavioral_interview", "technical_interview", "case_study", "presentation_prep", "portfolio_review", "resume_workshop"}
        assert any(c in prep_cats for c in cats)

    def test_extravert_gets_improvisation(self):
        f = InterviewPrepFulfiller()
        det = DetectorResults(mbti={"type": "ENTP"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        improv_cats = {"mock_interview", "networking_strategy"}
        assert any(c in improv_cats for c in cats)

    def test_has_reminder(self):
        f = InterviewPrepFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_fragile_prefers_gentle(self):
        f = InterviewPrepFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        gentle_cats = {"cultural_fit", "elevator_pitch", "linkedin_review", "resume_workshop"}
        assert any(c in gentle_cats for c in cats)

    def test_no_mbti_still_works(self):
        f = InterviewPrepFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) >= 1
