"""Tests for MusicFulfiller — music recommendation with emotion-to-genre mapping."""

import pytest
from unittest.mock import patch

from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.apis.music_api import is_available
from wish_engine.l2_music import MusicFulfiller, MUSIC_CATALOG, _match_candidates


class TestMusicApiAvailability:
    def test_not_available_without_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            assert not is_available()

    def test_available_with_keys(self):
        with patch.dict("os.environ", {"SPOTIFY_CLIENT_ID": "test", "SPOTIFY_CLIENT_SECRET": "test"}):
            assert is_available()

    def test_not_available_with_partial_keys(self):
        with patch.dict("os.environ", {"SPOTIFY_CLIENT_ID": "test"}, clear=True):
            assert not is_available()


class TestMusicCatalog:
    def test_catalog_not_empty(self):
        assert len(MUSIC_CATALOG) >= 20

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "noise", "social", "mood", "tags", "emotion_match"}
        for item in MUSIC_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_catalog_covers_all_emotions(self):
        all_emotions = set()
        for item in MUSIC_CATALOG:
            all_emotions.update(item.get("emotion_match", []))
        for emo in ["anxiety", "sadness", "anger", "joy", "loneliness", "fatigue"]:
            assert emo in all_emotions, f"Missing emotion: {emo}"


class TestMusicFulfiller:
    def _make_wish(self, text="想听音乐") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="music_recommendation",
        )

    def test_returns_l2_result(self):
        f = MusicFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_anxiety_gets_calming(self):
        f = MusicFulfiller()
        det = DetectorResults(emotion={"emotions": {"anxiety": 0.8}})
        result = f.fulfill(self._make_wish("想听放松的音乐"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("calming", "quiet", "ambient", "acoustic") for t in tags)

    def test_joy_gets_upbeat(self):
        f = MusicFulfiller()
        det = DetectorResults(emotion={"emotions": {"joy": 0.8}})
        result = f.fulfill(self._make_wish("想听开心的歌"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("upbeat", "dance", "fun", "happy") for t in tags)

    def test_introvert_gets_quiet_genres(self):
        f = MusicFulfiller()
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        result = f.fulfill(self._make_wish(), det)
        # PersonalityFilter should exclude loud+high social
        for rec in result.recommendations:
            if "loud" in rec.tags:
                assert "high" not in rec.tags or rec.category != "playlist"

    def test_max_3(self):
        f = MusicFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = MusicFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_anger_gets_intense(self):
        f = MusicFulfiller()
        det = DetectorResults(emotion={"emotions": {"anger": 0.8}})
        result = f.fulfill(self._make_wish("想听摇滚发泄"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("release", "intense", "rock", "cathartic") for t in tags)

    def test_loneliness_gets_warm(self):
        f = MusicFulfiller()
        det = DetectorResults(emotion={"emotions": {"loneliness": 0.7}})
        result = f.fulfill(self._make_wish("感觉孤独"), det)
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert any(t in ("warm", "soul", "emotional") for t in tags)
