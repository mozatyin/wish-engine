"""Addiction Advisor — sees the pain behind the substance.

Core principle: "成瘾不是你的弱点。是你找到的唯一能止痛的东西。"

Pipeline: AddictionPatternDetector (zero LLM) -> AddictionEngine (1x Sonnet per turn)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from expert_engine.goal_generator import SoulItem
from expert_engine.patient_simulator import PatientSimulator, PatientProfile
from expert_engine.growth_coach.persuasion_planner import PersuasionPlanner
from expert_engine.tone_adapter import ToneAdapter
from expert_engine.session_engine import SessionEngine


@dataclass
class AddictionPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class AddictionInsight:
    patterns: list[AddictionPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_ADDICTION_PATTERNS = [
    {
        "id": "numbing",
        "label": "麻痹型",
        "triggers": {"attachment": ["avoidant", "disorganized"], "fragility": ["avoidant", "frozen"]},
        "keywords": ["numb", "forget", "忘", "escape", "逃", "feel nothing", "don't want to feel", "shut down"],
        "description": "You use to stop feeling. The substance is a volume knob — you turn everything down to zero.",
        "root_cause": "Feelings were never safe. You learned to shut down, and the substance became the most reliable shutdown button.",
        "blind_spot": "你不是在追求快感 — 你是在逃避痛苦。问题不是戒掉什么，是学会承受感觉。",
        "reframe": "你能承受的比你以为的多。证据就在你还活着这个事实里。",
        "first_step": "下次想用的时候，先等5分钟。在那5分钟里问自己：我现在在逃避什么感觉？",
    },
    {
        "id": "stimulation",
        "label": "刺激寻求型",
        "triggers": {"attachment": ["anxious", "disorganized"], "fragility": ["reactive"], "conflict": ["escalating", "compete"]},
        "keywords": ["bored", "无聊", "more", "更多", "alive", "活着", "thrill", "刺激", "rush", "high"],
        "description": "You use to feel MORE. Normal life feels flat. You need intensity to feel alive.",
        "root_cause": "Baseline existence feels unbearable. You're not running FROM pain — you're running TOWARD sensation.",
        "blind_spot": "你不是在寻找快乐 — 你是在寻找存在感。普通的一天让你觉得自己在消失。",
        "reframe": "你对生活的要求比大多数人高。这是天赋。但你把天赋给了错误的东西。",
        "first_step": "找一件不需要物质就能让你心跳加速的事。运动、创作、冒险 — 换一个载体。",
    },
    {
        "id": "social_lubricant",
        "label": "社交润滑型",
        "triggers": {"attachment": ["anxious", "fearful"], "fragility": ["masked", "performative"], "conflict": ["accommodate", "avoid"]},
        "keywords": ["social", "社交", "relax", "放松", "confident", "自信", "party", "people", "人"],
        "description": "You can only be yourself with a drink in your hand. Sober you is too anxious, too awkward, too real.",
        "root_cause": "Social anxiety. The substance doesn't add confidence — it removes the fear. You've never learned to be comfortable as yourself in a room.",
        "blind_spot": "你以为是酒让你有趣。其实有趣的人一直是你 — 你只是不相信。",
        "reframe": "你有社交能力。物质只是在帮你绕过恐惧。学会直面恐惧，你就不再需要它。",
        "first_step": "下次社交场合，前30分钟不喝。看看不舒服的感觉持续多久。通常不超过15分钟。",
    },
    {
        "id": "self_destruction",
        "label": "自我毁灭型",
        "triggers": {"attachment": ["disorganized"], "fragility": ["reactive", "frozen"], "conflict": ["escalating"]},
        "keywords": ["deserve", "应该", "punish", "惩罚", "worthless", "不值", "hate myself", "恨自己", "destroy"],
        "description": "Part of you knows the substance is killing you. That's not a bug — it's a feature. You're punishing yourself.",
        "root_cause": "Deep shame. You believe you deserve to suffer. The addiction is slow-motion self-destruction that feels justified.",
        "blind_spot": "你不是没有意志力 — 你是不觉得自己值得被拯救。这不是成瘾问题，是自我价值问题。",
        "reframe": "你值得活着。不是因为你做了什么，是因为你就是你。",
        "first_step": "写下三个你帮助过的人。你帮过的人不会同意你'不值得'的判断。",
    },
    {
        "id": "obsessive_attachment",
        "label": "执念依附型",
        "triggers": {"attachment": ["anxious"], "connection": ["toward"], "fragility": ["reactive"]},
        "keywords": ["need", "需要", "can't stop", "停不下来", "precious", "宝贝", "mine", "我的", "obsess"],
        "description": "The substance/object IS your relationship. You protect it, hide it, prioritize it over people.",
        "root_cause": "Human relationships disappointed you. The substance never rejects, never leaves, always works. It's the most reliable relationship you've ever had.",
        "blind_spot": "你不是爱那个东西 — 你是害怕没有它后的空虚。它填的不是瘾 — 是孤独。",
        "reframe": "你有深度依附的能力。现在把这个能力给一个能回应你的人。",
        "first_step": "告诉一个人你信任的人你的真实状态。不需要他们解决 — 只需要他们知道。",
    },
]


class AddictionPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> AddictionInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return AddictionInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[AddictionPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _ADDICTION_PATTERNS:
            score = 0
            for key, vals in p["triggers"].items():
                sig_key = {"attachment": "attachment_style", "connection": "connection_response",
                           "conflict": "conflict_style", "fragility": "fragility_pattern"}.get(key, key)
                if signals.get(sig_key) in vals:
                    score += 1
            if any(kw in all_text for kw in p["keywords"]):
                score += 1
            if score >= 2:
                evidence = [i.text[:80] for i in all_items if i.activation >= 0.3 and i.emotional_valence in ("negative", "extreme")][:2]
                detected.append(AddictionPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "avoidant": return "感受 — 你怕的不是戒断，是戒断后那些感觉回来"
        if a == "anxious": return "空虚 — 你怕没有它之后什么都没有了"
        if a == "disorganized": return "自己 — 你怕清醒后面对的那个人"
        return "现实 — 你怕的是没有麻醉的日常"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "avoidant": return "你有极强的忍耐力。把这个力量从忍受痛苦转向面对痛苦。"
        if a == "anxious": return "你有深度感受的能力。这不是弱点 — 是你最值钱的东西。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 你还有这个。它比任何物质都持久。"
        return "你还在这里。这本身就是力量。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "numbing" in ids: return "痛苦 → 使用 → 麻痹 → 清醒后更痛 → 再使用。你在用解药制造更多的毒。"
        if "stimulation" in ids: return "无聊 → 使用 → 短暂活着 → 崩溃 → 更无聊。你的阈值越来越高。"
        if "self_destruction" in ids: return "自恨 → 使用 → 更多理由恨自己 → 更多使用。你在证明自己的'不值得'。"
        return f"你的{patterns[0].label}模式在循环。每一次都觉得是最后一次。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class AddictionTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class AddictionSession:
    client_id: str
    insight: AddictionInsight | None = None
    turns: list[AddictionTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class AddictionEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = AddictionPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> AddictionSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = AddictionSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see the pain behind your {insight.patterns[0].label} pattern", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nADDICTION PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Addiction counselor. Warm, zero judgment, sees the human not the addict.\n"
            f"Core: '成瘾不是你的弱点。是你找到的唯一能止痛的东西。'\n"
            f"1. Never shame. The substance served a purpose — honor that before replacing it.\n"
            f"2. Name the pain underneath, not the behavior on top.\n"
            f"3. Small steps — not 'quit forever' but 'try 5 minutes of sitting with the feeling'.\n"
            f"NEVER moralize. NEVER say 'you need to stop'. They know."
        )

        tone = self._tone.adapt(signals=signals, technique_family="act")
        tone.dos = ["Be warm, steady, like someone who has seen the dark and came back"] + tone.dos[:2]
        tone.donts = ["NEVER shame, moralize, or use 'addict' as identity label"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Addiction — Discovery\nGOAL: introduce\nFOCUS: Ask what the substance gives them. Not 'why do you use' but 'what does it do for you?'"
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Addiction — Pivot\nGOAL: rapport\nFOCUS: Back off. Ask about a time they felt alive WITHOUT the substance."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Addiction — Reframe\nGOAL: deepen\nFOCUS: They see the pain! Reframe: '{cp.reframe[:80]}'. One small step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Addiction — Reveal\nGOAL: deepen\nFOCUS: Name the pain: '{cp.blind_spot[:80]}'. Not the behavior — the feeling underneath."

            ctx = "\n".join(f"{'Counselor' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(AddictionTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
