"""Elderly Care Consultant — dignity, meaning, and companionship for aging adults.

Pipeline: ElderlyNeedsDetector (zero LLM) -> ElderlyEngine (1x Sonnet per reply)

Core principle: "你的一生都是你的力量" — Your entire life is your strength.

Communication principles:
1. NEVER patronize or use baby talk
2. Acknowledge their full life of experience
3. Use THEIR memories as therapeutic resources
4. Slower pacing, patient, repeat key points
5. Address mortality directly when they bring it up — don't deflect
6. Their stories ARE the therapy — life review is healing
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from expert_engine.goal_generator import SoulItem
from expert_engine.patient_simulator import PatientSimulator, PatientProfile, PatientResponse
from expert_engine.session_engine import SessionEngine


# ---------------------------------------------------------------------------
# ElderlyNeedsDetector — zero LLM, keyword-based
# ---------------------------------------------------------------------------

@dataclass
class ElderlyConcern:
    """A concern identified in the elder's words."""
    category: str  # one of the 8 categories
    severity: str  # "normal", "acute", "chronic"
    description: str
    suggested_approach: str


# 8 core elderly concerns with keyword patterns
_CONCERN_KEYWORDS: dict[str, set[str]] = {
    "identity_loss": {
        "retire", "retired", "retirement", "used to be", "no longer", "not needed",
        "useless", "finished", "who am i", "purpose", "role", "irrelevant",
        "was once", "i was", "曾经", "退休", "没用了", "完了", "不需要我",
    },
    "loneliness": {
        "alone", "lonely", "nobody", "no one", "isolated", "forgotten",
        "invisible", "empty house", "silence", "miss", "孤独", "没人", "一个人",
        "寂寞", "冷清",
    },
    "health_decline": {
        "pain", "sick", "disease", "can't walk", "wheelchair", "blind", "deaf",
        "hospital", "doctor", "medication", "body", "weak", "failing",
        "身体", "痛", "病", "走不动", "老了",
    },
    "mortality_anxiety": {
        "die", "dying", "death", "dead", "funeral", "time left", "how long",
        "end", "afraid of dying", "last", "final", "死", "走了", "剩下的日子",
        "还能活多久", "消失",
    },
    "grief": {
        "lost", "passed away", "gone", "miss them", "spouse", "wife", "husband",
        "friend died", "funeral", "buried", "widow", "widower",
        "走了", "去世", "离开", "想念", "丧", "都走了",
    },
    "legacy": {
        "legacy", "remember me", "life matter", "did it matter", "what i leave",
        "grandchildren", "story", "meaning", "worth", "contribution",
        "意义", "值得", "留下", "一辈子", "有什么用",
    },
    "dignity": {
        "burden", "pity", "treat me like", "baby", "child", "helpless", "dependent",
        "can't do", "need help", "dignity", "respect", "still here", "still me",
        "负担", "可怜", "看不起", "还在", "还是我",
    },
    "family_conflict": {
        "children", "daughter", "son", "family", "care", "nursing home",
        "abandon", "betrayed", "ungrateful", "fight", "argue",
        "孩子", "女儿", "儿子", "家人", "养老院", "不孝", "抛弃",
    },
}

_CONCERN_APPROACHES: dict[str, str] = {
    "identity_loss": (
        "Acknowledge the grief of losing roles. Then explore: 'Who are you beyond "
        "what you did? What did you bring to every role you ever held?' Use their "
        "Soul memories of mastery as evidence that their essence transcends any title."
    ),
    "loneliness": (
        "Don't minimize it. Loneliness in old age is real and structural. "
        "Validate first. Then explore remaining connections — even one matters. "
        "Use memories of deep bonds to show their capacity for connection is intact."
    ),
    "health_decline": (
        "Never say 'at least you still have...' — they know what they've lost. "
        "Ask what they CAN still do. Find agency within limitation. "
        "Their body is failing but their mind and heart may not be."
    ),
    "mortality_anxiety": (
        "DO NOT DEFLECT. If they talk about death, meet them there. "
        "'What scares you most about it?' 'What would a good death look like?' "
        "This is not morbid — it is the most important conversation of their life. "
        "Use their life story to show what they've already given the world."
    ),
    "grief": (
        "Grief in old age is cumulative — they may have lost dozens of people. "
        "Don't say 'they're in a better place.' Instead: 'Tell me about them.' "
        "Their stories of the dead are how the dead stay alive. LISTEN."
    ),
    "legacy": (
        "Help them see the ripple effects of their life. 'Who did you shape? "
        "What did you teach someone that they still carry?' Use their Soul "
        "memories to reconstruct their impact — they may have forgotten."
    ),
    "dignity": (
        "The deepest wound of aging is being treated as less-than. "
        "Treat them as a wise elder, not a patient. Ask for THEIR advice. "
        "'You've lived through things I can only imagine — what would you tell "
        "someone facing what you faced?'"
    ),
    "family_conflict": (
        "Family conflicts in old age carry decades of history. Don't take sides. "
        "Help them express what they need vs. what they fear. "
        "'What do you wish your children understood about you right now?'"
    ),
}


