"""Digital Detox Coach — your phone is not the problem. The problem is what you are avoiding.

Core principle: "手机不是问题。问题是你在逃避什么。"

Pipeline: DetoxPatternDetector (zero LLM) -> DetoxEngine (1x Sonnet per turn)
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
class DetoxPattern:
    pattern_id: str; label: str; description: str; root_cause: str
    soul_evidence: list[str]; blind_spot: str; reframe: str; first_step: str

@dataclass
class DetoxInsight:
    patterns: list[DetoxPattern] = field(default_factory=list)
    core_fear: str = ""; authentic_strength: str = ""; repeated_cycle: str = ""; soul_resource: str = ""

_DETOX_PATTERNS = [
    {"id": "escapism_scroll", "label": "逃避式刷屏",
     "triggers": {"attachment": ["avoidant", "disorganized"], "fragility": ["frozen", "reactive"]},
     "keywords": ["escape", "逃", "scroll", "刷", "hours", "小时", "numb", "麻木", "avoid", "躲", "real life", "现实", "lost time"],
     "description": "You open your phone to avoid something. Hours later you surface, feeling worse. The real world is still there.",
     "root_cause": "The screen is an anesthetic. Real life hurts; scrolling numbs. But numbing isn't healing.",
     "blind_spot": "你不是'上瘾' — 你是在用屏幕逃避你不愿面对的情绪。手机是症状，不是病。",
     "reframe": "你找到了一种止痛方式 — 这说明你在痛。现在可以找到不需要屏幕的止痛药。",
     "first_step": "下次拿起手机前，先停3秒问自己：我在逃避什么？写下答案。"},
    {"id": "curated_identity", "label": "人设经营",
     "triggers": {"fragility": ["performative", "masked"], "conflict": ["avoid"]},
     "keywords": ["image", "形象", "post", "发", "likes", "赞", "followers", "粉丝", "perfect", "完美", "curate", "filter", "滤镜"],
     "description": "Your online self is a masterpiece. Your real self is exhausted from maintaining it. The gap is killing you.",
     "root_cause": "If you control how others see you, you control whether they reject you. Social media is the perfect stage.",
     "blind_spot": "你经营的人设越完美，你越怕被真实地看到。赞不是爱 — 是租来的认可。",
     "reframe": "你是一个出色的编辑。但被编辑过的生活不是被活过的生活。",
     "first_step": "发一条不完美的内容。不加滤镜。看看什么会发生。"},
    {"id": "comparison_trap", "label": "比较陷阱",
     "triggers": {"attachment": ["anxious"], "fragility": ["reactive"], "conflict": ["avoid"]},
     "keywords": ["compare", "比", "better", "别人", "everyone", "大家", "behind", "落后", "envy", "羡慕", "highlight reel"],
     "description": "You compare your behind-the-scenes to everyone's highlight reel. You always lose.",
     "root_cause": "Social media is a comparison engine. And comparison is the thief of joy. You know this — but you can't stop looking.",
     "blind_spot": "你在拿你的幕后和别人的精选比赛。你永远赢不了 — 因为规则就是不公平的。",
     "reframe": "羡慕其实是指南针 — 它告诉你你在乎什么。问题不是别人有什么，是你想要什么。",
     "first_step": "取关三个让你觉得自己不够好的账号。不需要理由。"},
    {"id": "paralysis_scroll", "label": "拖延式刷屏",
     "triggers": {"fragility": ["frozen"], "conflict": ["avoid"], "attachment": ["disorganized"]},
     "keywords": ["procrastinate", "拖", "should be", "应该", "paralyzed", "瘫", "frozen", "动不了", "waste", "浪费", "nothing done"],
     "description": "You have things to do. Important things. Instead you scroll. Not because you want to — because you can't start.",
     "root_cause": "Paralysis, not laziness. Starting means risking failure. Scrolling means never failing — and never succeeding.",
     "blind_spot": "你不是懒 — 你是怕开始后失败。刷手机是你的'安全区'，因为刷手机不会失败。",
     "reframe": "你的拖延保护了你免于失败。但它也偷走了你成功的机会。",
     "first_step": "设定一个5分钟计时器做你一直在拖的事。5分钟后你可以停。通常你不会停。"},
]

class DetoxPatternDetector:
    def analyze(self, signals: dict, focus_items: list[SoulItem] | None = None,
                deep_items: list[SoulItem] | None = None, memory_items: list[SoulItem] | None = None) -> DetoxInsight:
        patterns = self._detect(signals, focus_items or [], deep_items or [], memory_items or [])
        return DetoxInsight(patterns=patterns, core_fear=self._core_fear(signals),
            authentic_strength=self._strength(signals, deep_items or []),
            repeated_cycle=self._cycle(patterns), soul_resource=self._resource(deep_items or [], memory_items or []))

    def _detect(self, signals, focus, deep, memory) -> list[DetoxPattern]:
        detected = []; all_items = focus + deep + (memory or []); all_text = " ".join(i.text.lower() for i in all_items)
        for p in _DETOX_PATTERNS:
            score = 0
            for key, vals in p["triggers"].items():
                sig_key = {"attachment": "attachment_style", "connection": "connection_response", "conflict": "conflict_style", "fragility": "fragility_pattern"}.get(key, key)
                if signals.get(sig_key) in vals: score += 1
            if any(kw in all_text for kw in p["keywords"]): score += 1
            if score >= 2:
                evidence = [i.text[:80] for i in all_items if i.activation >= 0.3 and i.emotional_valence in ("negative", "extreme")][:2]
                detected.append(DetoxPattern(pattern_id=p["id"], label=p["label"], description=p["description"],
                    root_cause=p["root_cause"], soul_evidence=evidence, blind_spot=p["blind_spot"], reframe=p["reframe"], first_step=p["first_step"]))
        return detected[:3]

    def _core_fear(self, s) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "错过 — 你怕放下手机就错过了什么重要的事"
        if a == "avoidant": return "无聊 — 你怕没有刺激的空白让你面对自己"
        if a == "disorganized": return "存在感 — 你怕不在线就不存在"
        return "面对现实 — 你怕放下手机后要面对的那个世界"

    def _strength(self, s, deep) -> str:
        a = s.get("attachment_style", "")
        if a == "anxious": return "你的在线活跃说明你渴望连接 — 这个渴望是真的，只是需要一个更好的容器。"
        if a == "avoidant": return "你的自制力在其他领域很强 — 把它借给屏幕时间。"
        for i in deep:
            if i.emotional_valence == "positive": return f"'{i.text[:60]}' — 这是不需要屏幕的满足感。"
        return "你承认自己需要改变就是第一步。"

    def _cycle(self, patterns) -> str:
        if not patterns: return ""
        ids = [p.pattern_id for p in patterns]
        if "escapism_scroll" in ids: return "不舒服 → 拿手机 → 暂时好了 → 放下更空虚 → 再拿。屏幕是止痛药，不是药。"
        if "comparison_trap" in ids: return "刷 → 比较 → 自卑 → 刷更多寻找安慰 → 更多比较。算法在喂你焦虑。"
        return f"你的{patterns[0].label}模式在循环。"

    def _resource(self, deep, memory) -> str:
        for i in deep + (memory or []):
            if i.emotional_valence == "positive" and i.activation < 0.3: return i.text
        for i in deep:
            if i.emotional_valence == "positive": return i.text
        return ""

@dataclass
class DetoxTurn:
    turn_number: int; coach_text: str; client_text: str; client_internal_state: str
    client_resistance: float; client_resistance_reason: str; client_insight: bool; pattern_addressed: str

@dataclass
class DetoxSession:
    client_id: str; insight: DetoxInsight | None = None
    turns: list[DetoxTurn] = field(default_factory=list); total_time_seconds: float = 0.0
    @property
    def insights_gained(self) -> int: return sum(1 for t in self.turns if t.client_insight)

class DetoxEngine:
    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._se = session_engine; self._patient = patient_simulator
        self._detector = DetoxPatternDetector(); self._persuasion = PersuasionPlanner(); self._tone = ToneAdapter()

    def run(self, client_profile: PatientProfile, signals: dict, focus_items: list[SoulItem], deep_items: list[SoulItem],
            memory_items: list[SoulItem] | None = None, num_turns: int = 5) -> DetoxSession:
        t0 = time.time()
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)
        session = DetoxSession(client_id=client_profile.character_id, insight=insight)
        if not insight.patterns: session.total_time_seconds = time.time() - t0; return session
        strategy = self._persuasion.plan(focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"understand your {insight.patterns[0].label}", memory_items=memory_items)
        pattern_sec = "\n".join(f"- {p.label}: {p.description[:100]}\n  Blind spot: {p.blind_spot[:100]}" for p in insight.patterns[:2])
        coach_ctx = (
            f"{client_profile.soul_context}\n\nDIGITAL PATTERNS:\n{pattern_sec}\n"
            f"CORE FEAR: {insight.core_fear}\nSTRENGTH: {insight.authentic_strength}\n"
            f"CYCLE: {insight.repeated_cycle}\nRESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION: deep_need={strategy.deep_need}\n\n"
            f"APPROACH: Digital detox coach. Direct, empathetic, no-shame.\n"
            f"Core: '手机不是问题。问题是你在逃避什么。'\n"
            f"1. Name what they're avoiding — the screen is just the vehicle\n"
            f"2. No shame — screens are designed to be addictive\n"
            f"3. One analog replacement, not a phone ban\nNEVER shame screen time. Address the WHY.")
        tone = self._tone.adapt(signals=signals, technique_family="cbt")
        tone.dos = ["Be direct but kind, like a friend who takes your phone and hands you a book"] + tone.dos[:2]
        tone.donts = ["NEVER shame screen time or lecture about blue light"] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()
        history: list[dict] = []; pidx = 0
        for turn in range(1, min(num_turns, 15) + 1):
            cp = insight.patterns[min(pidx, len(insight.patterns) - 1)]
            if turn == 1:
                plan = f"TECHNIQUE: Detox — Discovery\nGOAL: introduce\nFOCUS: Ask what they reach for their phone to escape. Listen for {cp.label}."
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                pidx = min(pidx + 1, len(insight.patterns) - 1); cp = insight.patterns[pidx]
                plan = f"TECHNIQUE: Detox — Pivot\nGOAL: rapport\nFOCUS: Ask about the last time they felt truly present without a screen."
            elif session.turns and session.turns[-1].client_insight:
                plan = f"TECHNIQUE: Detox — Reframe\nGOAL: deepen\nFOCUS: Reframe: '{cp.reframe[:80]}'. Step: '{cp.first_step[:80]}'"
            else:
                plan = f"TECHNIQUE: Detox — Reveal\nGOAL: deepen\nFOCUS: Name it: '{cp.blind_spot[:80]}'. Gently."
            ctx = "\n".join(f"{'Coach' if e['role']=='therapist' else 'Client'}: {e['content'][:200]}" for e in history[-4:])
            resp = self._se.generate_reply(plan_text=plan, tone_text=tone_text, context=ctx, soul_context=coach_ctx)
            history.append({"role": "therapist", "content": resp.reply_text})
            cr = self._patient.respond(profile=client_profile, therapist_message=resp.reply_text, conversation_history=history[:-1])
            history.append({"role": "patient", "content": cr.text})
            session.turns.append(DetoxTurn(turn_number=turn, coach_text=resp.reply_text, client_text=cr.text,
                client_internal_state=cr.internal_state, client_resistance=cr.resistance_level,
                client_resistance_reason=cr.resistance_reason, client_insight=cr.insight_gained, pattern_addressed=cp.label))
        session.total_time_seconds = time.time() - t0; return session
