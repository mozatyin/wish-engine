"""Growth Coach Engine — runs growth-oriented dialogue sessions.

Uses the same modular pipeline as Expert Engine:
  PotentialDetector → GrowthPlanner → ToneAdapter → ReplyGenerator

But the DIRECTION is inverted:
  Therapy: reduce problems in Focus
  Growth: activate potentials from Deep into Focus
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from expert_engine.goal_generator import SoulItem
from expert_engine.patient_simulator import PatientSimulator, PatientProfile, PatientResponse
from expert_engine.growth_coach.potential_detector import PotentialDetector, GrowthGoal, Potential
from expert_engine.growth_coach.persuasion_planner import PersuasionPlanner, PersuasionStrategy
from expert_engine.tone_adapter import ToneAdapter, ToneDirective
from expert_engine.session_engine import SessionEngine


@dataclass
class GrowthTurn:
    """One exchange in a growth coaching session."""
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    potential_referenced: str  # Which potential was the coach working on


@dataclass
class GrowthSession:
    """Complete growth coaching dialogue."""
    client_id: str
    potentials_found: list[Potential] = field(default_factory=list)
    goal: GrowthGoal | None = None
    turns: list[GrowthTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)

    @property
    def activation_achieved(self) -> bool:
        """Did at least one potential get activated (resistance < 0.3 + insight)?"""
        return any(t.client_resistance <= 0.3 and t.client_insight for t in self.turns[-2:]) if self.turns else False


class GrowthEngine:
    """Runs growth coaching dialogues.

    Pipeline:
    1. PotentialDetector finds dormant strengths/dreams/talents
    2. GrowthPlanner picks which potential to work on this turn
    3. ToneAdapter adapts style (growth = more energizing than therapy)
    4. ReplyGenerator generates coaching response
    5. Client responds (PatientSimulator in "growth mode")
    """

    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._session_engine = session_engine
        self._patient = patient_simulator
        self._detector = PotentialDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(
        self,
        client_profile: PatientProfile,
        focus_items: list[SoulItem],
        deep_items: list[SoulItem],
        memory_items: list[SoulItem] | None = None,
        num_turns: int = 5,
    ) -> GrowthSession:
        """Run a growth coaching dialogue."""
        num_turns = min(num_turns, 15)
        t0 = time.time()

        # Step 1: Detect potentials
        potentials = self._detector.detect(focus_items, deep_items, memory_items)
        goal = self._detector.generate_growth_goal(potentials, focus_items)

        session = GrowthSession(
            client_id=client_profile.character_id,
            potentials_found=potentials,
            goal=goal,
        )

        if not potentials:
            session.total_time_seconds = time.time() - t0
            return session

        # Step 1b: Generate persuasion strategy
        strategy = self._persuasion.plan(
            focus_items=focus_items,
            deep_items=deep_items,
            target_suggestion=client_profile.soul_context[:100] if client_profile.soul_context else "pursue growth",
            memory_items=memory_items,
        )

        # Build coaching context with persuasion intelligence
        potential_hints = "\n".join(
            f"- HIDDEN {p.category.upper()}: {p.text} (dormancy={p.dormancy:.0%})"
            for p in potentials[:5]
        )

        persuasion_section = (
            f"\nPERSUASION STRATEGY (CRITICAL — follow this):\n"
            f"Their surface resistance: {strategy.surface_resistance}\n"
            f"Their REAL need underneath: {strategy.deep_need}\n"
            f"REFRAME: {strategy.reframe}\n"
            f"Soul lever (use this!): {strategy.soul_lever[:80]}\n"
            f"OPENING: {strategy.opening_angle[:120]}\n"
            f"USE these words: {', '.join(strategy.use_words[:6])}\n"
            f"AVOID these words: {', '.join(strategy.avoid_words[:6])}"
        )

        coaching_context = (
            f"{client_profile.soul_context}\n\n"
            f"POTENTIALS:\n{potential_hints}\n"
            f"{persuasion_section}\n\n"
            f"YOUR APPROACH: Growth coach, NOT therapist. "
            f"EXCITE them about potential. Use their Soul material to make THEM discover the answer. "
            f"Never suggest directly — lead them to discover it themselves."
        )

        # Adapt tone for growth (more energizing than therapy)
        signals = client_profile.signals or {}
        tone = self._tone.adapt(signals=signals, technique_family="life_coaching")
        # Override: growth tone is always more energizing
        tone.dos.insert(0, "Be energizing and forward-looking — this is about POSSIBILITY not problems")
        tone.donts.insert(0, "Don't dwell on pain or past trauma — redirect to future potential")

        tone_text = tone.to_prompt_lines()
        conversation_history: list[dict] = []

        # Step 2: Run dialogue
        current_potential_idx = 0
        for turn_num in range(1, num_turns + 1):
            # Pick which potential to work on
            current_potential = potentials[min(current_potential_idx, len(potentials) - 1)]

            # Build plan
            if turn_num == 1:
                plan_text = (
                    f"TECHNIQUE: Growth Coaching — Potential Activation\n"
                    f"GOAL: introduce | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: Build rapport. Then casually mention something from their past that hints at their hidden {current_potential.category}: '{current_potential.text[:50]}'. "
                    f"Don't push — just plant the seed. Ask 'did you ever...?' or 'I notice something interesting about you...'"
                )
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                # Resistance high — switch to a different potential
                current_potential_idx = min(current_potential_idx + 1, len(potentials) - 1)
                current_potential = potentials[current_potential_idx]
                plan_text = (
                    f"TECHNIQUE: Growth Coaching — Pivot\n"
                    f"GOAL: build_rapport | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: They weren't ready for that angle. Try a different one. "
                    f"Ask about their {current_potential.category}: '{current_potential.text[:50]}'. "
                    f"Be lighter, more curious."
                )
            elif session.turns and session.turns[-1].client_insight:
                # They had an insight — deepen this potential
                plan_text = (
                    f"TECHNIQUE: Growth Coaching — Deepen Potential\n"
                    f"GOAL: deepen | DEPTH: deep | PACING: push\n"
                    f"FOCUS: They're connecting to their {current_potential.category}. Build on it. "
                    f"Ask: 'What would it look like if you actually pursued this?' "
                    f"'What's the smallest step you could take THIS WEEK?' "
                    f"Make it concrete and exciting."
                )
            else:
                plan_text = (
                    f"TECHNIQUE: Growth Coaching — Explore Potential\n"
                    f"GOAL: deepen | DEPTH: medium | PACING: normal\n"
                    f"FOCUS: Continue exploring their {current_potential.category}: '{current_potential.text[:50]}'. "
                    f"Connect it to their current life. 'How could this fit into who you are now?'"
                )

            # Build context
            context_lines = []
            for entry in conversation_history[-4:]:
                role = "Coach" if entry["role"] == "therapist" else "Client"
                context_lines.append(f"{role}: {entry['content'][:200]}")
            context = "\n".join(context_lines) if context_lines else ""

            # Generate coach reply
            coach_resp = self._session_engine.generate_reply(
                plan_text=plan_text,
                tone_text=tone_text,
                context=context,
                soul_context=coaching_context,
            )

            conversation_history.append({"role": "therapist", "content": coach_resp.reply_text})

            # Client responds
            client_resp = self._patient.respond(
                profile=client_profile,
                therapist_message=coach_resp.reply_text,
                conversation_history=conversation_history[:-1],
            )

            conversation_history.append({"role": "patient", "content": client_resp.text})

            session.turns.append(GrowthTurn(
                turn_number=turn_num,
                coach_text=coach_resp.reply_text,
                client_text=client_resp.text,
                client_internal_state=client_resp.internal_state,
                client_resistance=client_resp.resistance_level,
                client_resistance_reason=client_resp.resistance_reason,
                client_insight=client_resp.insight_gained,
                potential_referenced=current_potential.text[:50],
            ))


        session.total_time_seconds = time.time() - t0
        return session
