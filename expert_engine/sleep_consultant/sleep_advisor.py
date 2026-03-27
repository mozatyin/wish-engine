"""Sleep Advisor — your insomnia is not a body problem, it is a mind still in daytime.

Core principle: "失眠不是你的身体有问题。是你的心还在白天。"

Pipeline: SleepPatternDetector (zero LLM) -> SleepEngine (1x Sonnet per turn)
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
class SleepPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class SleepInsight:
    patterns: list[SleepPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_SLEEP_PATTERNS = [
    {
        "id": "guilt_insomnia",
        "label": "内疚失眠",
        "triggers": {"fragility": ["reactive", "masked"], "conflict": ["avoid", "accommodate"]},
        "keywords": ["guilt", "罪", "wrong", "错", "forgive", "原谅", "regret", "后悔", "haunt", "blood", "done"],
        "description": "Your mind replays what you did wrong. At 3am, the jury convenes and you're always guilty.",
        "root_cause": "Unprocessed guilt. Daytime is busy enough to suppress it. Night strips away the distractions and the truth arrives.",
        "blind_spot": "你不是失眠 — 你是在用清醒惩罚自己。你的大脑觉得你不配安睡。",
        "reframe": "你的内疚说明你有良知。但良知的工作是指引你改变 — 不是折磨你不眠。",
        "first_step": "睡前写下今天让你内疚的事。然后写一句：'明天我可以做什么'。把法庭从脑子里搬到纸上。",
    },
    {
        "id": "anxiety_vigilance",
        "label": "焦虑警觉型",
        "triggers": {"attachment": ["anxious"], "fragility": ["reactive", "anxious"], "conflict": ["avoid"]},
        "keywords": ["worry", "担心", "what if", "万一", "tomorrow", "明天", "can't stop thinking", "停不下来", "mind racing"],
        "description": "Your mind won't stop planning, worrying, anticipating. Sleep feels like letting your guard down in enemy territory.",
        "root_cause": "Hypervigilance. Your nervous system doesn't believe it's safe to power down. Sleeping = vulnerability.",
        "blind_spot": "你不是'想太多' — 你是不信任世界在你睡着的时候不会出事。这不是思维问题，是安全感问题。",
        "reframe": "你的警觉保护了你很多年。但夜晚可以是安全的。什么都不会发生 — 至少今晚不会。",
        "first_step": "睡前做一个'worry dump'：把所有担心的事写下来，合上本子。告诉大脑：'我登记了，明天处理。'",
    },
    {
        "id": "loneliness_insomnia",
        "label": "孤独失眠",
        "triggers": {"attachment": ["anxious", "disorganized"], "connection": ["toward"], "fragility": ["reactive"]},
        "keywords": ["alone", "孤独", "lonely", "nobody", "没人", "empty bed", "dark", "夜", "silence", "安静"],
        "description": "The room is too quiet. The bed is too big. Night amplifies loneliness to an unbearable volume.",
        "root_cause": "Daytime has distractions. Night has none. The aloneness you can ignore at noon becomes inescapable at midnight.",
        "blind_spot": "你不是怕黑 — 你是怕安静。安静的时候你能听见自己有多孤独。",
        "reframe": "你渴望连接 — 这是人类最基本的需求。你不是weak — 你是human。",
        "first_step": "睡前给一个人发一条晚安消息。不长，几个字就够。让你知道世界上有人知道你存在。",
    },
    {
        "id": "unfinished_day",
        "label": "未完成的白天",
        "triggers": {"conflict": ["compete"], "fragility": ["masked", "performative"]},
        "keywords": ["not enough", "不够", "more to do", "还有", "wasted", "浪费", "productive", "效率", "deadline"],
        "description": "You can't sleep because the day didn't have enough hours. There's always more to do. Rest feels like failure.",
        "root_cause": "Your worth is tied to productivity. Sleeping is 'wasting time.' Resting is 'lazy.' Your body needs sleep but your identity won't allow it.",
        "blind_spot": "你不是太忙不能睡 — 你是用忙碌逃避静下来后的空虚感。如果你不做事，你是谁？",
        "reframe": "休息不是懒惰 — 是投资。最高效的人知道：睡眠是效率的地基。",
        "first_step": "设一个'关机时间'。10pm之后不工作。不是因为你不想 — 是因为明天需要你满血。",
    },
    {
        "id": "nightmare_dread",
        "label": "噩梦恐惧型",
        "triggers": {"attachment": ["disorganized"], "fragility": ["frozen", "reactive"]},
        "keywords": ["nightmare", "噩梦", "dream", "梦", "afraid to sleep", "怕睡", "wake up", "screaming", "sweat"],
        "description": "You're not afraid of not sleeping — you're afraid of what happens when you do. Sleep is where the monsters live.",
        "root_cause": "Unprocessed trauma surfaces in dreams. Your brain tries to process at night what it couldn't handle during the day.",
        "blind_spot": "噩梦不是你大脑的故障 — 是你大脑在试图处理白天无法面对的东西。它在工作，不是在攻击你。",
        "reframe": "你的大脑在试图帮你。噩梦是处理痛苦的方式 — 笨拙的、可怕的，但它在尝试。",
        "first_step": "醒来后写下梦的内容。不分析，只记录。把它从脑子里搬到纸上。它在纸上比在脑子里安全。",
    },
]


class SleepPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> SleepInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return SleepInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[SleepPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _SLEEP_PATTERNS:
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
                detected.append(SleepPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "失控 — 你怕睡着的时候世界出事"
        if a == "avoidant": return "脆弱 — 你怕睡眠暴露了你不设防的自己"
        if a == "disorganized": return "黑暗 — 你怕关灯后来的不是休息是噩梦"
        return "面对自己 — 你怕安静的时候听见自己真实的声音"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的警觉保护了你。现在告诉它：今晚可以下班了。"
        if a == "avoidant": return "你的自制力是真实的。用同样的纪律建立睡眠仪式。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 这个记忆可以成为你的安眠锚点。"
        return "你还在寻找解决方案就说明你还没放弃自己。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "guilt_insomnia" in ids: return "睡不着 → 想太多 → 更内疚 → 更睡不着。你的大脑在用失眠惩罚你。"
        if "anxiety_vigilance" in ids: return "担心 → 睡不着 → 担心睡不着 → 更睡不着。焦虑变成了自我实现的预言。"
        if "nightmare_dread" in ids: return "怕噩梦 → 抗拒入睡 → 终于睡着 → 噩梦 → 更怕。你在和自己的大脑打仗。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class SleepTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class SleepSession:
    client_id: str
    insight: SleepInsight | None = None
    turns: list[SleepTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class SleepEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = SleepPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> SleepSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = SleepSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"understand your {insight.patterns[0].label} and find peace", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nSLEEP PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Sleep consultant. Calm, gentle, like a voice at bedtime.\n"
            f"Core: '失眠不是你的身体有问题。是你的心还在白天。'\n"
            f"1. Name what keeps them awake — not the symptom, the feeling\n"
            f"2. Normalize: your brain is trying to protect you, not torture you\n"
            f"3. One bedtime ritual, not a sleep hygiene lecture\n"
            f"NEVER say 'just relax'. NEVER list sleep tips. Address the WHY."
        )

        tone = self._tone.adapt(signals=signals, technique_family="act")
        tone.dos = ["Be calm and gentle, like a bedtime voice that makes the room feel safe"] + tone.dos[:2]
        tone.donts = ["NEVER lecture about sleep hygiene or say 'just relax'"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Sleep — Discovery\nGOAL: introduce\nFOCUS: Ask what happens when they close their eyes. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Sleep — Pivot\nGOAL: rapport\nFOCUS: Ask about the last time they slept peacefully. What was different?"
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Sleep — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Ritual: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Sleep — Reveal\nGOAL: deepen\nFOCUS: Name what's really happening: '{cp.blind_spot[:80]}'. Gently."

            ctx = "\n".join(f"{'Consultant' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(SleepTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
