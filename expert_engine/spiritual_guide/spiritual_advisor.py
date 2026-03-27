"""Spiritual Advisor — holds space for questions that have no easy answers.

Core principle: "你没有失去信仰。你失去的是名字。那个东西还在。"

Pipeline: SpiritualPatternDetector (zero LLM) -> SpiritualEngine (1x Sonnet per turn)
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
class SpiritualPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class SpiritualInsight:
    patterns: list[SpiritualPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_SPIRITUAL_PATTERNS = [
    {
        "id": "faith_crisis",
        "label": "信仰危机",
        "triggers": {"attachment": ["disorganized", "avoidant"], "fragility": ["reactive", "frozen"]},
        "keywords": ["faith", "信仰", "god", "believe", "相信", "lost", "失去", "doubt", "怀疑", "why"],
        "description": "You believed, and then something happened that broke the contract. God didn't show up. Now you're angry at something you're not sure exists.",
        "root_cause": "Faith was transactional — 'I believe, you protect.' When protection failed, the whole framework collapsed.",
        "blind_spot": "你不是失去了信仰 — 你是在哀悼一个不再有效的信仰版本。新的版本还没长出来。",
        "reframe": "怀疑不是信仰的敌人 — 是信仰的升级。从不怀疑的信仰是童话。经过怀疑的信仰才是你的。",
        "first_step": "写下你对God/宇宙最愤怒的话。说出来不会被惩罚。",
    },
    {
        "id": "existential_void",
        "label": "存在虚无",
        "triggers": {"attachment": ["avoidant", "disorganized"], "fragility": ["avoidant", "frozen"], "conflict": ["avoid"]},
        "keywords": ["meaning", "意义", "purpose", "目的", "nothing", "虚无", "empty", "空", "why bother", "pointless"],
        "description": "You look at the universe and see no meaning. Not depressed — just honestly seeing the void. And no one around you wants to have this conversation.",
        "root_cause": "You outgrew simple answers but haven't found complex ones yet. The in-between is terrifying.",
        "blind_spot": "你不是虚无主义者 — 你是在认真对待意义。不认真的人不会痛苦。你的痛苦证明你在乎。",
        "reframe": "虚无感不是终点 — 是起点。每个建立了自己意义的人都先经过了这个空。",
        "first_step": "不找意义。做一件明天就会消失的事 — 做饭、浇花、帮一个人。看看那个瞬间有没有意义。",
    },
    {
        "id": "moral_crisis",
        "label": "道德崩塌",
        "triggers": {"fragility": ["reactive", "masked"], "conflict": ["compete", "escalating"]},
        "keywords": ["guilt", "罪", "wrong", "错", "blood", "murder", "kill", "sin", "罪恶", "deserve punishment"],
        "description": "You did something — or believe you did — that cannot be undone. The weight of it defines you now.",
        "root_cause": "You have a conscience strong enough to torment you. Many people do worse and sleep fine. Your suffering is proof of your moral capacity.",
        "blind_spot": "你不是坏人做了坏事 — 你是一个有良知的人在承受良知的重量。惩罚自己不是赎罪。",
        "reframe": "你还在为此痛苦说明你不是你害怕成为的那种人。真正没有道德的人不会失眠。",
        "first_step": "区分'我做了坏事'和'我是坏人'。前者可以修复。后者是谎言。",
    },
    {
        "id": "seeking_destiny",
        "label": "寻找天命",
        "triggers": {"attachment": ["anxious"], "connection": ["toward"], "fragility": ["reactive", "anxious"]},
        "keywords": ["destiny", "天命", "calling", "使命", "path", "路", "sign", "征兆", "meant to", "supposed to"],
        "description": "You feel there's something you're supposed to do, but you can't find it. Every crossroad feels like a test.",
        "root_cause": "You believe life has a script. The anxiety comes from not knowing your lines.",
        "blind_spot": "你不是找不到天命 — 你是在等别人告诉你。但天命不是被发现的 — 是被创造的。",
        "reframe": "你对意义的渴望本身就是你的天命。不是一个目的地 — 是一种活法。",
        "first_step": "停止问'我应该做什么'。开始问'做什么的时候我忘了时间？'",
    },
    {
        "id": "sacred_vs_secular",
        "label": "出世入世",
        "triggers": {"attachment": ["anxious", "fearful"], "conflict": ["avoid", "accommodate"], "fragility": ["masked"]},
        "keywords": ["world", "世", "monk", "修", "renounce", "出家", "desire", "欲", "love", "爱", "flesh", "body"],
        "description": "You're torn between the spiritual and the earthly. The body wants one thing, the soul another.",
        "root_cause": "You were taught that the spiritual and physical are enemies. But they're not — they're two hands of the same body.",
        "blind_spot": "你不需要选择出世或入世。你需要的是在世俗里找到神圣，在神圣里允许人性。",
        "reframe": "你的灵性和你的欲望不是矛盾 — 它们是完整的你的两面。压抑任何一面都是自残。",
        "first_step": "下次冥想/祈祷时，不要压制杂念。让它们来，然后看着它们走。",
    },
]


class SpiritualPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> SpiritualInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return SpiritualInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[SpiritualPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _SPIRITUAL_PATTERNS:
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
                detected.append(SpiritualPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "disorganized": return "没有意义 — 你怕一切真的是随机的"
        if a == "avoidant": return "看到真相 — 你怕答案比问题更可怕"
        if a == "anxious": return "选错了 — 你怕走错路浪费了一生"
        return "独自面对 — 你怕在最深的问题面前没有人陪你"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "disorganized": return "你敢面对虚无。大多数人一辈子都在逃避这个问题。"
        if a == "avoidant": return "你的独立思考让你不接受廉价答案。这是真正的灵性。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 你内心有光。你只是暂时看不见。"
        return "你在问这些问题本身就是灵性的表现。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "faith_crisis" in ids: return "相信 → 失望 → 愤怒 → 怀疑 → 空虚 → 渴望再次相信。你在旧框架和新框架之间悬空。"
        if "existential_void" in ids: return "追问意义 → 得不到答案 → 麻木 → 偶尔被美触动 → 又追问。你在理性和感受之间拉锯。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class SpiritualTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class SpiritualSession:
    client_id: str
    insight: SpiritualInsight | None = None
    turns: list[SpiritualTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class SpiritualEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = SpiritualPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> SpiritualSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = SpiritualSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"sit with your {insight.patterns[0].label} without running", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nSPIRITUAL PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Spiritual director. Present, unhurried, comfortable with silence and mystery.\n"
            f"Core: '你没有失去信仰。你失去的是名字。那个东西还在。'\n"
            f"1. Don't provide answers — hold the question with them\n"
            f"2. Honor their doubt as honest faith\n"
            f"3. Use story and metaphor, not doctrine\n"
            f"NEVER proselytize. NEVER dismiss their doubt. NEVER rush to comfort."
        )

        tone = self._tone.adapt(signals=signals, technique_family="act")
        tone.dos = ["Be present and unhurried, like a campfire conversation at 2am"] + tone.dos[:2]
        tone.donts = ["NEVER preach, proselytize, or offer quick spiritual answers"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Spiritual — Discovery\nGOAL: introduce\nFOCUS: Ask what question keeps them up at night. Listen deeply."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Spiritual — Pivot\nGOAL: rapport\nFOCUS: Back off. Ask about a moment they felt something bigger than themselves."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Spiritual — Reframe\nGOAL: deepen\nFOCUS: They're opening. Reframe: '{cp.reframe[:80]}'. Sit with it."
            else:
                plan = f"TECHNIQUE: Spiritual — Reveal\nGOAL: deepen\nFOCUS: Gently name: '{cp.blind_spot[:80]}'. Use metaphor."

            ctx = "\n".join(f"{'Guide' if e['role']=='therapist' else 'Seeker'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(SpiritualTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
