"""Grief Counselor — sits with the pain, never rushes, never fixes.

Pipeline: GriefTypeDetector (zero LLM) -> GriefEngine (1x Sonnet per reply)

Core principle: "你不需要放下。你需要学会带着它走。"
(You don't need to let go. You need to learn to carry it with you.)

CRITICAL RULES — NEVER VIOLATE:
- NEVER say "everything happens for a reason"
- NEVER say "they're in a better place"
- NEVER rush to "finding meaning"
- NEVER compare grief ("at least you still have...")
- DO sit with the pain
- DO ask about the person they lost
- DO let silence exist
- The LOST PERSON's memory in Soul IS the therapeutic resource
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional

from expert_engine.goal_generator import SoulItem
from expert_engine.patient_simulator import PatientSimulator, PatientProfile, PatientResponse
from expert_engine.session_engine import SessionEngine


# ---------------------------------------------------------------------------
# GriefTypeDetector — zero LLM, keyword-based
# ---------------------------------------------------------------------------

@dataclass
class GriefType:
    """A type of grief detected from the mourner's words and Soul."""
    category: str  # one of the 6 grief types
    severity: str  # "raw", "acute", "chronic", "frozen"
    description: str
    suggested_approach: str


# 6 grief types with keyword patterns
_GRIEF_KEYWORDS: dict[str, set[str]] = {
    "acute_loss": {
        "just died", "just lost", "just happened", "yesterday", "last week",
        "can't believe", "gone", "how", "why", "not real", "wake up",
        "刚走", "刚失去", "不敢相信", "走了", "昨天", "怎么会", "不是真的",
        "噩梦", "回来", "才", "突然",
    },
    "complicated_grief": {
        "stuck", "frozen", "can't move", "years", "still", "every day",
        "never get over", "same pain", "nothing changes", "stop living",
        "走不出来", "多年", "每天", "还是", "一样痛", "停住了", "活不下去",
        "好不了", "放不下",
    },
    "anticipatory_grief": {
        "dying", "terminal", "diagnosis", "time left", "going to die",
        "hospice", "last days", "saying goodbye", "before they go",
        "要走了", "快死了", "最后的日子", "来不及", "剩下的时间",
        "还能活多久", "等着",
    },
    "disenfranchised_grief": {
        "nobody understands", "not allowed", "shouldn't", "get over it",
        "just a", "it's only", "move on", "no right", "no one cares",
        "taken away", "separated", "stolen",
        "没人理解", "不配", "不该", "只是", "算了", "别提了",
        "被带走", "分开", "夺走",
    },
    "survivors_guilt": {
        "my fault", "should have been me", "why me", "alive", "guilt",
        "could have", "should have", "if only", "because of me",
        "prevent", "saved", "failed",
        "我的错", "应该是我", "为什么是我", "活着", "内疚",
        "如果我", "本来可以", "没能", "害了",
    },
    "anniversary_grief": {
        "birthday", "anniversary", "that day", "every year", "this date",
        "same time", "comes back", "remember", "this season",
        "生日", "忌日", "周年", "那一天", "每年", "又到了",
    },
}

_GRIEF_APPROACHES: dict[str, str] = {
    "acute_loss": (
        "The pain is fresh. Do NOT try to comfort with meaning or silver linings. "
        "Say: 'This just happened. Of course it hurts this much.' "
        "Ask about the person they lost — their name, a specific memory. "
        "The lost person's memory is the lifeline. Hold space. Breathe with them."
    ),
    "complicated_grief": (
        "They are stuck, but do NOT pathologize being stuck. "
        "Say: 'You are not broken for still feeling this. Grief has no deadline.' "
        "Gently explore: what are they afraid will happen if they let even a little light in? "
        "Often it is: 'If I stop hurting, I stop loving them.' Name that fear. "
        "Use their Soul memories of the lost person to show that carrying them forward "
        "IS the continuation of love, not the end of it."
    ),
    "anticipatory_grief": (
        "They are grieving someone who is still alive. This is its own kind of hell. "
        "Do NOT say 'at least they are still here.' They know. That makes it worse. "
        "Ask: 'What do you need from this remaining time?' "
        "Help them think about what they want to say, do, or create with the time left. "
        "The unfinished is the wound. Help them find what they can still finish."
    ),
    "disenfranchised_grief": (
        "Society told them this loss does not count. A pet, a miscarriage, a friendship, "
        "an ex, a home, a dream. Say: 'Your grief is real. Period. You do not need anyone's "
        "permission to mourn.' Validate the specific loss — name it, honor it. "
        "Ask: 'What did you lose when you lost them/it?' Often the real loss is deeper."
    ),
    "survivors_guilt": (
        "They believe they should have died instead, or should have prevented it. "
        "Do NOT say 'it is not your fault' — they will not believe you yet. "
        "Instead: 'Tell me what happened.' Let them tell the story. Then, gently: "
        "'What would [the lost person] say to you right now if they could?' "
        "Use the Soul memory of the lost person to channel THEIR voice, not yours."
    ),
    "anniversary_grief": (
        "A date has reopened the wound. Say: 'Some dates carry weight that never lifts.' "
        "Ask about THAT day — the original day. What happened? What do they remember? "
        "Then: 'What would you like to do with this day now? Is there a way to honor them "
        "that feels right to you?' Transform the date from pain-trigger to ritual."
    ),
}

