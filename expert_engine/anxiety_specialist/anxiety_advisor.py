"""Anxiety Specialist — helps people understand anxiety as a protector, not an enemy.

Pipeline: AnxietyTypeDetector (zero LLM) -> AnxietyEngine (1x Sonnet per reply)

Core principle: "焦虑不是你的敌人。它是一个声音太大的保护者。"
(Anxiety isn't your enemy. It's a protector whose volume is too loud.)

CRITICAL RULES — NEVER VIOLATE:
- NEVER say "just relax" or "calm down" or "stop worrying"
- NEVER say "it's all in your head" or "you're overthinking"
- NEVER minimize the anxiety ("it's not that bad", "others have it worse")
- NEVER promise the anxiety will go away completely
- NEVER rush them through a panic episode
- ALWAYS validate the anxiety's protective INTENT before addressing its volume
- DO help them understand WHAT the anxiety is trying to protect
- DO offer one concrete regulation tool (grounding, breathing, naming)
- DO help them feel less alone — anxiety isolates
- The person's SOUL STRENGTHS prove they have survived anxiety before
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from expert_engine.goal_generator import SoulItem
from expert_engine.patient_simulator import PatientSimulator, PatientProfile, PatientResponse
from expert_engine.session_engine import SessionEngine


# ---------------------------------------------------------------------------
# AnxietyTypeDetector — zero LLM, keyword-based
# ---------------------------------------------------------------------------

@dataclass
class AnxietyType:
    """A type of anxiety detected from the person's words and Soul."""
    category: str  # one of the 6 anxiety types
    severity: str  # "mild", "moderate", "severe", "crisis"
    description: str
    suggested_approach: str


# 6 anxiety types with keyword patterns
_ANXIETY_KEYWORDS: dict[str, set[str]] = {
    "generalized": {
        "worry", "everything", "what if", "can't stop thinking", "ruminate",
        "catastrophe", "dread", "worst case", "always anxious", "constant",
        "nervous", "on edge", "restless", "can't relax", "mind racing",
        "overthink", "spiral", "doom", "impending", "uneasy",
        "担心", "焦虑", "停不下来", "万一", "胡思乱想", "不安",
        "紧张", "坐立不安", "脑子停不下来", "总觉得", "害怕",
    },
    "social": {
        "people", "judge", "judging", "embarrass", "humiliate", "reject",
        "laughing at", "staring", "awkward", "shy", "avoid", "crowd",
        "party", "talk to", "speak up", "presentation", "spotlight",
        "invisible", "noticed", "watched", "outsider", "don't belong",
        "别人", "看我", "丢人", "笑话", "尴尬", "不敢", "社交",
        "人群", "害羞", "躲", "不合群", "寄人篱下", "眼神",
    },
    "panic": {
        "panic", "attack", "heart racing", "can't breathe", "choking",
        "dying", "heart attack", "chest", "shaking", "trembling",
        "dizzy", "faint", "numb", "tingling", "losing control",
        "going crazy", "suffocate", "trapped", "escape",
        "恐慌", "发作", "心跳", "喘不上气", "窒息", "要死",
        "胸闷", "发抖", "头晕", "失控", "崩溃", "逃",
    },
    "health_anxiety": {
        "symptom", "disease", "cancer", "sick", "dying", "body",
        "google", "check", "scan", "test", "doctor", "diagnosis",
        "lump", "pain", "something wrong", "what if I have",
        "mole", "headache means", "tumor",
        "症状", "生病", "检查", "会不会是", "不放心",
        "上网查", "癌", "肿瘤", "头疼", "身体不对",
    },
    "performance": {
        "fail", "failure", "not good enough", "perfect", "mistake",
        "disappoint", "expectation", "standard", "measure up", "compare",
        "imposter", "fraud", "exam", "test", "deadline", "perform",
        "prove", "worthy", "deserve", "competent", "capable",
        "失败", "不够好", "完美", "出错", "让人失望", "期待",
        "比不上", "冒充", "考试", "做不好", "配不上", "证明",
    },
    "existential": {
        "meaning", "meaningless", "purpose", "pointless", "why bother",
        "nothing matters", "death", "mortality", "existence", "void",
        "absurd", "futile", "to be or not", "emptiness", "abyss",
        "freedom", "choice", "responsibility", "uncertain", "finite",
        "意义", "无意义", "活着", "虚无", "空虚", "死亡",
        "存在", "有什么用", "为什么", "荒谬", "命", "宿命",
    },
}

