"""Tests for AddictionMeetingFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_addiction_meetings import AddictionMeetingFulfiller, ADDICTION_MEETING_CATALOG


class TestAddictionMeetingCatalog:
    def test_catalog_has_10_entries(self):
        assert len(ADDICTION_MEETING_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in ADDICTION_MEETING_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestAddictionMeetingFulfiller:
    def _make_wish(self, text="I need an AA meeting") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="addiction_meetings",
        )

    def test_returns_l2_result(self):
        f = AddictionMeetingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = AddictionMeetingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_aa_keyword(self):
        f = AddictionMeetingFulfiller()
        result = f.fulfill(self._make_wish("find AA meeting"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any("aa" in t or "recovery" in t for t in tags)

    def test_chinese_keyword(self):
        f = AddictionMeetingFulfiller()
        result = f.fulfill(self._make_wish("戒瘾互助"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_arabic_keyword(self):
        f = AddictionMeetingFulfiller()
        result = f.fulfill(self._make_wish("إدمان"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_sober_keyword(self):
        f = AddictionMeetingFulfiller()
        result = f.fulfill(self._make_wish("I want to stay sober"), DetectorResults())
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = AddictionMeetingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = AddictionMeetingFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
