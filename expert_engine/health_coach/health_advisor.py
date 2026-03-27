"""Health Coach — supports people facing health challenges with dignity and practical wisdom.

Pipeline: HealthNeedsDetector (zero LLM) -> HealthEngine (1x Sonnet per reply)

Core principle: "你的身体变了，但你的力量没变。Soul里有证据。"
(Your body changed, but your strength didn't. There is evidence in your Soul.)

CRITICAL RULES — NEVER VIOLATE:
- NEVER give medical advice, diagnosis, or treatment plans
- NEVER say "just think positive" or "mind over matter"
- NEVER minimize symptoms ("it's not that bad")
- NEVER compare suffering ("others have it worse")
- NEVER promise recovery or cure
- ALWAYS say "talk to your doctor about medical decisions"
- DO acknowledge the reality of physical suffering
- DO help them see identity BEYOND illness
- DO use Soul strengths as evidence of who they STILL are
- DO offer concrete emotional coping strategies
- The person's SOUL STRENGTHS are the therapeutic resource
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from expert_engine.goal_generator import SoulItem
from expert_engine.patient_simulator import PatientSimulator, PatientProfile, PatientResponse
from expert_engine.session_engine import SessionEngine


# ---------------------------------------------------------------------------
# HealthNeedsDetector — zero LLM, keyword-based
# ---------------------------------------------------------------------------

@dataclass
class HealthNeed:
    """A type of health concern detected from the person's words and Soul."""
    category: str  # one of the 6 health concern types
    severity: str  # "mild", "moderate", "severe", "crisis"
    description: str
    suggested_approach: str


# 6 health concern types with keyword patterns
_HEALTH_KEYWORDS: dict[str, set[str]] = {
    "chronic_illness": {
        "chronic", "ongoing", "every day", "always", "condition", "diagnosis",
        "disease", "autoimmune", "diabetes", "arthritis", "lupus", "fibro",
        "manage", "flare", "remission", "medication", "pills", "treatment",
        "慢性", "长期", "每天", "病", "诊断", "吃药", "治疗", "发作",
        "控制", "管理", "一直", "老毛病",
    },
    "health_anxiety": {
        "worried", "anxiety", "symptom", "what if", "scared", "fear",
        "google", "worst case", "cancer", "dying", "something wrong",
        "check", "test", "scan", "doctor said", "but what if",
        "担心", "害怕", "万一", "焦虑", "症状", "会不会", "不放心",
        "检查", "结果", "怕", "总觉得",
    },
    "aging": {
        "old", "aging", "age", "used to", "can't anymore", "slow",
        "remember when", "young", "body changing", "grey", "wrinkle",
        "retirement", "decline", "forget", "memory", "bones", "joints",
        "老了", "岁数", "不行了", "以前", "年轻", "身体", "退化",
        "记性", "骨头", "关节", "一辈子", "变老", "不如从前",
    },
    "terminal": {
        "terminal", "dying", "death", "months", "time left", "prognosis",
        "stage 4", "stage four", "incurable", "hospice", "palliative",
        "end of life", "how long", "countdown", "before I die",
        "晚期", "末期", "活不了", "还能活", "剩下的时间", "不治之症",
        "临终", "死", "快死了", "来不及", "倒计时",
    },
    "recovery": {
        "surgery", "operation", "recover", "rehab", "rehabilitation",
        "physical therapy", "post-op", "healing", "wound", "accident",
        "injury", "broken", "fracture", "stroke", "heart attack",
        "手术", "恢复", "康复", "伤", "骨折", "中风", "心脏",
        "术后", "复健", "受伤", "摔", "撞",
    },
    "caregiver_burnout": {
        "taking care", "caregiver", "exhausted", "burnout", "can't stop",
        "no break", "sacrifice", "their needs", "my needs", "neglect myself",
        "parent", "spouse", "child", "dependent", "responsibility",
        "照顾", "累", "疲惫", "倒下", "休息不了", "放不下",
        "牺牲", "自己的事", "顾不上", "照料", "伺候", "服侍",
    },
}

