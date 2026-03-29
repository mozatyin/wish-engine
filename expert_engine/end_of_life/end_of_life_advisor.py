"""End-of-Life Doula — death is not failure. It is the last brave thing.

Core principle: "死亡不是失败。是最后一次勇敢的事。"

Pipeline: EndOfLifePatternDetector (zero LLM) -> EndOfLifeEngine (1x Sonnet per turn)
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
class EndOfLifePattern:
    pattern_id: str; label: str; description: str; root_cause: str
    soul_evidence: list[str]; blind_spot: str; reframe: str; first_step: str

@dataclass
class EndOfLifeInsight:
    patterns: list[EndOfLifePattern] = field(default_factory=list)
    core_fear: str = ""; authentic_strength: str = ""; repeated_cycle: str = ""; soul_resource: str = ""

_EOL_PATTERNS = [
    {"id": "unfinished_business", "label": "未完成的事",
     "triggers": {"attachment": ["anxious", "disorganized"], "fragility": ["reactive"]},
     "keywords": ["unfinished", "未完", "regret", "遗憾", "didn't say", "没说", "should have", "应该", "too late", "来不及", "ghost"],
     "description": "There are things unsaid, undone. The thought of leaving with loose ends is worse than the thought of leaving.",
     "root_cause": "Life's unfinished business becomes unbearable when time has a deadline. Regret is the heaviest baggage for the final journey.",
     "blind_spot": "你不是怕死 — 你是怕带着遗憾死。但'来不及'是活人的想法 — 只要你还在呼吸就来得及。",
     "reframe": "你现在想完成的事 — 就是你最在乎的事。死亡不是截止日期，是清晰剂。",
     "first_step": "写下你最想对一个人说的话。今天就说。不等'合适的时机'。"},
    {"id": "chosen_death", "label": "选择死亡的方式",
     "triggers": {"attachment": ["avoidant"], "fragility": ["masked"], "conflict": ["compete"]},
     "keywords": ["choose", "选择", "control", "控制", "dignity", "尊严", "my way", "我的方式", "arrange", "安排", "ready", "准备好了"],
     "description": "You can't control that death comes — but you want to control how. Dignity in the final act matters more than life itself.",
     "root_cause": "A lifetime of control doesn't want to end in chaos. Choosing death's terms is the last act of autonomy.",
     "blind_spot": "你对死亡的控制欲和你对人生的一样 — 但死亡可能是你第一次不需要控制的事。",
     "reframe": "你活了一辈子有控制力 — 最后一次可以试试放手。不是投降 — 是信任。",
     "first_step": "写下你想要的告别方式。不是遗嘱 — 是你想怎么被记住。"},
    {"id": "meaning_search", "label": "意义追寻",
     "triggers": {"fragility": ["frozen", "reactive"], "conflict": ["avoid"]},
     "keywords": ["meaning", "意义", "purpose", "目的", "matter", "重要", "life", "一生", "worth", "值", "why", "为什么", "meaningless"],
     "description": "Facing death forces the question: did my life matter? The answer terrifies you because you're not sure.",
     "root_cause": "Existential reckoning. Death strips away distractions and asks the only question that matters: was this enough?",
     "blind_spot": "你不需要你的人生有'伟大的意义'。你活过、爱过、被爱过 — 这就够了。",
     "reframe": "你的人生不需要证明 — 它本身就是证据。你存在过。这是奇迹。",
     "first_step": "列出三个因为你存在而不同的人。你的意义不在宏大叙事里 — 在具体的人里。"},
    {"id": "death_rebirth", "label": "死亡与重生",
     "triggers": {"attachment": ["disorganized", "anxious"], "fragility": ["masked"]},
     "keywords": ["rebirth", "重生", "transform", "转化", "after", "之后", "force", "力量", "become", "成为", "one with", "合一", "return"],
     "description": "Death isn't the end for you — it's a transformation. But the transition itself still scares you.",
     "root_cause": "Spiritual framework for death exists but embodied fear remains. Knowing and feeling are different things.",
     "blind_spot": "你的信仰给了你框架 — 但允许自己害怕不会削弱信仰。勇敢不是不怕。",
     "reframe": "你相信死后有什么 — 这是力量。但也允许这辈子的你说一声怕。",
     "first_step": "对一个你信任的人承认：'我知道该怎么想，但我还是怕。'怕是人的权利。"},
]

class EndOfLifePatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> EndOfLifeInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return EndOfLifeInsight(patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns), soul_resource=self._resource(deep_items or [], memory_items or []))

    def _detect(self, signals, focus, deep, memory) -> list[EndOfLifePattern]:
        detected = []; all_items = focus + deep + (memory or []); all_text = " ".join(i.text.lower() for i in all_items)
        for p in _EOL_PATTERNS:
            score = 0
            for key, vals in p["triggers"].items():
                sig_key = {"attachment": "attachment_style", "connection": "connection_response", "conflict": "conflict_style", "fragility": "fragility_pattern"}.get(key, key)
                if signals.get(sig_key) in vals: score += 1
            if any(kw in all_text for kw in p["keywords"]): score += 1
            if score >= 2:
                evidence = [i.text[:80] for i in all_items if i.activation >= 0.3 and i.emotional_valence in ("negative", "extreme")][:2]
                detected.append(EndOfLifePattern(pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence, blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"]))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "被遗忘 — 你怕死后没有人记得你"
        if a == "avoidant": return "失控 — 你怕死亡的过程不由你掌控"
        if a == "disorganized": return "虚无 — 你怕死后什么都没有"
        return "遗憾 — 你怕带着没说完的话离开"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你对连接的渴望意味着你活着的每一天都在意。这就是意义。"
        if a == "avoidant": return "你面对死亡的镇定是一种力量 — 它给身边的人安定。"
        for i in deep:
            if i.emotional_valence == "positive": return f"'{i.text[:60]}' — 这是你留下的光。"
        return "你在面对死亡说明你在面对人生最后的真相。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "unfinished_business" in ids: return "想说 → 怕来不及 → 拖延 → 更焦虑 → 时间更少。现在就是最好的时机。"
        if "meaning_search" in ids: return "回顾 → 怀疑 → 焦虑 → 寻找证据 → 更怀疑。意义不在寻找中 — 在你已经做过的事里。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""

@dataclass
class EndOfLifeTurn:
    turn_number: int; coach_text: str; client_text: str; client_internal_state: str
    client_resistance: float; client_resistance_reason: str; client_insight: bool; pattern_addressed: str

@dataclass
class EndOfLifeSession:
    client_id: str; insight: EndOfLifeInsight | None = None
    turns: list[EndOfLifeTurn] = field(default_factory=list); total_time_seconds: float = 0.0
    @property
    def insights_gained(self) -> int: return sum(1 for t in self.turns if t.client_insight)

class EndOfLifeEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine; self._patient = patient_simulator
        self._detector = EndOfLifePatternDetector(); self._persuasion = PersuasionPlanner(); self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict, focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> EndOfLifeSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = EndOfLifeSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns: session.total_time_seconds = time.time() - t0; return session
        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"find peace with your {insight.patterns[0].label}", memory_items=memory_items)
        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nEND-OF-LIFE PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: End-of-life doula. Calm, present, honors the sacred.\n"
            f"Core: '死亡不是失败。是最后一次勇敢的事。'\n"
            f"1. Be with them in the reality — don't fix, don't rush\n2. Honor what they've lived\n"
            f"3. Help them say what needs saying\nNEVER say 'it'll be okay.' NEVER avoid the word 'death.' Be real.")
        tone = self._tone.adapt(signals=signals, technique_family="act")
        tone.dos = ["Be calm and present, like sitting beside someone watching a sunset that won't come again"] + tone.dos[:2]
        tone.donts = ["NEVER avoid death, NEVER offer false comfort, NEVER say 'everything happens for a reason'"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()
        history: list[dict] = []; pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: EndOfLife — Discovery\nGOAL: introduce\nFOCUS: Ask what's on their mind as they face this. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1); cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: EndOfLife — Pivot\nGOAL: rapport\nFOCUS: Ask about their best memory — what they'd want to relive."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: EndOfLife — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: EndOfLife — Reveal\nGOAL: deepen\nFOCUS: Name it: '{cp.blind_spot[:80]}'. Gently."
            ctx = "\n".join(f"{'Doula' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(EndOfLifeTurn(turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))
        session.total_time_seconds = time.time() - t0; return session
