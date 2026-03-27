"""Layer 3 Session Engine — 1x Sonnet per response for personalized therapeutic dialogue."""

from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from expert_engine.llm_client import get_client, call_llm_with_retry, parse_json_response
from expert_engine.models import (
    CaseFormulation,
    Homework,
    HomeworkType,
    SessionResponse,
    SessionState,
    TechniqueRecommendation,
)
from expert_engine.prompt_builder import PromptBuilder
from expert_engine.techniques import TechniqueRegistry

logger = logging.getLogger(__name__)

# Map technique families to default homework types
_FAMILY_HOMEWORK_MAP: dict[str, HomeworkType] = {
    "cbt": HomeworkType.THOUGHT_RECORD,
    "act": HomeworkType.DEFUSION_PRACTICE,
    "schema": HomeworkType.SCHEMA_DIARY,
    "dbt": HomeworkType.DISTRESS_TOLERANCE,
    "attachment": HomeworkType.ATTACHMENT_REFLECTION,
    "relationship": HomeworkType.RELATIONSHIP_JOURNAL,
    "career": HomeworkType.CAREER_REFLECTION,
    "emotion_coaching": HomeworkType.EMOTION_LOG,
    "life_coaching": HomeworkType.GRATITUDE_JOURNAL,
    "social": HomeworkType.SOCIAL_EXPOSURE,
    "parenting": HomeworkType.PARENTING_JOURNAL,
    "mindfulness": HomeworkType.MINDFULNESS_LOG,
    "finance": HomeworkType.FINANCE_TRACKER,
    "sleep": HomeworkType.SLEEP_DIARY,
    "education": HomeworkType.LEARNING_LOG,
}