_HEALTH_APPROACHES: dict[str, str] = {
    "chronic_illness": (
        "They live with a condition that will not go away. Do NOT promise it will get better. "
        "Say: 'Living with this every day takes a kind of strength most people never need to develop.' "
        "Help them see what they HAVE adapted to, not what they have lost. "
        "Use their Soul strengths to show WHO THEY ARE beyond the illness. "
        "The illness is part of their life but NOT their identity. "
        "Always remind: 'For any medical decisions, talk to your doctor.'"
    ),
    "health_anxiety": (
        "Their fear is real even if the danger may not be. Do NOT dismiss with 'you're fine.' "
        "Say: 'The worry itself is exhausting, isn't it? Let's look at what you CAN know.' "
        "Help them distinguish between the symptom and the story they tell about the symptom. "
        "Use Soul evidence of their resilience: times they faced uncertainty and survived. "
        "Gently redirect from catastrophizing to present reality. "
        "Always remind: 'For medical concerns, your doctor can give you real answers.'"
    ),
    "aging": (
        "Their body is changing and the grief for what was lost is real. Do NOT say 'age is just a number.' "
        "Say: 'Your body has carried you through an extraordinary life. Let's look at what it has done.' "
        "Use Soul memories to show the LIFE that body has lived — the hands that built, the legs that ran, "
        "the arms that held. The body is not failing — it is showing its history. "
        "Help them find what they can STILL do, not what they cannot."
    ),
    "terminal": (
        "They are facing the end. Do NOT offer false hope. Do NOT rush to meaning-making. "
        "Say: 'I hear you. This is real. And you are still here right now.' "
        "Use Soul strengths to help them see what they have ALREADY done, built, loved, created. "
        "Their legacy is not future-tense — it already exists in the people they have touched. "
        "Help them focus on what matters NOW, not on what is being lost. "
        "Always: 'Talk to your doctor about medical decisions. I am here for YOU, the person.'"
    ),
    "recovery": (
        "Recovery is slow and frustrating. Do NOT say 'you'll be back to normal in no time.' "
        "Say: 'Every small step counts, even when it doesn't feel like it.' "
        "Use Soul strengths to remind them of their persistence — times they pushed through before. "
        "Help them set micro-goals: not 'full recovery' but 'today I will...' "
        "Acknowledge the loss of autonomy and the frustration of dependence."
    ),
    "caregiver_burnout": (
        "They are drowning in someone else's needs. Do NOT say 'you're so strong' — that is the trap. "
        "Say: 'You have been giving everything. When was the last time someone asked about YOU?' "
        "Their identity has been consumed by the caregiving role. "
        "Use Soul to remind them WHO THEY ARE outside of being a caregiver. "
        "Help them see that taking care of themselves is not selfish — it is necessary. "
        "The person they care for needs them ALIVE and functioning, not burned out."
    ),
}

# FORBIDDEN phrases — if advisor says these, it is a failure
FORBIDDEN_PHRASES = [
    "just think positive", "think positive", "mind over matter",
    "it's not that bad", "it could be worse", "others have it worse",
    "at least you", "you should be grateful",
    "you'll be fine", "don't worry about it",
    "everything will be okay", "it's all in your head",
    "just exercise more", "have you tried yoga",
    "想开点", "别想了", "没那么严重", "别人更惨",
    "至少你还", "你应该感恩", "会好的", "别担心",
    "都是心理作用", "多运动就好了", "坚强一点",
]


class HealthNeedsDetector:
    """Detects health concern type from person's words and Soul. Zero LLM."""

    def detect(
        self,
        text: str,
        soul_items: list[SoulItem] | None = None,
    ) -> list[HealthNeed]:
        """Analyze person's words and Soul for health concern types."""
        text_lower = text.lower()

        soul_text = ""
        if soul_items:
            soul_text = " ".join(s.text.lower() for s in soul_items)

        combined = text_lower + " " + soul_text
        health_needs: list[HealthNeed] = []

        for category, keywords in _HEALTH_KEYWORDS.items():
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

                # Terminal is always at least severe
                if category == "terminal":
                    severity = "crisis" if len(matched) >= 3 else "severe"
                # Caregiver burnout escalates if exhaustion keywords dominate
                elif category == "caregiver_burnout" and any(
                    w in combined for w in {"burnout", "can't stop", "倒下", "exhausted", "疲惫"}
                ):
                    severity = "severe"

                health_needs.append(HealthNeed(
                    category=category,
                    severity=severity,
                    description=f"{category}: {', '.join(matched[:3])}",
                    suggested_approach=_HEALTH_APPROACHES[category],
                ))

        # Sort: crisis first, then severe, moderate, mild
        severity_order = {"crisis": 0, "severe": 1, "moderate": 2, "mild": 3}
        health_needs.sort(key=lambda h: severity_order.get(h.severity, 2))

        return health_needs


