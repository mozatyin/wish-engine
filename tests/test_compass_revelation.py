"""Tests for Revelation Renderer."""

import pytest

from wish_engine.compass.models import ContradictionPattern, Shell
from wish_engine.compass.revelation import (
    Revelation,
    RevelationRenderer,
    RevelationStyle,
)


def _make_shell(confidence: float, pattern: ContradictionPattern = ContradictionPattern.MOUTH_HARD_HEART_SOFT, topic: str = "vulnerability") -> Shell:
    return Shell(pattern=pattern, topic=topic, confidence=confidence)


@pytest.fixture
def renderer() -> RevelationRenderer:
    return RevelationRenderer()


# --- Style selection by stage ---

class TestStyleSelection:
    def test_sprout_gets_metaphor(self, renderer: RevelationRenderer) -> None:
        shell = _make_shell(0.35)  # sprout
        rev = renderer.render(shell)
        assert rev.style == RevelationStyle.METAPHOR

    def test_bud_gets_question(self, renderer: RevelationRenderer) -> None:
        shell = _make_shell(0.55)  # bud
        rev = renderer.render(shell)
        assert rev.style == RevelationStyle.QUESTION

    def test_bloom_gets_gentle_statement(self, renderer: RevelationRenderer) -> None:
        shell = _make_shell(0.75)  # bloom
        rev = renderer.render(shell)
        assert rev.style == RevelationStyle.GENTLE_STATEMENT


# --- Content ---

class TestContent:
    def test_metaphor_does_not_mention_topic(self, renderer: RevelationRenderer) -> None:
        shell = _make_shell(0.35, topic="career change")
        rev = renderer.render(shell)
        assert "career change" not in rev.text.lower()

    def test_question_contains_topic(self, renderer: RevelationRenderer) -> None:
        shell = _make_shell(0.55, topic="career change")
        rev = renderer.render(shell)
        assert "career change" in rev.text

    def test_gentle_statement_contains_topic(self, renderer: RevelationRenderer) -> None:
        shell = _make_shell(0.75, topic="career change")
        rev = renderer.render(shell)
        assert "career change" in rev.text


# --- Sensitivity cap ---

class TestSensitivity:
    def test_high_sensitivity_caps_bloom_at_question(self, renderer: RevelationRenderer) -> None:
        shell = _make_shell(0.75)  # bloom
        rev = renderer.render(shell, sensitivity="high")
        assert rev.style == RevelationStyle.QUESTION

    def test_medium_sensitivity_allows_bloom(self, renderer: RevelationRenderer) -> None:
        shell = _make_shell(0.75)  # bloom
        rev = renderer.render(shell, sensitivity="medium")
        assert rev.style == RevelationStyle.GENTLE_STATEMENT


# --- Model fields ---

class TestModelFields:
    def test_revelation_fields(self, renderer: RevelationRenderer) -> None:
        shell = _make_shell(0.55)
        rev = renderer.render(shell)
        assert isinstance(rev, Revelation)
        assert rev.shell_id == shell.id
        assert isinstance(rev.style, RevelationStyle)
        assert isinstance(rev.text, str)
        assert len(rev.text) > 0