class SessionEngine:
    """Generates personalized therapeutic dialogue within a technique's framework.

    Calls 1x Sonnet per response. The ``_call_llm`` method is designed to be
    easily mocked in tests — no real API calls should occur during testing.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        base_url: Optional[str] = None,
    ):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._is_openrouter = self._api_key.startswith("sk-or-")
        if self._is_openrouter and model == "claude-sonnet-4-20250514":
            model = "anthropic/claude-sonnet-4"
        self._model = model
        self._base_url = base_url or os.environ.get("ANTHROPIC_BASE_URL")
        if self._is_openrouter and not self._base_url:
            self._base_url = "https://openrouter.ai/api"
        self._client = get_client(api_key=self._api_key, base_url=self._base_url)
        self._prompt_builder = PromptBuilder()
        self._registry = TechniqueRegistry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def first_session(
        self,
        case_formulation: CaseFormulation,
        technique: TechniqueRecommendation,
        soul_context_summary: str,
        signals: Optional[dict] = None,
    ) -> SessionResponse:
        """Generate first expert session response."""
        system_prompt = self._prompt_builder.build_first_session(
            case_formulation=case_formulation,
            technique=technique,
            soul_context_summary=soul_context_summary,
            signals=signals or {},
        )
        # Build patient context for the user message
        patient_intro = ""
        if soul_context_summary:
            patient_intro = f"ABOUT THIS PERSON:\n{soul_context_summary}\n\n"

        user_message = (
            f"{patient_intro}"
            "Begin the first session. Your goals:\n"
            "1. Build rapport FIRST — show you understand their world. Do NOT probe deep wounds yet.\n"
            "2. Name ONE pattern you see, gently. Let them correct you if wrong.\n"
            "3. Introduce ONE small exercise from the technique — keep it light and safe.\n"
            "4. Assign easy homework for THIS WEEK — something they'll actually do.\n\n"
            "PACING: This is turn 1. Go SLOW. Earn trust before going deep. "
            "If they seem open, still hold back — depth comes in turns 2-3, not turn 1. "
            "Match their communication style. No flowery metaphors with direct people.\n\n"
            'Respond in JSON: {"reply": "...", "homework_instruction": "...", '
            '"session_summary": "...", "progress_note": "..."}'
        )
        response = self._call_llm(system_prompt, user_message)
        return self._parse_response(response, technique)

    def continue_session(
        self,
        case_formulation: CaseFormulation,
        technique: TechniqueRecommendation,
        session_state: SessionState,
        soul_context_summary: str,
        dimension_changes: dict[str, float],
        signals: Optional[dict] = None,
    ) -> SessionResponse:
        """Generate continuing session response."""
        system_prompt = self._prompt_builder.build_ongoing_session(
            case_formulation=case_formulation,
            technique=technique,
            session_state=session_state,
            soul_context_summary=soul_context_summary,
            dimension_changes=dimension_changes,
            signals=signals or {},
        )
        # Build continuation context
        continuation_context = ""
        if dimension_changes:
            improvements = [f"{k}: {v:+.2f}" for k, v in dimension_changes.items() if v != 0]
            if improvements:
                continuation_context += f"CHANGES SINCE LAST SESSION: {', '.join(improvements)}\n"
        # Add previous session summary so LLM can reference specifics
        if session_state.history:
            last_reply = ""
            for entry in reversed(session_state.history):
                if entry.get("content"):
                    last_reply = entry["content"][:200]
                    break
            if last_reply:
                continuation_context += f"LAST SESSION SUMMARY: {last_reply}\n"
        if session_state.homework_pending:
            hw = session_state.homework_pending[-1]
            if hw.completed and hw.user_reflection:
                continuation_context += f"HOMEWORK REFLECTION: {hw.user_reflection}\n"

        session_num = session_state.session_number
        deepening = (
            "3. DEEPEN: Now that they've done the initial work, take it further. "
            "Say something like 'Now that you've noticed X, let's go deeper into...' or "
            "'Building on what you discovered, let's explore...' or "
            "'You're ready for the next step...'\n"
        ) if session_num >= 3 else (
            "3. Deepen the technique — go one level further than last session\n"
        )

        user_message = (
            f"{continuation_context}\n"
            f"This is session {session_num}. Continue the session. Your goals:\n"
            "1. Start by referencing something specific from the last session — show you remember\n"
            "2. Ask about their homework — 'How did [specific homework] go for you?'\n"
            f"{deepening}"
            "4. Assign new homework that builds on what they've done\n\n"
            'Respond in JSON: {"reply": "...", "homework_instruction": "...", '
            '"session_summary": "...", "progress_note": "..."}'
        )
        response = self._call_llm(system_prompt, user_message)
        return self._parse_response(response, technique)

    def generate_reply(
        self,
        plan_text: str,
        tone_text: str,
        context: str,
        soul_context: str = "",
    ) -> SessionResponse:
        """Generate therapist reply from pre-computed plan and tone.

        NEW PATH (modular pipeline):
            DialogueEngine.run() -> PlanGenerator -> ToneAdapter -> generate_reply()
            Plan and tone are pre-computed; this method just renders the final reply.
            Prompt is ~300 tokens instead of PromptBuilder's ~700.

        OLD PATH (single-shot API, backward-compatible):
            ExpertEngine.first_session() / continue_session() -> PromptBuilder
            PromptBuilder (prompt_builder.py, 817 lines) constructs technique-constrained
            prompts with stars language, soul-aware guidance, defense matrices, etc.
            Kept for backward compatibility — not used by DialogueEngine.

        Homework parsing: uses a dummy technique ("modular"), so homework_type
        defaults to PATTERN_AWARENESS via _FAMILY_HOMEWORK_MAP fallback.
        This is intentional — the modular pipeline doesn't route by technique family.
        """
        # Fallbacks for empty inputs
        effective_plan = plan_text if plan_text.strip() else (
            "Listen actively. Reflect back what the patient shares. "
            "Ask one open-ended question to deepen understanding."
        )
        effective_tone = tone_text if tone_text.strip() else (
            "Speak in a warm and supportive tone. Be genuine and present."
        )

        system_prompt = (
            "You are a therapist. Generate ONE response to your patient.\n"
            f"{effective_tone}\n"
            f"{effective_plan}\n"
            "Never use clinical jargon (CBT, schema, transference). Use natural words.\n"
            "End with a specific homework assignment if appropriate."
        )

        soul_part = f"{soul_context}\n\n" if soul_context else ""
        user_message = (
            f"{context}\n\n"
            f"{soul_part}"
            'Respond in JSON: {"reply": "your response (150 words max)", '
            '"homework_instruction": "specific homework or empty string", '
            '"session_summary": "1 sentence summary", '
            '"progress_note": "1 sentence clinical note"}'
        )

        response = self._call_llm(system_prompt, user_message)
        dummy_tech = TechniqueRecommendation(
            technique_id="modular", technique_name="modular", family="modular",
            rationale="", match_score=0.0,
        )
        return self._parse_response(response, dummy_tech)

    # ------------------------------------------------------------------
    # LLM interaction
    # ------------------------------------------------------------------

    def _call_llm(self, system_prompt: str, user_message: str):
        """Call Anthropic API with retry. This method is designed to be easily mocked in tests."""
        return call_llm_with_retry(
            self._client,
            model=self._model,
            max_tokens=768,  # Reduced from 1024, enough for reply+homework JSON
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, response, technique: TechniqueRecommendation) -> SessionResponse:
        """Parse LLM JSON response into SessionResponse."""
        text = response.content[0].text

        # Parse JSON with fallback + logging
        data = parse_json_response(text)
        json_parsed = data.get("reply") != text  # True if JSON was successfully parsed

        # Build homework from response
        hw_instruction = data.get("homework_instruction", "")
        homework = None
        if hw_instruction:
            # Get homework type from technique's family (default)
            hw_type = _FAMILY_HOMEWORK_MAP.get(technique.family, HomeworkType.PATTERN_AWARENESS)
            # Try to get from registry for more specific type
            tech = self._registry.get(technique.technique_id)
            if tech:
                hw_type = tech.homework_type
            homework = Homework(
                homework_type=hw_type,
                instruction=hw_instruction,
                technique_id=technique.technique_id,
            )

        reply_text = data.get("reply", "")
        # Fallback: if JSON parsing failed and the parsed reply is suspiciously
        # short but raw text is longer, the JSON was likely malformed — use raw text
        if not json_parsed and len(reply_text) < 200 and len(text) > 200:
            reply_text = text

        return SessionResponse(
            reply_text=reply_text,
            technique_used=technique.technique_id,
            homework=homework,
            session_summary=data.get("session_summary", ""),
            progress_note=data.get("progress_note", ""),
        )
