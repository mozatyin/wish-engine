"""Nutrition Advisor — food is not the enemy. It is how you talk to your body.

Core principle: "食物不是敌人。它是你和身体的对话方式。"

Pipeline: NutritionPatternDetector (zero LLM) -> NutritionEngine (1x Sonnet per turn)
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
class NutritionPattern:
    pattern_id: str
    label: str
    description: str
    root_cause: str
    soul_evidence: list[str]
    blind_spot: str
    reframe: str
    first_step: str


@dataclass
class NutritionInsight:
    patterns: list[NutritionPattern] = field(default_factory=list)
    core_fear: str = ""
    authentic_strength: str = ""
    repeated_cycle: str = ""
    soul_resource: str = ""


_NUTRITION_PATTERNS = [
    {
        "id": "emotional_eating",
        "label": "情绪化进食",
        "triggers": {"attachment": ["anxious"], "fragility": ["reactive"], "conflict": ["avoid"]},
        "keywords": ["comfort food", "吃", "hungry", "饿", "binge", "暴食", "stress eat", "压力", "can't stop", "停不下来", "honey", "sweet"],
        "description": "You eat not because you're hungry — but because you're feeling something you can't name.",
        "root_cause": "Food became your first reliable comfort. When emotions overflow, eating is the one thing that always 'works.'",
        "blind_spot": "你不是贪吃 — 你是在用食物填补情绪的空洞。胃饱了但心还是空的。",
        "reframe": "你找到了一种自我安慰的方式 — 这说明你有求生本能。现在可以找到不伤害身体的安慰。",
        "first_step": "下次想吃东西之前，先问自己：我是饿了还是在感受什么？写下那个感受。",
    },
    {
        "id": "food_fear",
        "label": "食物恐惧",
        "triggers": {"attachment": ["avoidant", "disorganized"], "fragility": ["frozen", "reactive"]},
        "keywords": ["poison", "毒", "afraid", "怕", "safe food", "安全", "contaminated", "不敢吃", "calories", "卡路里", "clean"],
        "description": "Food feels dangerous. Every bite is a risk. You've shrunk your world to a few 'safe' foods.",
        "root_cause": "When life felt out of control, controlling food was the one power you had. Safety through restriction.",
        "blind_spot": "你不是在控制饮食 — 你是在用食物控制恐惧。限制吃什么让你觉得世界没那么危险。",
        "reframe": "你的谨慎保护了你。但食物不是敌人 — 它是盟友。你可以慢慢扩大安全区。",
        "first_step": "这周尝试一种新食物。很小的一口。不是因为你必须 — 是因为你在试探世界是否安全。",
    },
    {
        "id": "deprivation_cycle",
        "label": "匮乏-暴食循环",
        "triggers": {"attachment": ["anxious", "disorganized"], "fragility": ["reactive", "masked"]},
        "keywords": ["diet", "节食", "restrict", "限制", "then binge", "然后暴食", "cycle", "循环", "guilty", "罪恶感", "all or nothing"],
        "description": "You restrict, restrict, restrict — then the dam breaks and you eat everything. Then guilt. Then restrict again.",
        "root_cause": "All-or-nothing thinking applied to food. Perfection or failure, no middle ground. The body rebels against deprivation.",
        "blind_spot": "节食-暴食不是意志力问题 — 是你身体的求生反应。你越压制它，它反弹得越狠。",
        "reframe": "暴食不是你的失败 — 是你身体在说'我需要被喂饱。'它在保护你。",
        "first_step": "每天三餐，不跳过任何一餐。不是因为你想吃 — 是因为稳定的喂养打破循环。",
    },
    {
        "id": "survival_eating",
        "label": "生存型进食",
        "triggers": {"attachment": ["disorganized"], "fragility": ["frozen"], "conflict": ["avoid"]},
        "keywords": ["poverty", "穷", "hunger", "饥饿", "not enough", "不够", "waste", "浪费", "save", "存", "hoard", "囤"],
        "description": "You eat like food might disappear tomorrow. Every meal could be your last. You can't waste a single grain.",
        "root_cause": "Real hunger in your past — or your family's past. The body remembers scarcity even when the pantry is full.",
        "blind_spot": "你的冰箱满了但你的恐惧还在。你不是在吃今天的饭 — 你在补偿过去饿过的每一天。",
        "reframe": "你活过了匮乏 — 这是真正的坚强。现在你可以告诉身体：够了，安全了。",
        "first_step": "故意留一点食物在盘子里。不吃完。告诉自己：明天还有。",
    },
    {
        "id": "body_punishment",
        "label": "身体惩罚型",
        "triggers": {"fragility": ["masked", "performative"], "conflict": ["compete"]},
        "keywords": ["deserve", "配", "punishment", "惩罚", "earn", "赚", "burn", "calories", "exercise", "运动", "compensation"],
        "description": "You eat — then punish yourself. Exercise to 'earn' food. Skip meals to 'make up for' eating.",
        "root_cause": "Your body is a battlefield. Food is the weapon, exercise the punishment. The real war is with self-worth.",
        "blind_spot": "你不需要'赚'吃东西的权利。呼吸不需要资格，吃饭也不需要。",
        "reframe": "你的身体不是需要惩罚的敌人 — 它是陪你走过一切的盟友。它配被善待。",
        "first_step": "今天吃一顿饭不补偿。不多运动，不少吃下一顿。就让这一餐是一餐。",
    },
]


class NutritionPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> NutritionInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return NutritionInsight(
            patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns),
            soul_resource=self._resource(deep_items or [], memory_items or []),
        )

    def _detect(self, signals, focus, deep, memory) -> list[NutritionPattern]:
        detected = []
        all_items = focus + deep + (memory or [])
        all_text = " ".join(i.text.lower() for i in all_items)
        for p in _NUTRITION_PATTERNS:
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
                detected.append(NutritionPattern(
                    pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence,
                    blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"],
                ))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "失控 — 你怕一旦开始吃就停不下来"
        if a == "avoidant": return "脆弱 — 你怕承认自己需要食物就是承认自己有需求"
        if a == "disorganized": return "匮乏 — 你怕回到没有食物的日子"
        return "不够好 — 你怕自己的身体不值得被善待"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的敏感让你能感受到身体的信号 — 学会听它说话而不是压制它。"
        if a == "avoidant": return "你的自制力是真实的力量 — 把它用在照顾自己上而不是惩罚自己。"
        for i in deep:
            if i.emotional_valence == "positive":
                return f"'{i.text[:60]}' — 这个记忆里有你和食物和平共处的线索。"
        return "你在寻求帮助就说明你想和身体和解。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "deprivation_cycle" in ids: return "节食 → 暴食 → 罪恶感 → 再节食。你的身体在和你的意志打仗。"
        if "emotional_eating" in ids: return "情绪来了 → 吃 → 暂时好了 → 情绪又来了 → 再吃。食物成了唯一的止痛药。"
        if "food_fear" in ids: return "怕吃 → 限制 → 营养不良 → 身体报警 → 更怕。恐惧在缩小你的世界。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class NutritionTurn:
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class NutritionSession:
    client_id: str
    insight: NutritionInsight | None = None
    turns: list[NutritionTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)


class NutritionEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine
        self._patient = patient_simulator
        self._detector = NutritionPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict,
            focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> NutritionSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = NutritionSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"understand your {insight.patterns[0].label} and heal your relationship with food", memory_items=memory_items)

        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nNUTRITION PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Nutritionist. Warm, non-judgmental, body-positive.\n"
            f"Core: '食物不是敌人。它是你和身体的对话方式。'\n"
            f"1. Name the emotional function of their eating pattern\n"
            f"2. Normalize: your body is trying to survive, not betray you\n"
            f"3. One small food peace step, not a meal plan\n"
            f"NEVER count calories. NEVER shame. Address the WHY behind the eating."
        )

        tone = self._tone.adapt(signals=signals, technique_family="act")
        tone.dos = ["Be warm and body-positive, like a friend who feeds you soup when you're sick"] + tone.dos[:2]
        tone.donts = ["NEVER count calories, weigh food, or shame eating habits"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        history: list[dict] = []
        pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Nutrition — Discovery\nGOAL: introduce\nFOCUS: Ask about their relationship with food. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1)
                cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Nutrition — Pivot\nGOAL: rapport\nFOCUS: Ask about a meal that made them happy. What was it?"
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Nutrition — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Nutrition — Reveal\nGOAL: deepen\nFOCUS: Name what's happening: '{cp.blind_spot[:80]}'. Gently."

            ctx = "\n".join(f"{'Nutritionist' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(NutritionTurn(
                turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))

        session.total_time_seconds = time.time() - t0
        return session
