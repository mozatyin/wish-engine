"""Communication Coach — you are not bad at talking. You just have not found your voice yet.

Core principle: "你不是不会说话。你是还没找到你的声音。"

Pipeline: CommPatternDetector (zero LLM) -> CommEngine (1x Sonnet per turn)
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
class CommPattern:
    pattern_id: str; label: str; description: str; root_cause: str
    soul_evidence: list[str]; blind_spot: str; reframe: str; first_step: str

@dataclass
class CommInsight:
    patterns: list[CommPattern] = field(default_factory=list)
    core_fear: str = ""; authentic_strength: str = ""; repeated_cycle: str = ""; soul_resource: str = ""

_COMM_PATTERNS = [
    {"id": "silenced_voice", "label": "被消音的声音",
     "triggers": {"attachment": ["anxious", "disorganized"], "fragility": ["frozen", "reactive"]},
     "keywords": ["silent", "沉默", "can't speak", "说不出", "voice", "声音", "afraid", "怕", "words", "话", "unheard", "没人听"],
     "description": "You have things to say but the words won't come. Silence became your safety — and your prison.",
     "root_cause": "You learned early: speaking up is dangerous. Silence was survival. But now safety IS the cage.",
     "blind_spot": "你不是'不会说话' — 你是被教会了闭嘴。你的沉默不是性格 — 是伤疤。",
     "reframe": "你的沉默保护了你。但现在你可以选择什么时候安静，什么时候开口。你有这个权利。",
     "first_step": "对一个安全的人说一件你一直没说的小事。不大。感受开口的感觉。"},
    {"id": "eloquent_paralysis", "label": "能说不能做",
     "triggers": {"fragility": ["performative", "masked"], "conflict": ["avoid"]},
     "keywords": ["talk", "说", "but never", "但从来", "action", "行动", "words", "言语", "beautifully", "漂亮", "paralyzed", "瘫", "speak but"],
     "description": "You speak beautifully. You analyze perfectly. But words become a substitute for action. You talk to avoid doing.",
     "root_cause": "Eloquence as defense: if you can describe the problem perfectly, you don't have to solve it. Words are safe; actions are risky.",
     "blind_spot": "你的口才不是力量 — 如果它只用来分析而不行动，它是最精致的拖延术。",
     "reframe": "你理解问题的能力是真的。下一步是把理解变成一步行动 — 哪怕很小。",
     "first_step": "这周把一个你反复说的想法变成一个行动。不说了 — 做。"},
    {"id": "lost_in_translation", "label": "被误解",
     "triggers": {"attachment": ["anxious"], "connection": ["toward"], "conflict": ["accommodate"]},
     "keywords": ["misunderstand", "误解", "mean", "意思", "didn't mean", "不是那个意思", "indirect", "间接", "hint", "暗示", "frustrated"],
     "description": "You say one thing and they hear another. You hint when you should state. You wrap truth in layers until it disappears.",
     "root_cause": "Indirect communication: fear of rejection disguised as politeness. You'd rather be misunderstood than confronted.",
     "blind_spot": "你不是'说不清楚' — 你是怕说清楚后被拒绝。间接是你的防弹衣。",
     "reframe": "你的含蓄是文化的力量。但有时候直说不是粗鲁 — 是尊重对方能承受真相。",
     "first_step": "下次想暗示的时候，试试直说。'我想要X'比'如果你愿意的话也许可以...'更清楚。"},
    {"id": "class_voice", "label": "阶级声音",
     "triggers": {"fragility": ["masked", "reactive"], "conflict": ["avoid", "compete"]},
     "keywords": ["class", "阶级", "accent", "口音", "proper", "得体", "educated", "受过教育", "speech", "说话方式", "judged", "被评判"],
     "description": "Your voice carries your class. You changed your accent, your vocabulary, your entire way of speaking to fit in. But inside you still speak the old language.",
     "root_cause": "Language as class marker. You polished your speech to climb — but the old voice still lives inside, ashamed.",
     "blind_spot": "你改了口音但没改恐惧。你怕的不是说错话 — 你怕别人听出你从哪里来。",
     "reframe": "你的两种声音都是你的。一个让你生存，一个让你真实。你不需要选。",
     "first_step": "在安全的地方用你'原来的声音'说话。感受它。那个声音不是耻辱 — 是根。"},
]

class CommPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> CommInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return CommInsight(patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns), soul_resource=self._resource(deep_items or [], memory_items or []))

    def _detect(self, signals, focus, deep, memory) -> list[CommPattern]:
        detected = []; all_items = focus + deep + (memory or []); all_text = " ".join(i.text.lower() for i in all_items)
        for p in _COMM_PATTERNS:
            score = 0
            for key, vals in p["triggers"].items():
                sig_key = {"attachment": "attachment_style", "connection": "connection_response", "conflict": "conflict_style", "fragility": "fragility_pattern"}.get(key, key)
                if signals.get(sig_key) in vals: score += 1
            if any(kw in all_text for kw in p["keywords"]): score += 1
            if score >= 2:
                evidence = [i.text[:80] for i in all_items if i.activation >= 0.3 and i.emotional_valence in ("negative", "extreme")][:2]
                detected.append(CommPattern(pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence, blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"]))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "被拒绝 — 你怕说真话后被人不喜欢"
        if a == "avoidant": return "暴露 — 你怕开口就暴露了真实的自己"
        if a == "disorganized": return "无力 — 你怕说了也没人听"
        return "不被理解 — 你怕永远说不清楚自己想要什么"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的敏感让你能读懂别人 — 你缺的不是理解力，是表达力。"
        if a == "avoidant": return "你选择的每一个字都经过思考 — 你的谨慎是一种力量。"
        for i in deep:
            if i.emotional_valence == "positive": return f"'{i.text[:60]}' — 这里有你真正的声音。"
        return "你在寻找自己的声音 — 这本身就是勇敢的表达。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "silenced_voice" in ids: return "想说 → 怕 → 沉默 → 被忽视 → 更怕说 → 更沉默。你的安全区在缩小。"
        if "lost_in_translation" in ids: return "暗示 → 被误解 → 失望 → 更间接 → 更被误解。你在用含蓄推开你想要的东西。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""

@dataclass
class CommTurn:
    turn_number: int; coach_text: str; client_text: str; client_internal_state: str
    client_resistance: float; client_resistance_reason: str; client_insight: bool; pattern_addressed: str

@dataclass
class CommSession:
    client_id: str; insight: CommInsight | None = None
    turns: list[CommTurn] = field(default_factory=list); total_time_seconds: float = 0.0
    @property
    def insights_gained(self) -> int: return sum(1 for t in self.turns if t.client_insight)

class CommEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine; self._patient = patient_simulator
        self._detector = CommPatternDetector(); self._persuasion = PersuasionPlanner(); self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict, focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> CommSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = CommSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns: session.total_time_seconds = time.time() - t0; return session
        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"find your voice through {insight.patterns[0].label}", memory_items=memory_items)
        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nCOMMUNICATION PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Communication coach. Encouraging, models clear speech.\n"
            f"Core: '你不是不会说话。你是还没找到你的声音。'\n"
            f"1. Find what they're trying to say — help them say it\n2. Model: be direct and warm yourself\n"
            f"3. One speaking exercise, not a public speaking course\nNEVER tell them to 'speak up.' Help them find WHY they're silent.")
        tone = self._tone.adapt(signals=signals, technique_family="social")
        tone.dos = ["Be encouraging and model clear warm speech yourself"] + tone.dos[:2]
        tone.donts = ["NEVER tell them to 'just speak up' or 'be more confident'"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()
        history: list[dict] = []; pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Comm — Discovery\nGOAL: introduce\nFOCUS: Ask when they last wanted to say something but couldn't. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1); cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Comm — Pivot\nGOAL: rapport\nFOCUS: Ask about a time their words really landed."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Comm — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Comm — Reveal\nGOAL: deepen\nFOCUS: Name it: '{cp.blind_spot[:80]}'. Gently."
            ctx = "\n".join(f"{'Coach' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(CommTurn(turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))
        session.total_time_seconds = time.time() - t0; return session