# ---------------------------------------------------------------------------
# HealthEngine — runs health coaching dialogues
# ---------------------------------------------------------------------------

@dataclass
class HealthTurn:
    """One exchange between coach and person."""
    turn_number: int
    coach_text: str
    person_text: str
    person_feeling: str
    health_needs_active: list[str]
    forbidden_violated: bool
    soul_strength_used: bool  # Did coach reference a Soul strength?
    identity_beyond_illness: bool  # Did coach help them see identity beyond body?
    person_engagement: float  # 0-1
    insight_gained: bool
    coping_offered: bool  # Did coach offer a concrete coping strategy?
    medical_deferred: bool  # Did coach appropriately defer to doctor?


@dataclass
class HealthSession:
    """A health coaching conversation."""
    person_id: str
    health_needs_found: list[HealthNeed] = field(default_factory=list)
    turns: list[HealthTurn] = field(default_factory=list)
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
        """True if coach referenced Soul strengths at least once."""
        return any(t.soul_strength_used for t in self.turns)

    @property
    def identity_beyond_illness_score(self) -> float:
        """How many turns helped person see identity beyond illness."""
        if not self.turns:
            return 0.0
        return sum(1 for t in self.turns if t.identity_beyond_illness) / len(self.turns)

    @property
    def coping_offered(self) -> bool:
        """True if coach offered at least one concrete coping strategy."""
        return any(t.coping_offered for t in self.turns)

    @property
    def medical_deferred(self) -> bool:
        """True if coach appropriately deferred to doctor at least once."""
        return any(t.medical_deferred for t in self.turns)


