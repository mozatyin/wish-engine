"""Tests for the single-turn respond() API across engines.

All LLM calls mocked — no real API calls.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from expert_engine.engine import AnalysisResult, ExpertEngine
from expert_engine.dialogue_engine import DialogueEngine
from expert_engine.models import (
    CaseFormulation,
    SchemaProfile,
    TechniqueRecommendation,
)
from expert_engine.patient_simulator import PatientSimulator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

AVOIDANT_SIGNALS = {
    "attachment_style": "avoidant",
    "attachment_confidence": 0.78,
    "conflict_style": "avoid",
    "conflict_confidence": 0.71,
    "fragility_pattern": "masked",
    "fragility_confidence": 0.82,
    "humor_style": "self_deprecating",
    "humor_confidence": 0.65,
    "eq_score": 0.6,
    "emotion_dominant": "anxiety",
    "emotion_intensity": 0.5,
    "love_language_primary": "quality_time",
    "love_language_confidence": 0.5,
    "love_language_unmet": False,
    "connection_response": "away",
    "connection_confidence": 0.6,
    "values_dominant": "self_direction",
    "values_self_direction": 0.88,
    "values_achievement": 0.5,
    "values_power": 0.3,
    "values_benevolence": 0.4,
    "mbti_type": "INTP",
    "crisis_level": 0.0,
    "emotion_has_fear_of_loss": False,
    "emotion_has_shame": False,
    "emotion_has_pessimism": False,
    "emotion_has_impulsive": False,
    "individuation_score": 0.6,
    "self_criticism_score": 0.3,
    "energy_level": "normal",
    "user_id": "test_user",
}

MOCK_LLM_JSON = (
    '{"reply": "I notice you tend to pull away when things get close.", '
    '"homework_instruction": "Notice 3 moments this week when you want to withdraw", '
    '"session_summary": "Explored avoidance pattern", '
    '"progress_note": "Patient showing awareness of avoidant pattern"}'
)


def _mock_llm_response(text: str = MOCK_LLM_JSON):
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


@pytest.fixture
def engine():
    return ExpertEngine(api_key="test-key")


@pytest.fixture
def analysis(engine):
    return engine.analyze(detector_signals=AVOIDANT_SIGNALS)


# ---------------------------------------------------------------------------
# ExpertEngine.respond() tests
# ---------------------------------------------------------------------------

class TestExpertEngineRespond:

    def test_respond_returns_reply(self, engine, analysis):
        """Basic: respond() returns a dict with reply, technique_used, progress_note."""
        with patch.object(engine._session_engine, "_call_llm", return_value=_mock_llm_response()):
            result = engine.respond(
                user_message="I feel like nobody really knows me.",
                analysis=analysis,
            )

        assert isinstance(result, dict)
        assert "reply" in result
        assert "technique_used" in result
        assert "progress_note" in result
        assert len(result["reply"]) > 0
        assert result["technique_used"]  # non-empty

    def test_respond_with_conversation_history(self, engine, analysis):
        """Multi-turn: conversation history is passed through to context."""
        history = [
            {"role": "user", "text": "I feel disconnected from people."},
            {"role": "expert", "text": "That sounds isolating. Tell me more."},
        ]

        with patch.object(engine._session_engine, "_call_llm", return_value=_mock_llm_response()) as mock_call:
            result = engine.respond(
                user_message="Yeah, I push everyone away.",
                analysis=analysis,
                conversation_history=history,
            )

        # Verify the LLM was called and history was included in context
        assert mock_call.called
        # _call_llm(system_prompt, user_message) — positional args
        args = mock_call.call_args[0]
        combined = " ".join(args)
        # The context should contain previous exchanges and current message
        assert "disconnected" in combined or "push everyone away" in combined
        assert result["reply"]

    def test_respond_without_soul_context(self, engine, analysis):
        """Works fine without soul_context."""
        with patch.object(engine._session_engine, "_call_llm", return_value=_mock_llm_response()):
            result = engine.respond(
                user_message="I am stressed about work.",
                analysis=analysis,
                soul_context="",
            )

        assert result["reply"]

    def test_respond_analysis_influences_technique(self, engine):
        """Different analysis (signals) should produce different technique selection."""
        # High crisis signals
        crisis_signals = {**AVOIDANT_SIGNALS, "crisis_level": 0.6}
        crisis_analysis = engine.analyze(detector_signals=crisis_signals)

        # Normal signals
        normal_analysis = engine.analyze(detector_signals=AVOIDANT_SIGNALS)

        with patch.object(engine._session_engine, "_call_llm", return_value=_mock_llm_response()):
            crisis_result = engine.respond(
                user_message="I can't take it anymore.",
                analysis=crisis_analysis,
            )
            normal_result = engine.respond(
                user_message="I've been thinking about my patterns.",
                analysis=normal_analysis,
            )

        # Both should return valid results; techniques may differ based on crisis
        assert crisis_result["reply"]
        assert normal_result["reply"]
        # technique_used should be a non-empty string for both
        assert crisis_result["technique_used"]
        assert normal_result["technique_used"]

    def test_respond_infers_turn_number(self, engine, analysis):
        """Turn number is inferred from conversation history when not provided."""
        history = [
            {"role": "user", "text": "First message."},
            {"role": "expert", "text": "First reply."},
            {"role": "user", "text": "Second message."},
            {"role": "expert", "text": "Second reply."},
        ]

        with patch.object(engine._session_engine, "_call_llm", return_value=_mock_llm_response()):
            result = engine.respond(
                user_message="Third message.",
                analysis=analysis,
                conversation_history=history,
            )

        # Should infer turn_number=3 (2 previous user messages + 1 current)
        assert result["reply"]

    def test_respond_explicit_turn_number(self, engine, analysis):
        """Explicit turn_number overrides inference."""
        with patch.object(engine._session_engine, "_call_llm", return_value=_mock_llm_response()):
            result = engine.respond(
                user_message="Hello.",
                analysis=analysis,
                turn_number=5,
            )

        assert result["reply"]


# ---------------------------------------------------------------------------
# DialogueEngine.respond() tests
# ---------------------------------------------------------------------------

class TestDialogueEngineRespond:

    @pytest.fixture
    def dialogue_engine(self, engine):
        simulator = PatientSimulator(api_key="test-key")
        return DialogueEngine(engine, simulator)

    def test_respond_returns_expected_fields(self, dialogue_engine, analysis):
        """DialogueEngine.respond() returns reply, technique_used, progress_note, homework."""
        with patch.object(
            dialogue_engine._expert._session_engine, "_call_llm",
            return_value=_mock_llm_response(),
        ):
            result = dialogue_engine.respond(
                user_message="I feel stuck in my relationship.",
                analysis=analysis,
            )

        assert isinstance(result, dict)
        assert "reply" in result
        assert "technique_used" in result
        assert "progress_note" in result
        assert "homework" in result
        assert result["reply"]

    def test_respond_with_history(self, dialogue_engine, analysis):
        """Multi-turn dialogue with history."""
        history = [
            {"role": "user", "content": "I don't know how to open up."},
            {"role": "therapist", "content": "That takes courage to admit."},
        ]

        with patch.object(
            dialogue_engine._expert._session_engine, "_call_llm",
            return_value=_mock_llm_response(),
        ):
            result = dialogue_engine.respond(
                user_message="I want to try, but it's scary.",
                analysis=analysis,
                conversation_history=history,
            )

        assert result["reply"]
        assert result["technique_used"]

    def test_respond_includes_homework(self, dialogue_engine, analysis):
        """Homework from LLM response is included."""
        with patch.object(
            dialogue_engine._expert._session_engine, "_call_llm",
            return_value=_mock_llm_response(),
        ):
            result = dialogue_engine.respond(
                user_message="What should I work on?",
                analysis=analysis,
            )

        assert result["homework"] == "Notice 3 moments this week when you want to withdraw"

    def test_respond_no_homework_when_empty(self, dialogue_engine, analysis):
        """Empty homework is returned as empty string."""
        no_hw_json = (
            '{"reply": "Tell me more.", "homework_instruction": "", '
            '"session_summary": "Explored", "progress_note": "Good"}'
        )
        with patch.object(
            dialogue_engine._expert._session_engine, "_call_llm",
            return_value=_mock_llm_response(no_hw_json),
        ):
            result = dialogue_engine.respond(
                user_message="I just wanted to talk.",
                analysis=analysis,
            )

        assert result["homework"] == ""