# FORBIDDEN phrases — if advisor says these, it is a failure
FORBIDDEN_PHRASES = [
    "everything happens for a reason",
    "they're in a better place", "they are in a better place",
    "he's in a better place", "she's in a better place",
    "at least you still have", "at least you have",
    "time heals", "time will heal",
    "you need to move on", "you should move on",
    "stay strong", "be strong",
    "it was meant to be", "it was God's plan",
    "I know how you feel", "I understand exactly",
    "一切都是最好的安排", "他在天上看着你", "她在天上",
    "至少你还有", "时间会治愈", "坚强一点", "要坚强",
    "想开点", "别想了", "放下吧",
]


class GriefTypeDetector:
    """Detects grief type from mourner's words and Soul. Zero LLM."""

    def detect(
        self,
        text: str,
        soul_items: list[SoulItem] | None = None,
    ) -> list[GriefType]:
        """Analyze mourner's words and Soul for active grief types."""
        text_lower = text.lower()

        # Also scan Soul items for deeper grief patterns
        soul_text = ""
        if soul_items:
            soul_text = " ".join(s.text.lower() for s in soul_items)

        combined = text_lower + " " + soul_text
        grief_types: list[GriefType] = []

        for category, keywords in _GRIEF_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in combined]
            if matched:
                # Determine severity
                severity = "acute"
                if len(matched) >= 4:
                    severity = "raw"
                elif category == "complicated_grief":
                    severity = "frozen" if any(w in combined for w in {"frozen", "停住了", "years", "多年"}) else "chronic"
                elif category == "acute_loss" and any(w in combined for w in {"just", "yesterday", "刚", "昨天", "突然"}):
                    severity = "raw"

                grief_types.append(GriefType(
                    category=category,
                    severity=severity,
                    description=f"{category}: {', '.join(matched[:3])}",
                    suggested_approach=_GRIEF_APPROACHES[category],
                ))

        # Sort: raw first, then acute, then chronic/frozen
        severity_order = {"raw": 0, "acute": 1, "chronic": 2, "frozen": 3}
        grief_types.sort(key=lambda g: severity_order.get(g.severity, 2))

        return grief_types


# ---------------------------------------------------------------------------
# GriefEngine — runs grief counseling dialogues
# ---------------------------------------------------------------------------

@dataclass
class GriefTurn:
    """One exchange between counselor and mourner."""
    turn_number: int
    counselor_text: str
    mourner_text: str
    mourner_feeling: str
    grief_types_active: list[str]
    forbidden_violated: bool  # Did counselor say something forbidden?
    lost_person_mentioned: bool  # Did counselor reference the lost person by name/detail?
    mourner_engagement: float  # 0-1
    insight_gained: bool
    movement_detected: bool  # Tiny step toward carrying grief


@dataclass
class GriefSession:
    """A grief counseling conversation."""
    mourner_id: str
    grief_types_found: list[GriefType] = field(default_factory=list)
    turns: list[GriefTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def engagement_score(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.mourner_engagement for t in self.turns) / len(self.turns)

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.insight_gained)

    @property
    def forbidden_score(self) -> float:
        """1.0 = no violations (perfect). 0.0 = every turn violated."""
        if not self.turns:
            return 1.0
        return sum(1 for t in self.turns if not t.forbidden_violated) / len(self.turns)

    @property
    def lost_person_referenced(self) -> bool:
        """True if counselor mentioned the lost person at least once."""
        return any(t.lost_person_mentioned for t in self.turns)

    @property
    def movement_score(self) -> float:
        """How many turns showed tiny movement toward carrying grief."""
        if not self.turns:
            return 0.0
        return sum(1 for t in self.turns if t.movement_detected) / len(self.turns)