class ElderlyNeedsDetector:
    """Detects which of the 8 elderly concerns are active. Zero LLM."""

    def detect(
        self,
        text: str,
        soul_items: list[SoulItem] | None = None,
    ) -> list[ElderlyConcern]:
        """Analyze elder's words and Soul for active concerns."""
        text_lower = text.lower()
        concerns: list[ElderlyConcern] = []

        # Also check Soul items for deeper patterns
        soul_text = ""
        if soul_items:
            soul_text = " ".join(s.text.lower() for s in soul_items)

        combined = text_lower + " " + soul_text

        for category, keywords in _CONCERN_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in combined]
            if matched:
                # Check severity: acute if multiple keywords or strong emotional words
                severity = "normal"
                if len(matched) >= 3:
                    severity = "acute"
                elif any(w in text_lower for w in {"dying", "dead", "abandon", "useless", "完了", "都走了"}):
                    severity = "acute"

                concerns.append(ElderlyConcern(
                    category=category,
                    severity=severity,
                    description=f"{category}: {', '.join(matched[:3])}",
                    suggested_approach=_CONCERN_APPROACHES[category],
                ))

        # Sort by severity (acute first)
        severity_order = {"acute": 0, "chronic": 1, "normal": 2}
        concerns.sort(key=lambda c: severity_order.get(c.severity, 2))

        return concerns


# ---------------------------------------------------------------------------
# ElderlyEngine — runs the advisory dialogue
# ---------------------------------------------------------------------------

@dataclass
class ElderlyTurn:
    """One exchange between advisor and elder."""
    turn_number: int
    advisor_text: str
    elder_text: str
    elder_feeling: str
    concerns_addressed: list[str]
    dignity_maintained: bool  # Did advisor avoid patronizing?
    elder_engagement: float  # 0-1
    insight_gained: bool


@dataclass
class ElderlySession:
    """A conversation session with an elderly person."""
    elder_id: str
    concerns_found: list[ElderlyConcern] = field(default_factory=list)
    turns: list[ElderlyTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def engagement_score(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.elder_engagement for t in self.turns) / len(self.turns)

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.insight_gained)

    @property
    def dignity_score(self) -> float:
        if not self.turns:
            return 0.0
        return sum(1 for t in self.turns if t.dignity_maintained) / len(self.turns)


