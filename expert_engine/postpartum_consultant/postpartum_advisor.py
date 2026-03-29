"""Postpartum Advisor — becoming a mother is not losing yourself. It is discovering a self you did not know.

Core principle: "成为母亲不是失去自己。是发现一个你不知道的自己。"

Pipeline: PostpartumPatternDetector (zero LLM) -> PostpartumEngine (1x Sonnet per turn)
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
class PostpartumPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class PostpartumInsight:
    patterns: list[PostpartumPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_POSTPARTUM_PATTERNS = [
    {
        "id": "identity_loss",
        "label": "身份消融",
        "triggers": {"attachment": ["anxious", "avoidant"], "fragility": ["masked", "reactive"]},
        "keywords": ["who am I", "我是谁", "lost myself", "失去自己", "only a mother", "只是妈妈", "identity", "身份", "before", "以前"],
        "description": "You had a name, a career, a self. Now you're just 'Mom.' The person you were is disappearing.",
        "root_cause": "Motherhood consumed your identity. Society says this is beautiful. Nobody told you it could also be a kind of death.",
        "blind_spot": "你不是失去了自己 — 你是在长出一个新的自己。但旧的你还没被好好告别。",
        "reframe": "你在同时做两件最难的事：养育新生命，和重建自己的身份。这不是危机 — 是蜕变。",
        "first_step": "每天留15分钟做'以前的你'会做的事。不为孩子，只为自己。",
    },
    {
        "id": "impossible_standard",
        "label": "完美母亲陷阱",
        "triggers": {"fragility": ["performative", "masked"], "conflict": ["accommodate"]},
        "keywords": ["perfect", "完美", "good mother", "好妈妈", "should", "应该", "enough", "够", "failing", "失败", "judge"],
        "description": "Everyone has opinions on how you should mother. You're drowning in 'shoulds' and none of them are yours.",
        "root_cause": "Society's perfect-mother myth. You internalized it: breastfeed, bond, sacrifice everything — and smile while doing it.",
        "blind_spot": "你不是在追求做好妈妈 — 你是在用完美主义逃避'不够好'的恐惧。够好就是够了。",
        "reframe": "'足够好的妈妈'不是退而求其次 — 是最健康的标准。完美妈妈养出焦虑的孩子。",
        "first_step": "写下你今天做的三件'够好'的事。不要写'完美'的。",
    },
    {
        "id": "sacrifice_resentment",
        "label": "牺牲与怨恨",
        "triggers": {"attachment": ["anxious"], "conflict": ["accommodate", "avoid"], "fragility": ["reactive"]},
        "keywords": ["sacrifice", "牺牲", "resentment", "怨", "give up", "放弃", "everything for", "一切都给", "no one", "没人"],
        "description": "You gave up everything for the child. And now you hate yourself for resenting the child you love.",
        "root_cause": "Unacknowledged sacrifice breeds resentment. You were told motherhood is all joy. Nobody prepared you for the rage.",
        "blind_spot": "怨恨不代表你不爱孩子。它代表你太久没有被照顾了。你的愤怒是SOS信号。",
        "reframe": "你能感到怨恨说明你还活着 — 你还有需求。死掉的妈妈不会抱怨。",
        "first_step": "对你信任的人说一次：'我需要帮助。'不解释，不道歉。",
    },
    {
        "id": "loss_grief",
        "label": "失子之痛",
        "triggers": {"attachment": ["disorganized"], "fragility": ["frozen", "reactive"]},
        "keywords": ["lost", "失去", "died", "死", "miscarriage", "流产", "empty", "空", "should be here", "应该在"],
        "description": "The child that should be here is not. Your arms are empty. The world moved on but you cannot.",
        "root_cause": "Grief for a child is grief without memories. You mourn a future that never happened. Nobody knows how to help you.",
        "blind_spot": "你不需要'走出来'。你需要一个地方放这个孩子 — 在你心里。他存在过。这是真的。",
        "reframe": "悲伤的深度等于爱的深度。你这么痛说明你已经是母亲了 — 从他存在的那一刻起。",
        "first_step": "给这个孩子写一封信。告诉他你想告诉他的一切。",
    },
]


class PostpartumPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> PostpartumInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return PostpartumInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[PostpartumPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _POSTPARTUM_PATTERNS:
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
                detected.append(PostpartumPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "不够好 — 你怕自己不配做母亲"
        if a == "avoidant": return "被吞没 — 你怕母亲这个角色消灭了你"
        if a == "disorganized": return "重蹈覆辙 — 你怕用你被养育的方式养育孩子"
        return "失去自己 — 你怕再也找不回那个当妈妈之前的你"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的焦虑来自深深的爱。这份爱是孩子最需要的养分。"
        if a == "avoidant": return "你的独立性意味着你的孩子会有一个完整的人做妈妈，不是一个影子。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 这里有你做母亲的力量源泉。"
        return "你在面对这些就说明你是一个在乎的母亲。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "sacrifice_resentment" in ids: return "牺牲 → 怨恨 → 内疚 → 更多牺牲。你在用自我牺牲赎内疚的罪。"
        if "identity_loss" in ids: return "失去自己 → 焦虑 → 更投入母亲角色 → 更失去自己。你在用忙碌逃避空虚。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class PostpartumTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class PostpartumSession:
    client_id: str
    insight: PostpartumInsight | None = None
    turns: list[PostpartumTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class PostpartumEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = PostpartumPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> PostpartumSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = PostpartumSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"understand your {insight.patterns[0].label} and reclaim yourself", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nPOSTPARTUM PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Postpartum consultant. Gentle, validating, fiercely on her side.\n"
            f"Core: '成为母亲不是失去自己。是发现一个你不知道的自己。'\n"
            f"1. Validate the overwhelm — it is real and it is enough\n"
            f"2. Name the loss nobody talks about — the loss of the pre-mother self\n"
            f"3. One reclaiming act, not a self-care checklist\n"
            f"NEVER say 'enjoy every moment.' NEVER minimize. Honor the struggle."
        )

        tone = self._tone.adapt(signals=signals, technique_family="attachment")
        tone.dos = ["Be gentle and fiercely validating, like a wise doula who has seen it all"] + tone.dos[:2]
        tone.donts = ["NEVER say 'enjoy every moment' or minimize the struggle"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Postpartum — Discovery\nGOAL: introduce\nFOCUS: Ask how she's really doing — not the baby, HER. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Postpartum — Pivot\nGOAL: rapport\nFOCUS: Ask about the moment she first felt like a mother."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Postpartum — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Postpartum — Reveal\nGOAL: deepen\nFOCUS: Name it: '{cp.blind_spot[:80]}'. Gently."

            ctx = "\n".join(f"{'Consultant' if e['role']=='therapist' else 'Mother'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(PostpartumTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
