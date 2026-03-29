"""Fertility Counselor — your worth does not depend on whether you can have children.

Core principle: "你的价值不取决于你能不能生孩子。"

Pipeline: FertilityPatternDetector (zero LLM) -> FertilityEngine (1x Sonnet per turn)
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
class FertilityPattern:
    pattern_id: str; label: str; description: str; root_cause: str
    soul_evidence: list[str]; blind_spot: str; reframe: str; first_step: str

@dataclass
class FertilityInsight:
    patterns: list[FertilityPattern] = field(default_factory=list)
    core_fear: str = ""; authentic_strength: str = ""; repeated_cycle: str = ""; soul_resource: str = ""

_FERTILITY_PATTERNS = [
    {"id": "body_betrayal", "label": "身体的背叛",
     "triggers": {"attachment": ["anxious", "disorganized"], "fragility": ["reactive"]},
     "keywords": ["body", "身体", "fail", "失败", "broken", "坏了", "barren", "不孕", "why me", "为什么", "betrayed", "背叛"],
     "description": "Your body won't do the one thing you need it to do. You feel betrayed by your own flesh.",
     "root_cause": "Fertility struggle makes the body feel like the enemy. Every month is a verdict: not pregnant = not enough.",
     "blind_spot": "你的身体没有背叛你 — 它和你一样想要这个孩子。你们是队友，不是对手。",
     "reframe": "你的身体扛过了所有的检查、注射、等待 — 它比你以为的更坚强。",
     "first_step": "对你的身体说一声谢谢。不是因为它怀孕了 — 是因为它还在陪你战斗。"},
    {"id": "identity_crisis", "label": "身份危机",
     "triggers": {"fragility": ["masked", "performative"], "conflict": ["avoid"]},
     "keywords": ["woman", "女人", "purpose", "意义", "identity", "身份", "children", "孩子", "only", "唯一", "complete", "完整"],
     "description": "Society said your purpose was motherhood. Without children, who are you? The question haunts you.",
     "root_cause": "Cultural conditioning: woman = mother. When fertility fails, identity crumbles because it was built on a single pillar.",
     "blind_spot": "你的价值不住在子宫里。你是完整的 — 不管有没有孩子。",
     "reframe": "成为母亲是一种可能的人生。不是唯一的。你的完整不需要另一个人来证明。",
     "first_step": "列出10件定义你的事 — 其中不能有'母亲'。看看你是多么丰富的人。"},
    {"id": "jealousy_shame", "label": "嫉妒与羞耻",
     "triggers": {"attachment": ["anxious"], "connection": ["toward"], "fragility": ["reactive"]},
     "keywords": ["jealous", "嫉妒", "pregnant", "怀孕", "baby shower", "announcement", "公告", "happy for", "替她高兴", "hate myself", "恨"],
     "description": "Your friend announces her pregnancy. You smile and die inside. Then you hate yourself for the jealousy.",
     "root_cause": "Jealousy is grief wearing a mask. You're not angry at her — you're mourning what you can't have (yet).",
     "blind_spot": "你的嫉妒不代表你是坏人 — 它代表你有多想要这个孩子。嫉妒是爱的影子。",
     "reframe": "你能为别人高兴的同时为自己难过 — 两种感情可以同时存在。这不是矛盾 — 是人性。",
     "first_step": "给自己许可：'我可以替她高兴。我也可以为自己哭。两个都是真的。'"},
    {"id": "children_strategy", "label": "孩子作为策略",
     "triggers": {"attachment": ["avoidant", "anxious"], "conflict": ["compete", "accommodate"]},
     "keywords": ["need", "需要", "heir", "继承", "strategy", "策略", "marriage", "婚姻", "save", "save", "pressure", "压力", "family name"],
     "description": "The child isn't just wanted — it's needed. For the marriage, the family, the legacy. The pressure is crushing.",
     "root_cause": "Children as instrumental: to save a marriage, continue a lineage, fulfill a duty. Love is buried under obligation.",
     "blind_spot": "你想要孩子 — 但你想要的是孩子还是孩子代表的东西？回答这个问题很痛但很重要。",
     "reframe": "卸下'必须生'的压力不是放弃 — 是给自己和未来的孩子一个更健康的起点。",
     "first_step": "分开两件事：'我想要孩子'和'别人需要我有孩子'。哪个是你自己的声音？"},
]

class FertilityPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> FertilityInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return FertilityInsight(patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns), soul_resource=self._resource(deep_items or [], memory_items or []))

    def _detect(self, signals, focus, deep, memory) -> list[FertilityPattern]:
        detected = []; all_items = focus + deep + (memory or []); all_text = " ".join(i.text.lower() for i in all_items)
        for p in _FERTILITY_PATTERNS:
            score = 0
            for key, vals in p["triggers"].items():
                sig_key = {"attachment": "attachment_style", "connection": "connection_response", "conflict": "conflict_style", "fragility": "fragility_pattern"}.get(key, key)
                if signals.get(sig_key) in vals: score += 1
            if any(kw in all_text for kw in p["keywords"]): score += 1
            if score >= 2:
                evidence = [i.text[:80] for i in all_items if i.activation >= 0.3 and i.emotional_valence in ("negative", "extreme")][:2]
                detected.append(FertilityPattern(pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence, blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"]))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "不完整 — 你怕没有孩子就不是完整的女人"
        if a == "avoidant": return "失控 — 你怕无法控制自己的生育就无法控制人生"
        if a == "disorganized": return "遗传 — 你怕不孕是某种惩罚或命运"
        return "不够好 — 你怕自己的身体不配创造生命"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的渴望有多深，你的爱就有多真。这个孩子已经被深深地爱着了。"
        if a == "avoidant": return "你的坚韧让你走到了今天 — 不管结果如何，你没有放弃。"
        for i in deep:
            if i.emotional_valence == "positive": return f"'{i.text[:60]}' — 这是你母性的源头。"
        return "你在面对这个痛苦说明你的爱是真的。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "body_betrayal" in ids: return "希望 → 等待 → 失望 → 恨身体 → 再试 → 再希望。你在和自己的身体打仗。"
        if "jealousy_shame" in ids: return "看到别人怀孕 → 嫉妒 → 羞耻 → 自我攻击 → 更痛。嫉妒不是你的错 — 是悲伤的表达。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""

@dataclass
class FertilityTurn:
    turn_number: int; coach_text: str; client_text: str; client_internal_state: str
    client_resistance: float; client_resistance_reason: str; client_insight: bool; pattern_addressed: str

@dataclass
class FertilitySession:
    client_id: str; insight: FertilityInsight | None = None
    turns: list[FertilityTurn] = field(default_factory=list); total_time_seconds: float = 0.0
    @property
    def insights_gained(self) -> int: return sum(1 for t in self.turns if t.client_insight)

class FertilityEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine; self._patient = patient_simulator
        self._detector = FertilityPatternDetector(); self._persuasion = PersuasionPlanner(); self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict, focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> FertilitySession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = FertilitySession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns: session.total_time_seconds = time.time() - t0; return session
        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"find peace with your {insight.patterns[0].label}", memory_items=memory_items)
        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nFERTILITY PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Fertility counselor. Tender, honoring grief, body-positive.\n"
            f"Core: '你的价值不取决于你能不能生孩子。'\n"
            f"1. Honor the grief — fertility struggle IS grief\n2. Separate identity from fertility\n"
            f"3. One self-compassion step\nNEVER say 'just relax and it'll happen.' NEVER minimize. Honor the journey.")
        tone = self._tone.adapt(signals=signals, technique_family="attachment")
        tone.dos = ["Be tender and honoring, like holding someone's hand through the hardest wait"] + tone.dos[:2]
        tone.donts = ["NEVER say 'just relax' or 'it'll happen when it's meant to'"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()
        history: list[dict] = []; pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Fertility — Discovery\nGOAL: introduce\nFOCUS: Ask how this journey has been for her. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1); cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Fertility — Pivot\nGOAL: rapport\nFOCUS: Ask what keeps her going through all of this."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Fertility — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Fertility — Reveal\nGOAL: deepen\nFOCUS: Name it: '{cp.blind_spot[:80]}'. Gently."
            ctx = "\n".join(f"{'Counselor' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(FertilityTurn(turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))
        session.total_time_seconds = time.time() - t0; return session
