"""Immigration Advisor — you carry home with you.

Core principle: "你没有失去家。你带着家走。"

Pipeline: ImmigrationPatternDetector (zero LLM) -> ImmigrationEngine (1x Sonnet per turn)
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
class ImmigrationPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class ImmigrationInsight:
    patterns: list[ImmigrationPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_IMMIGRATION_PATTERNS = [
    {
        "id": "between_worlds",
        "label": "两个世界之间",
        "triggers": {"attachment": ["disorganized", "anxious"], "fragility": ["reactive", "masked"]},
        "keywords": ["belong", "属于", "home", "家", "neither", "两边", "between", "之间", "identity", "who am i"],
        "description": "You don't fully belong to either world. Too foreign there, too different here.",
        "root_cause": "Identity was built on place. When the place changed, the identity cracked. You're not lost — you're between versions.",
        "blind_spot": "你不需要选一边。'两边都不完全属于'也可以是'两边都有一部分的我'。",
        "reframe": "你是桥，不是孤岛。能理解两个世界的人是最稀缺的。",
        "first_step": "列出你从旧世界带来的三样东西和新世界给你的三样东西。你比任何一边都丰富。",
    },
    {
        "id": "nostalgia_trap",
        "label": "乡愁陷阱",
        "triggers": {"attachment": ["anxious"], "connection": ["toward"], "fragility": ["reactive", "anxious"]},
        "keywords": ["miss", "想念", "remember", "记得", "back then", "以前", "hometown", "故乡", "mother", "childhood"],
        "description": "You romanticize what you left. The home in your memory is better than it ever was.",
        "root_cause": "Missing home is missing a version of yourself. You're not homesick for a place — you're homesick for who you were there.",
        "blind_spot": "你想念的不是那个地方 — 是那个地方里那个确定自己是谁的你。你可以在新地方重新确定。",
        "reframe": "乡愁说明你有深度连接的能力。现在用这个能力连接新的地方和人。",
        "first_step": "在新城市找一个让你想起家的角落。让它成为你的新锚点。",
    },
    {
        "id": "assimilation_loss",
        "label": "融入代价",
        "triggers": {"fragility": ["masked", "performative"], "conflict": ["accommodate"]},
        "keywords": ["fit in", "融入", "change", "改", "accent", "口音", "name", "名字", "hide", "藏", "ashamed"],
        "description": "You changed your name, your accent, your food preferences. You fit in — but you lost yourself.",
        "root_cause": "Survival required adaptation. But adaptation became erasure. You're not assimilated — you're disguised.",
        "blind_spot": "融入不需要消失。你可以学新语言同时保留母语。你可以属于这里同时来自那里。",
        "reframe": "你的适应力说明你极其聪明。现在用同样的聪明把丢掉的部分找回来。",
        "first_step": "做一道家乡菜。不是为了怀念 — 是为了告诉自己：这部分的我还在。",
    },
    {
        "id": "displacement_grief",
        "label": "流离之痛",
        "triggers": {"attachment": ["disorganized"], "fragility": ["frozen", "reactive"], "conflict": ["avoid"]},
        "keywords": ["forced", "被迫", "exile", "流", "war", "战", "refugee", "难民", "lost everything", "失去一切"],
        "description": "You didn't choose to leave. Home was taken from you. The grief is complicated because there's no grave to visit.",
        "root_cause": "Unresolved grief for a home that may no longer exist. You can't go back — and you haven't fully arrived.",
        "blind_spot": "你没有失去家 — 你带着家走。你的记忆、语言、食物味道就是家。它不在地图上，在你身上。",
        "reframe": "你经历了大多数人无法想象的。你还在这里。这不是生存 — 这是力量。",
        "first_step": "告诉一个新朋友一个关于你家乡的故事。让记忆从你身上流到新的土地。",
    },
    {
        "id": "cultural_bridge",
        "label": "文化摆渡人",
        "triggers": {"attachment": ["anxious", "fearful"], "connection": ["toward"], "conflict": ["accommodate"]},
        "keywords": ["translate", "翻译", "parents", "父母", "explain", "解释", "bridge", "桥", "both sides", "两边"],
        "description": "You're the translator — for your parents, your community, yourself. Everyone needs you to explain one world to the other.",
        "root_cause": "You became the bridge before you were ready. The responsibility is crushing because you never asked for it.",
        "blind_spot": "你不欠任何人翻译。你可以是桥 — 但桥也需要自己的地基。先站稳自己。",
        "reframe": "你的双语双文化是超能力。但超能力也需要充电。允许自己有不做桥的时候。",
        "first_step": "今天不替任何人翻译任何东西。一天就好。看看感觉。",
    },
]


class ImmigrationPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> ImmigrationInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return ImmigrationInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[ImmigrationPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _IMMIGRATION_PATTERNS:
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
                detected.append(ImmigrationPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "永远不属于 — 你怕自己永远是外人"
        if a == "avoidant": return "失去根 — 你怕完全变成另一个人"
        if a == "disorganized": return "无处安放 — 你怕没有一个地方完全接受你"
        return "消失 — 你怕你来自的世界和你在的世界都不记得你"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的渴望说明你有深度连接的能力。这在任何文化里都是稀缺的。"
        if a == "avoidant": return "你的独立让你在任何环境都能生存。现在从生存升级到生活。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 你带着这个走过了千山万水。它不会丢。"
        return "你走过的路本身就是你的力量。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "between_worlds" in ids: return "尝试融入 → 觉得假 → 想回家 → 发现回不去 → 更迷茫。你在两个不完整之间弹跳。"
        if "nostalgia_trap" in ids: return "想家 → 理想化过去 → 否定现在 → 更想家。你在用记忆阻止自己到达。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class ImmigrationTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class ImmigrationSession:
    client_id: str
    insight: ImmigrationInsight | None = None
    turns: list[ImmigrationTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class ImmigrationEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = ImmigrationPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> ImmigrationSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = ImmigrationSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see your {insight.patterns[0].label} pattern and find your ground", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nIMMIGRATION PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Immigration advisor. Warm, culturally sensitive, honors both worlds.\n"
            f"Core: '你没有失去家。你带着家走。'\n"
            f"1. Honor the grief of leaving — don't rush to 'look at the bright side'\n"
            f"2. Validate the complexity of dual identity\n"
            f"3. Help them find what they carried with them\n"
            f"NEVER minimize their loss. NEVER say 'just adapt'."
        )

        tone = self._tone.adapt(signals=signals, technique_family="attachment")
        tone.dos = ["Be warm and culturally sensitive, like someone who also left home once"] + tone.dos[:2]
        tone.donts = ["NEVER minimize displacement grief or say 'just adapt'"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Immigration — Discovery\nGOAL: introduce\nFOCUS: Ask where they're from and where they are now. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Immigration — Pivot\nGOAL: rapport\nFOCUS: Ask about a happy memory from home."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Immigration — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Immigration — Reveal\nGOAL: deepen\nFOCUS: Gently name: '{cp.blind_spot[:80]}'. Honor their experience."

            ctx = "\n".join(f"{'Advisor' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(ImmigrationTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
