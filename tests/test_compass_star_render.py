"""Tests for Compass star rendering."""

from wish_engine.compass.models import ContradictionPattern, Shell, ShellStage
from wish_engine.compass.star_render import CompassStarOutput, render_shell_star


def _make_shell(confidence: float) -> Shell:
    return Shell(pattern=ContradictionPattern.MOUTH_HARD_HEART_SOFT, topic="trust", confidence=confidence)


class TestSeedInvisible:
    def test_seed_returns_none(self) -> None:
        shell = _make_shell(0.1)  # seed
        assert render_shell_star(shell) is None


class TestSprout:
    def test_sprout_rendering(self) -> None:
        shell = _make_shell(0.35)
        result = render_shell_star(shell)
        assert result is not None
        assert result.color == "#2A2035"
        assert result.animation == "flicker_rare"
        assert result.animation_duration_ms == 10000


class TestBud:
    def test_bud_rendering(self) -> None:
        shell = _make_shell(0.55)
        result = render_shell_star(shell)
        assert result is not None
        assert result.color == "#5B4A8A"
        assert result.animation == "pulse_slow"
        assert result.animation_duration_ms == 4000


class TestBloom:
    def test_bloom_rendering(self) -> None:
        shell = _make_shell(0.75)
        result = render_shell_star(shell)
        assert result is not None
        assert result.color == "#E8A0BF"
        assert result.animation == "glow_warm"
        assert result.animation_duration_ms == 2000


class TestOutputFields:
    def test_output_is_compass_star_output(self) -> None:
        shell = _make_shell(0.55)
        result = render_shell_star(shell)
        assert isinstance(result, CompassStarOutput)
        assert result.shell_id == shell.id
        assert result.stage == ShellStage.BUD

    def test_stage_matches_shell(self) -> None:
        shell = _make_shell(0.75)
        result = render_shell_star(shell)
        assert result is not None
        assert result.stage == ShellStage.BLOOM