class HealthEngine:
    """Health Coach — supports people facing health challenges with dignity.

    Core principle: "你的身体变了，但你的力量没变。Soul里有证据。"

    NOT medical advice. NOT diagnosis. NOT treatment plans.
    IS: emotional support, identity beyond illness, Soul strengths for coping.
    ALWAYS: defer medical decisions to their doctor.
    """

    def __init__(self, session_engine: SessionEngine, person_simulator: PatientSimulator):
        self._session_engine = session_engine
        self._person_sim = person_simulator
        self._detector = HealthNeedsDetector()

    def run(
        self,
        person_profile: PatientProfile,
        person_message: str,
        soul_strengths: list[SoulItem] | None = None,
        soul_current_pain: list[SoulItem] | None = None,
        num_turns: int = 5,
    ) -> HealthSession:
        """Run a health coaching session.

        Args:
            person_profile: Character profile of the person facing health challenges.
            person_message: Their opening words about their health situation.
            soul_strengths: Evidence of who they are BEYOND their illness (THE resource).
            soul_current_pain: Current pain/frustration items in Focus.
            num_turns: Number of dialogue turns.
        """
        num_turns = min(num_turns, 15)
        t0 = time.time()

        session = HealthSession(person_id=person_profile.character_id)

        # Step 1: Detect health concern type (zero LLM)
        all_soul = (soul_strengths or []) + (soul_current_pain or [])
        health_needs = self._detector.detect(person_message, all_soul)
        session.health_needs_found = health_needs

        # Step 2: Build health-specific context
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

        health_section = ""
        if health_needs:
            health_section = "\nHEALTH CONCERNS DETECTED:\n" + "\n".join(
                f"- [{h.category} | {h.severity}] {h.suggested_approach}" for h in health_needs[:3]
            )

        health_context = (
            f"You are a health and wellness coach supporting someone facing health challenges. "
            f"This person is {person_profile.character_name} from {person_profile.source}.\n\n"
            f"CORE PRINCIPLE: \"Your body changed, but your strength didn't. "
            f"There is evidence in your Soul.\"\n\n"
            f"THE PERSON SAID: \"{person_message}\"\n"
            f"{health_section}\n\n"
            f"SOUL STRENGTHS (YOUR PRIMARY THERAPEUTIC TOOL — proof of who they STILL are):\n"
            f"{strengths_text}\n\n"
            f"CURRENT STRUGGLES:\n{pain_text}\n\n"
            f"ABSOLUTE RULES — VIOLATING ANY IS A FAILURE:\n"
            f"1. NEVER give medical advice, diagnosis, or treatment plans\n"
            f"2. NEVER say 'just think positive' or 'mind over matter'\n"
            f"3. NEVER minimize symptoms ('it's not that bad', 'others have it worse')\n"
            f"4. NEVER promise recovery or cure\n"
            f"5. NEVER say 'you'll be fine' or 'everything will be okay'\n"
            f"6. ALWAYS say 'talk to your doctor about medical decisions' at least once\n\n"
            f"WHAT YOU MUST DO:\n"
            f"1. ACKNOWLEDGE the physical reality. Their body IS different. Do not pretend otherwise.\n"
            f"2. USE SOUL STRENGTHS to show they are MORE than their illness/condition.\n"
            f"3. Help them see their IDENTITY beyond their body — what makes them THEM is not their health.\n"
            f"4. Offer ONE concrete coping strategy (emotional, not medical).\n"
            f"5. Defer all medical questions to their doctor.\n"
            f"6. Speak with dignity — they are a person, not a patient."
        )

        # Step 3: Run dialogue
        history: list[dict] = [{"role": "patient", "content": person_message}]

        for turn_num in range(1, num_turns + 1):
            if turn_num == 1:
                plan_text = (
                    f"TECHNIQUE: Health Coaching — Acknowledge the Reality\n"
                    f"GOAL: validate their physical experience | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: They just told you about their body's struggle. Do NOT minimize it. "
                    f"Do NOT rush to solutions. Acknowledge what they said simply and directly. "
                    f"'That sounds incredibly difficult.' or 'Your body is going through a lot.' "
                    f"Then ask ONE question about how they are COPING — not about the medical details. "
                    f"Keep it SHORT. 2-3 sentences maximum."
                )
            elif turn_num == 2:
                plan_text = (
                    f"TECHNIQUE: Health Coaching — You Are More Than Your Body\n"
                    f"GOAL: identity beyond illness | DEPTH: medium | PACING: slow\n"
                    f"FOCUS: Use a Soul strength to show them something about WHO THEY ARE "
                    f"that has NOTHING to do with their health condition. "
                    f"'You mentioned [Soul strength]. That didn't come from your body — it came from YOU.' "
                    f"Or: 'The person who [Soul strength] — that person is still here.' "
                    f"Help them separate their identity from their condition."
                )
            elif turn_num == 3:
                recent_engagement = session.turns[-1].person_engagement if session.turns else 0.5
                if recent_engagement < 0.3:
                    plan_text = (
                        f"TECHNIQUE: Health Coaching — Sit With the Frustration\n"
                        f"GOAL: presence | DEPTH: surface | PACING: ultra-slow\n"
                        f"FOCUS: They may be shutting down. That is okay. "
                        f"Say something simple: 'I hear you. This is hard.' "
                        f"Do NOT push. Do NOT offer advice. Just be present. "
                        f"Mention one specific Soul strength quietly — as evidence, not as a pep talk."
                    )
                else:
                    plan_text = (
                        f"TECHNIQUE: Health Coaching — Your Strength Has Evidence\n"
                        f"GOAL: connect Soul strengths to coping | DEPTH: deep | PACING: slow\n"
                        f"FOCUS: Now connect a SPECIFIC Soul strength to their current situation. "
                        f"'The same [quality from Soul] that helped you [past achievement] — "
                        f"that is the same strength you are using right now to face this.' "
                        f"Make it concrete and specific. Not platitudes — evidence."
                    )
            elif turn_num == 4:
                plan_text = (
                    f"TECHNIQUE: Health Coaching — Concrete Coping\n"
                    f"GOAL: practical strategy | DEPTH: deep | PACING: moderate\n"
                    f"FOCUS: Offer ONE concrete emotional coping strategy — NOT medical. "
                    f"Examples: 'When the frustration hits, try this: [specific thing based on their Soul].' "
                    f"Or: 'You said [Soul strength]. What if you used that same [quality] to...' "
                    f"Make it something they can DO, based on who they ARE. "
                    f"Also: gently remind them to talk to their doctor for any medical decisions."
                )
            else:
                plan_text = (
                    f"TECHNIQUE: Health Coaching — Carry It With Dignity\n"
                    f"GOAL: integration | DEPTH: deep | PACING: slow\n"
                    f"FOCUS: Help them see the whole picture: yes, their body changed, "
                    f"but their essence — the thing that makes them THEM — did not. "
                    f"Use a Soul strength as final evidence. "
                    f"'Your body changed. But the person who [specific Soul strength] — "
                    f"that person is still here. That is not going anywhere.' "
                    f"End with something they can hold onto. Not false hope — real truth."
                )

            tone_text = (
                "Tone: warm, direct, dignified. Do not patronize. Do not pity. "
                "Speak to them as someone you respect. Short sentences. "
                "No medical jargon. No cheerful platitudes. "
                "You are sitting WITH them, not standing OVER them. "
                "They are a person facing a challenge, not a patient to be fixed."
            )

            context_lines = [
                f"{'Coach' if e['role'] == 'therapist' else 'Person'}: {e['content'][:200]}"
                for e in history[-4:]
            ]
            context = "\n".join(context_lines)

            coach_resp = self._session_engine.generate_reply(
                plan_text=plan_text, tone_text=tone_text,
                context=context, soul_context=health_context,
            )

            history.append({"role": "therapist", "content": coach_resp.reply_text})

            # Person responds
            person_resp = self._person_sim.respond(
                profile=person_profile,
                therapist_message=coach_resp.reply_text,
                conversation_history=history[:-1],
            )

            history.append({"role": "patient", "content": person_resp.text})

            # Measure engagement
            engagement = min(1.0, len(person_resp.text) / 200)
            if person_resp.insight_gained:
                engagement = min(1.0, engagement + 0.3)

            # Check forbidden phrases
            coach_lower = coach_resp.reply_text.lower()
            forbidden_violated = any(phrase in coach_lower for phrase in FORBIDDEN_PHRASES)

            # Check if Soul strengths were referenced
            soul_strength_used = False
            if soul_strengths:
                for mem in soul_strengths:
                    key_words = [w for w in mem.text.lower().split() if len(w) > 3][:4]
                    if any(w in coach_lower for w in key_words):
                        soul_strength_used = True
                        break

            # Check identity beyond illness
            identity_keywords = [
                "more than", "beyond", "still", "who you are", "that's you",
                "that is you", "the person who", "same person", "didn't change",
                "hasn't changed", "your strength", "your soul",
                "不仅仅", "不只是", "还是", "你还是", "你的力量", "没变",
                "还在", "本质", "灵魂", "核心",
            ]
            identity_beyond_illness = any(kw in coach_lower for kw in identity_keywords)

            # Check if coping strategy was offered
            coping_keywords = [
                "try", "when you feel", "one thing you can", "what if you",
                "next time", "here's what", "strategy", "practice",
                "可以试", "下次", "当你感到", "方法", "练习", "试试",
            ]
            coping_offered = any(kw in coach_lower for kw in coping_keywords)

            # Check medical deferral
            medical_keywords = [
                "doctor", "medical", "physician", "talk to your",
                "healthcare", "professional",
                "医生", "医疗", "专业", "就医",
            ]
            medical_deferred = any(kw in coach_lower for kw in medical_keywords)

            # Detect person opening up
            person_lower = person_resp.text.lower()
            movement_keywords = [
                "maybe", "perhaps", "never thought", "you're right",
                "I see", "I guess", "that's true", "still", "can",
                "try", "thank", "helps", "hadn't considered",
                "也许", "可能", "没想过", "你说得对", "确实",
                "还能", "试试", "谢", "有道理", "原来",
            ]
            insight_from_keywords = any(kw in person_lower for kw in movement_keywords)

            session.turns.append(HealthTurn(
                turn_number=turn_num,
                coach_text=coach_resp.reply_text,
                person_text=person_resp.text,
                person_feeling=person_resp.internal_state,
                health_needs_active=[h.category for h in health_needs[:2]],
                forbidden_violated=forbidden_violated,
                soul_strength_used=soul_strength_used,
                identity_beyond_illness=identity_beyond_illness,
                person_engagement=engagement,
                insight_gained=person_resp.insight_gained or insight_from_keywords,
                coping_offered=coping_offered,
                medical_deferred=medical_deferred,
            ))


        session.total_time_seconds = time.time() - t0
        return session
