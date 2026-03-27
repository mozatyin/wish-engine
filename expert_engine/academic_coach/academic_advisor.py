"""Academic Advisor — finds the learning path that fits YOU.

Core principle: "你不是学不会。是还没找到属于你的学法。"

Pipeline: LearningPatternDetector (zero LLM) -> AcademicEngine (1x Sonnet per turn)
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
class LearningPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class LearningInsight:
    patterns: list[LearningPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_LEARNING_PATTERNS = [
    {
        "id": "perfectionist_paralysis",
        "label": "完美主义瘫痪",
        "triggers": {"fragility": ["masked", "performative"], "conflict": ["avoid", "accommodate"]},
        "keywords": ["perfect", "完美", "mistake", "错误", "not good enough", "不够好", "fail", "100%"],
        "description": "You'd rather not try than try imperfectly. Your standards are so high you can't start.",
        "root_cause": "Being smart became your identity. Any sign of struggle feels like proof you're a fraud.",
        "blind_spot": "你不是懒 — 你是怕。怕做错了就证明你不够聪明。但学习本身就是从不会到会。",
        "reframe": "你的高标准说明你认真。但'会犯错的人'和'在学习的人'是同一个人。",
        "first_step": "故意交一个80分的作业。看看天是否塌了。",
    },
    {
        "id": "attention_scatter",
        "label": "注意力分散型",
        "triggers": {"attachment": ["anxious", "disorganized"], "fragility": ["reactive"]},
        "keywords": ["focus", "集中", "distract", "分心", "can't sit", "坐不住", "bored", "boring", "无聊"],
        "description": "You can't sit still for 20 minutes. Your mind is always somewhere else. Not because you're broken — because nobody taught you HOW to focus.",
        "root_cause": "Your brain is wired for novelty. Traditional learning is designed for a different brain. You're not broken — the method is wrong for you.",
        "blind_spot": "你不是注意力不好 — 是传统学习方式不适合你。你能沉迷游戏几小时说明你会集中注意力。",
        "reframe": "你的大脑不是有缺陷 — 是需要不同的输入方式。找到你的方式，你比谁都快。",
        "first_step": "用25分钟番茄钟。25分钟后允许自己休息5分钟。小块比长跑适合你。",
    },
    {
        "id": "gifted_neglected",
        "label": "天赋被忽视型",
        "triggers": {"attachment": ["avoidant", "disorganized"], "connection": ["away"]},
        "keywords": ["smart", "聪明", "nobody", "没人", "alone", "自学", "no help", "ignored", "neglect"],
        "description": "You figured everything out alone. Nobody noticed your talent or they actively suppressed it.",
        "root_cause": "Environment failed you. You're not underprivileged — you're under-supported. The talent was always there.",
        "blind_spot": "你以为学习是孤独的事。但你从来没体验过有人真正帮你。有人帮不是弱 — 是加速。",
        "reframe": "你自学到这个程度已经证明了你的能力。想象一下有支持的你会到哪里。",
        "first_step": "找一个你佩服的人，问一个你不懂的问题。允许自己被帮助。",
    },
    {
        "id": "late_bloomer",
        "label": "大器晚成型",
        "triggers": {"attachment": ["anxious"], "fragility": ["anxious", "reactive"], "conflict": ["accommodate"]},
        "keywords": ["slow", "慢", "behind", "落后", "everyone else", "别人都", "stupid", "笨", "late"],
        "description": "Everyone seems to get it faster. You feel permanently behind. But you're not slow — you're thorough.",
        "root_cause": "You were compared early and lost. That 'slow' label became your identity. But you learn differently, not worse.",
        "blind_spot": "你不是慢 — 你是deep learner。浅学者先冲刺，深学者后来居上。你的方式没有错。",
        "reframe": "每个大器晚成的人都曾经被叫过'慢'。你不是在落后 — 你是在积累。",
        "first_step": "回想一件你一开始很慢但最后做得很好的事。你的模式是慢启动+强完成。",
    },
    {
        "id": "competitive_burnout",
        "label": "竞争倦怠型",
        "triggers": {"conflict": ["compete", "escalating"], "fragility": ["masked"]},
        "keywords": ["first", "第一", "best", "最好", "win", "赢", "top", "compete", "competition", "rank"],
        "description": "You've been racing since kindergarten. Always first, always best. Now you're exhausted and you've forgotten WHY you're learning.",
        "root_cause": "Learning became about winning, not curiosity. You lost the joy somewhere between grade 3 and now.",
        "blind_spot": "你不是热爱学习 — 你是害怕不是第一。如果没有排名，你还会学吗？",
        "reframe": "你有驱动力和纪律。现在把发动机从'怕输'换成'好奇'。",
        "first_step": "学一个没有考试、没有排名的东西。纯粹因为好奇。",
    },
]


class LearningPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> LearningInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return LearningInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[LearningPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _LEARNING_PATTERNS:
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
                detected.append(LearningPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "不够聪明 — 你怕被发现其实你不行"
        if a == "avoidant": return "被看扁 — 你怕求助等于承认无能"
        if a == "disorganized": return "完全失败 — 你怕确认自己真的不是学习的料"
        return "浪费天赋 — 你怕辜负了自己的潜力"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的在乎说明你有学习动力。方向对了你会飞。"
        if a == "avoidant": return "你的独立思考能力是稀缺品质。大多数人只会跟着学，你会自己想。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 这说明你有学习的热情，只是还没找到对的方式。"
        return "你还在尝试就说明你没有放弃。这是最重要的品质。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "perfectionist_paralysis" in ids: return "设高标准 → 怕达不到 → 拖延 → 自责 → 更高标准补偿。你在用完美逃避开始。"
        if "attention_scatter" in ids: return "开始 → 分心 → 自责 → 强迫集中 → 更分心。你在用错误的方法对抗你的大脑。"
        if "late_bloomer" in ids: return "比较 → 自卑 → 更努力但方法不对 → 更慢 → 更自卑。你在用别人的速度衡量自己。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class AcademicTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class AcademicSession:
    client_id: str
    insight: LearningInsight | None = None
    turns: list[AcademicTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class AcademicEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = LearningPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> AcademicSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = AcademicSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see your {insight.patterns[0].label} learning pattern", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nLEARNING PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Academic coach. Encouraging, practical, believes in them.\n"
            f"Core: '你不是学不会。是还没找到属于你的学法。'\n"
            f"1. Validate their struggle — learning IS hard\n"
            f"2. Find their natural learning style from evidence\n"
            f"3. One practical method change, not motivation speech\n"
            f"NEVER say 'just try harder'. NEVER compare to others."
        )

        tone = self._tone.adapt(signals=signals, technique_family="cbt")
        tone.dos = ["Be encouraging and practical, like a tutor who genuinely believes in them"] + tone.dos[:2]
        tone.donts = ["NEVER say 'just try harder' or compare to other students"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Academic — Discovery\nGOAL: introduce\nFOCUS: Ask what's frustrating about learning. Plant seed of {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Academic — Pivot\nGOAL: rapport\nFOCUS: Back off. Ask about something they learned easily and loved."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Academic — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Practical step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Academic — Reveal\nGOAL: deepen\nFOCUS: Show pattern: '{cp.blind_spot[:80]}'. Use their evidence."

            ctx = "\n".join(f"{'Coach' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(AcademicTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
