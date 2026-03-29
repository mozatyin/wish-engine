"""Family Mediator — families fight not because they do not love, but because they love differently.

Core principle: "家人吵架不是因为不爱。是因为爱得方式不同。"

Pipeline: FamilyPatternDetector (zero LLM) -> FamilyEngine (1x Sonnet per turn)
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
class FamilyPattern:
    pattern_id: str; label: str; description: str; root_cause: str
    soul_evidence: list[str]; blind_spot: str; reframe: str; first_step: str

@dataclass
class FamilyInsight:
    patterns: list[FamilyPattern] = field(default_factory=list)
    core_fear: str = ""; authentic_strength: str = ""; repeated_cycle: str = ""; soul_resource: str = ""

_FAMILY_PATTERNS = [
    {"id": "expectation_gap", "label": "期望鸿沟",
     "triggers": {"attachment": ["anxious", "avoidant"], "conflict": ["compete", "avoid"]},
     "keywords": ["disappointed", "失望", "expect", "期望", "not good enough", "不够好", "proud", "骄傲", "approval", "认可", "father", "父亲"],
     "description": "Parent and child speak different languages of love. One expects, the other rebels — or crumbles.",
     "root_cause": "Unspoken expectations are pre-loaded disappointments. The parent loves through standards; the child hears rejection.",
     "blind_spot": "你父亲的严厉不是不爱 — 是他不知道怎么爱。他用他被爱的方式爱你。",
     "reframe": "期望是爱的变形。当你理解了它的来源，你可以选择接受爱而拒绝形式。",
     "first_step": "写下你父母从未说出口的一句话。也许是'我为你骄傲'。然后问：他们用什么方式说了？"},
    {"id": "parentification", "label": "角色颠倒",
     "triggers": {"attachment": ["anxious", "disorganized"], "fragility": ["masked", "reactive"]},
     "keywords": ["take care", "照顾", "parent", "父母", "responsible", "负责", "child", "孩子", "too young", "太小", "grown up", "长大"],
     "description": "You became the parent before you were done being a child. The family needed you to be strong.",
     "root_cause": "When the adults couldn't cope, you stepped up. You lost your childhood to keep the family from falling apart.",
     "blind_spot": "你不是'懂事' — 你是被迫早熟。你的'成熟'是一个孩子的生存策略。",
     "reframe": "你扛过了不该你扛的重量。现在你可以放下一些 — 不是因为不爱他们，是因为你也配被照顾。",
     "first_step": "这周让别人帮你做一件事。不指导，不检查。让别人也有机会照顾你。"},
    {"id": "loyalty_bind", "label": "忠诚困境",
     "triggers": {"attachment": ["anxious", "disorganized"], "conflict": ["avoid", "accommodate"]},
     "keywords": ["choose", "选", "side", "边", "between", "之间", "loyalty", "忠", "betray", "背叛", "divorce", "离", "caught"],
     "description": "You're caught between family members. Choosing one means betraying the other. So you freeze.",
     "root_cause": "Triangulation — you were made the mediator, the messenger, the peacekeeper. Your needs disappeared in the crossfire.",
     "blind_spot": "你不需要选边站。你的忠诚可以是对自己的 — 而不是对任何一方的。",
     "reframe": "拒绝选边不是不孝 — 是最健康的边界。你不是法官，也不是被告。",
     "first_step": "下次有人让你传话或选边，说：'这是你们之间的事。我爱你们两个。'"},
    {"id": "legacy_weight", "label": "家族重担",
     "triggers": {"fragility": ["masked", "performative"], "conflict": ["compete"]},
     "keywords": ["legacy", "家族", "honor", "荣誉", "name", "名", "dynasty", "dynasty", "heir", "继承", "carry on", "传承", "burden"],
     "description": "You carry a family name like a sentence. Every choice is judged against generations of expectation.",
     "root_cause": "The family invested its identity in you. Your success is their validation. Your failure is their shame.",
     "blind_spot": "家族的荣耀不应该是你的枷锁。你可以带着它走，但不需要被它压垮。",
     "reframe": "你是家族的延续 — 不是复制品。你可以用自己的方式延续这个名字。",
     "first_step": "写下你想从家族传统中保留什么，放下什么。你有权选择。"},
]


class FamilyPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> FamilyInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return FamilyInsight(patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns), soul_resource=self._resource(deep_items or [], memory_items or []))

    def _detect(self, signals, focus, deep, memory) -> list[FamilyPattern]:
        detected = []; all_items = focus + deep + (memory or []); all_text = " ".join(i.text.lower() for i in all_items)
        for p in _FAMILY_PATTERNS:
            score = 0
            for key, vals in p["triggers"].items():
                sig_key = {"attachment": "attachment_style", "connection": "connection_response", "conflict": "conflict_style", "fragility": "fragility_pattern"}.get(key, key)
                if signals.get(sig_key) in vals: score += 1
            if any(kw in all_text for kw in p["keywords"]): score += 1
            if score >= 2:
                evidence = [i.text[:80] for i in all_items if i.activation >= 0.3 and i.emotional_valence in ("negative", "extreme")][:2]
                detected.append(FamilyPattern(pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence, blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"]))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "被抛弃 — 你怕不够好就会失去家人的爱"
        if a == "avoidant": return "被控制 — 你怕家庭的爱是有条件的绳索"
        if a == "disorganized": return "重复 — 你怕把家里的痛苦传给下一代"
        return "不被理解 — 你怕家人永远看不到真正的你"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你对家人的敏感是天赋 — 没人比你更懂这个家的温度。"
        if a == "avoidant": return "你的独立给了家人空间 — 有时候最好的爱是不窒息。"
        for i in deep:
            if i.emotional_valence == "positive": return f"'{i.text[:60]}' — 这里有你们家真正的爱。"
        return "你在面对家庭问题说明你还没放弃这个家。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "expectation_gap" in ids: return "期望 → 失望 → 距离 → 内疚 → 更努力 → 再失望。你们在同一个循环里打转。"
        if "parentification" in ids: return "照顾别人 → 忽略自己 → 崩溃 → 内疚 → 再照顾。你在用牺牲换存在感。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""


@dataclass
class FamilyTurn:
    turn_number: int; coach_text: str; client_text: str; client_internal_state: str
    client_resistance: float; client_resistance_reason: str; client_insight: bool; pattern_addressed: str

@dataclass
class FamilySession:
    client_id: str; insight: FamilyInsight | None = None
    turns: list[FamilyTurn] = field(default_factory=list); total_time_seconds: float = 0.0
    @property
    def insights_gained(self) -> int: return sum(1 for t in self.turns if t.client_insight)


class FamilyEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine; self._patient = patient_simulator
        self._detector = FamilyPatternDetector(); self._persuasion = PersuasionPlanner(); self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict, focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> FamilySession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = FamilySession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns:
            session.total_time_seconds = time.time() - t0; return session
        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see the {insight.patterns[0].label} in your family", memory_items=memory_items)
        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nFAMILY PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Family mediator. Neutral, warm, sees all sides.\n"
            f"Core: '家人吵架不是因为不爱。是因为爱得方式不同。'\n"
            f"1. Help them see the other person's love language\n"
            f"2. Name the pattern both sides are trapped in\n"
            f"3. One boundary or bridge, not a family therapy lecture\n"
            f"NEVER take sides. NEVER blame parents or children. See the system.")
        tone = self._tone.adapt(signals=signals, technique_family="relationship")
        tone.dos = ["Be neutral and warm, like a wise uncle who loves both sides"] + tone.dos[:2]
        tone.donts = ["NEVER take sides or blame anyone in the family"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()
        history: list[dict] = []; pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Family — Discovery\nGOAL: introduce\nFOCUS: Ask about their family and who they clash with most. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1); cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Family — Pivot\nGOAL: rapport\nFOCUS: Ask about a good memory with that family member."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Family — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Family — Reveal\nGOAL: deepen\nFOCUS: Name it: '{cp.blind_spot[:80]}'. Gently."
            ctx = "\n".join(f"{'Mediator' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(FamilyTurn(turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))
        session.total_time_seconds = time.time() - t0; return session
