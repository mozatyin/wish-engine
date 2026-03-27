"""Tests for CourseTrackerFulfiller — online course progress tracking."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_course_tracker import CourseTrackerFulfiller, COURSE_CATALOG, PROGRESS_STATES


class TestCourseCatalog:
    def test_catalog_has_10_entries(self):
        assert len(COURSE_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "progress_nudge"}
        for item in COURSE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_progress_states_defined(self):
        assert len(PROGRESS_STATES) == 5
        assert "stalled" in PROGRESS_STATES


class TestCourseTrackerFulfiller:
    def _make_wish(self, text="课程进度") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.LEARN_SKILL,
            level=WishLevel.L2, fulfillment_strategy="course_tracker",
        )

    def test_returns_l2_result(self):
        f = CourseTrackerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = CourseTrackerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_stalled_gets_nudge(self):
        f = CourseTrackerFulfiller()
        result = f.fulfill(self._make_wish("我的课程停了"), DetectorResults())
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("waiting" in r.lower() or "momentum" in r.lower() or "today" in r.lower() for r in reasons)

    def test_almost_done_gets_encouragement(self):
        f = CourseTrackerFulfiller()
        result = f.fulfill(self._make_wish("almost done with my course"), DetectorResults())
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("close" in r.lower() or "push" in r.lower() for r in reasons)

    def test_has_reminder(self):
        f = CourseTrackerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_no_map_data(self):
        f = CourseTrackerFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_coding_keyword_match(self):
        f = CourseTrackerFulfiller()
        result = f.fulfill(self._make_wish("continue my bootcamp"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_introvert_filters_workshop(self):
        f = CourseTrackerFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        for rec in result.recommendations:
            # Workshop series has loud noise + high social, should be filtered
            assert rec.category != "workshop_series"
