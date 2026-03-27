"""ExpertEngine — unified public API that ties all layers together."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from expert_engine.case_formulator import CaseFormulator
from expert_engine.models import (
    CaseFormulation,
    SchemaProfile,
    SessionResponse,
    SessionState,
    TechniqueRecommendation,
)
from expert_engine.progress_tracker import ProgressTracker
from expert_engine.schema_detector import SchemaDetector
from expert_engine.session_engine import SessionEngine
from expert_engine.session_planner import SessionPlanner
from expert_engine.technique_selector import TechniqueSelector
from expert_engine.tone_adapter import ToneAdapter

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of analyzing a user's detector signals."""

    case_formulation: CaseFormulation
    schema_profile: SchemaProfile
    technique_recommendations: list[TechniqueRecommendation]
    detector_signals: dict = None  # Original signals for prompt builder
    domain: Optional[str] = None  # User's presenting domain (mindfulness, relationship, etc.)


class ExpertEngine:
    """Unified facade for the Expert Engine pipeline.

    Layer 1+2: analyze() — case formulation + schema detection + technique selection
    Layer 3:   first_session() / continue_session() — LLM-powered therapeutic dialogue
    Utility:   compute_progress() — dimension change tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self._case_formulator = CaseFormulator()
        self._schema_detector = SchemaDetector()
        self._technique_selector = TechniqueSelector()
        self._session_engine = SessionEngine(api_key=api_key, base_url=base_url, model=model)
        self._progress_tracker = ProgressTracker()
        self._session_planner = SessionPlanner()
        self._tone_adapter = ToneAdapter()

    def analyze(
        self,
        detector_signals: dict,
        deep_soul_items: list[dict] | None = None,
        surface_facts: list[dict] | None = None,
        cross_detector_patterns: list[dict] | None = None,
        domain: Optional[str] = None,
    ) -> AnalysisResult:
        """Layer 1+2: Analyze user signals -> case formulation + schemas + technique recommendations."""
        cf = self._case_formulator.formulate(
            detector_signals=detector_signals,
            deep_soul_items=deep_soul_items or [],
            surface_facts=surface_facts or [],
            cross_detector_patterns=cross_detector_patterns or [],
        )
        sp = self._schema_detector.detect(detector_signals, user_id=cf.user_id)
        recommendations = self._technique_selector.select(cf, sp, detector_signals, domain=domain)
        return AnalysisResult(
            case_formulation=cf,
            schema_profile=sp,
            technique_recommendations=recommendations,
            detector_signals=detector_signals,
            domain=domain,
        )

    def first_session(
        self,
        analysis: AnalysisResult,
        soul_context_summary: str = "",
        technique_index: int = 0,
    ) -> SessionResponse:
        """Layer 3: Generate first session response using top technique."""
        technique = analysis.technique_recommendations[technique_index]
        return self._session_engine.first_session(
            case_formulation=analysis.case_formulation,
            technique=technique,
            soul_context_summary=soul_context_summary,
            signals=analysis.detector_signals or {},
        )

    def continue_session(
        self,
        analysis: AnalysisResult,
        session_state: SessionState,
        soul_context_summary: str = "",
        dimension_changes: dict[str, float] | None = None,
        technique_index: int = 0,
    ) -> SessionResponse:
        """Layer 3: Generate continuing session response."""
        technique = analysis.technique_recommendations[technique_index]
        return self._session_engine.continue_session(
            case_formulation=analysis.case_formulation,
            technique=technique,
            session_state=session_state,
            soul_context_summary=soul_context_summary,
            dimension_changes=dimension_changes or {},
            signals=analysis.detector_signals or {},
        )

    def respond(
        self,
        user_message: str,
        analysis: AnalysisResult,
        conversation_history: list[dict] | None = None,
        soul_context: str = "",
        turn_number: int | None = None,
    ) -> dict:
        """Single-turn expert response for real-time dialogue. 1 LLM call.

        Unlike the simulation path (DialogueEngine.run), this accepts a real
        user message and returns only the therapist reply — no patient
        simulator involved.

        Args:
            user_message: The real user's message.
            analysis: Pre-computed AnalysisResult from analyze().
            conversation_history: Previous exchanges as
                [{"role": "user"|"expert", "text": "..."}].
            soul_context: Optional soul context summary for personalization.
            turn_number: Explicit turn number. If None, inferred from
                conversation_history length.

        Returns:
            {"reply": str, "technique_used": str, "progress_note": str}
        """
        history = conversation_history or []
        if turn_number is None:
            turn_number = len([h for h in history if h.get("role") == "user"]) + 1

        signals = analysis.detector_signals or {}

        # --- Step 1: Plan this turn (0 LLM) ---
        plan = self._session_planner.plan(
            techniques=analysis.technique_recommendations,
            turn_number=turn_number,
            crisis_level=float(signals.get("crisis_level", 0)),
            grief_active=bool(signals.get("grief_active", False)),
        )

        # --- Step 2: Adapt tone (0 LLM) ---
        tone = self._tone_adapter.adapt(
            signals=signals,
            technique_family=plan.technique_family,
        )

        # --- Step 3: Build plan_text and tone_text ---
        plan_text = (
            f"TECHNIQUE: {plan.technique_name}\n"
            f"GOAL: {plan.goal} | DEPTH: {plan.depth} | PACING: {plan.pacing}\n"
            f"FOCUS: {plan.focus_hint}"
        )
        tone_text = tone.to_prompt_lines()

        # --- Step 4: Build context from conversation_history + user_message ---
        context_parts = []
        if history:
            recent = history[-(min(6, len(history))):]
            context_parts.append("[Previous exchanges]")
            for entry in recent:
                role = "Expert" if entry.get("role") == "expert" else "User"
                text = entry.get("text", entry.get("content", ""))
                context_parts.append(f"{role}: {text[:200]}")
        context_parts.append(f"User: {user_message}")
        context = "\n".join(context_parts)

        # --- Step 5: Generate reply (1 LLM call) ---
        session_resp = self._session_engine.generate_reply(
            plan_text=plan_text,
            tone_text=tone_text,
            context=context,
            soul_context=soul_context,
        )

        return {
            "reply": session_resp.reply_text,
            "technique_used": plan.technique_id,
            "progress_note": session_resp.progress_note,
        }

    def compute_progress(
        self, before: dict[str, float], after: dict[str, float]
    ) -> tuple[dict[str, float], float]:
        """Compute dimension changes and improvement score."""
        changes = self._progress_tracker.compute_changes(before, after)
        score = self._progress_tracker.improvement_score(changes)
        return changes, score

    def batch_first_sessions(
        self,
        analyses: dict[str, AnalysisResult],
        soul_contexts: dict[str, str],
        max_workers: int = 5,
    ) -> dict[str, SessionResponse]:
        """Run first_session for multiple patients in parallel using ThreadPoolExecutor."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results: dict[str, SessionResponse] = {}

        def _run(pid: str) -> tuple[str, SessionResponse | Exception]:
            try:
                resp = self.first_session(
                    analysis=analyses[pid],
                    soul_context_summary=soul_contexts.get(pid, ""),
                    technique_index=0,
                )
                return pid, resp
            except Exception as e:
                logger.warning("Expert session failed for %s: %s", pid, e)
                return pid, e

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_run, pid): pid for pid in analyses}
            for future in as_completed(futures):
                pid, result = future.result()
                if isinstance(result, Exception):
                    results[pid] = None
                else:
                    results[pid] = result

        return results
