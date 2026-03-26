"""Test Compass integration with WishEngine."""
import pytest
from wish_engine.models import DetectorResults
from wish_engine.engine import WishEngine
from wish_engine.compass.compass import WishCompass


class TestCompassEngineBridge:
    def test_engine_with_compass_scans(self):
        compass = WishCompass()
        engine = WishEngine(fulfill_l1=False, post_l3=False, compass=compass)
        result = engine.process(
            raw_wishes=["想找个安静的地方"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        assert result.compass_scan is not None

    def test_engine_without_compass_works(self):
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        result = engine.process(
            raw_wishes=["想找个安静的地方"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        assert result.compass_scan is None

    def test_compass_renders_in_result(self):
        compass = WishCompass()
        engine = WishEngine(fulfill_l1=False, post_l3=False, compass=compass)
        result = engine.process(
            raw_wishes=["想找个安静的地方"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        assert isinstance(result.compass_renders, list)

    def test_compass_property(self):
        compass = WishCompass()
        engine = WishEngine(fulfill_l1=False, post_l3=False, compass=compass)
        assert engine.compass is compass

    def test_no_compass_property_is_none(self):
        engine = WishEngine(fulfill_l1=False, post_l3=False)
        assert engine.compass is None

    def test_summary_includes_compass_shells(self):
        compass = WishCompass()
        engine = WishEngine(fulfill_l1=False, post_l3=False, compass=compass)
        result = engine.process(
            raw_wishes=["想找个安静的地方"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        summary = result.summary()
        assert "compass_shells" in summary

    def test_bloom_shells_harvested(self):
        from wish_engine.compass.models import Shell, ContradictionPattern
        compass = WishCompass()
        # Add a bloom shell directly
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="hidden_love", confidence=0.8)
        compass.vault.add(shell)
        engine = WishEngine(fulfill_l1=False, post_l3=False, compass=compass)
        result = engine.process(
            raw_wishes=["想找个安静的地方"],
            detector_results=DetectorResults(),
            session_id="s1",
            user_id="u1",
        )
        assert len(result.compass_blooms) >= 1
        assert result.compass_blooms[0]["shell_topic"] == "hidden_love"

    def test_bloom_harvested_only_once(self):
        from wish_engine.compass.models import Shell, ContradictionPattern
        compass = WishCompass()
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="test", confidence=0.8)
        compass.vault.add(shell)
        engine = WishEngine(fulfill_l1=False, post_l3=False, compass=compass)
        r1 = engine.process(raw_wishes=["想理解自己"], detector_results=DetectorResults(), session_id="s1", user_id="u1")
        r2 = engine.process(raw_wishes=["想找个朋友"], detector_results=DetectorResults(), session_id="s2", user_id="u1")
        assert len(r1.compass_blooms) >= 1
        assert len(r2.compass_blooms) == 0  # already harvested
