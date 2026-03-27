"""Relationship Advisor Engine — runs relationship self-insight sessions.

Uses ONLY one person's Soul to show them their relationship patterns.
Never analyzes the other person. Same principle as Growth Coach:
"你以为问题是对方，但你的 Soul 说..."

Pipeline: PatternMirror → PersuasionPlanner → ToneAdapter → ReplyGenerator
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from expert_engine.goal_generator import SoulItem
from expert_engine.patient_simulator import PatientSimulator, PatientProfile, PatientResponse
from expert_engine.relationship_advisor.pattern_mirror import PatternMirror, RelationshipInsight
from expert_engine.growth_coach.persuasion_planner import PersuasionPlanner
from expert_engine.tone_adapter import ToneAdapter
from expert_engine.session_engine import SessionEngine


@dataclass
class InsightTurn:
    """One exchange in a relationship insight session."""
    turn_number: int
    advisor_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class InsightSession:
    """Complete relationship insight session."""
    client_id: str
    insight: RelationshipInsight | None = None
    turns: list[InsightTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)

    @property
    def pattern_recognized(self) -> bool:
        """Did the client recognize at least one pattern?"""
        return self.insights_gained >= 2 and any(
            t.client_resistance <= 0.3 and t.client_insight for t in self.turns[-3:]
        ) if self.turns else False


class RelationshipEngine:
    """Runs relationship self-insight sessions.

    Key difference from therapy and growth:
    - Therapy: reduce pain
    - Growth: amplify potential
    - Relationship: reveal pattern ("你以为问题是对方...")
    """

    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._session_engine = session_engine
        self._patient = patient_simulator
        self._mirror = PatternMirror()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(
        self,
        client_profile: PatientProfile,
        signals: dict,
        focus_items: list[SoulItem],
        deep_items: list[SoulItem],
        memory_items: list[SoulItem] | None = None,
        num_turns: int = 5,
    ) -> InsightSession:
        """Run a relationship insight session."""
        num_turns = min(num_turns, 15)
        t0 = time.time()

        # Step 1: Analyze relationship patterns
        insight = self._mirror.analyze(signals, focus_items, deep_items, memory_items)

        session = InsightSession(client_id=client_profile.character_id, insight=insight)

        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        # Step 2: Generate persuasion strategy for the main pattern
        strategy = self._persuasion.plan(
            focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"recognize your {insight.patterns[0].pattern_name} pattern",
            memory_items=memory_items,
        )

        # Step 3: Build advisor context
        pattern_section = "\n".join(
            f"- STRENGTH: {p.capability}\n"
            f"  Shadow side: {p.description}\n"
            f"  Blind spot: {p.blind_spot}\n"
            f"  Reframe: {p.reframe}\n"
            f"  Action: {p.action_step}"
            for p in insight.patterns[:2]
        )

        mismatch_section = f"\nLOVE MISMATCH: {insight.mismatch}" if insight.mismatch else ""

        advisor_context = (
            f"{client_profile.soul_context}\n\n"
            f"THEIR RELATIONSHIP STRENGTHS (lead with these!):\n{pattern_section}\n"
            f"CORE NEED: {insight.core_need}\n"
            f"GIVING STYLE: {insight.giving_style}\n"
            f"RECEIVING NEED: {insight.receiving_need}"
            f"{mismatch_section}\n\n"
            f"SOUL RESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION:\n"
            f"  Deep need: {strategy.deep_need}\n"
            f"  USE: {', '.join(strategy.use_words[:5])}\n"
            f"  AVOID: {', '.join(strategy.avoid_words[:5])}\n\n"
            f"YOUR APPROACH: Relationship advisor. STRENGTH-BASED, not diagnostic.\n"
            f"1. START by naming their CAPABILITY (not their problem)\n"
            f"2. Show how this capability has a shadow side (using their Soul evidence)\n"
            f"3. REFRAME: 'you already know how to love — the evidence is [soul_evidence]'\n"
            f"4. END with the concrete ACTION STEP\n"
            f"NEVER blame the other person. NEVER say 'your pattern is...' — say 'your gift is...'"
        )

        # Adapt tone
        tone = self._tone.adapt(signals=signals, technique_family="relationship")
        tone.dos.insert(0, "Mirror, don't judge. Show them their pattern using their own evidence")
        tone.donts.insert(0, "NEVER blame the other person. NEVER say 'your partner should...'")
        tone_text = tone.to_prompt_lines()

        conversation_history: list[dict] = []
        current_pattern_idx = 0

        for turn_num in range(1, num_turns + 1):
            current_pattern = insight.patterns[min(current_pattern_idx, len(insight.patterns) - 1)]

            # Build plan
            if turn_num == 1:
                plan_text = (
                    f"TECHNIQUE: Relationship Self-Insight — Pattern Mirror\n"
                    f"GOAL: introduce | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: Ask about their relationship complaint. Listen. Then gently reflect: "
                    f"'I notice something interesting in what you just said...' "
                    f"Plant the seed of {current_pattern.pattern_name} without naming it yet."
                )
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                current_pattern_idx = min(current_pattern_idx + 1, len(insight.patterns) - 1)
                current_pattern = insight.patterns[current_pattern_idx]
                plan_text = (
                    f"TECHNIQUE: Relationship Self-Insight — Pivot\n"
                    f"GOAL: build_rapport | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: They resisted that angle. Back off. Ask about a positive relationship memory instead. "
                    f"Then approach {current_pattern.pattern_name} from a different angle."
                )
            elif session.turns and session.turns[-1].client_insight:
                plan_text = (
                    f"TECHNIQUE: Relationship Self-Insight — Deepen\n"
                    f"GOAL: deepen | DEPTH: deep | PACING: push\n"
                    f"FOCUS: They saw the pattern. Now connect it to the REFRAME: '{current_pattern.reframe[:80]}'. "
                    f"Ask: 'What would change if you tried [reframe] instead of [current behavior]?'"
                )
            else:
                plan_text = (
                    f"TECHNIQUE: Relationship Self-Insight — Reveal\n"
                    f"GOAL: deepen | DEPTH: medium | PACING: normal\n"
                    f"FOCUS: Show them the pattern: '{current_pattern.blind_spot[:80]}'. "
                    f"Use their Soul evidence: {current_pattern.soul_evidence[:2]}."
                )

            # Build context
            context_lines = [f"{'Advisor' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}"
                           for e in conversation_history[-4:]]
            context = "\n".join(context_lines)

            # Generate advisor reply
            advisor_resp = self._session_engine.generate_reply(
                plan_text=plan_text, tone_text=tone_text,
                context=context, soul_context=advisor_context,
            )

            conversation_history.append({"role": "therapist", "content": advisor_resp.reply_text})

            # Client responds
            client_resp = self._patient.respond(
                profile=client_profile,
                therapist_message=advisor_resp.reply_text,
                conversation_history=conversation_history[:-1],
            )

            conversation_history.append({"role": "patient", "content": client_resp.text})

            session.turns.append(InsightTurn(
                turn_number=turn_num,
                advisor_text=advisor_resp.reply_text,
                client_text=client_resp.text,
                client_internal_state=client_resp.internal_state,
                client_resistance=client_resp.resistance_level,
                client_resistance_reason=client_resp.resistance_reason,
                client_insight=client_resp.insight_gained,
                pattern_addressed=current_pattern.pattern_name,
            ))


        session.total_time_seconds = time.time() - t0
        return session
