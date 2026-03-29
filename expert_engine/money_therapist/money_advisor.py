"""Money Therapist — your relationship with money is your relationship with safety.

Core principle: "你和钱的关系，就是你和安全感的关系。"

Pipeline: MoneyPatternDetector (zero LLM) -> MoneyEngine (1x Sonnet per turn)
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
class MoneyPattern:
    pattern_id: str; label: str; description: str; root_cause: str
    soul_evidence: list[str]; blind_spot: str; reframe: str; first_step: str

@dataclass
class MoneyInsight:
    patterns: list[MoneyPattern] = field(default_factory=list)
    core_fear: str = ""; authentic_strength: str = ""; repeated_cycle: str = ""; soul_resource: str = ""

_MONEY_PATTERNS = [
    {"id": "hoarding_fear", "label": "囤积恐惧",
     "triggers": {"attachment": ["avoidant"], "fragility": ["frozen", "masked"]},
     "keywords": ["save", "存", "hoard", "囤", "spend", "花不出", "enough", "够", "emergency", "万一", "poor", "穷", "Scrooge"],
     "description": "You have money but can't spend it. Every purchase triggers panic. The number in your account is your security blanket.",
     "root_cause": "Poverty trauma — yours or inherited. Money = survival. Spending = dying. The fear is real even when the bank account isn't empty.",
     "blind_spot": "你不是节俭 — 你是用钱买安全感。但安全感不住在银行账户里。",
     "reframe": "你的储蓄纪律保护了你。但钱是工具不是盾牌。它的价值在使用中实现。",
     "first_step": "这周用钱买一件让你开心的东西。不贵。感受'花钱也可以是安全的。'"},
    {"id": "money_love", "label": "用钱换爱",
     "triggers": {"attachment": ["anxious"], "connection": ["toward"], "fragility": ["reactive"]},
     "keywords": ["buy", "买", "gift", "礼物", "love", "爱", "impress", "打动", "worth", "值", "prove", "证明", "deserve"],
     "description": "You spend to be loved. Gifts, dinners, bail-outs. Your wallet is your love language — and it's going bankrupt.",
     "root_cause": "If you're generous enough, they'll stay. Money becomes a proxy for love because love felt conditional.",
     "blind_spot": "你在用钱买的不是东西 — 是爱。但买来的爱不是免费的，有利息。",
     "reframe": "你的慷慨是真实的爱的表达。但你不需要付费才能被爱。",
     "first_step": "下次想送礼物时，换成写一段话。不花钱地表达爱。看看感觉如何。"},
    {"id": "poverty_trauma", "label": "贫困创伤",
     "triggers": {"attachment": ["disorganized"], "fragility": ["frozen", "reactive"]},
     "keywords": ["hungry", "饿", "poverty", "穷", "never again", "再也不", "blood", "卖血", "survive", "活", "nothing", "没有"],
     "description": "You know what it's like to have nothing. That memory drives everything — earn more, spend less, never go back.",
     "root_cause": "Real poverty leaves scars that money can't heal. You escaped but your nervous system is still in survival mode.",
     "blind_spot": "你逃出了贫穷但没逃出恐惧。你的银行账户变了，你的心理账户还在零。",
     "reframe": "你从零开始建起了现在的生活 — 这是真正的力量。你不会回去的。你可以相信自己。",
     "first_step": "写下你现在拥有的10件你小时候没有的东西。让身体记住：你已经安全了。"},
    {"id": "money_worth", "label": "金钱=价值",
     "triggers": {"fragility": ["performative", "masked"], "conflict": ["compete"]},
     "keywords": ["success", "成功", "worth", "价值", "earn", "赚", "salary", "收入", "status", "地位", "failure", "失败", "money is"],
     "description": "Your net worth IS your self-worth. When the number goes up, you're someone. When it drops, you're nothing.",
     "root_cause": "Money became the scoreboard for a game you didn't choose to play. But you can't stop playing because losing = disappearing.",
     "blind_spot": "你的银行余额不是你的成绩单。你用赚钱证明的不是能力 — 是存在的价值。",
     "reframe": "你的价值在你出生那天就确定了。钱可以变，你的价值不变。",
     "first_step": "列出5件让你有价值感但和钱无关的事。你是谁不等于你有多少。"},
]

class MoneyPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> MoneyInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return MoneyInsight(patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns), soul_resource=self._resource(deep_items or [], memory_items or []))

    def _detect(self, signals, focus, deep, memory) -> list[MoneyPattern]:
        detected = []; all_items = focus + deep + (memory or []); all_text = " ".join(i.text.lower() for i in all_items)
        for p in _MONEY_PATTERNS:
            score = 0
            for key, vals in p["triggers"].items():
                sig_key = {"attachment": "attachment_style", "connection": "connection_response", "conflict": "conflict_style", "fragility": "fragility_pattern"}.get(key, key)
                if signals.get(sig_key) in vals: score += 1
            if any(kw in all_text for kw in p["keywords"]): score += 1
            if score >= 2:
                evidence = [i.text[:80] for i in all_items if i.activation >= 0.3 and i.emotional_valence in ("negative", "extreme")][:2]
                detected.append(MoneyPattern(pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence, blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"]))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "不被爱 — 你怕没钱就没人要你"
        if a == "avoidant": return "失控 — 你怕失去钱就失去对生活的控制"
        if a == "disorganized": return "回到原点 — 你怕有一天醒来一切又归零"
        return "不够 — 你怕永远赚不够让自己安全"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的慷慨说明你心里有爱 — 这比钱珍贵。"
        if a == "avoidant": return "你的财务纪律是真正的能力 — 现在给它加上一点灵活。"
        for i in deep:
            if i.emotional_valence == "positive": return f"'{i.text[:60]}' — 这里有不用钱买的安全感。"
        return "你在面对金钱问题就说明你在寻找真正的安全。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "hoarding_fear" in ids: return "赚 → 存 → 不敢花 → 焦虑 → 赚更多。你在用数字喂焦虑。"
        if "money_love" in ids: return "花钱 → 被感谢 → 觉得被爱 → 钱用完 → 焦虑 → 赚钱 → 再花。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""

@dataclass
class MoneyTurn:
    turn_number: int; coach_text: str; client_text: str; client_internal_state: str
    client_resistance: float; client_resistance_reason: str; client_insight: bool; pattern_addressed: str

@dataclass
class MoneySession:
    client_id: str; insight: MoneyInsight | None = None
    turns: list[MoneyTurn] = field(default_factory=list); total_time_seconds: float = 0.0
    @property
    def insights_gained(self) -> int: return sum(1 for t in self.turns if t.client_insight)

class MoneyEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine; self._patient = patient_simulator
        self._detector = MoneyPatternDetector(); self._persuasion = PersuasionPlanner(); self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict, focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> MoneySession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = MoneySession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns: session.total_time_seconds = time.time() - t0; return session
        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"understand your {insight.patterns[0].label}", memory_items=memory_items)
        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nMONEY PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Money therapist. Non-judgmental, sees money as emotional language.\n"
            f"Core: '你和钱的关系，就是你和安全感的关系。'\n"
            f"1. Name the emotion behind the money behavior\n2. Normalize: money shame is universal\n"
            f"3. One money peace step, not a budget plan\nNEVER give financial advice. Address the psychology.")
        tone = self._tone.adapt(signals=signals, technique_family="schema")
        tone.dos = ["Be non-judgmental about money, like a friend who knows your bank balance and still respects you"] + tone.dos[:2]
        tone.donts = ["NEVER give financial advice or shame spending/saving habits"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()
        history: list[dict] = []; pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Money — Discovery\nGOAL: introduce\nFOCUS: Ask about their earliest money memory. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1); cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Money — Pivot\nGOAL: rapport\nFOCUS: Ask about a time money made them feel safe."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Money — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Money — Reveal\nGOAL: deepen\nFOCUS: Name it: '{cp.blind_spot[:80]}'. Gently."
            ctx = "\n".join(f"{'Therapist' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(MoneyTurn(turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))
        session.total_time_seconds = time.time() - t0; return session
