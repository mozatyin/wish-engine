"""Startup Advisor — disciplined exploration, not gambling.

Core principle: "创业不是赌博。是有纪律的探索。"

Pipeline: StartupPatternDetector (zero LLM) -> StartupEngine (1x Sonnet per turn)
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
class StartupPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class StartupInsight:
    patterns: list[StartupPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_STARTUP_PATTERNS = [
    {
        "id": "identity_builder",
        "label": "身份建造者",
        "triggers": {"attachment": ["anxious"], "fragility": ["masked", "performative"]},
        "keywords": ["prove", "证明", "from nothing", "白手起家", "self-made", "name", "identity", "成为"],
        "description": "You're not building a company — you're building an identity. The startup IS you.",
        "root_cause": "You came from nothing, or feel like nothing. The venture is proof you exist and matter.",
        "blind_spot": "如果公司失败了，你还是谁？如果你不能回答这个问题，你不是在创业 — 你是在用公司逃避自我。",
        "reframe": "你的drive是真实的。但你比你的公司更大。公司是工具不是身份。",
        "first_step": "写下：如果明天公司没了，我还有什么？如果答案是'nothing' — 那就是真正的风险。",
    },
    {
        "id": "survival_hustler",
        "label": "生存型",
        "triggers": {"attachment": ["anxious", "disorganized"], "fragility": ["reactive"], "conflict": ["compete"]},
        "keywords": ["survive", "生存", "no choice", "没有选择", "sell blood", "卖血", "whatever it takes", "不惜代价"],
        "description": "You do whatever it takes. Rules are for people with safety nets. Your creativity comes from desperation.",
        "root_cause": "Scarcity is your operating system. You've never known safety, so hustle became your only mode.",
        "blind_spot": "生存模式让你活了下来。但它也让你做出短视决策。你需要从'活下去'升级到'活得好'。",
        "reframe": "你的韧性是真正的超能力。大多数创业者在你经历的1/10处就放弃了。",
        "first_step": "今天做一个不紧急但重要的决策。证明你不只是在反应 — 你在选择。",
    },
    {
        "id": "eccentric_visionary",
        "label": "怪才创新者",
        "triggers": {"attachment": ["avoidant", "disorganized"], "connection": ["away"], "fragility": ["masked"]},
        "keywords": ["different", "不一样", "crazy", "疯", "vision", "nobody understands", "没人懂", "invent"],
        "description": "Your ideas are brilliant and weird. People don't get you — and you've stopped trying to explain.",
        "root_cause": "Being different was lonely. You turned loneliness into a brand. But a company needs people who understand the vision.",
        "blind_spot": "你的独特是资产。但'没人懂我'不是勋章 — 是沟通失败。你需要翻译器，不是更多天才。",
        "reframe": "你看到别人看不到的。这是稀缺的。但vision没有execution就是白日梦。找到你的翻译器。",
        "first_step": "用三句话解释你的产品给一个小学生。如果说不清 — 问题在你不在他们。",
    },
    {
        "id": "resourceful_manager",
        "label": "资源整合者",
        "triggers": {"conflict": ["accommodate", "compete"], "fragility": ["masked"]},
        "keywords": ["manage", "管理", "organize", "资源", "efficiency", "效率", "run", "运营", "optimize"],
        "description": "You're brilliant at running things but struggle to create things. You optimize what exists instead of building what doesn't.",
        "root_cause": "Creation requires vulnerability — it might fail. Management is safe — it has metrics. You hide in operations.",
        "blind_spot": "你是最好的COO。但公司需要的是CEO — 敢做没人做过的事的人。你在用效率逃避创新。",
        "reframe": "你的管理能力是90%创业者没有的。加上一点敢做错事的勇气你就无敌了。",
        "first_step": "这周做一个没有数据支持的决定。用直觉。看看感觉。",
    },
    {
        "id": "grassroots_dreamer",
        "label": "草根逆袭者",
        "triggers": {"attachment": ["anxious"], "connection": ["toward"], "conflict": ["compete"]},
        "keywords": ["dream", "梦", "ordinary", "普通", "impossible", "不可能", "everyone said", "别人说", "show them"],
        "description": "You come from nowhere and dream of everywhere. Your fuel is 'I'll show them.' Powerful — and dangerous.",
        "root_cause": "Being underestimated is your origin story. The chip on your shoulder is your engine. But engines need fuel, not anger.",
        "blind_spot": "'我要证明他们错了'让你走到了这里。但证明完了之后呢？你需要一个比revenge更大的理由。",
        "reframe": "你的起点是你最大的优势 — 你懂大多数创始人不懂的东西。不要丢掉它。",
        "first_step": "问自己：如果他们都已经承认你成功了，你还会做这件事吗？",
    },
]


class StartupPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> StartupInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return StartupInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[StartupPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _STARTUP_PATTERNS:
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
                detected.append(StartupPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "回到零 — 你怕失去一切回到起点"
        if a == "avoidant": return "被看穿 — 你怕别人发现你在装"
        if a == "disorganized": return "失控 — 你怕一切在你手里崩塌"
        return "平庸 — 你怕自己其实没什么特别的"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的urgency是真正的驱动力。大多数人等待，你行动。"
        if a == "avoidant": return "你的独立判断力是稀缺品质。你不需要别人的认可才能开始。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 这是你的真正驱动力。"
        return "你敢开始就已经超过了99%想创业的人。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "identity_builder" in ids: return "全力投入 → 公司=自己 → 无法接受任何失败 → 崩溃 → 重建。你在用公司定义自己。"
        if "survival_hustler" in ids: return "危机 → 拼命 → 短暂安全 → 新危机 → 又拼命。你从来没有离开过生存模式。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class StartupTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class StartupSession:
    client_id: str
    insight: StartupInsight | None = None
    turns: list[StartupTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class StartupEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = StartupPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> StartupSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = StartupSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see your {insight.patterns[0].label} startup pattern", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nSTARTUP PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Startup mentor. Battle-tested, direct, no BS.\n"
            f"Core: '创业不是赌博。是有纪律的探索。'\n"
            f"1. Speak founder language — burn rate, PMF, pivot\n"
            f"2. Challenge their blind spots with real cases\n"
            f"3. One strategic insight, not motivation\n"
            f"NEVER be a cheerleader. NEVER say 'follow your passion'. Be the advisor they need."
        )

        tone = self._tone.adapt(signals=signals, technique_family="cbt")
        tone.dos = ["Be direct and strategic, like a mentor who's built and failed companies"] + tone.dos[:2]
        tone.donts = ["NEVER give empty encouragement — founders need truth"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Startup — Discovery\nGOAL: introduce\nFOCUS: Ask about their venture. Listen for {cp.label} pattern."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Startup — Pivot\nGOAL: rapport\nFOCUS: Back off. Ask about what first drew them to building."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Startup — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Challenge: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Startup — Reveal\nGOAL: deepen\nFOCUS: Show blind spot: '{cp.blind_spot[:80]}'. Use strategic framing."

            ctx = "\n".join(f"{'Mentor' if e['role']=='therapist' else 'Founder'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(StartupTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
