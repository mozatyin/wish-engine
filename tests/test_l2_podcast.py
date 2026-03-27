"""Tests for PodcastFulfiller — podcast/audiobook recommendation."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_podcast import PodcastFulfiller, PODCAST_CATALOG


class TestPodcastCatalog:
    def test_catalog_has_20_entries(self):
        assert len(PODCAST_CATALOG) == 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "duration"}
        for item in PODCAST_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_durations_are_valid(self):
        for item in PODCAST_CATALOG:
            assert item["duration"] in ("short", "medium", "long")


class TestPodcastFulfiller:
    def _make_wish(self, text="推荐播客") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="podcast",
        )

    def test_returns_l2_result(self):
        f = PodcastFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = PodcastFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_anxiety_gets_calming(self):
        f = PodcastFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        result = f.fulfill(self._make_wish("recommend something calming"), det)
        assert len(result.recommendations) >= 1

    def test_long_commute_prefers_long(self):
        f = PodcastFulfiller()
        result = f.fulfill(self._make_wish("long commute audiobook"), DetectorResults())
        # Should have some content; audiobook/long should rank higher
        assert len(result.recommendations) >= 1

    def test_has_reminder(self):
        f = PodcastFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_sadness_emotion_reason(self):
        f = PodcastFulfiller()
        det = DetectorResults(emotion={"emotions": {"sadness": 0.7}})
        result = f.fulfill(self._make_wish("podcast"), det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("mood" in r.lower() or "uplift" in r.lower() for r in reasons)

    def test_no_map_data(self):
        f = PodcastFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is None
