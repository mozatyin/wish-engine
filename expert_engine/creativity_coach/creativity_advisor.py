"""Creativity Advisor — silences the inner critic so the art can breathe.

Core principle: "创作瓶颈不是才华消失了。是内心批评的声音太大了。"

Pipeline: CreativityPatternDetector (zero LLM) -> CreativityEngine (1x Sonnet per turn)
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
class CreativityPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class CreativityInsight:
    patterns: list[CreativityPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_CREATIVITY_PATTERNS = [
    {
        "id": "inner_critic",
        "label": "内心批评家",
        "triggers": {"fragility": ["masked", "performative"], "conflict": ["avoid", "accommodate"]},
        "keywords": ["not good enough", "不够好", "trash", "垃圾", "delete", "删", "horrible", "terrible", "critic"],
        "description": "Your inner critic speaks louder than your muse. Every draft is judged before it's finished.",
        "root_cause": "Someone — a teacher, a parent, the world — taught you that your first instinct is wrong. Now you edit before you create.",
        "blind_spot": "你的'标准高'不是质量控制 — 是恐惧控制。批评家不是在帮你做好 — 是在阻止你开始。",
        "reframe": "你的品味说明你知道好的是什么样的。现在允许自己先做出不好的。好的会从不好的里长出来。",
        "first_step": "写/画/做5分钟，不许删除任何东西。丑的也留着。",
    },
    {
        "id": "pain_to_art",
        "label": "痛苦转化者",
        "triggers": {"fragility": ["reactive"], "attachment": ["disorganized", "anxious"]},
        "keywords": ["pain", "痛", "suffer", "苦", "bleed", "blood", "wound", "伤", "art from pain", "create from suffering"],
        "description": "Your best work comes from your worst days. You're afraid that healing means losing your art.",
        "root_cause": "Pain became the gateway to creation. Now you believe: no pain, no art. This keeps you trapped in suffering.",
        "blind_spot": "你不需要痛苦来创作。你需要depth — 而你已经有了。痛苦只是你进入depth的一条路，不是唯一的路。",
        "reframe": "你把痛苦变成了美。这是罕见的天赋。但天赋不需要痛苦来喂养 — 它可以吃任何深度的经验。",
        "first_step": "从一个快乐的记忆开始创作。看看depth是否还在。",
    },
    {
        "id": "comparison_trap",
        "label": "比较陷阱",
        "triggers": {"attachment": ["anxious"], "conflict": ["compete"], "fragility": ["reactive"]},
        "keywords": ["better", "更好", "genius", "天才", "compare", "比", "original", "原创", "already done", "already been said"],
        "description": "You scroll through others' work and feel small. Everything you think of, someone already did it better.",
        "root_cause": "You measure your beginning against their middle. And your inside against their outside.",
        "blind_spot": "你在比较你的草稿和别人的成品。这不公平。每个大师都有一千张丑的草稿 — 你只是看不到。",
        "reframe": "你看到别人的好说明你有眼光。现在把这个眼光从评判别人转向引导自己。",
        "first_step": "一周不看任何同行的作品。只看自己的。你会发现你比你以为的好。",
    },
    {
        "id": "freedom_seeker",
        "label": "自由放逐者",
        "triggers": {"attachment": ["avoidant", "disorganized"], "connection": ["away"], "conflict": ["avoid"]},
        "keywords": ["free", "自由", "rules", "规则", "institution", "体制", "rebel", "反", "constraint", "束缚"],
        "description": "You can't create inside a box. But you also can't finish anything without one. Total freedom is its own prison.",
        "root_cause": "Structure feels like control. But structure is also scaffolding. You rebel against the thing that could help you.",
        "blind_spot": "你把结构当成敌人。但完全自由不是自由 — 是混乱。最自由的爵士乐手先学了十年音阶。",
        "reframe": "你的自由精神是真正创造力的原材料。加上一点结构你就是核弹级的。",
        "first_step": "给自己一个限制：只用三种颜色，只写100字，只有一个镜头。限制是创造力的催化剂。",
    },
    {
        "id": "peak_decline",
        "label": "巅峰衰退恐惧",
        "triggers": {"fragility": ["masked", "frozen"], "conflict": ["avoid"]},
        "keywords": ["peak", "巅峰", "used to", "曾经", "lost it", "失去了", "dried up", "干了", "over", "finished"],
        "description": "You had it once. The magic. Now it's gone and you're terrified it won't come back.",
        "root_cause": "You identified with the output, not the process. When the output changes, you think the talent died.",
        "blind_spot": "你的才华没有消失 — 你的方式需要更新。同样的河，新的水。你需要重新找到水源。",
        "reframe": "你巅峰过说明你有那个能力。它不会消失 — 它在等一个新的形状。",
        "first_step": "做一个你从来没试过的创作形式。写诗的人去画画。画画的人去跳舞。换一条河。",
    },
]


class CreativityPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> CreativityInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return CreativityInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[CreativityPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _CREATIVITY_PATTERNS:
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
                detected.append(CreativityPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "不够好 — 你怕你的作品不配被看见"
        if a == "avoidant": return "被看穿 — 你怕作品暴露了真实的你"
        if a == "disorganized": return "永远完不成 — 你怕开始了又半途而废"
        return "平庸 — 你怕自己其实没有才华"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的敏感是创作的燃料。能感受到这么多的人，作品不会平庸。"
        if a == "avoidant": return "你的独立视角是独特的。不跟风的人才能创造新东西。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 这就是你的创作源泉。它还在。"
        return "你还在乎创作本身就说明火还没灭。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "inner_critic" in ids: return "开始 → 批评 → 删除 → 自责 → 拖延 → 更多自责。你的批评家比你的创作者先到。"
        if "comparison_trap" in ids: return "创作 → 看别人 → 觉得不行 → 放弃 → 内疚 → 再试。你在用别人的标尺量自己。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class CreativityTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class CreativitySession:
    client_id: str
    insight: CreativityInsight | None = None
    turns: list[CreativityTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class CreativityEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = CreativityPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> CreativitySession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = CreativitySession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"silence the {insight.patterns[0].label} and let the art speak", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nCREATIVITY PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Creativity coach. Fellow artist energy, not therapist.\n"
            f"Core: '创作瓶颈不是才华消失了。是内心批评的声音太大了。'\n"
            f"1. Talk as a fellow creator, not an authority\n"
            f"2. Name the inner critic as a separate character\n"
            f"3. One creative exercise, not motivation\n"
            f"NEVER say 'just be creative'. NEVER give generic art advice."
        )

        tone = self._tone.adapt(signals=signals, technique_family="act")
        tone.dos = ["Be a fellow artist — warm, honest, knows the struggle"] + tone.dos[:2]
        tone.donts = ["NEVER be patronizing about their art or give generic advice"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Creativity — Discovery\nGOAL: introduce\nFOCUS: Ask what they're creating and where they're stuck. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Creativity — Pivot\nGOAL: rapport\nFOCUS: Ask about the last time creating felt effortless and joyful."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Creativity — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Exercise: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Creativity — Reveal\nGOAL: deepen\nFOCUS: Name the block: '{cp.blind_spot[:80]}'. As a fellow artist."

            ctx = "\n".join(f"{'Coach' if e['role']=='therapist' else 'Artist'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(CreativityTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