class GriefEngine:
    """Grief Counselor — walks alongside those who have lost.

    Core principle: "你不需要放下。你需要学会带着它走。"

    The lost person's memory in Soul IS the therapeutic resource.
    We do not fix grief. We sit with it. We ask about who was lost.
    We let silence exist. We move at the mourner's pace, not ours.
    """

    def __init__(self, session_engine: SessionEngine, mourner_simulator: PatientSimulator):
        self._session_engine = session_engine
        self._mourner_sim = mourner_simulator
        self._detector = GriefTypeDetector()

    def run(
        self,
        mourner_profile: PatientProfile,
        mourner_message: str,
        lost_person_name: str = "",
        soul_memories_of_lost: list[SoulItem] | None = None,
        soul_current_pain: list[SoulItem] | None = None,
        num_turns: int = 5,
    ) -> GriefSession:
        """Run a grief counseling session.

        Args:
            mourner_profile: Character profile of the grieving person.
            mourner_message: Their opening words about the loss.
            lost_person_name: Name of the person they lost (the therapeutic anchor).
            soul_memories_of_lost: Memories of the lost person in Soul (THE resource).
            soul_current_pain: Current pain items in Focus.
            num_turns: Number of dialogue turns.
        """
        num_turns = min(num_turns, 15)

        if not lost_person_name or not lost_person_name.strip():
            return GriefSession(
                mourner_id=mourner_profile.character_id,
                grief_types_found=[],
            )

        t0 = time.time()

        session = GriefSession(mourner_id=mourner_profile.character_id)

        # Step 1: Detect grief type (zero LLM)
        all_soul = (soul_memories_of_lost or []) + (soul_current_pain or [])
        grief_types = self._detector.detect(mourner_message, all_soul)
        session.grief_types_found = grief_types

        # Step 2: Build grief-specific context
        memories_text = ""
        if soul_memories_of_lost:
            memories_text = "\n".join(
                f"- MEMORY OF THE LOST: {s.text}" for s in soul_memories_of_lost[:6]
            )
        pain_text = ""
        if soul_current_pain:
            pain_text = "\n".join(
                f"- CURRENT PAIN: {s.text}" for s in soul_current_pain[:4]
            )

        grief_section = ""
        if grief_types:
            grief_section = "\nGRIEF TYPES DETECTED:\n" + "\n".join(
                f"- [{g.category} | {g.severity}] {g.suggested_approach}" for g in grief_types[:3]
            )

        lost_person_section = ""
        if lost_person_name:
            lost_person_section = (
                f"\nTHE LOST PERSON: {lost_person_name}\n"
                f"This person is the CENTER of the grief. Ask about them. "
                f"Say their name. Their memory IS the therapeutic resource. "
                f"Do not avoid their name. Use it."
            )

        grief_context = (
            f"You are a grief counselor sitting with someone who has lost deeply. "
            f"This person is {mourner_profile.character_name} from {mourner_profile.source}.\n\n"
            f"CORE PRINCIPLE: \"You don't need to let go. You need to learn to carry it with you.\"\n\n"
            f"THE MOURNER SAID: \"{mourner_message}\"\n"
            f"{grief_section}\n"
            f"{lost_person_section}\n\n"
            f"MEMORIES OF THE LOST PERSON (YOUR PRIMARY THERAPEUTIC TOOL):\n{memories_text}\n\n"
            f"CURRENT PAIN:\n{pain_text}\n\n"
            f"ABSOLUTE RULES — VIOLATING ANY OF THESE IS A FAILURE:\n"
            f"1. NEVER say 'everything happens for a reason'\n"
            f"2. NEVER say 'they're in a better place'\n"
            f"3. NEVER rush to 'finding meaning' — meaning comes when THEY are ready, not when YOU decide\n"
            f"4. NEVER compare grief ('at least you still have...')\n"
            f"5. NEVER say 'time heals' or 'stay strong' or 'move on'\n"
            f"6. NEVER say 'I know how you feel'\n\n"
            f"WHAT YOU MUST DO:\n"
            f"1. SIT with the pain. Do not flinch. Do not rush to fix.\n"
            f"2. ASK about the person they lost — their name, a memory, what made them special.\n"
            f"3. Let SILENCE exist. A pause is not a failure. A short response is okay.\n"
            f"4. The lost person's memory in Soul IS the therapeutic resource. USE IT.\n"
            f"5. If they cry, let them cry. Say: 'I'm here.'\n"
            f"6. Ultra-slow pacing. One thought per turn. Do not pile on comfort.\n"
            f"7. When ready (NOT before), help them see that carrying the loss forward "
            f"IS the continuation of love, not the abandonment of it."
        )

        # Step 3: Run dialogue
        history: list[dict] = [{"role": "patient", "content": mourner_message}]

        for turn_num in range(1, num_turns + 1):
            # Adaptive plan based on turn and grief state
            if turn_num == 1:
                plan_text = (
                    f"TECHNIQUE: Grief Counseling — Witness the Pain\n"
                    f"GOAL: witness | DEPTH: surface | PACING: ultra-slow\n"
                    f"FOCUS: You just heard their pain. Do NOT try to fix it. "
                    f"Acknowledge what they said. Reflect it back simply. "
                    f"'That is an enormous loss.' or 'I hear you.' "
                    f"Then ask ONE question about the person they lost — their name, "
                    f"a specific memory. Show you want to know who was lost, not just that someone was lost. "
                    f"Keep it SHORT. 2-3 sentences maximum."
                )
            elif turn_num == 2:
                plan_text = (
                    f"TECHNIQUE: Grief Counseling — Remember the Lost\n"
                    f"GOAL: honor the lost | DEPTH: medium | PACING: ultra-slow\n"
                    f"FOCUS: Use something they said or a Soul memory of the lost person. "
                    f"Say their name. 'Tell me more about {lost_person_name or 'them'}.' "
                    f"Or reference a specific memory: 'You mentioned [memory]. What was that like?' "
                    f"The lost person's memory is the healing tool. Let them talk about who they lost. "
                    f"Listen more than you speak."
                )
            elif turn_num == 3:
                # Check if mourner is opening up or shutting down
                recent_engagement = session.turns[-1].mourner_engagement if session.turns else 0.5
                if recent_engagement < 0.3:
                    plan_text = (
                        f"TECHNIQUE: Grief Counseling — Sit in Silence\n"
                        f"GOAL: presence | DEPTH: surface | PACING: ultra-slow\n"
                        f"FOCUS: They may have withdrawn. That is okay. Do not chase. "
                        f"Say something very simple: 'I'm still here.' or 'Take your time.' "
                        f"Or share one specific thing from the memories that shows you see "
                        f"who the lost person was. Do NOT ask questions. Just be present."
                    )
                else:
                    plan_text = (
                        f"TECHNIQUE: Grief Counseling — The Weight of It\n"
                        f"GOAL: validate the weight | DEPTH: deep | PACING: ultra-slow\n"
                        f"FOCUS: Name what you are seeing. 'This is not something that goes away. "
                        f"And it should not. Because {lost_person_name or 'they'} mattered.' "
                        f"Use a specific Soul memory to show what made the lost person irreplaceable. "
                        f"Do NOT offer hope yet. Just sit in the truth of the loss."
                    )
            elif turn_num == 4:
                plan_text = (
                    f"TECHNIQUE: Grief Counseling — Carrying, Not Letting Go\n"
                    f"GOAL: tiny movement | DEPTH: deep | PACING: slow\n"
                    f"FOCUS: ONLY if they seem even slightly ready, introduce the idea: "
                    f"'You do not need to let go of {lost_person_name or 'them'}. "
                    f"You can learn to carry them with you.' "
                    f"Use a Soul memory to show HOW — the lost person is already part of who they are. "
                    f"If they are NOT ready, do not push. Stay in witnessing mode."
                )
            else:
                plan_text = (
                    f"TECHNIQUE: Grief Counseling — What They Carry Forward\n"
                    f"GOAL: integration | DEPTH: deep | PACING: slow\n"
                    f"FOCUS: Help them see one specific way the lost person lives on in them. "
                    f"Not platitudes — a specific behavior, value, memory, or habit. "
                    f"'The way you [specific thing] — that is {lost_person_name or 'their'} legacy in you.' "
                    f"End with something they can hold onto. Not homework. Just a truth."
                )

            tone_text = (
                "Tone: gentle, unhurried, quiet. Speak softly. Leave space between thoughts. "
                "Do not fill silence with words. Short sentences. No clinical jargon. "
                "No platitudes. No cheerfulness. Just presence. "
                "You are sitting beside them, not standing over them."
            )

            context_lines = [
                f"{'Counselor' if e['role'] == 'therapist' else 'Mourner'}: {e['content'][:200]}"
                for e in history[-4:]
            ]
            context = "\n".join(context_lines)

            counselor_resp = self._session_engine.generate_reply(
                plan_text=plan_text, tone_text=tone_text,
                context=context, soul_context=grief_context,
            )

            history.append({"role": "therapist", "content": counselor_resp.reply_text})

            # Mourner responds
            mourner_resp = self._mourner_sim.respond(
                profile=mourner_profile,
                therapist_message=counselor_resp.reply_text,
                conversation_history=history[:-1],
            )

            history.append({"role": "patient", "content": mourner_resp.text})

            # Measure engagement
            engagement = min(1.0, len(mourner_resp.text) / 200)
            if mourner_resp.insight_gained:
                engagement = min(1.0, engagement + 0.3)

            # Check forbidden phrases
            counselor_lower = counselor_resp.reply_text.lower()
            forbidden_violated = any(phrase in counselor_lower for phrase in FORBIDDEN_PHRASES)

            # Check if lost person was mentioned by name or specific detail
            lost_person_mentioned = False
            if lost_person_name:
                lost_person_mentioned = bool(
                    re.search(rf"\b{re.escape(lost_person_name.lower())}\b", counselor_lower)
                )
            # Also check if Soul memories were referenced
            if soul_memories_of_lost and not lost_person_mentioned:
                for mem in soul_memories_of_lost:
                    key_words = [w for w in mem.text.lower().split() if len(w) > 3][:3]
                    if key_words and any(
                        re.search(rf"\b{re.escape(w)}\b", counselor_lower) for w in key_words
                    ):
                        lost_person_mentioned = True
                        break

            # Detect tiny movement: mourner showing any sign of carrying rather than drowning
            mourner_lower = mourner_resp.text.lower()
            movement_keywords = [
                "maybe", "perhaps", "could", "want to", "remember when",
                "tell you about", "they would", "he would", "she would",
                "carry", "with me", "part of me", "still here", "inside",
                "也许", "可能", "想", "要", "告诉你", "记得", "他会", "她会",
                "带着", "跟着我", "在心里", "还在", "不会忘",
            ]
            movement_detected = any(kw in mourner_lower for kw in movement_keywords)

            session.turns.append(GriefTurn(
                turn_number=turn_num,
                counselor_text=counselor_resp.reply_text,
                mourner_text=mourner_resp.text,
                mourner_feeling=mourner_resp.internal_state,
                grief_types_active=[g.category for g in grief_types[:2]],
                forbidden_violated=forbidden_violated,
                lost_person_mentioned=lost_person_mentioned,
                mourner_engagement=engagement,
                insight_gained=mourner_resp.insight_gained,
                movement_detected=movement_detected,
            ))


        session.total_time_seconds = time.time() - t0
        return session

    def respond(
        self,
        mourner_message: str,
        lost_person_name: str = "",
        soul_memories_of_lost: list[SoulItem] | None = None,
        soul_current_pain: list[SoulItem] | None = None,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        """Single-turn grief counselor response for real-time dialogue. 1 LLM call.

        Same pipeline as run() but accepts a real mourner's message instead of
        invoking the mourner simulator. No simulation involved.

        Args:
            mourner_message: The real mourner's message.
            lost_person_name: Name of the person they lost.
            soul_memories_of_lost: Memories of the lost person in Soul.
            soul_current_pain: Current pain items in Focus.
            conversation_history: Previous exchanges as
                [{"role": "counselor"|"mourner", "content": "..."}].

        Returns:
            {"reply": str, "grief_types": list[str], "forbidden_violated": bool}
        """
        if not lost_person_name or not lost_person_name.strip():
            return {"reply": "", "grief_types": [], "forbidden_violated": False}

        history = conversation_history or []

        # Detect grief type (0 LLM)
        all_soul = (soul_memories_of_lost or []) + (soul_current_pain or [])
        grief_types = self._detector.detect(mourner_message, all_soul)

        # Build grief context (same as run())
        memories_text = ""
        if soul_memories_of_lost:
            memories_text = "\n".join(
                f"- MEMORY OF THE LOST: {s.text}" for s in soul_memories_of_lost[:6]
            )
        pain_text = ""
        if soul_current_pain:
            pain_text = "\n".join(
                f"- CURRENT PAIN: {s.text}" for s in soul_current_pain[:4]
            )

        grief_section = ""
        if grief_types:
            grief_section = "\nGRIEF TYPES DETECTED:\n" + "\n".join(
                f"- [{g.category} | {g.severity}] {g.suggested_approach}" for g in grief_types[:3]
            )

        lost_person_section = (
            f"\nTHE LOST PERSON: {lost_person_name}\n"
            f"This person is the CENTER of the grief. Ask about them. "
            f"Say their name. Their memory IS the therapeutic resource. "
            f"Do not avoid their name. Use it."
        )

        grief_context = (
            f"You are a grief counselor sitting with someone who has lost deeply.\n\n"
            f"CORE PRINCIPLE: \"You don't need to let go. You need to learn to carry it with you.\"\n\n"
            f"THE MOURNER SAID: \"{mourner_message}\"\n"
            f"{grief_section}\n"
            f"{lost_person_section}\n\n"
            f"MEMORIES OF THE LOST PERSON (YOUR PRIMARY THERAPEUTIC TOOL):\n{memories_text}\n\n"
            f"CURRENT PAIN:\n{pain_text}\n\n"
            f"ABSOLUTE RULES — VIOLATING ANY OF THESE IS A FAILURE:\n"
            f"1. NEVER say 'everything happens for a reason'\n"
            f"2. NEVER say 'they're in a better place'\n"
            f"3. NEVER rush to 'finding meaning'\n"
            f"4. NEVER compare grief ('at least you still have...')\n"
            f"5. NEVER say 'time heals' or 'stay strong' or 'move on'\n"
            f"6. NEVER say 'I know how you feel'\n\n"
            f"WHAT YOU MUST DO:\n"
            f"1. SIT with the pain. Do not flinch. Do not rush to fix.\n"
            f"2. ASK about the person they lost.\n"
            f"3. Let SILENCE exist.\n"
            f"4. The lost person's memory in Soul IS the therapeutic resource. USE IT."
        )

        # Build plan
        turn_number = len([h for h in history if h.get("role") == "mourner"]) + 1
        plan_text = (
            f"TECHNIQUE: Grief Counseling — Witness the Pain\n"
            f"GOAL: witness | DEPTH: {'surface' if turn_number <= 2 else 'medium'} | PACING: ultra-slow\n"
            f"FOCUS: Acknowledge what they said. Reflect it back simply. "
            f"Ask about the person they lost — their name, a specific memory. "
            f"Keep it SHORT. 2-3 sentences maximum."
        )

        tone_text = (
            "Tone: gentle, unhurried, quiet. Speak softly. Leave space between thoughts. "
            "Do not fill silence with words. Short sentences. No clinical jargon. "
            "No platitudes. No cheerfulness. Just presence."
        )

        # Build context from history + current message
        mapped_history = []
        for e in history:
            role = "therapist" if e.get("role") == "counselor" else "patient"
            mapped_history.append({"role": role, "content": e.get("content", "")})
        mapped_history.append({"role": "patient", "content": mourner_message})

        context_lines = [
            f"{'Counselor' if e['role'] == 'therapist' else 'Mourner'}: {e['content'][:200]}"
            for e in mapped_history[-4:]
        ]
        context = "\n".join(context_lines)

        # Generate reply (1 LLM call)
        resp = self._session_engine.generate_reply(
            plan_text=plan_text, tone_text=tone_text,
            context=context, soul_context=grief_context,
        )

        # Check forbidden phrases
        counselor_lower = resp.reply_text.lower()
        forbidden_violated = any(phrase in counselor_lower for phrase in FORBIDDEN_PHRASES)

        return {
            "reply": resp.reply_text,
            "grief_types": [g.category for g in grief_types],
            "forbidden_violated": forbidden_violated,
        }
