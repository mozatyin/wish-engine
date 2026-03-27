"""Tests for EmotionCalendarFulfiller — monthly emotion themes."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_emotion_calendar import EmotionCalendarFulfiller, CALENDAR_CATALOG


class TestCalendarCatalog:
    def test_catalog_has_12_entries(self):
        assert len(CALENDAR_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty", "month"}
        for item in CALENDAR_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_12_months_covered(self):
        months = {item["month"] for item in CALENDAR_CATALOG}
        assert months == set(range(1, 13))


class TestEmotionCalendarFulfiller:
    def _make_wish(self, text="情绪日历") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="emotion_calendar",
        )

    def test_returns_l2_result(self):
        f = EmotionCalendarFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = EmotionCalendarFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_current_month_ranked_high(self):
        f = EmotionCalendarFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        # Current month entry should be in top 3
        import datetime
        current_month = datetime.date.today().month
        month_cats = {item["category"] for item in CALENDAR_CATALOG if item["month"] == current_month}
        top_cats = {r.category for r in result.recommendations}
        assert month_cats & top_cats, f"Current month {current_month} not in top results"

    def test_has_reminder(self):
        f = EmotionCalendarFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_introvert_filter(self):
        f = EmotionCalendarFulfiller()
        det = DetectorResults(mbti={"type": "INFP", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        assert len(result.recommendations) >= 1

    def test_all_entries_have_month(self):
        for item in CALENDAR_CATALOG:
            assert 1 <= item["month"] <= 12

    def test_relevance_reason_present(self):
        f = EmotionCalendarFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for rec in result.recommendations:
            assert rec.relevance_reason
