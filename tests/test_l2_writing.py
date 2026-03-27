"""Tests for WritingFulfiller — writing/journal space."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_writing import WritingFulfiller, WRITING_CATALOG


class TestWritingCatalog:
    def test_catalog_has_15_entries(self):
        assert len(WRITING_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "mbti_match"}
        for item in WRITING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_mbti_matches_are_valid(self):
        valid_types = {
            "INFP", "INFJ", "ENFP", "ENFJ", "INTJ", "INTP", "ENTJ", "ENTP",
            "ISFP", "ISFJ", "ESFP", "ESFJ", "ISTJ", "ISTP", "ESTJ", "ESTP",
        }
        for item in WRITING_CATALOG:
            for t in item["mbti_match"]:
                assert t in valid_types, f"{item['title']} has invalid MBTI {t}"


class TestWritingFulfiller:
    def _make_wish(self, text="想写日记") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="writing",
        )

    def test_returns_l2_result(self):
        f = WritingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = WritingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_infp_gets_matched_prompts(self):
        f = WritingFulfiller()
        det = DetectorResults(mbti={"type": "INFP"})
        result = f.fulfill(self._make_wish(), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("INFP" in r for r in reasons)

    def test_estj_gets_matched_prompts(self):
        f = WritingFulfiller()
        det = DetectorResults(mbti={"type": "ESTJ"})
        result = f.fulfill(self._make_wish(), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("ESTJ" in r for r in reasons)

    def test_has_reminder(self):
        f = WritingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_no_mbti_still_works(self):
        f = WritingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults(mbti={}))
        assert len(result.recommendations) >= 1

    def test_no_map_data(self):
        f = WritingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None

    def test_all_recommendations_have_tags(self):
        f = WritingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for rec in result.recommendations:
            assert len(rec.tags) > 0
