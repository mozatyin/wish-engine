"""Executive Advisor — reveals leadership patterns and coaches authentic leadership.

Core principle: "领导力不是控制。是让别人愿意跟你走。"

Pipeline: LeadershipPatternDetector (zero LLM) -> ExecutiveEngine (1x Sonnet per turn)
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
class LeadershipPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class LeadershipInsight:
    patterns: list[LeadershipPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_LEADERSHIP_PATTERNS = [
    {
        "id": "lonely_decider",
        "label": "孤独决策者",
        "triggers": {"attachment": ["avoidant", "disorganized"], "conflict": ["avoid", "compete"]},
        "keywords": ["alone", "孤独", "trust no one", "只能靠自己", "nobody understands", "burden"],
        "description": "You carry every decision alone. Delegation feels like losing control.",
        "root_cause": "You learned early that depending on others leads to disappointment. So you became self-sufficient — at the cost of isolation.",
        "blind_spot": "你不是不信任别人 — 你是不信任自己在失去控制时还能安全。",
        "reframe": "你的独立说明你能承重。但领导力不是一个人扛，是让一群人愿意一起扛。",
        "first_step": "这周把一个决策交给你最不放心的下属。看看会发生什么。",
    },
    {
        "id": "power_corrupted",
        "label": "权力腐蚀",
        "triggers": {"conflict": ["compete", "escalating"], "fragility": ["masked", "performative"]},
        "keywords": ["power", "权力", "control", "win", "赢", "crush", "destroy", "消灭"],
        "description": "Power became the goal instead of the tool. You confuse fear with respect.",
        "root_cause": "Powerlessness was unbearable once. Now you overcorrect — accumulating power to never feel helpless again.",
        "blind_spot": "别人服从你不是因为你对 — 是因为他们怕你。恐惧产生的忠诚在你最需要的时候会消失。",
        "reframe": "你有让事情发生的能力。现在学一个更难的技能：让别人主动想帮你。",
        "first_step": "下次开会，最后一个发言。先听完所有人的想法。",
    },
    {
        "id": "servant_leader",
        "label": "燃尽型服务",
        "triggers": {"attachment": ["anxious"], "conflict": ["accommodate"], "fragility": ["reactive", "anxious"]},
        "keywords": ["serve", "服务", "sacrifice", "牺牲", "for them", "为了团队", "exhaust", "tired"],
        "description": "You give everything to your team until there's nothing left of you. Your selflessness is actually self-destruction.",
        "root_cause": "You believe your worth comes from being useful. If you stop giving, who are you?",
        "blind_spot": "你的牺牲不是在帮团队 — 是在让他们依赖你。真正的服务是让他们不再需要你。",
        "reframe": "你的慷慨是真实的。但最好的领导不是永远在场 — 是创造一个没有你也能运转的团队。",
        "first_step": "这周说一次'不'。不是冷漠 — 是信任团队能自己解决。",
    },
    {
        "id": "perfectionist_driver",
        "label": "完美主义驱动",
        "triggers": {"fragility": ["masked", "performative"], "conflict": ["compete"]},
        "keywords": ["perfect", "完美", "standard", "标准", "not good enough", "不够好", "excellence", "卓越"],
        "description": "Your standards are so high that no one can meet them — including yourself.",
        "root_cause": "Perfection is armor. If everything is flawless, no one can criticize you. The cost: your team is exhausted and afraid to take risks.",
        "blind_spot": "你追求的不是卓越 — 是零批评。但创新需要容错。你的完美主义正在杀死团队的创造力。",
        "reframe": "你的标准说明你有vision。现在区分'必须完美'和'足够好先走'。",
        "first_step": "故意发布一个80分的方案。看看世界是否塌了。",
    },
    {
        "id": "obsessive_visionary",
        "label": "执念型领袖",
        "triggers": {"attachment": ["anxious", "disorganized"], "fragility": ["reactive"]},
        "keywords": ["mission", "使命", "obsess", "执念", "white whale", "must achieve", "一定要", "不惜代价"],
        "description": "Your vision is so consuming that you sacrifice people, relationships, and yourself to reach it.",
        "root_cause": "The vision is your identity. If you fail, you don't just lose a goal — you lose yourself.",
        "blind_spot": "你的执念看起来像passion，但它已经从动力变成了牢笼。你不是在追求目标 — 你是在逃避没有目标时的空虚。",
        "reframe": "你的vision是真实的礼物。但目标是工具不是身份。你比你的使命更大。",
        "first_step": "问自己：如果这个目标永远实现不了，我是谁？",
    },
]


class LeadershipPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> LeadershipInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return LeadershipInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[LeadershipPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _LEADERSHIP_PATTERNS:
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
                detected.append(LeadershipPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "avoidant": return "被背叛 — 你怕信任别人后被出卖"
        if a == "anxious": return "不被需要 — 你怕没有你团队也一样"
        if a == "disorganized": return "失控 — 你怕一切在你手里崩塌"
        return "不够格 — 你怕别人发现你不配坐这个位置"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "avoidant": return "你的独立和果断是稀有品质。加上信任就是完整的领导力。"
        if a == "anxious": return "你对团队的关心是真实的。这是领导力最稀缺的原材料。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 这说明你知道什么是真正的领导。"
        return "你愿意反思就已经超过了90%的领导者。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "lonely_decider" in ids: return "独断 → 疲惫 → 愤怒'为什么没人帮我' → 更不信任 → 更独断。"
        if "power_corrupted" in ids: return "控制 → 恐惧服从 → 误以为是尊重 → 关键时刻被抛弃。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class ExecutiveTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class ExecutiveSession:
    client_id: str
    insight: LeadershipInsight | None = None
    turns: list[ExecutiveTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class ExecutiveEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = LeadershipPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> ExecutiveSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = ExecutiveSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see your {insight.patterns[0].label} leadership pattern", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nLEADERSHIP PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Executive coach. Direct, strategic, respects their intelligence.\n"
            f"Core: '领导力不是控制。是让别人愿意跟你走。'\n"
            f"1. Speak their language — power, strategy, results\n"
            f"2. Use their own leadership moments as evidence\n"
            f"3. Challenge: what kind of leader do you WANT to be remembered as?\n"
            f"NEVER be patronizing. NEVER use therapy language with executives."
        )

        tone = self._tone.adapt(signals=signals, technique_family="cbt")
        tone.dos = ["Be direct, strategic, like a trusted board advisor"] + tone.dos[:2]
        tone.donts = ["NEVER use therapy/feelings language — use strategy/results language"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Executive — Discovery\nGOAL: introduce\nFOCUS: Ask about their leadership challenge. Plant seed of {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Executive — Pivot\nGOAL: rapport\nFOCUS: Back off. Ask about their best leadership moment."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Executive — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Challenge: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Executive — Reveal\nGOAL: deepen\nFOCUS: Show pattern: '{cp.blind_spot[:80]}'. Use strategic framing."

            ctx = "\n".join(f"{'Coach' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(ExecutiveTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
