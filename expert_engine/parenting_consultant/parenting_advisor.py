"""Parenting Advisor — reveals parenting patterns from Soul and coaches authentic parenting.

Core principle: "你不需要完美的父母。你需要一个真实的父母。"

Pipeline: ParentingPatternDetector (zero LLM) -> ParentingEngine (1x Sonnet per turn)
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
class ParentingPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class ParentingInsight:
    patterns: list[ParentingPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_PARENTING_PATTERNS = [
    {
        "id": "controlling",
        "label": "控制型",
        "triggers": {"conflict": ["compete", "escalating"], "fragility": ["masked", "performative"]},
        "keywords": ["必须", "should", "must", "规矩", "discipline", "obey", "听话", "不许"],
        "description": "You set the rules and expect obedience. Your child's independence feels like disobedience.",
        "root_cause": "Control masks fear — if you let go, something bad might happen. Your own childhood taught you that chaos is dangerous.",
        "blind_spot": "你不是在保护孩子 — 你是在保护自己免受失控的恐惧。孩子需要的不是规矩，是安全感。",
        "reframe": "你的严格说明你在乎。但在乎可以有另一种形状 — 不是墙，是桥。",
        "first_step": "今天问孩子一个开放问题：'你觉得呢？'然后闭嘴听完。",
    },
    {
        "id": "overprotective",
        "label": "过度保护型",
        "triggers": {"attachment": ["anxious"], "connection": ["toward"], "fragility": ["reactive", "anxious"]},
        "keywords": ["worry", "dangerous", "担心", "害怕", "protect", "safe", "小心", "别去"],
        "description": "You see danger everywhere. Every scraped knee is a near-miss. Your love is a bubble wrap around your child.",
        "root_cause": "Your anxiety became your parenting style. You experienced loss or helplessness, and now you try to prevent ALL pain for your child.",
        "blind_spot": "你不让孩子摔跤 — 但摔跤是学走路的一部分。你的保护正在偷走他们的勇气。",
        "reframe": "你的警觉说明你是一个用心的父母。但用心也可以是放手看着他们飞。",
        "first_step": "让孩子做一件让你紧张但不危险的事。忍住不说'小心'。",
    },
    {
        "id": "absent",
        "label": "缺席型",
        "triggers": {"attachment": ["avoidant", "disorganized"], "connection": ["away"], "fragility": ["avoidant", "frozen"]},
        "keywords": ["busy", "忙", "work", "later", "以后", "provide", "赚钱", "没时间"],
        "description": "You provide everything except presence. You tell yourself working hard IS loving them.",
        "root_cause": "Emotional presence was never modeled for you. You show love through providing because that feels safe — feelings don't.",
        "blind_spot": "你给了他们一切除了你。孩子不记得你买了什么 — 他们记得你在不在。",
        "reframe": "你拼命工作说明你爱他们。但他们需要的不是更好的生活 — 是你坐下来的十分钟。",
        "first_step": "今晚回家，放下手机，问孩子：'今天最好玩的事是什么？'",
    },
    {
        "id": "enmeshed",
        "label": "共生型",
        "triggers": {"attachment": ["anxious", "fearful"], "connection": ["toward"], "conflict": ["accommodate"]},
        "keywords": ["我们", "together", "need me", "离不开", "为了你", "sacrifice", "everything for"],
        "description": "Your identity IS being a parent. When they grow up, you lose yourself.",
        "root_cause": "You found your worth in being needed. The child growing up feels like abandonment — not theirs, yours.",
        "blind_spot": "你不是为了孩子活 — 你是用孩子填满自己的空。他们独立不是离开你，是成为自己。",
        "reframe": "你的全心投入说明你知道怎么爱。现在学一个新课题：爱一个不再需要你的人。",
        "first_step": "这周做一件只为自己的事 — 不和孩子有关的。",
    },
    {
        "id": "harsh_critic",
        "label": "严厉批评型",
        "triggers": {"conflict": ["compete", "escalating"], "fragility": ["masked"], "attachment": ["avoidant"]},
        "keywords": ["不够好", "not enough", "harder", "更努力", "fail", "disappoint", "丢人", "shame"],
        "description": "You push because you believe pressure makes diamonds. But your child hears 'I'm not enough' on repeat.",
        "root_cause": "Someone did this to you. You internalized the critic and now you pass it on, believing it's love.",
        "blind_spot": "你以为严格是爱。但孩子分不清'你可以更好'和'你不够好'。他们听到的是后者。",
        "reframe": "你的高标准说明你相信孩子的潜力。换一种说法：'我看到你能做到'比'你怎么又搞砸了'有力一百倍。",
        "first_step": "今天表扬孩子一件具体的事。不是'你真棒'，是'你刚才帮妹妹那个举动很温暖'。",
    },
]


class ParentingPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> ParentingInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return ParentingInsight(
            patterns=patterns,
            core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[ParentingPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _PARENTING_PATTERNS:
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
                resource = next((i.text[:80] for i in deep + (memory or []) if i.emotional_valence == "positive"), "your past")
                detected.append(ParentingPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "失去他们 — 你怕孩子不再需要你"
        if a == "avoidant": return "做错了 — 你怕自己毁了他们"
        if a == "disorganized": return "重蹈覆辙 — 你怕变成你的父母"
        return "不够好 — 你怕自己不是一个好父母"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的全心投入是真的。孩子能感受到。你需要的不是少爱，是换一种形状。"
        if a == "avoidant": return "你的独立教会了孩子自立。现在加上温度就完美了。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"你的Soul里有这个: '{i.text[:60]}' — 这说明你知道什么是好的养育。"
        return "你在想这个问题本身就说明你是一个用心的父母。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "controlling" in ids: return "立规矩 → 孩子反抗 → 更严 → 关系疏远 → 后悔。你在用控制表达爱，但孩子收到的是压迫。"
        if "overprotective" in ids: return "担心 → 限制 → 孩子退缩 → 更担心。你的保护正在制造你害怕的脆弱。"
        if "absent" in ids: return "工作 → 缺席 → 内疚 → 用物质补偿 → 继续工作。你在用忙碌逃避亲密。"
        return f"你的{patterns[0].label}模式在重复。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3:
                return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class ParentingTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class ParentingSession:
    client_id: str
    insight: ParentingInsight | None = None
    turns: list[ParentingTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class ParentingEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = ParentingPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> ParentingSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = ParentingSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see your {insight.patterns[0].label} parenting pattern", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}"
                                for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nPARENTING PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}, USE={', '.join(strategy.use_words[:5])}\n\n"
            f"APPROACH: Warm parenting consultant. Core: '你不需要完美的父母。你需要一个真实的父母。'\n"
            f"1. No judgment — every parent is trying their best\n"
            f"2. Use their own childhood memories as mirrors\n"
            f"3. One concrete change, not a lecture\n"
            f"NEVER blame. NEVER say 'you're damaging your child'."
        )

        tone = self._tone.adapt(signals=signals, technique_family="relationship")
        tone.dos = ["Be warm, non-judgmental, like a wise friend who also has kids"] + tone.dos[:2]
        tone.donts = ["NEVER guilt-trip about parenting failures"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Parenting — Discovery\nGOAL: introduce\nFOCUS: Listen to their parenting struggle. Plant seed of {cp.label} pattern."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Parenting — Pivot\nGOAL: rapport\nFOCUS: Back off. Ask about a good parenting moment."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Parenting — Reframe\nGOAL: deepen\nFOCUS: They see it! Reframe: '{cp.reframe[:80]}'. Give first step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Parenting — Reveal\nGOAL: deepen\nFOCUS: Show pattern: '{cp.blind_spot[:80]}'. Ask a question, don't lecture."

            ctx = "\n".join(f"{'Coach' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(ParentingTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
