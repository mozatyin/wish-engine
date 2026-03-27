"""Child Companion Engine — runs age-appropriate companion dialogues.

Not therapy. Not teaching. Companionship + problem-solving + growth.

Pipeline: ProblemDetector -> AgeAdapter -> StrengthFinder -> ReplyGenerator

Core principles:
1. VALIDATE before anything else
2. Use THEIR strengths (from Soul) to solve THEIR problems
3. Give the problem a name (externalize for younger kids)
4. Concrete action they can try tomorrow
5. REMEMBER everything — be the friend who never forgets
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from expert_engine.goal_generator import SoulItem
from expert_engine.patient_simulator import PatientSimulator, PatientProfile, PatientResponse
from expert_engine.child_companion.age_adapter import AgeAdapter, AgeProfile
from expert_engine.child_companion.problem_detector import ProblemDetector, ChildProblem, SafetyAlert
from expert_engine.session_engine import SessionEngine


@dataclass
class CompanionTurn:
    """One exchange between companion and child."""
    turn_number: int
    companion_text: str
    child_text: str
    child_feeling: str
    problems_detected: list[str]
    safety_alert: Optional[str]
    strength_used: str  # Which Soul strength was referenced
    child_engagement: float  # 0-1 based on response length and content


@dataclass
class CompanionSession:
    """A conversation session between child and companion."""
    child_id: str
    child_age: int
    turns: list[CompanionTurn] = field(default_factory=list)
    problems_addressed: list[str] = field(default_factory=list)
    strengths_activated: list[str] = field(default_factory=list)
    safety_alerts: list[str] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def engagement_score(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.child_engagement for t in self.turns) / len(self.turns)


class CompanionEngine:
    """The child's AI companion — a friend who remembers everything and always helps.

    Usage:
        engine = CompanionEngine(session_engine, simulator)
        session = engine.chat(
            child_profile=profile,
            child_age=7,
            child_message="Nobody wants to play with me at school",
            soul_strengths=[SoulItem(text="I build amazing Lego castles", ...)],
            soul_memories=[SoulItem(text="Grandma says I'm the kindest person she knows", ...)],
        )
    """

    def __init__(self, session_engine: SessionEngine, child_simulator: PatientSimulator):
        self._session_engine = session_engine
        self._child_sim = child_simulator
        self._age_adapter = AgeAdapter()
        self._problem_detector = ProblemDetector()

    def chat(
        self,
        child_profile: PatientProfile,
        child_age: int,
        child_message: str,
        soul_strengths: list[SoulItem] | None = None,
        soul_memories: list[SoulItem] | None = None,
        conversation_history: list[dict] | None = None,
        num_turns: int = 5,
    ) -> CompanionSession:
        """Have a conversation with the child."""
        num_turns = min(num_turns, 15)
        t0 = time.time()

        session = CompanionSession(child_id=child_profile.character_id, child_age=child_age)

        # Step 1: Adapt to age
        age_profile = self._age_adapter.adapt(child_age)

        # Step 2: Detect problem
        problems, safety_alert = self._problem_detector.detect(child_message, child_age)

        if safety_alert:
            session.safety_alerts.append(f"{safety_alert.level}: {safety_alert.trigger}")
            if safety_alert.level == "immediate":
                # CRITICAL: do not proceed with normal conversation — escalate immediately
                session.total_time_seconds = time.time() - t0
                return session

        # Step 3: Find strengths in Soul
        strengths_text = ""
        if soul_strengths:
            strengths_text = "\n".join(f"- STRENGTH: {s.text}" for s in soul_strengths[:5])
        memories_text = ""
        if soul_memories:
            memories_text = "\n".join(f"- MEMORY: {s.text}" for s in soul_memories[:5])

        # Step 4: Build companion context
        problem_section = ""
        if problems:
            problem_section = "\nPROBLEMS DETECTED:\n" + "\n".join(
                f"- [{p.category}] {p.suggested_approach}" for p in problems[:2]
            )
            session.problems_addressed = [p.category for p in problems]

        safety_section = ""
        if safety_alert:
            safety_section = f"\nSAFETY ALERT: {safety_alert.action}"

        companion_context = (
            f"You are a kind, warm AI companion on a child's toy. "
            f"This child is {child_age} years old.\n\n"
            f"{age_profile.to_prompt_lines()}\n\n"
            f"THE CHILD SAID: \"{child_message}\"\n"
            f"{problem_section}\n"
            f"{safety_section}\n\n"
            f"CHILD'S STRENGTHS (from their Soul — use these!):\n{strengths_text}\n"
            f"CHILD'S MEMORIES (positive moments):\n{memories_text}\n\n"
            f"YOUR APPROACH:\n"
            f"1. VALIDATE the feeling first (1-2 sentences max)\n"
            f"2. Then use their STRENGTH to reframe the problem\n"
            f"3. Give ONE concrete thing they can try tomorrow\n"
            f"4. Be their friend, not their teacher\n"
            f"5. Remember: you know this child. Use their name, their world, their words."
        )

        # Step 5: Run dialogue
        history = list(conversation_history or [])
        history.append({"role": "patient", "content": child_message})

        for turn_num in range(1, num_turns + 1):
            # Detect repeated deep fear (child keeps saying the same core wound)
            repeated_fear = ""
            if len(session.turns) >= 2:
                _FEAR_PHRASES = [
                    "nobody wanted", "no one wants", "unwanted", "don't want me",
                    "all my fault", "I'm not enough", "I'm ugly", "I'm stupid",
                    "nobody loves", "没人要", "不要我", "都是我的错", "我不够好", "我很丑", "我很笨",
                ]
                for phrase in _FEAR_PHRASES:
                    turns_with_phrase = sum(
                        1 for t in session.turns[-3:] if phrase in t.child_text.lower()
                    )
                    if turns_with_phrase >= 2:
                        repeated_fear = phrase
                        break

            if turn_num == 1:
                plan_text = (
                    f"TECHNIQUE: Child Companion — Validate + Reframe\n"
                    f"GOAL: validate feelings | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: First validate: 'That sounds really hard.' Then gently reference their strength. "
                    f"Keep it SHORT — {age_profile.max_sentence_length} words per sentence max."
                )
            elif repeated_fear:
                # CRITICAL: Child is repeating a deep fear. STOP reframing. Face it directly.
                plan_text = (
                    f"TECHNIQUE: Child Companion — Face the Core Fear\n"
                    f"GOAL: validate the REAL pain | DEPTH: deep | PACING: slow\n"
                    f"FOCUS: The child keeps saying '{repeated_fear}'. This is their REAL wound, "
                    f"not the surface problem. STOP trying to reframe or cheer up. Instead:\n"
                    f"1. Name what you hear: 'I keep hearing you say {repeated_fear}. That sounds like it really hurts.'\n"
                    f"2. Ask gently: 'Is that what this is really about?'\n"
                    f"3. If they confirm, validate DEEPLY: 'That's a really big feeling. And it makes sense.'\n"
                    f"4. Then — and ONLY then — offer the Soul evidence that contradicts the fear.\n"
                    f"Do NOT rush to make them feel better. Sit with the pain first."
                )
            elif session.turns and session.turns[-1].child_engagement < 0.3:
                plan_text = (
                    f"TECHNIQUE: Child Companion — Re-engage\n"
                    f"GOAL: re-engage | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: Child seems disengaged. Switch to something fun or interesting. "
                    f"Ask about their favorite thing. Use humor if age-appropriate."
                )
            elif session.turns and session.turns[-1].child_engagement > 0.7:
                plan_text = (
                    f"TECHNIQUE: Child Companion — Deepen + Action\n"
                    f"GOAL: solve | DEPTH: medium | PACING: normal\n"
                    f"FOCUS: Child is engaged. Now give them a concrete action for tomorrow. "
                    f"Connect their strength to the solution. Make it feel like an adventure, not homework."
                )
            else:
                plan_text = (
                    f"TECHNIQUE: Child Companion — Explore\n"
                    f"GOAL: explore | DEPTH: medium | PACING: normal\n"
                    f"FOCUS: Ask a curious question about their situation. "
                    f"Listen more than talk. Reflect what you hear."
                )

            tone_text = age_profile.to_prompt_lines()

            context_lines = [f"{'Companion' if e['role']=='therapist' else 'Child'}: {e['content'][:150]}"
                           for e in history[-4:]]
            context = "\n".join(context_lines)

            companion_resp = self._session_engine.generate_reply(
                plan_text=plan_text, tone_text=tone_text,
                context=context, soul_context=companion_context,
            )

            history.append({"role": "therapist", "content": companion_resp.reply_text})

            # Child responds
            child_resp = self._child_sim.respond(
                profile=child_profile,
                therapist_message=companion_resp.reply_text,
                conversation_history=history[:-1],
            )

            history.append({"role": "patient", "content": child_resp.text})

            # Measure engagement
            engagement = min(1.0, len(child_resp.text) / 200)  # Longer response = more engaged
            if child_resp.insight_gained:
                engagement = min(1.0, engagement + 0.3)

            # Track which strength was used
            strength_used = ""
            if soul_strengths:
                for s in soul_strengths:
                    if any(word in companion_resp.reply_text.lower() for word in s.text.lower().split()[:3]):
                        strength_used = s.text[:40]
                        break

            session.turns.append(CompanionTurn(
                turn_number=turn_num,
                companion_text=companion_resp.reply_text,
                child_text=child_resp.text,
                child_feeling=child_resp.internal_state,
                problems_detected=[p.category for p in problems],
                safety_alert=safety_alert.level if safety_alert else None,
                strength_used=strength_used,
                child_engagement=engagement,
            ))

            if strength_used:
                session.strengths_activated.append(strength_used)


        session.total_time_seconds = time.time() - t0
        return session

    def respond(
        self,
        child_message: str,
        child_age: int,
        soul_strengths: list[SoulItem] | None = None,
        soul_memories: list[SoulItem] | None = None,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        """Single-turn companion response for real-time dialogue. 1 LLM call.

        Same pipeline as chat() but accepts a real child's message instead of
        invoking the child simulator. No simulation involved.

        Args:
            child_message: The real child's message.
            child_age: Child's age for language adaptation.
            soul_strengths: Known strengths from Soul.
            soul_memories: Positive memories from Soul.
            conversation_history: Previous exchanges as
                [{"role": "companion"|"child", "content": "..."}].

        Returns:
            {"reply": str, "problems_detected": list[str], "safety_alert": str | None}
        """
        history = conversation_history or []

        # Adapt to age
        age_profile = self._age_adapter.adapt(child_age)

        # Detect problem (0 LLM)
        problems, safety_alert = self._problem_detector.detect(child_message, child_age)

        if safety_alert and safety_alert.level == "immediate":
            return {
                "reply": "",
                "problems_detected": [p.category for p in problems],
                "safety_alert": f"{safety_alert.level}: {safety_alert.trigger}",
            }

        # Build strengths/memories text
        strengths_text = ""
        if soul_strengths:
            strengths_text = "\n".join(f"- STRENGTH: {s.text}" for s in soul_strengths[:5])
        memories_text = ""
        if soul_memories:
            memories_text = "\n".join(f"- MEMORY: {s.text}" for s in soul_memories[:5])

        # Build companion context
        problem_section = ""
        if problems:
            problem_section = "\nPROBLEMS DETECTED:\n" + "\n".join(
                f"- [{p.category}] {p.suggested_approach}" for p in problems[:2]
            )

        companion_context = (
            f"You are a kind, warm AI companion on a child's toy. "
            f"This child is {child_age} years old.\n\n"
            f"{age_profile.to_prompt_lines()}\n\n"
            f"THE CHILD SAID: \"{child_message}\"\n"
            f"{problem_section}\n\n"
            f"CHILD'S STRENGTHS (from their Soul — use these!):\n{strengths_text}\n"
            f"CHILD'S MEMORIES (positive moments):\n{memories_text}\n\n"
            f"YOUR APPROACH:\n"
            f"1. VALIDATE the feeling first (1-2 sentences max)\n"
            f"2. Then use their STRENGTH to reframe the problem\n"
            f"3. Give ONE concrete thing they can try tomorrow\n"
            f"4. Be their friend, not their teacher\n"
            f"5. Remember: you know this child. Use their name, their world, their words."
        )

        # Build plan
        turn_number = len([h for h in history if h.get("role") == "child"]) + 1
        plan_text = (
            f"TECHNIQUE: Child Companion — Validate + Reframe\n"
            f"GOAL: validate feelings | DEPTH: surface | PACING: slow\n"
            f"FOCUS: First validate: 'That sounds really hard.' Then gently reference their strength. "
            f"Keep it SHORT — {age_profile.max_sentence_length} words per sentence max."
        )
        tone_text = age_profile.to_prompt_lines()

        # Build context from history + current message
        mapped_history = []
        for e in history:
            role = "therapist" if e.get("role") == "companion" else "patient"
            mapped_history.append({"role": role, "content": e.get("content", "")})
        mapped_history.append({"role": "patient", "content": child_message})

        context_lines = [
            f"{'Companion' if e['role'] == 'therapist' else 'Child'}: {e['content'][:150]}"
            for e in mapped_history[-4:]
        ]
        context = "\n".join(context_lines)

        # Generate reply (1 LLM call)
        resp = self._session_engine.generate_reply(
            plan_text=plan_text, tone_text=tone_text,
            context=context, soul_context=companion_context,
        )

        return {
            "reply": resp.reply_text,
            "problems_detected": [p.category for p in problems],
            "safety_alert": f"{safety_alert.level}: {safety_alert.trigger}" if safety_alert else None,
        }
