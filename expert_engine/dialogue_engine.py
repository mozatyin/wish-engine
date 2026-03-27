"""Dialogue Engine — orchestrates multi-turn therapy conversations.

Runs a therapist<->patient dialogue loop using a unified generate_reply() pipeline:
1. Plan the turn (SessionPlanner — zero LLM)
2. Adapt tone (ToneAdapter — zero LLM)
3. Generate therapist reply (SessionEngine.generate_reply — 1x Sonnet, ~300 tokens)
4. Patient responds in-character (PatientSimulator.respond)
5. Repeat for N turns

Each turn produces a DialogueTurn with both sides + metadata.
A full dialogue produces a DialogueSession with all turns + quality metrics.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from expert_engine.engine import ExpertEngine, AnalysisResult
from expert_engine.patient_simulator import PatientSimulator, PatientProfile, PatientResponse
from expert_engine.session_planner import SessionPlanner
from expert_engine.tone_adapter import ToneAdapter


@dataclass
class DialogueTurn:
    """One exchange: therapist speaks, patient responds."""
    turn_number: int
    therapist_text: str
    therapist_homework: str
    patient_text: str
    patient_internal_state: str
    patient_resistance: float
    patient_resistance_reason: str
    patient_insight: bool


@dataclass
class DialogueSession:
    """Complete multi-turn therapy dialogue."""
    patient_id: str
    technique_used: str
    turns: list[DialogueTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    @property
    def avg_resistance(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.patient_resistance for t in self.turns) / len(self.turns)

    @property
    def resistance_trend(self) -> float:
        """Negative = resistance decreasing (good). Positive = increasing (bad)."""
        if len(self.turns) < 2:
            return 0.0
        return self.turns[-1].patient_resistance - self.turns[0].patient_resistance

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.patient_insight)

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "technique_used": self.technique_used,
            "turn_count": self.turn_count,
            "avg_resistance": round(self.avg_resistance, 2),
            "resistance_trend": round(self.resistance_trend, 2),
            "insights_gained": self.insights_gained,
            "total_time_seconds": round(self.total_time_seconds, 1),
            "turns": [
                {
                    "turn": t.turn_number,
                    "therapist": t.therapist_text[:300],
                    "homework": t.therapist_homework,
                    "patient": t.patient_text,
                    "internal": t.patient_internal_state,
                    "resistance": t.patient_resistance,
                    "resistance_reason": t.patient_resistance_reason,
                    "insight": t.patient_insight,
                }
                for t in self.turns
            ],
        }


class DialogueEngine:
    """Runs multi-turn therapy dialogues.

    Usage:
        engine = ExpertEngine(api_key=...)
        simulator = PatientSimulator(api_key=...)
        dialogue = DialogueEngine(engine, simulator)

        analysis = engine.analyze(signals, domain="mindfulness")
        profile = PatientSimulator.load_from_trisoul("tony_soprano")

        session = dialogue.run(
            analysis=analysis,
            patient_profile=profile,
            soul_context="Tony is a man who...",
            num_turns=5,
        )
    """

    def __init__(self, expert_engine: ExpertEngine, patient_simulator: PatientSimulator):
        self._expert = expert_engine
        self._patient = patient_simulator
        self._planner = SessionPlanner()
        self._tone = ToneAdapter()

    def _run_single_attempt(
        self,
        plan_text: str,
        tone_text: str,
        context: str,
        soul_context: str,
        profile: PatientProfile,
        conversation_history: list[dict],
    ) -> tuple:
        """One attempt at a therapist turn + patient response.

        Returns (therapist_response, patient_response) pair.
        Costs 2 LLM calls: 1 therapist + 1 patient.
        """
        therapist_resp = self._expert._session_engine.generate_reply(
            plan_text=plan_text,
            tone_text=tone_text,
            context=context,
            soul_context=soul_context,
        )
        patient_resp = self._patient.respond(
            profile=profile,
            therapist_message=therapist_resp.reply_text,
            conversation_history=conversation_history,
        )
        return therapist_resp, patient_resp

    def run(
        self,
        analysis: AnalysisResult,
        patient_profile: PatientProfile,
        soul_context: str = "",
        num_turns: int = 5,
        best_of: int = 1,
    ) -> DialogueSession:
        """Run a multi-turn therapy dialogue.

        Uses SessionEngine.generate_reply() for ALL turns (unified ~300-token pipeline).
        No more split between first_session() and continue_session().

        Args:
            best_of: Number of candidate replies per turn. 1=normal, 2+=generate
                     N replies and pick the one with lowest patient resistance.
                     Costs best_of * 2 LLM calls per turn.
        """
        t0 = time.time()
        technique = analysis.technique_recommendations[0]
        session = DialogueSession(
            patient_id=patient_profile.character_id,
            technique_used=technique.technique_id,
        )

        conversation_history: list[dict] = []
        signals = analysis.detector_signals or {}

        for turn_num in range(1, num_turns + 1):
            # --- Plan this turn (zero LLM) ---
            prev_r = session.turns[-1].patient_resistance if session.turns else None
            prev_prev_r = session.turns[-2].patient_resistance if len(session.turns) >= 2 else None
            prev_reason = session.turns[-1].patient_resistance_reason if session.turns else ""

            plan = self._planner.plan(
                techniques=analysis.technique_recommendations,
                turn_number=turn_num,
                crisis_level=float(signals.get("crisis_level", 0)),
                grief_active=bool(signals.get("grief_active", False)),
                prev_resistance=prev_r,
                prev_insight=session.turns[-1].patient_insight if session.turns else False,
                prev_technique_id=session.technique_used if session.turns else None,
                prev_prev_resistance=prev_prev_r,
                prev_resistance_reason=prev_reason,
            )

            # --- Adapt tone (zero LLM) ---
            tone = self._tone.adapt(
                signals=signals,
                technique_family=plan.technique_family,
            )

            # --- Build compact plan_text ---
            plan_text = (
                f"TECHNIQUE: {plan.technique_name}\n"
                f"GOAL: {plan.goal} | DEPTH: {plan.depth} | PACING: {plan.pacing}\n"
                f"FOCUS: {plan.focus_hint}"
            )

            # --- Build tone_text ---
            tone_text = tone.to_prompt_lines()

            # --- Build context ---
            if turn_num == 1:
                # Turn 1: just soul_context
                context = soul_context or ""
            else:
                # Turn 2+: recent conversation history (last 2-3 exchanges, 200 chars each)
                recent = conversation_history[-(min(6, len(conversation_history))):]
                lines = ["[Previous exchanges]"]
                for entry in recent:
                    role = "Therapist" if entry["role"] == "therapist" else "Patient"
                    lines.append(f"{role}: {entry['content'][:200]}")
                context = "\n".join(lines)

            # --- Generate reply (with optional best-of-N sampling) ---
            if best_of <= 1:
                therapist_resp, patient_resp = self._run_single_attempt(
                    plan_text, tone_text, context, soul_context,
                    patient_profile, conversation_history,
                )
            else:
                candidates = []
                for _ in range(best_of):
                    t, p = self._run_single_attempt(
                        plan_text, tone_text, context, soul_context,
                        patient_profile, conversation_history,
                    )
                    candidates.append((t, p))
                # Pick the pair with lowest patient resistance
                therapist_resp, patient_resp = min(
                    candidates, key=lambda x: x[1].resistance_level
                )

            therapist_text = therapist_resp.reply_text
            homework = therapist_resp.homework.instruction if therapist_resp.homework else ""

            conversation_history.append({"role": "therapist", "content": therapist_text})
            conversation_history.append({"role": "patient", "content": patient_resp.text})

            session.turns.append(DialogueTurn(
                turn_number=turn_num,
                therapist_text=therapist_text,
                therapist_homework=homework,
                patient_text=patient_resp.text,
                patient_internal_state=patient_resp.internal_state,
                patient_resistance=patient_resp.resistance_level,
                patient_resistance_reason=patient_resp.resistance_reason,
                patient_insight=patient_resp.insight_gained,
            ))


        session.total_time_seconds = time.time() - t0
        return session

    def respond(
        self,
        user_message: str,
        analysis: AnalysisResult,
        conversation_history: list[dict] | None = None,
        soul_context: str = "",
        turn_number: int | None = None,
    ) -> dict:
        """Single-turn therapist response for real-time dialogue. 1 LLM call.

        Same pipeline as run() but accepts a real user message instead of
        invoking the PatientSimulator. No patient simulation involved.

        Args:
            user_message: The real user's message.
            analysis: Pre-computed AnalysisResult from ExpertEngine.analyze().
            conversation_history: Previous exchanges as
                [{"role": "user"|"therapist", "content": "..."}].
            soul_context: Optional soul context summary for personalization.
            turn_number: Explicit turn number. If None, inferred from history.

        Returns:
            {"reply": str, "technique_used": str, "progress_note": str,
             "homework": str}
        """
        history = conversation_history or []
        if turn_number is None:
            turn_number = len([h for h in history if h.get("role") == "user"]) + 1

        signals = analysis.detector_signals or {}

        # --- Plan this turn (0 LLM) ---
        plan = self._planner.plan(
            techniques=analysis.technique_recommendations,
            turn_number=turn_number,
            crisis_level=float(signals.get("crisis_level", 0)),
            grief_active=bool(signals.get("grief_active", False)),
        )

        # --- Adapt tone (0 LLM) ---
        tone = self._tone.adapt(
            signals=signals,
            technique_family=plan.technique_family,
        )

        # --- Build plan_text and tone_text ---
        plan_text = (
            f"TECHNIQUE: {plan.technique_name}\n"
            f"GOAL: {plan.goal} | DEPTH: {plan.depth} | PACING: {plan.pacing}\n"
            f"FOCUS: {plan.focus_hint}"
        )
        tone_text = tone.to_prompt_lines()

        # --- Build context from history + current user message ---
        context_parts = []
        if history:
            recent = history[-(min(6, len(history))):]
            context_parts.append("[Previous exchanges]")
            for entry in recent:
                role = "Therapist" if entry.get("role") == "therapist" else "Patient"
                context_parts.append(f"{role}: {entry.get('content', '')[:200]}")
        context_parts.append(f"Patient: {user_message}")
        context = "\n".join(context_parts)

        # --- Generate reply (1 LLM call) ---
        therapist_resp = self._expert._session_engine.generate_reply(
            plan_text=plan_text,
            tone_text=tone_text,
            context=context,
            soul_context=soul_context,
        )

        homework = therapist_resp.homework.instruction if therapist_resp.homework else ""

        return {
            "reply": therapist_resp.reply_text,
            "technique_used": plan.technique_id,
            "progress_note": therapist_resp.progress_note,
            "homework": homework,
        }
