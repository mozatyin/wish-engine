"""Cross-Cultural Coach — you are not torn between two worlds. You are one of the few who can see both.

Core principle: "你不是在两个世界之间撕裂。你是少数能看到两个世界的人。"

Pipeline: CulturalPatternDetector (zero LLM) -> CulturalEngine (1x Sonnet per turn)
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
class CulturalPattern:
    pattern_id: str; label: str; description: str; root_cause: str
    soul_evidence: list[str]; blind_spot: str; reframe: str; first_step: str

@dataclass
class CulturalInsight:
    patterns: list[CulturalPattern] = field(default_factory=list)
    core_fear: str = ""; authentic_strength: str = ""; repeated_cycle: str = ""; soul_resource: str = ""

_CULTURAL_PATTERNS = [
    {"id": "dual_identity", "label": "双重身份撕裂",
     "triggers": {"attachment": ["disorganized", "anxious"], "fragility": ["reactive", "masked"]},
     "keywords": ["between", "之间", "torn", "撕裂", "two worlds", "两个世界", "belong", "属于", "neither", "哪个都不", "home", "家"],
     "description": "You live between two cultures. In one, you're too foreign. In the other, you're too native. You belong everywhere and nowhere.",
     "root_cause": "Bicultural identity without integration. You code-switch so well that you forgot which code is real.",
     "blind_spot": "你不是'哪边都不属于' — 你是少数两边都能看懂的人。你的撕裂感是翻译者的孤独。",
     "reframe": "能在两个世界都活着不是分裂 — 是丰富。你的复杂性是你的超能力。",
     "first_step": "列出你从每个文化里带走的最好的东西。你不需要选 — 你可以都要。"},
    {"id": "code_switch_exhaustion", "label": "切换疲劳",
     "triggers": {"fragility": ["masked", "performative"], "conflict": ["accommodate"]},
     "keywords": ["switch", "切换", "mask", "面具", "pretend", "假装", "exhausted", "累", "perform", "表演", "adapt", "适应"],
     "description": "You're a different person in each world. The constant switching is exhausting. You're running out of selves.",
     "root_cause": "Survival through adaptation. You learned to read the room perfectly — but lost yourself in the performance.",
     "blind_spot": "你的适应力不是假的 — 每个版本的你都是真的。你不是在演戏，你是多面体。",
     "reframe": "变色龙不是没有颜色 — 它有所有的颜色。你的切换是天赋，不是诅咒。",
     "first_step": "找一个你不需要切换的人。和他们待着。感受不表演是什么感觉。"},
    {"id": "rootless_freedom", "label": "无根的自由",
     "triggers": {"attachment": ["avoidant"], "connection": ["away"], "fragility": ["masked"]},
     "keywords": ["roots", "根", "home", "家", "wander", "漂泊", "freedom", "自由", "rootless", "无根", "everywhere", "到处"],
     "description": "You made freedom your home. But sometimes at 3am you wonder — is wandering a choice or an escape?",
     "root_cause": "If you don't belong anywhere, you can't be rejected from anywhere. Rootlessness as a defense mechanism.",
     "blind_spot": "你说你'不需要根' — 但你在找什么？自由的另一面可能是逃避。",
     "reframe": "你可以有根和翅膀。根不是监狱 — 根是你知道自己是谁的基础。",
     "first_step": "选一个地方（物理的或人际的）当作你的锚点。不是永远 — 就是现在。"},
    {"id": "translation_burden", "label": "翻译者重担",
     "triggers": {"attachment": ["anxious"], "conflict": ["accommodate"], "fragility": ["reactive"]},
     "keywords": ["translate", "翻译", "explain", "解释", "bridge", "桥", "middle", "中间", "mediate", "调解", "understand both"],
     "description": "You're the bridge between worlds. Everyone uses you to cross — but nobody asks if the bridge is tired.",
     "root_cause": "You became indispensable by being the translator. But the cost is never being fully understood yourself.",
     "blind_spot": "你帮所有人理解对方 — 但谁来理解你？翻译者也需要自己的语言。",
     "reframe": "你的翻译能力是稀有的天赋。但翻译者也配有自己不需要翻译的时刻。",
     "first_step": "这周对一个翻译请求说'不'。你不是24小时的桥 — 你也有关闭的时候。"},
]

class CulturalPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> CulturalInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return CulturalInsight(patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns), soul_resource=self._resource(deep_items or [], memory_items or []))

    def _detect(self, signals, focus, deep, memory) -> list[CulturalPattern]:
        detected = []; all_items = focus + deep + (memory or []); all_text = " ".join(i.text.lower() for i in all_items)
        for p in _CULTURAL_PATTERNS:
            score = 0
            for key, vals in p["triggers"].items():
                sig_key = {"attachment": "attachment_style", "connection": "connection_response", "conflict": "conflict_style", "fragility": "fragility_pattern"}.get(key, key)
                if signals.get(sig_key) in vals: score += 1
            if any(kw in all_text for kw in p["keywords"]): score += 1
            if score >= 2:
                evidence = [i.text[:80] for i in all_items if i.activation >= 0.3 and i.emotional_valence in ("negative", "extreme")][:2]
                detected.append(CulturalPattern(pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence, blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"]))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "不被接受 — 你怕两边都把你当外人"
        if a == "avoidant": return "被困住 — 你怕任何一个身份都是牢笼"
        if a == "disorganized": return "没有自我 — 你怕适应了太久已经不知道真实的自己"
        return "无处归属 — 你怕永远是过客"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你对两个世界的敏感让你成为最好的文化翻译者。"
        if a == "avoidant": return "你的独立让你不被任何一个文化绑架 — 这是真正的自由。"
        for i in deep:
            if i.emotional_valence == "positive": return f"'{i.text[:60]}' — 这是你的文化锚点。"
        return "能在两个世界都活着的人不是无根的 — 是生命力强的。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "dual_identity" in ids: return "适应A → 想念B → 回到B → 想念A。你在两个世界之间永远是游客。"
        if "code_switch_exhaustion" in ids: return "切换 → 疲惫 → 想做自己 → 发现不知道谁是'自己' → 再切换。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""

@dataclass
class CulturalTurn:
    turn_number: int; coach_text: str; client_text: str; client_internal_state: str
    client_resistance: float; client_resistance_reason: str; client_insight: bool; pattern_addressed: str

@dataclass
class CulturalSession:
    client_id: str; insight: CulturalInsight | None = None
    turns: list[CulturalTurn] = field(default_factory=list); total_time_seconds: float = 0.0
    @property
    def insights_gained(self) -> int: return sum(1 for t in self.turns if t.client_insight)

class CulturalEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine; self._patient = patient_simulator
        self._detector = CulturalPatternDetector(); self._persuasion = PersuasionPlanner(); self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict, focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> CulturalSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = CulturalSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns: session.total_time_seconds = time.time() - t0; return session
        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"embrace your {insight.patterns[0].label}", memory_items=memory_items)
        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nCULTURAL PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Cross-cultural coach. Curious, worldly, celebrates complexity.\n"
            f"Core: '你不是在两个世界之间撕裂。你是少数能看到两个世界的人。'\n"
            f"1. Honor both cultures — never rank them\n2. Name the gift of bicultural vision\n"
            f"3. One integration step, not assimilation\nNEVER say 'just pick one.' NEVER rank cultures.")
        tone = self._tone.adapt(signals=signals, technique_family="act")
        tone.dos = ["Be curious and worldly, like a fellow traveler who has also lived between worlds"] + tone.dos[:2]
        tone.donts = ["NEVER rank cultures or say 'just pick one'"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()
        history: list[dict] = []; pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Cultural — Discovery\nGOAL: introduce\nFOCUS: Ask which worlds they live between. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1); cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Cultural — Pivot\nGOAL: rapport\nFOCUS: Ask about the best thing they got from each culture."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Cultural — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Cultural — Reveal\nGOAL: deepen\nFOCUS: Name it: '{cp.blind_spot[:80]}'. Gently."
            ctx = "\n".join(f"{'Coach' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(CulturalTurn(turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))
        session.total_time_seconds = time.time() - t0; return session