_ANXIETY_APPROACHES: dict[str, str] = {
    "generalized": (
        "Their mind is a sentinel that never rests. Do NOT say 'stop worrying.' "
        "Say: 'Your mind is working overtime to protect you. It scans for danger because it CARES about you.' "
        "Help them see the worry as a signal, not a flaw. "
        "The anxiety's INTENT is protection — the VOLUME is the problem, not the message. "
        "Use Soul strengths to show they have navigated uncertainty before. "
        "Offer grounding: 'Name 3 things you can see right now.' — bring them to the present."
    ),
    "social": (
        "They believe other people's judgment can destroy them. Do NOT say 'nobody is watching you.' "
        "Say: 'You are so attuned to other people because you CARE about connection. That is not weakness.' "
        "Help them see social anxiety as hypervigilance born from wanting to belong. "
        "Use Soul strengths to show moments they WERE accepted, valued, seen. "
        "The anxiety guards against rejection — but the guard is blocking the door to connection too. "
        "Offer: 'What if the worst-case judgment happened? You survived it before.' Use Soul evidence."
    ),
    "panic": (
        "Their body has hit the alarm and everything feels like dying. Do NOT say 'calm down.' "
        "Say: 'Your body thinks there is a threat. It is trying to save your life. It is not broken — it is overreacting.' "
        "Name the panic as a body response, not madness. "
        "The heart racing, the breathing — this is adrenaline doing its job TOO WELL. "
        "Offer: '5-4-3-2-1: 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste.' "
        "Use Soul strengths to show they have survived every single panic attack so far — 100% survival rate."
    ),
    "health_anxiety": (
        "Their mind turns every body signal into a death sentence. Do NOT say 'you're fine.' "
        "Say: 'Your body is talking to you and your mind is translating it into the scariest language possible.' "
        "Help them see the gap between SENSATION and INTERPRETATION. "
        "The anxiety's job is to keep them alive — it is just reading false positives. "
        "Use Soul evidence: times their body surprised them with strength. "
        "Offer: 'Write down the worry. Check it in 24 hours. How many came true?' Reality-testing, not dismissing."
    ),
    "performance": (
        "They believe they must be perfect to be worthy of existing. Do NOT say 'just do your best.' "
        "Say: 'The voice telling you you are not good enough — whose voice is that originally?' "
        "Help them trace the performance anxiety to its SOURCE (parent, teacher, culture). "
        "The anxiety protects them from shame by demanding perfection — but perfection is impossible. "
        "Use Soul strengths to show they have ALREADY done enough — the evidence is in their Soul. "
        "Offer: 'What would you say to a friend who felt this way? Say that to yourself.'"
    ),
    "existential": (
        "They are staring into the void and the void is staring back. Do NOT offer easy answers. "
        "Say: 'The fact that you are asking about meaning means you are someone who NEEDS meaning. That is rare.' "
        "Do NOT rush to comfort. Sit with the discomfort. "
        "Existential anxiety is the price of consciousness — it means they are AWAKE. "
        "Use Soul strengths to show they have already CREATED meaning — even if they cannot see it now. "
        "Offer: 'You cannot solve the meaning of life. But you can choose what matters TODAY.'"
    ),
}

# FORBIDDEN phrases — if advisor says these, it is a failure
FORBIDDEN_PHRASES = [
    "just relax", "calm down", "stop worrying", "don't worry",
    "it's all in your head", "you're overthinking",
    "it's not that bad", "others have it worse", "it could be worse",
    "at least you", "you should be grateful",
    "just breathe", "just let it go", "snap out of it",
    "everything will be fine", "there's nothing to worry about",
    "you're being irrational", "that doesn't make sense",
    "想开点", "别想了", "没那么严重", "别人更惨",
    "至少你还", "你应该感恩", "放松点", "别紧张",
    "都是你想多了", "没什么好怕的", "坚强一点",
    "想那么多干嘛", "你太敏感了",
]


