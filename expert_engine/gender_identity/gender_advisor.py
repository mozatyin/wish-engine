"""Gender Identity Counselor — you do not need anyone's permission to be yourself.

Core principle: "你不需要别人的许可来做你自己。"

Pipeline: GenderPatternDetector (zero LLM) -> GenderEngine (1x Sonnet per turn)
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
class GenderPattern:
    pattern_id: str; label: str; description: str; root_cause: str
    soul_evidence: list[str]; blind_spot: str; reframe: str; first_step: str

@dataclass
class GenderInsight:
    patterns: list[GenderPattern] = field(default_factory=list)
    core_fear: str = ""; authentic_strength: str = ""; repeated_cycle: str = ""; soul_resource: str = ""

_GENDER_PATTERNS = [
    {"id": "hidden_self", "label": "隐藏的自我",
     "triggers": {"attachment": ["avoidant", "disorganized"], "fragility": ["masked", "frozen"]},
     "keywords": ["hide", "藏", "disguise", "伪装", "pretend", "假装", "secret", "秘密", "true self", "真实", "mask", "面具", "man", "woman"],
     "description": "You wear a disguise so well that people love the costume, not you. Taking it off means risking everything.",
     "root_cause": "The world told you who you should be before you could decide who you are. Safety meant performing the expected role.",
     "blind_spot": "你不是在'假装' — 你是在保护自己。但保护太久，你开始忘记面具下面是谁了。",
     "reframe": "你的伪装是生存策略 — 它帮你活到了今天。但现在你可以选择何时、在谁面前摘下来。",
     "first_step": "找一个安全的人或空间，做一件'面具下的你'会做的事。很小的事就够了。"},
    {"id": "role_rejection", "label": "角色拒绝",
     "triggers": {"attachment": ["avoidant"], "conflict": ["compete"], "fragility": ["reactive"]},
     "keywords": ["refuse", "拒绝", "won't", "不要", "lady", "淑女", "gentleman", "绅士", "expected", "应该", "rebel", "反叛", "fight"],
     "description": "You rejected the gender role assigned to you. But rebellion is exhausting when the world keeps pushing back.",
     "root_cause": "You saw through the performance earlier than most. But saying 'no' to expectations is a full-time job.",
     "blind_spot": "反叛是力量。但如果你只知道自己'不是'什么，你还不知道自己'是'什么。",
     "reframe": "你拒绝了不属于你的标签 — 这需要勇气。下一步是定义自己的标签。",
     "first_step": "写下三个描述你的词 — 不用任何性别词汇。你是谁不需要性别来定义。"},
    {"id": "fluid_confusion", "label": "流动迷茫",
     "triggers": {"attachment": ["disorganized"], "fragility": ["reactive", "masked"]},
     "keywords": ["fluid", "流动", "change", "变", "both", "都是", "neither", "都不是", "confused", "迷", "spectrum", "光谱", "who am I"],
     "description": "Your gender shifts like water. Some days you're one thing, some days another. People want a fixed answer you can't give.",
     "root_cause": "Gender fluidity is real — but the world demands boxes. The exhaustion comes from translating your experience for others.",
     "blind_spot": "你不是'迷茫' — 你是丰富的。问题不是你不确定自己是谁，是世界的标签装不下你。",
     "reframe": "水不需要解释自己为什么不是冰。你的流动是自然的 — 不需要辩护。",
     "first_step": "今天不解释自己。当别人问'你到底是什么'，试试：'我是我。'"},
    {"id": "seen_unseen", "label": "被看见的渴望",
     "triggers": {"attachment": ["anxious"], "connection": ["toward"], "fragility": ["reactive"]},
     "keywords": ["see me", "看见", "understand", "理解", "accept", "接受", "love me", "爱我", "real me", "真正的我", "voice", "声音"],
     "description": "You want to be seen as who you really are. But every time you show up, people see what they expect, not what's there.",
     "root_cause": "Visibility hunger. You've been invisible or misread for so long that being truly seen feels like oxygen.",
     "blind_spot": "你渴望被看见不是'太多' — 是太久没有被看见。你的需求是合理的。",
     "reframe": "你不需要全世界都看见你。你需要一个人完全看见你 — 从你自己开始。",
     "first_step": "对着镜子说你的名字和一个真实的描述。让自己先看见自己。"},
]

class GenderPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> GenderInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return GenderInsight(patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns), soul_resource=self._resource(deep_items or [], memory_items or []))

    def _detect(self, signals, focus, deep, memory) -> list[GenderPattern]:
        detected = []; all_items = focus + deep + (memory or []); all_text = " ".join(i.text.lower() for i in all_items)
        for p in _GENDER_PATTERNS:
            score = 0
            for key, vals in p["triggers"].items():
                sig_key = {"attachment": "attachment_style", "connection": "connection_response", "conflict": "conflict_style", "fragility": "fragility_pattern"}.get(key, key)
                if signals.get(sig_key) in vals: score += 1
            if any(kw in all_text for kw in p["keywords"]): score += 1
            if score >= 2:
                evidence = [i.text[:80] for i in all_items if i.activation >= 0.3 and i.emotional_valence in ("negative", "extreme")][:2]
                detected.append(GenderPattern(pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence, blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"]))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "被拒绝 — 你怕真实的自己不被爱"
        if a == "avoidant": return "被定义 — 你怕任何标签都是牢笼"
        if a == "disorganized": return "不存在 — 你怕如果你不符合任何类别就不存在"
        return "不被理解 — 你怕永远没人真正看到你"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的渴望被看见是勇气 — 很多人选择永远藏着。"
        if a == "avoidant": return "你的独立让你不被别人的期望定义 — 这是自由。"
        for i in deep:
            if i.emotional_valence == "positive": return f"'{i.text[:60]}' — 这里有你真实的样子。"
        return "你在面对这个问题就说明你在走向真实。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "hidden_self" in ids: return "隐藏 → 安全但孤独 → 渴望被看见 → 害怕暴露 → 继续隐藏。你在安全和真实之间挣扎。"
        if "role_rejection" in ids: return "反叛 → 被排斥 → 更愤怒 → 更反叛。你在用力推开的同时渴望被接纳。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""

@dataclass
class GenderTurn:
    turn_number: int; coach_text: str; client_text: str; client_internal_state: str
    client_resistance: float; client_resistance_reason: str; client_insight: bool; pattern_addressed: str

@dataclass
class GenderSession:
    client_id: str; insight: GenderInsight | None = None
    turns: list[GenderTurn] = field(default_factory=list); total_time_seconds: float = 0.0
    @property
    def insights_gained(self) -> int: return sum(1 for t in self.turns if t.client_insight)

class GenderEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine; self._patient = patient_simulator
        self._detector = GenderPatternDetector(); self._persuasion = PersuasionPlanner(); self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict, focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> GenderSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = GenderSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns: session.total_time_seconds = time.time() - t0; return session
        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"explore your {insight.patterns[0].label}", memory_items=memory_items)
        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nGENDER PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Gender identity counselor. Affirming, patient, zero judgment.\n"
            f"Core: '你不需要别人的许可来做你自己。'\n"
            f"1. Follow their language — use the words THEY use\n2. Affirm: there is no wrong way to be yourself\n"
            f"3. One expression step, not a transition plan\nNEVER label them. NEVER rush. Let them lead.")
        tone = self._tone.adapt(signals=signals, technique_family="act")
        tone.dos = ["Be affirming and patient, like a safe harbor where all identities dock"] + tone.dos[:2]
        tone.donts = ["NEVER label, categorize, or rush their identity journey"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()
        history: list[dict] = []; pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Gender — Discovery\nGOAL: introduce\nFOCUS: Ask when they first felt different from what was expected. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1); cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Gender — Pivot\nGOAL: rapport\nFOCUS: Ask about a moment they felt most like themselves."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Gender — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Gender — Reveal\nGOAL: deepen\nFOCUS: Name it: '{cp.blind_spot[:80]}'. Gently."
            ctx = "\n".join(f"{'Counselor' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(GenderTurn(turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))
        session.total_time_seconds = time.time() - t0; return session
