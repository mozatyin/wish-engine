"""Integration tests for the Wish Compass — full pipeline."""

import pytest
from wish_engine.models import DetectorResults, EmotionState
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import ShellStage, ContradictionPattern


class TestCompassScan:
    def test_scan_detects_emotion_anomaly(self):
        compass = WishCompass()
        result = compass.scan(
            topics=[
                {"entity": "Rhett", "sentiment": "negative", "arousal": 0.8, "mentions": 3},
            ],
            detector_results=DetectorResults(),
            session_id="s1",
        )
        assert result.new_shells >= 1
        assert len(compass.vault.all_shells) >= 1

    def test_scan_accumulates_over_sessions(self):
        compass = WishCompass()
        compass.scan(
            topics=[{"entity": "Rhett", "sentiment": "negative", "arousal": 0.75, "mentions": 2}],
            detector_results=DetectorResults(),
            session_id="s1",
        )
        compass.scan(
            topics=[{"entity": "Rhett", "sentiment": "negative", "arousal": 0.80, "mentions": 3}],
            detector_results=DetectorResults(),
            session_id="s2",
        )
        rhett_shells = compass.vault.get_by_topic("Rhett")
        assert len(rhett_shells) == 1  # merged, not duplicated
        assert rhett_shells[0].confidence > 0.25  # grew from evidence

    def test_no_shells_for_normal_conversation(self):
        compass = WishCompass()
        result = compass.scan(
            topics=[{"entity": "weather", "sentiment": "neutral", "arousal": 0.2, "mentions": 1}],
            detector_results=DetectorResults(),
            session_id="s1",
        )
        assert result.new_shells == 0


class TestCompassTrigger:
    def test_trigger_at_bud_stage(self):
        compass = WishCompass()
        # Manually add a bud-stage shell
        from wish_engine.compass.models import Shell
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.6)
        compass.vault.add(shell)

        revelation = compass.check_trigger(
            current_text="我该选 Ashley 还是 Rhett？",
            session_id="s5",
            distress=0.2,
            topics_mentioned=["Rhett", "Ashley"],
        )
        assert revelation is not None
        assert "Rhett" in revelation.text or "？" in revelation.text

    def test_no_trigger_during_crisis(self):
        compass = WishCompass()
        from wish_engine.compass.models import Shell
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="Rhett", confidence=0.6)
        compass.vault.add(shell)

        revelation = compass.check_trigger(
            current_text="我该选谁？",
            session_id="s5",
            distress=0.9,
            topics_mentioned=["Rhett"],
        )
        assert revelation is None


class TestCompassFeedback:
    def test_confirm_increases_confidence(self):
        compass = WishCompass()
        from wish_engine.compass.models import Shell
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="test", confidence=0.5)
        compass.vault.add(shell)
        old_conf = shell.confidence
        compass.record_feedback(shell.id, "confirm")
        assert compass.vault.get(shell.id).confidence > old_conf

    def test_deny_decreases_confidence(self):
        compass = WishCompass()
        from wish_engine.compass.models import Shell
        shell = Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="test", confidence=0.5)
        compass.vault.add(shell)
        compass.record_feedback(shell.id, "deny")
        assert compass.vault.get(shell.id).confidence < 0.5


class TestCompassStarMap:
    def test_get_visible_stars(self):
        compass = WishCompass()
        from wish_engine.compass.models import Shell
        compass.vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="seed", confidence=0.15))
        compass.vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="visible", confidence=0.4))
        stars = compass.get_star_renders()
        assert len(stars) == 1
        assert stars[0].stage == ShellStage.SPROUT


class TestCompassSummary:
    def test_summary(self):
        compass = WishCompass()
        from wish_engine.compass.models import Shell
        compass.vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="a", confidence=0.15))
        compass.vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="b", confidence=0.4))
        compass.vault.add(Shell(pattern=ContradictionPattern.EMOTION_ANOMALY, topic="c", confidence=0.75))
        s = compass.summary()
        assert s["total_shells"] == 3
        assert s["seeds"] == 1
        assert s["sprouts"] == 1
        assert s["blooms"] == 1