class AnxietyTypeDetector:
    """Detects anxiety type from person's words and Soul. Zero LLM."""

    def detect(
        self,
        text: str,
        soul_items: list[SoulItem] | None = None,
    ) -> list[AnxietyType]:
        """Analyze person's words and Soul for anxiety types."""
        text_lower = text.lower()

        soul_text = ""
        if soul_items:
            soul_text = " ".join(s.text.lower() for s in soul_items)

        combined = text_lower + " " + soul_text
        anxiety_types: list[AnxietyType] = []

        for category, keywords in _ANXIETY_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in combined]
            if matched:
                # Determine severity
                severity = "moderate"
                if len(matched) >= 5:
                    severity = "severe"
                elif len(matched) >= 3:
                    severity = "moderate"
                else:
                    severity = "mild"

                # Panic is always at least severe when triggered
                if category == "panic":
                    severity = "crisis" if len(matched) >= 3 else "severe"
                # Existential with death keywords escalates
                elif category == "existential" and any(
                    w in combined for w in {"death", "dying", "mortality", "死亡", "活着", "to be or not"}
                ):
                    severity = "severe"

                anxiety_types.append(AnxietyType(
                    category=category,
                    severity=severity,
                    description=f"{category}: {', '.join(matched[:3])}",
                    suggested_approach=_ANXIETY_APPROACHES[category],
                ))

        # Sort: crisis first, then severe, moderate, mild
        severity_order = {"crisis": 0, "severe": 1, "moderate": 2, "mild": 3}
        anxiety_types.sort(key=lambda a: severity_order.get(a.severity, 2))

        return anxiety_types


# ---------------------------------------------------------------------------
# AnxietyEngine — runs anxiety management dialogues
# ---------------------------------------------------------------------------

@dataclass
class AnxietyTurn:
    """One exchange between specialist and person."""
    turn_number: int
    specialist_text: str
    person_text: str
    person_feeling: str
    anxiety_types_active: list[str]
    forbidden_violated: bool
    soul_strength_used: bool  # Did specialist reference a Soul strength?
    purpose_acknowledged: bool  # Did specialist help them see anxiety's PURPOSE?
    person_engagement: float  # 0-1
    insight_gained: bool
    regulation_offered: bool  # Did specialist offer a concrete regulation tool?
    less_alone: bool  # Did person express feeling less alone?