class ElderlyEngine:
    """Elderly Care Consultant — companionship with dignity.

    Core principle: "你的一生都是你的力量"
    Their memories are not nostalgia — they are therapeutic resources.
    """

    def __init__(self, session_engine: SessionEngine, elder_simulator: PatientSimulator):
        self._session_engine = session_engine
        self._elder_sim = elder_simulator
        self._detector = ElderlyNeedsDetector()

    def run(
        self,
        elder_profile: PatientProfile,
        elder_message: str,
        soul_strengths: list[SoulItem] | None = None,
        soul_memories: list[SoulItem] | None = None,
        num_turns: int = 4,
    ) -> ElderlySession:
        """Run an elderly care dialogue session."""
        num_turns = min(num_turns, 15)
        t0 = time.time()

        session = ElderlySession(elder_id=elder_profile.character_id)

        # Step 1: Detect concerns (zero LLM)
        all_soul = (soul_strengths or []) + (soul_memories or [])
        concerns = self._detector.detect(elder_message, all_soul)
        session.concerns_found = concerns

        # Step 2: Build elderly-specific context
        strengths_text = ""
        if soul_strengths:
            strengths_text = "\n".join(f"- LIFE STRENGTH: {s.text}" for s in soul_strengths[:5])
        memories_text = ""
        if soul_memories:
            memories_text = "\n".join(f"- LIFE MEMORY: {s.text}" for s in soul_memories[:5])

        concern_section = ""
        if concerns:
            concern_section = "\nCONCERNS DETECTED:\n" + "\n".join(
                f"- [{c.category}] {c.suggested_approach}" for c in concerns[:3]
            )

        elderly_context = (
            f"You are a companion and advisor speaking with an elderly person. "
            f"This person is {elder_profile.character_name} from {elder_profile.source}.\n\n"
            f"CORE PRINCIPLE: Their entire life is their strength. "
            f"Their memories are not nostalgia — they are therapeutic resources.\n\n"
            f"THE ELDER SAID: \"{elder_message}\"\n"
            f"{concern_section}\n\n"
            f"THEIR LIFE STRENGTHS:\n{strengths_text}\n"
            f"THEIR LIFE MEMORIES:\n{memories_text}\n\n"
            f"COMMUNICATION RULES (MANDATORY):\n"
            f"1. NEVER patronize. No baby talk. No 'dear' or 'sweetie'.\n"
            f"2. They have lived an ENTIRE LIFE — acknowledge their experience.\n"
            f"3. Use THEIR memories as healing tools, not empty comfort.\n"
            f"4. If they talk about death, MEET THEM THERE. Do not deflect.\n"
            f"5. Their stories ARE the therapy. Ask for stories. LISTEN.\n"
            f"6. Treat them as a wise elder sharing their journey, not a patient.\n"
            f"7. Speak naturally. Repeat key points. Be patient.\n"
            f"8. NEVER say 'at your age' or 'for someone your age'."
        )

        # Step 3: Run dialogue
        history: list[dict] = [{"role": "patient", "content": elder_message}]

        for turn_num in range(1, num_turns + 1):
            # Adaptive plan based on turn and engagement
            if turn_num == 1:
                plan_text = (
                    f"TECHNIQUE: Elderly Care — Honor + Listen\n"
                    f"GOAL: earn trust | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: First, honor what they just said. 'I hear you.' "
                    f"Do not rush to fix. Ask them to tell you more about their life — "
                    f"a specific memory, a moment of strength. Show you see them as a "
                    f"whole person, not just their current pain."
                )
            elif turn_num == 2:
                plan_text = (
                    f"TECHNIQUE: Elderly Care — Life Review as Healing\n"
                    f"GOAL: activate memories | DEPTH: medium | PACING: slow\n"
                    f"FOCUS: Use a specific Soul memory or strength to show them "
                    f"who they truly are. 'You said [memory] — that tells me something "
                    f"important about you.' Connect their past self to their present worth."
                )
            elif session.turns and session.turns[-1].elder_engagement < 0.3:
                plan_text = (
                    f"TECHNIQUE: Elderly Care — Re-engage with Respect\n"
                    f"GOAL: re-engage | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: They may have withdrawn. Ask for their ADVICE — "
                    f"'What would you tell someone going through this?' "
                    f"This restores their role as the wise one, not the helpless one."
                )
            else:
                plan_text = (
                    f"TECHNIQUE: Elderly Care — Meaning + Legacy\n"
                    f"GOAL: meaning-making | DEPTH: deep | PACING: slow\n"
                    f"FOCUS: Help them see the ripple effects of their life. "
                    f"Who did they shape? What did they give the world? "
                    f"Use their Soul evidence. Name it specifically. "
                    f"If they mentioned death or ending, face it with them — "
                    f"'What would it mean to finish well?'"
                )

            tone_text = (
                "Tone: warm, respectful, unhurried. Speak as an equal. "
                "Use simple, direct language. No clinical jargon. "
                "Honor their wisdom and experience."
            )

            context_lines = [
                f"{'Advisor' if e['role'] == 'therapist' else 'Elder'}: {e['content'][:150]}"
                for e in history[-4:]
            ]
            context = "\n".join(context_lines)

            advisor_resp = self._session_engine.generate_reply(
                plan_text=plan_text, tone_text=tone_text,
                context=context, soul_context=elderly_context,
            )

            history.append({"role": "therapist", "content": advisor_resp.reply_text})

            # Elder responds
            elder_resp = self._elder_sim.respond(
                profile=elder_profile,
                therapist_message=advisor_resp.reply_text,
                conversation_history=history[:-1],
            )

            history.append({"role": "patient", "content": elder_resp.text})

            # Measure engagement
            engagement = min(1.0, len(elder_resp.text) / 200)
            if elder_resp.insight_gained:
                engagement = min(1.0, engagement + 0.3)

            # Check dignity: advisor didn't patronize
            patronizing_markers = [
                "dear", "sweetie", "honey", "at your age", "for your age",
                "you poor", "bless your heart",
            ]
            advisor_lower = advisor_resp.reply_text.lower()
            dignity_ok = not any(m in advisor_lower for m in patronizing_markers)

            session.turns.append(ElderlyTurn(
                turn_number=turn_num,
                advisor_text=advisor_resp.reply_text,
                elder_text=elder_resp.text,
                elder_feeling=elder_resp.internal_state,
                concerns_addressed=[c.category for c in concerns[:2]],
                dignity_maintained=dignity_ok,
                elder_engagement=engagement,
                insight_gained=elder_resp.insight_gained,
            ))


        session.total_time_seconds = time.time() - t0
        return session
