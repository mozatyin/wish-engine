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
