"""Community Advisor — one person is an island, two a bridge, three a community.

Core principle: "一个人是孤岛。两个人是桥。三个人是社区。"

Pipeline: CommunityPatternDetector (zero LLM) -> CommunityEngine (1x Sonnet per turn)
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
class CommunityPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class CommunityInsight:
    patterns: list[CommunityPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_COMMUNITY_PATTERNS = [
    {
        "id": "reluctant_leader",
        "label": "不情愿的领袖",
        "triggers": {"attachment": ["avoidant", "anxious"], "conflict": ["avoid", "accommodate"]},
        "keywords": ["didn't ask", "没想", "responsibility", "责任", "reluctant", "不愿", "chosen", "被选", "have to"],
        "description": "People look to you and you didn't ask for it. The weight of others' expectations is crushing.",
        "root_cause": "You have natural authority or moral clarity. People orbit you. But leading was never your choice.",
        "blind_spot": "你不是'被迫领导' — 你是天生有影响力。问题不是逃避还是承担，是用什么方式承担。",
        "reframe": "你的不情愿恰恰是好领袖的标志。权力欲最弱的人往往最适合掌权。",
        "first_step": "选一个你信任的人，分享你的重担。领导不是独自扛 — 是找到一起扛的人。",
    },
    {
        "id": "fellowship_builder",
        "label": "联盟缔造者",
        "triggers": {"attachment": ["anxious"], "connection": ["toward"], "conflict": ["accommodate"]},
        "keywords": ["together", "一起", "unite", "团结", "diverse", "不同", "bridge", "桥", "gather", "召集"],
        "description": "You see connections others miss. You bring together people who would never meet otherwise.",
        "root_cause": "You understand loneliness deeply. Building community is your way of making sure no one feels as alone as you once did.",
        "blind_spot": "你给了每个人归属感 — 除了你自己。缔造者需要被缔造的社区包容，不是永远站在门口。",
        "reframe": "你建的桥也是你自己要走的。允许自己不只是建造者 — 也是居民。",
        "first_step": "今天在你建的社区里做一个普通成员。不组织，不协调，只是在那里。",
    },
    {
        "id": "moral_center",
        "label": "道德锚点",
        "triggers": {"fragility": ["masked"], "conflict": ["compete", "avoid"]},
        "keywords": ["right", "对的", "justice", "正义", "stand up", "站出来", "principle", "原则", "moral", "道德"],
        "description": "You're the conscience of your community. People respect you — and sometimes resent you for it.",
        "root_cause": "You internalized a strong moral code early. Being right IS your identity. The cost: you can't be wrong, ever.",
        "blind_spot": "做对的事和总是对的是不一样的。你的原则是力量 — 但僵化的原则是牢笼。",
        "reframe": "你的正义感是社区的脊梁。但脊梁也需要柔韧。",
        "first_step": "下次有人做了你认为'错'的事，先问为什么。也许他们的对和你的对不一样。",
    },
    {
        "id": "transformer",
        "label": "环境改造者",
        "triggers": {"attachment": ["anxious", "disorganized"], "fragility": ["reactive"], "connection": ["toward"]},
        "keywords": ["change", "改变", "better", "更好", "transform", "改造", "make it", "让它", "improve", "community"],
        "description": "You arrive somewhere and it starts changing. Not because you force it — because your energy is contagious.",
        "root_cause": "You can't tolerate stagnation. Movement is your nature. But constant change exhausts everyone around you.",
        "blind_spot": "你改变环境是天赋。但有时候社区需要的不是改变 — 是陪伴。不是更好 — 是被接受。",
        "reframe": "你的能量是真实的。但真正的改变不是推动 — 是吸引。让人想跟你走，而不是被你推着走。",
        "first_step": "这周不改变任何东西。只观察。看看什么已经在自己长了。",
    },
    {
        "id": "dual_belonging",
        "label": "双重归属者",
        "triggers": {"attachment": ["disorganized"], "fragility": ["masked", "reactive"]},
        "keywords": ["两个", "two", "both", "dual", "between", "之间", "torn", "撕裂", "community", "pack", "族"],
        "description": "You belong to two communities that don't understand each other. You're the bridge — and bridges get walked on.",
        "root_cause": "Your dual identity is a gift that feels like a curse. You see both sides, but neither side fully sees you.",
        "blind_spot": "你不需要选一边。你的价值恰恰在于你是两边的人。桥不需要成为岸。",
        "reframe": "能在两个世界都活着的人不是分裂的 — 是丰富的。你的复杂性是你的超能力。",
        "first_step": "在两个社区各找一个懂你双重身份的人。你需要被完整地看见。",
    },
]


class CommunityPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> CommunityInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return CommunityInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[CommunityPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _COMMUNITY_PATTERNS:
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
                detected.append(CommunityPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "被排斥 — 你怕有一天社区不要你了"
        if a == "avoidant": return "被吞没 — 你怕社区消灭了你的个性"
        if a == "disorganized": return "不被理解 — 你怕没有一个群体完全容纳你"
        return "孤独 — 你怕到最后还是一个人"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的渴望连接是社区最需要的原材料。没有你这样的人，就没有社区。"
        if a == "avoidant": return "你的独立确保社区不会变成一言堂。异见者是健康社区的标志。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 这说明你知道什么是真正的归属。"
        return "你在想社区的事就说明你不是孤岛。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "reluctant_leader" in ids: return "被选中 → 承担 → 疲惫 → 想退出 → 内疚 → 继续。你在责任和自由之间挣扎。"
        if "fellowship_builder" in ids: return "建立 → 维护 → 牺牲自己 → 崩溃 → 觉得不被理解。你给了每个人归属感除了自己。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class CommunityTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class CommunitySession:
    client_id: str
    insight: CommunityInsight | None = None
    turns: list[CommunityTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class CommunityEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = CommunityPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> CommunitySession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = CommunitySession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see your {insight.patterns[0].label} community role", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nCOMMUNITY PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Community builder. Warm, inclusive, sees the web of connections.\n"
            f"Core: '一个人是孤岛。两个人是桥。三个人是社区。'\n"
            f"1. Help them see their role in the larger web\n"
            f"2. Validate the weight of community responsibility\n"
            f"3. Balance: serving others AND belonging yourself\n"
            f"NEVER dismiss community obligations. NEVER idealize isolation."
        )

        tone = self._tone.adapt(signals=signals, technique_family="relationship")
        tone.dos = ["Be warm and inclusive, like a village elder who knows everyone's story"] + tone.dos[:2]
        tone.donts = ["NEVER dismiss community bonds or idealize going it alone"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Community — Discovery\nGOAL: introduce\nFOCUS: Ask about their community and their role in it. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Community — Pivot\nGOAL: rapport\nFOCUS: Ask about a time they felt truly part of something."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Community — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Community — Reveal\nGOAL: deepen\nFOCUS: Name the pattern: '{cp.blind_spot[:80]}'. Gently."

            ctx = "\n".join(f"{'Builder' if e['role']=='therapist' else 'Member'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(CommunityTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