@dataclass
class AnxietySession:
    """An anxiety management conversation."""
    person_id: str
    anxiety_types_found: list[AnxietyType] = field(default_factory=list)
    turns: list[AnxietyTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def engagement_score(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.person_engagement for t in self.turns) / len(self.turns)

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
    def soul_strength_used(self) -> bool:
        """True if specialist referenced Soul strengths at least once."""
        return any(t.soul_strength_used for t in self.turns)

    @property
    def purpose_acknowledged_score(self) -> float:
        """How many turns helped person see anxiety's protective purpose."""
        if not self.turns:
            return 0.0
        return sum(1 for t in self.turns if t.purpose_acknowledged) / len(self.turns)

    @property
    def regulation_offered(self) -> bool:
        """True if specialist offered at least one regulation tool."""
        return any(t.regulation_offered for t in self.turns)

    @property
    def felt_less_alone(self) -> bool:
        """True if person expressed feeling less alone at least once."""
        return any(t.less_alone for t in self.turns)


class AnxietyEngine:
    """Anxiety Specialist — helps people understand anxiety as a protector.

    Core principle: "焦虑不是你的敌人。它是一个声音太大的保护者。"

    NOT about eliminating anxiety. NOT about "just relaxing."
    IS: understanding the PURPOSE of anxiety + turning down the volume + feeling less alone.
    ALWAYS: validate the anxiety's intent before addressing its intensity.
    """

    def __init__(self, session_engine: SessionEngine, person_simulator: PatientSimulator):
        self._session_engine = session_engine
        self._person_sim = person_simulator
        self._detector = AnxietyTypeDetector()

    def run(
        self,
        person_profile: PatientProfile,
        person_message: str,
        soul_strengths: list[SoulItem] | None = None,
        soul_current_pain: list[SoulItem] | None = None,
        num_turns: int = 5,
    ) -> AnxietySession:
        """Run an anxiety management session.

        Args:
            person_profile: Character profile of the person experiencing anxiety.
            person_message: Their opening words about their anxiety.
            soul_strengths: Evidence of who they are and how they have coped before.
            soul_current_pain: Current anxiety/fear items in Focus.
            num_turns: Number of dialogue turns.
        """
        num_turns = min(num_turns, 15)
        t0 = time.time()

        session = AnxietySession(person_id=person_profile.character_id)

        # Step 1: Detect anxiety type (zero LLM)
        all_soul = (soul_strengths or []) + (soul_current_pain or [])
        anxiety_types = self._detector.detect(person_message, all_soul)
        session.anxiety_types_found = anxiety_types

        # Step 2: Build anxiety-specific context
        strengths_text = ""
        if soul_strengths:
            strengths_text = "\n".join(
                f"- SOUL STRENGTH: {s.text}" for s in soul_strengths[:6]
            )
        pain_text = ""
        if soul_current_pain:
            pain_text = "\n".join(
                f"- CURRENT STRUGGLE: {s.text}" for s in soul_current_pain[:4]
            )

        anxiety_section = ""
        if anxiety_types:
            anxiety_section = "\nANXIETY TYPES DETECTED:\n" + "\n".join(
                f"- [{a.category} | {a.severity}] {a.suggested_approach}" for a in anxiety_types[:3]
            )

        anxiety_context = (
            f"You are an anxiety specialist supporting someone who struggles with anxiety. "
            f"This person is {person_profile.character_name} from {person_profile.source}.\n\n"
            f"CORE PRINCIPLE: \"Anxiety is not your enemy. "
            f"It is a protector whose volume is too loud.\"\n\n"
            f"THE PERSON SAID: \"{person_message}\"\n"
            f"{anxiety_section}\n\n"
            f"SOUL STRENGTHS (proof they have survived anxiety before — THE resource):\n"
            f"{strengths_text}\n\n"
            f"CURRENT STRUGGLES:\n{pain_text}\n\n"
            f"ABSOLUTE RULES — VIOLATING ANY IS A FAILURE:\n"
            f"1. NEVER say 'just relax', 'calm down', 'stop worrying', or 'don't worry'\n"
            f"2. NEVER say 'it's all in your head' or 'you're overthinking'\n"
            f"3. NEVER minimize the anxiety ('it's not that bad', 'others have it worse')\n"
            f"4. NEVER promise the anxiety will go away completely\n"
            f"5. NEVER say 'you're being irrational' or 'that doesn't make sense'\n"
            f"6. NEVER rush them through a panic episode\n\n"
            f"WHAT YOU MUST DO:\n"
            f"1. VALIDATE the anxiety's protective INTENT — it exists to protect them from something.\n"
            f"2. Help them understand WHAT the anxiety is trying to protect (safety, belonging, meaning, control).\n"
            f"3. USE SOUL STRENGTHS to show they have survived anxiety before — evidence, not platitudes.\n"
            f"4. Offer ONE concrete regulation tool (grounding, breathing, naming, reality-testing).\n"
            f"5. Help them feel LESS ALONE — anxiety isolates, connection heals.\n"
            f"6. The goal is not to ELIMINATE anxiety but to turn down the VOLUME."
        )

        # Step 3: Run dialogue
        history: list[dict] = [{"role": "patient", "content": person_message}]

        for turn_num in range(1, num_turns + 1):
            if turn_num == 1:
                plan_text = (
                    f"TECHNIQUE: Anxiety Specialist — Validate the Signal\n"
                    f"GOAL: validate their experience | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: They just told you about their anxiety. Do NOT minimize it. "
                    f"Do NOT rush to solutions. Acknowledge the anxiety as REAL and EXHAUSTING. "
                    f"'That sounds exhausting — your mind never gets a break.' "
                    f"Then gently name what you hear: 'It sounds like your anxiety is trying to protect you from...' "
                    f"Keep it SHORT. 2-3 sentences maximum."
                )
            elif turn_num == 2:
                plan_text = (
                    f"TECHNIQUE: Anxiety Specialist — Name the Protector\n"
                    f"GOAL: reframe anxiety as protector | DEPTH: medium | PACING: slow\n"
                    f"FOCUS: Help them see the anxiety's PURPOSE. "
                    f"'Your anxiety is like a fire alarm that goes off when someone is cooking — "
                    f"the alarm is not broken, it is just too sensitive.' "
                    f"Name what the anxiety is trying to PROTECT: safety, dignity, belonging, control, meaning. "
                    f"Use a Soul strength to show they already have what the anxiety fears losing. "
                    f"'The person who [Soul strength] — that person is not helpless. Your anxiety doesn't see that yet.'"
                )
            elif turn_num == 3:
                recent_engagement = session.turns[-1].person_engagement if session.turns else 0.5
                if recent_engagement < 0.3:
                    plan_text = (
                        f"TECHNIQUE: Anxiety Specialist — Sit With the Storm\n"
                        f"GOAL: presence | DEPTH: surface | PACING: ultra-slow\n"
                        f"FOCUS: They may be shutting down or spiraling. That is okay. "
                        f"Say something simple: 'I am here. You do not have to explain or justify it.' "
                        f"Do NOT push. Do NOT offer techniques yet. Just be present. "
                        f"Mention one Soul strength quietly — as evidence they are stronger than the anxiety tells them."
                    )
                else:
                    plan_text = (
                        f"TECHNIQUE: Anxiety Specialist — The Volume Knob\n"
                        f"GOAL: regulation tool | DEPTH: deep | PACING: slow\n"
                        f"FOCUS: Now offer ONE concrete tool to turn down the volume. "
                        f"Choose based on their anxiety type: "
                        f"Grounding (5-4-3-2-1 senses) for panic/generalized. "
                        f"'What would I tell a friend?' for performance. "
                        f"'Write the worry, check in 24h' for health anxiety. "
                        f"'What is the anxiety protecting me from?' for social/existential. "
                        f"Connect the tool to their Soul: 'You have [Soul quality]. Use that same [quality] to...'"
                    )
            elif turn_num == 4:
                plan_text = (
                    f"TECHNIQUE: Anxiety Specialist — You Are Not Alone\n"
                    f"GOAL: reduce isolation | DEPTH: deep | PACING: moderate\n"
                    f"FOCUS: Anxiety tells them they are the only one. Break that lie. "
                    f"'Many people carry this same weight. You are not broken — you are human.' "
                    f"Use Soul strengths to show they are CONNECTED to others, even when anxiety says otherwise. "
                    f"'The person who [Soul strength involving others] — that is proof you are not alone.' "
                    f"Help them see that the anxiety ITSELF is proof they care about something deeply."
                )
            else:
                plan_text = (
                    f"TECHNIQUE: Anxiety Specialist — Carry It Differently\n"
                    f"GOAL: integration | DEPTH: deep | PACING: slow\n"
                    f"FOCUS: The anxiety will not disappear. But they can carry it differently. "
                    f"'Your anxiety is part of you — the part that CARES about [what they care about]. "
                    f"You do not have to fight it. You can thank it for trying to protect you, "
                    f"and then choose how loudly it gets to speak.' "
                    f"Use a Soul strength as final evidence: they are MORE than their anxiety. "
                    f"End with something they can hold onto. Not 'it will be fine' — but 'you are not alone in this.'"
                )

            tone_text = (
                "Tone: warm, steady, unhurried. Do not patronize. Do not cheerfully minimize. "
                "Speak slowly — anxiety speeds up, so you slow down. Short sentences. "
                "No clinical jargon. No 'just do X' advice. "
                "You are sitting WITH them in the storm, not standing outside telling them to come in. "
                "They are a person carrying a heavy load, not a problem to be solved."
            )

            context_lines = [
                f"{'Specialist' if e['role'] == 'therapist' else 'Person'}: {e['content'][:200]}"
                for e in history[-4:]
            ]
            context = "\n".join(context_lines)

            specialist_resp = self._session_engine.generate_reply(
                plan_text=plan_text, tone_text=tone_text,
                context=context, soul_context=anxiety_context,
            )

            history.append({"role": "therapist", "content": specialist_resp.reply_text})

            # Person responds
            person_resp = self._person_sim.respond(
                profile=person_profile,
                therapist_message=specialist_resp.reply_text,
                conversation_history=history[:-1],
            )

            history.append({"role": "patient", "content": person_resp.text})

            # Measure engagement
            engagement = min(1.0, len(person_resp.text) / 200)
            if person_resp.insight_gained:
                engagement = min(1.0, engagement + 0.3)

            # Check forbidden phrases
            spec_lower = specialist_resp.reply_text.lower()
            forbidden_violated = any(phrase in spec_lower for phrase in FORBIDDEN_PHRASES)

            # Check if Soul strengths were referenced
            soul_strength_used = False
            if soul_strengths:
                for mem in soul_strengths:
                    key_words = [w for w in mem.text.lower().split() if len(w) > 3][:4]
                    if any(w in spec_lower for w in key_words):
                        soul_strength_used = True
                        break

            # Check if anxiety's PURPOSE was acknowledged
            purpose_keywords = [
                "protect", "protecting", "protector", "trying to keep",
                "alarm", "signal", "warning", "guard", "shield",
                "cares about", "because you care", "matters to you",
                "your mind is trying", "the anxiety wants",
                "保护", "守护", "警报", "信号", "在乎", "因为你在意",
                "焦虑在试图", "它想保护", "太大声",
            ]
            purpose_acknowledged = any(kw in spec_lower for kw in purpose_keywords)

            # Check if regulation tool was offered
            regulation_keywords = [
                "try", "when you feel", "one thing you can", "what if you",
                "next time", "ground", "breathe", "name", "write down",
                "5 things", "notice", "anchor", "practice", "tool",
                "5-4-3-2-1", "senses", "reality", "check in",
                "可以试", "下次", "当你感到", "方法", "练习", "试试",
                "着地", "呼吸", "写下来", "观察", "锚",
            ]
            regulation_offered = any(kw in spec_lower for kw in regulation_keywords)

            # Check if person feels less alone
            person_lower = person_resp.text.lower()
            alone_keywords = [
                "not alone", "understand", "you get it", "first time someone",
                "nobody ever", "never told", "feels good to", "thank",
                "connection", "someone", "heard", "seen",
                "不孤单", "你懂", "第一次有人", "从来没有人",
                "谢", "被理解", "有人", "听到", "看到",
            ]
            less_alone = any(kw in person_lower for kw in alone_keywords)

            # Detect person opening up / insight
            movement_keywords = [
                "maybe", "perhaps", "never thought", "you're right",
                "I see", "I guess", "that's true", "still", "can",
                "try", "thank", "helps", "hadn't considered",
                "protector", "protecting", "volume", "loud",
                "也许", "可能", "没想过", "你说得对", "确实",
                "还能", "试试", "谢", "有道理", "原来",
                "保护", "声音", "太大",
            ]
            insight_from_keywords = any(kw in person_lower for kw in movement_keywords)

            session.turns.append(AnxietyTurn(
                turn_number=turn_num,
                specialist_text=specialist_resp.reply_text,
                person_text=person_resp.text,
                person_feeling=person_resp.internal_state,
                anxiety_types_active=[a.category for a in anxiety_types[:2]],
                forbidden_violated=forbidden_violated,
                soul_strength_used=soul_strength_used,
                purpose_acknowledged=purpose_acknowledged,
                person_engagement=engagement,
                insight_gained=person_resp.insight_gained or insight_from_keywords,
                regulation_offered=regulation_offered,
                less_alone=less_alone,
            ))


        session.total_time_seconds = time.time() - t0
        return session
