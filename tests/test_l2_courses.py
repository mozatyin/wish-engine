"""Tests for CourseFulfiller — course recommendations with cognitive style matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_courses import CourseFulfiller, COURSE_CATALOG


class TestCourseCatalog:
    def test_catalog_not_empty(self):
        assert len(COURSE_CATALOG) >= 25

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "topic", "format", "tags"}
        for course in COURSE_CATALOG:
            missing = required - set(course.keys())
            assert not missing, f"{course['title']} missing: {missing}"


class TestCourseFulfiller:
    def _make_wish(self, text="想学心理学") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.LEARN_SKILL,
            level=WishLevel.L2, fulfillment_strategy="course_recommendation",
        )

    def test_returns_l2_result(self):
        f = CourseFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_intuitive_gets_theory_courses(self):
        f = CourseFulfiller()
        det = DetectorResults(mbti={"type": "INTJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        assert any("theory" in r.tags for r in result.recommendations)

    def test_sensing_gets_practical_courses(self):
        f = CourseFulfiller()
        det = DetectorResults(mbti={"type": "ISTJ", "dimensions": {"E_I": 0.3}})
        result = f.fulfill(self._make_wish(), det)
        assert any("practical" in r.tags for r in result.recommendations)

    def test_introvert_prefers_self_paced(self):
        f = CourseFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        assert any("self-paced" in r.tags for r in result.recommendations)

    def test_programming_wish(self):
        f = CourseFulfiller()
        result = f.fulfill(self._make_wish("想学编程"), DetectorResults())
        topics = []
        for r in result.recommendations:
            topics.extend(r.tags)
        assert any(t in ("programming", "coding", "tech") for t in topics)

    def test_max_3(self):
        f = CourseFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = CourseFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
