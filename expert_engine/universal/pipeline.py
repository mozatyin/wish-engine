"""Universal Pipeline — 6 modules, works for ANY domain via config.

SELF-CONTAINED: Does not depend on legacy modules (tone_adapter, models, etc.)
Only dependency: domain_config.py + LLM client for Module 5.

Module 1: ProblemClassifier  (zero LLM)
Module 2: SoulSearcher       (zero LLM)
Module 3: StrategyPlanner    (zero LLM)
Module 4: ToneBuilder        (zero LLM, inline)
Module 5: ReplyGenerator     (1x LLM, ~300 tok)
Module 6: EffectivenessCheck (zero LLM)
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from expert_engine.universal.domain_config import DomainConfig


# ─── Minimal Soul Item (self-contained) ─────────────────────────

@dataclass
class SoulItem:
    id: str = ""
    text: str = ""
    activation: float = 0.0
    emotional_valence: str = ""  # positive, negative, neutral, extreme
    tags: list[str] = field(default_factory=list)


# ─── Module 1: ProblemClassifier ────────────────────────────────

@dataclass
class ClassifiedProblem:
    problem_type: str
    severity: str
    approach: str
    matched_keywords: list[str]
    is_safety: bool = False


_SAFETY_KW = {"kill myself", "want to die", "hurt myself", "end it",
              "suicide", "自杀", "不想活", "伤害自己"}


class ProblemClassifier:
    def classify(self, message: str, config: DomainConfig) -> ClassifiedProblem:
        low = message.lower()
        for kw in _SAFETY_KW:
            if kw in low:
                return ClassifiedProblem("safety_crisis", "critical",
                    "STOP. Validate. Encourage professional help.", [kw], True)
        best, best_n = None, 0
        for pt in config.problem_types:
            matched = [k for k in pt.keywords if k in low]
            if len(matched) > best_n:
                best_n = len(matched)
                best = ClassifiedProblem(pt.name, pt.severity, pt.approach, matched)
        return best or ClassifiedProblem("general", "low",
            f"Explore using: {config.core_principle}", [])

    def classify_multi(self, message: str, all_configs: dict[str, DomainConfig]) -> list[ClassifiedProblem]:
        """Classify across ALL domains — returns all matching problems sorted by severity."""
        low = message.lower()
        # Safety first
        for kw in _SAFETY_KW:
            if kw in low:
                return [ClassifiedProblem("safety_crisis", "critical",
                    "STOP. Validate. Professional referral.", [kw], True)]

        hits = []
        for domain_name, config in all_configs.items():
            for pt in config.problem_types:
                matched = [k for k in pt.keywords if k in low]
                if matched:
                    hits.append(ClassifiedProblem(
                        f"{domain_name}:{pt.name}", pt.severity,
                        f"[{config.name}] {pt.approach}", matched))

        # Sort: critical > high > medium > low
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        hits.sort(key=lambda h: severity_order.get(h.severity, 4))
        return hits or [ClassifiedProblem("general", "low", "Listen and explore.", [])]


# ─── Module 2: SoulSearcher ────────────────────────────────────

@dataclass
class SoulResources:
    strengths: list[SoulItem]
    wounds: list[SoulItem]
    best_lever: str


_POS_KW = {"love", "proud", "happy", "strong", "brave", "survived", "talent",
           "gift", "dream", "hope", "friend", "family",
           "爱", "骄傲", "强", "勇敢", "天赋", "梦想", "希望"}


class SoulSearcher:
    def search(self, focus: list[SoulItem] | None, deep: list[SoulItem] | None,
               memory: list[SoulItem] | None) -> SoulResources:
        all_items = list(focus or []) + list(deep or []) + list(memory or [])
        strengths, wounds = [], []
        for item in all_items:
            low = item.text.lower()
            if item.emotional_valence in ("positive", "neutral") or any(k in low for k in _POS_KW):
                strengths.append(item)
            elif item.emotional_valence in ("negative", "extreme"):
                wounds.append(item)
        strengths.sort(key=lambda s: s.activation)
        wounds.sort(key=lambda w: -w.activation)
        return SoulResources(strengths[:5], wounds[:3],
                             strengths[0].text[:80] if strengths else "")


# ─── Module 3: StrategyPlanner ──────────────────────────────────

@dataclass
class Strategy:
    core_principle: str
    approach: str
    soul_lever: str
    reframe: str
    avoid: list[str]
    use: list[str]
    action: str


class StrategyPlanner:
    def plan(self, problem: ClassifiedProblem, resources: SoulResources,
             config: DomainConfig) -> Strategy:
        lever = resources.best_lever
        reframe = config.core_principle
        if lever:
            reframe += f" Evidence: '{lever}'"
        return Strategy(
            core_principle=config.core_principle,
            approach=problem.approach,
            soul_lever=lever,
            reframe=reframe,
            avoid=config.forbidden_phrases[:5],
            use=[d[:30] for d in config.dos[:5]],
            action=f"One thing this week: {problem.approach[:60]}",
        )


# ─── Module 4: ToneBuilder (inline, zero LLM) ──────────────────

def build_tone(signals: dict, config: DomainConfig) -> str:
    """Build communication tone directive from signals + config."""
    lines = []
    fragility = signals.get("fragility_pattern", "")
    conflict = signals.get("conflict_style", "")
    humor = signals.get("humor_style", "")

    if conflict in ("compete", "escalating") and fragility in ("masked", "defensive"):
        lines.append("STYLE: challenging. Match their energy. Be blunt. Use strategy language.")
    elif fragility == "avoidant" or signals.get("emotion_dominant") == "neutral":
        lines.append("STYLE: direct. Short sentences. No metaphors. Respect their authenticity.")
    elif humor == "aggressive" and fragility in ("reactive", "defensive"):
        lines.append("STYLE: direct. Show strength. Don't be overly gentle.")
    elif fragility == "reactive":
        lines.append("STYLE: gentle. Go slowly. Validate before exploring.")
    else:
        lines.append("STYLE: warm. Be genuine, empathic, natural.")

    lines.append("DO: " + ". ".join(config.dos[:3]))
    lines.append("DON'T: " + ". ".join(config.donts[:3]))
    return "\n".join(lines)


# ─── Module 5: ReplyGenerator (1x LLM) ─────────────────────────

def generate_reply(api_key: str, model: str, base_url: str,
                   plan_text: str, tone_text: str, context: str,
                   soul_context: str) -> str:
    """Generate expert reply. 1 LLM call, ~300 token prompt."""
    try:
        from anthropic import Anthropic
    except ImportError:
        return "(LLM unavailable)"

    system = (
        f"You are an expert advisor. Generate ONE response.\n"
        f"{tone_text}\n{plan_text}\n"
        f"Never use clinical jargon. End with specific actionable homework if appropriate."
    )
    user_msg = f"{context}\n\n{soul_context}" if soul_context else context
    user_msg += '\n\nRespond in JSON: {"reply": "your response (150 words max)", "homework": "or empty"}'

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = Anthropic(**kwargs)
    resp = client.messages.create(model=model, max_tokens=768, system=system,
                                  messages=[{"role": "user", "content": user_msg}])
    text = resp.content[0].text
    try:
        start, end = text.find("{"), text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            return data.get("reply", text)
    except (json.JSONDecodeError, ValueError):
        pass
    return text


# ─── Module 6: EffectivenessCheck (zero LLM) ───────────────────

@dataclass
class Effectiveness:
    engaged: bool
    felt_better: bool
    soul_used: bool
    no_violations: bool
    overall: bool


_POS_SIGNALS = ["maybe", "perhaps", "could try", "never thought", "thank", "feel better",
                "you're right", "never named", "never considered", "diagnosed", "accurate",
                "i see", "i suppose", "fair point", "interesting", "that's true",
                "i admit", "you've", "i didn't realize", "first time",
                "也许", "试试", "从来没想过", "谢谢", "好多了", "原来", "对啊",
                "你说得对", "没想到", "第一次", "有道理", "承认"]


_REJECTION_SIGNALS = ["whatever", "dont care", "shut up", "leave me alone", "pointless",
                      "go away", "useless", "waste of time", "无所谓", "别管我", "闭嘴", "没用"]


class EffectivenessChecker:
    def check(self, client_text: str, expert_text: str, config: DomainConfig,
              soul_lever: str = "") -> Effectiveness:
        ct, et = client_text.lower(), expert_text.lower()

        # Detect full rejection — overrides engagement
        is_rejecting = any(s in ct for s in _REJECTION_SIGNALS)
        engaged = len(client_text) > 30 and not is_rejecting

        felt = any(s in ct for s in _POS_SIGNALS) and not is_rejecting
        soul = bool(soul_lever) and any(w in et for w in soul_lever.lower().split()[:3])
        clean = not any(fp.lower() in et for fp in config.forbidden_phrases)
        return Effectiveness(engaged, felt, soul, clean,
                             engaged and (felt or soul) and clean and not is_rejecting)


# ─── Universal Session ──────────────────────────────────────────

@dataclass
class UniversalTurn:
    turn_number: int
    expert_text: str
    client_text: str
    client_internal: str = ""
    resistance: float = 0.5
    resistance_reason: str = ""
    insight: bool = False
    effectiveness: Effectiveness = None


@dataclass
class UniversalSession:
    domain: str
    client_id: str
    turns: list[UniversalTurn] = field(default_factory=list)
    problem: Optional[ClassifiedProblem] = None
    strategy: Optional[Strategy] = None
    total_time: float = 0.0

    @property
    def success(self) -> bool:
        return any(t.effectiveness and t.effectiveness.overall for t in self.turns[-2:]) if self.turns else False

    @property
    def insights(self) -> int:
        return sum(1 for t in self.turns if t.insight)


# ─── Universal Engine ───────────────────────────────────────────

class UniversalEngine:
    """One engine for ALL domains. Config-driven. Self-contained."""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = "anthropic/claude-sonnet-4"):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._base_url = base_url or ("https://openrouter.ai/api" if self._api_key.startswith("sk-or-") else "")
        self._model = model if not self._api_key.startswith("sk-or-") or "/" in model else "anthropic/claude-sonnet-4"
        self._classifier = ProblemClassifier()
        self._searcher = SoulSearcher()
        self._planner = StrategyPlanner()
        self._checker = EffectivenessChecker()

    def run(self, config: DomainConfig, client_message: str,
            focus: list[SoulItem] | None = None, deep: list[SoulItem] | None = None,
            memory: list[SoulItem] | None = None, signals: dict | None = None,
            num_turns: int = 4, simulate_client=None) -> UniversalSession:
        """Run a domain-expert session.

        Args:
            config: Domain configuration
            client_message: User's presenting problem
            focus/deep/memory: Soul items
            signals: Detector signals for tone adaptation
            num_turns: Number of dialogue turns
            simulate_client: Optional callable(expert_text, history) -> dict with text, resistance, insight, internal, reason
        """
        t0 = time.time()
        session = UniversalSession(domain=config.domain, client_id="user")

        # M1: Classify
        problem = self._classifier.classify(client_message, config)
        session.problem = problem
        if problem.is_safety:
            session.total_time = time.time() - t0
            return session

        # M2: Search Soul
        resources = self._searcher.search(focus, deep, memory)

        # M3: Strategy
        strategy = self._planner.plan(problem, resources, config)
        session.strategy = strategy

        # M4: Tone
        sigs = signals or {}
        tone_text = build_tone(sigs, config)

        # Build soul context
        strengths_text = "\n".join(f"- {s.text}" for s in resources.strengths[:3])
        soul_ctx = (
            f"DOMAIN: {config.name}\nPRINCIPLE: {strategy.core_principle}\n"
            f"PROBLEM: [{problem.problem_type}] {problem.approach}\n"
            f"SOUL LEVER: {strategy.soul_lever}\nREFRAME: {strategy.reframe}\n"
            f"AVOID: {', '.join(strategy.avoid[:4])}\n"
            f"STRENGTHS:\n{strengths_text}\n"
            f"RULES:\n" + "\n".join(f"DO: {d}" for d in config.dos[:3])
            + "\n" + "\n".join(f"DON'T: {d}" for d in config.donts[:3])
        )

        history: list[dict] = [{"role": "patient", "content": client_message}]

        for turn in range(1, num_turns + 1):
            plan_text = (
                f"TECHNIQUE: {config.name}\n"
                f"GOAL: {'validate' if turn == 1 else 'deepen'} | "
                f"DEPTH: {'surface' if turn == 1 else 'medium'} | PACING: slow\n"
                f"FOCUS: {problem.approach[:80]}"
            )
            ctx = "\n".join(
                f"{'Expert' if e['role'] == 'therapist' else 'Client'}: {e['content'][:150]}"
                for e in history[-4:]
            )

            # M5: Generate reply
            expert_text = generate_reply(
                self._api_key, self._model, self._base_url,
                plan_text, tone_text, ctx, soul_ctx
            )
            history.append({"role": "therapist", "content": expert_text})

            # Client response (simulated or placeholder)
            client_text, resistance, insight, internal, reason = "", 0.5, False, "", ""
            if simulate_client:
                cr = simulate_client(expert_text, history[:-1])
                client_text = cr.get("text", "")
                resistance = cr.get("resistance", 0.5)
                insight = cr.get("insight", False)
                internal = cr.get("internal", "")
                reason = cr.get("reason", "")
                history.append({"role": "patient", "content": client_text})

            # M6: Check
            eff = self._checker.check(client_text, expert_text, config, strategy.soul_lever)

            session.turns.append(UniversalTurn(
                turn, expert_text, client_text, internal,
                resistance, reason, insight, eff,
            ))
            time.sleep(0.3)

        session.total_time = time.time() - t0
        return session

    def respond_single(self, config: DomainConfig, message: str,
                       focus: list[SoulItem] | None = None,
                       deep: list[SoulItem] | None = None,
                       signals: dict | None = None) -> dict:
        """Single-turn response. 1 LLM call. For production use."""
        problem = self._classifier.classify(message, config)
        if problem.is_safety:
            return {"reply": "", "safety_alert": "critical", "problem": problem.problem_type}

        resources = self._searcher.search(focus, deep, None)
        strategy = self._planner.plan(problem, resources, config)
        tone_text = build_tone(signals or {}, config)

        strengths = "\n".join(f"- {s.text}" for s in resources.strengths[:3])
        soul_ctx = (
            f"DOMAIN: {config.name}\nPRINCIPLE: {strategy.core_principle}\n"
            f"PROBLEM: {problem.approach}\nSOUL LEVER: {strategy.soul_lever}\n"
            f"STRENGTHS:\n{strengths}"
        )
        plan_text = f"TECHNIQUE: {config.name}\nGOAL: validate | DEPTH: surface\nFOCUS: {problem.approach[:80]}"

        reply = generate_reply(self._api_key, self._model, self._base_url,
                               plan_text, tone_text, f"Client: {message}", soul_ctx)

        return {"reply": reply, "domain": config.domain, "problem": problem.problem_type,
                "soul_lever": strategy.soul_lever}
