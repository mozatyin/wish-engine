"""Dating Advisor — reveals romantic patterns from Soul and coaches authentic connection.

Core principle: "你已经知道怎么吸引对的人了 — Soul 里有证据"

Not about "techniques" or "tricks." About understanding YOUR pattern and being authentic.

Pipeline: DatingPatternDetector (zero LLM) → DatingEngine (1x Sonnet per turn)
Communication style: friend-like, direct, sometimes funny. Not clinical.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from expert_engine.goal_generator import SoulItem
from expert_engine.patient_simulator import PatientSimulator, PatientProfile, PatientResponse
from expert_engine.growth_coach.persuasion_planner import PersuasionPlanner
from expert_engine.tone_adapter import ToneAdapter
from expert_engine.session_engine import SessionEngine


# ---------------------------------------------------------------------------
# Dating Pattern Detector — zero LLM, rule-based from Soul signals
# ---------------------------------------------------------------------------

@dataclass
class DatingPattern:
    """A romantic pattern detected from Soul."""
    pattern_id: str
    label: str  # human-readable name
    description: str  # what this pattern looks like
    root_cause: str  # why they do this (from Soul)
    soul_evidence: list[str]  # quotes from Soul items
    blind_spot: str  # what they can't see about themselves
    reframe: str  # the "你已经知道了" reframe
    first_step: str  # one concrete thing to try


@dataclass
class DatingInsight:
    """Complete dating pattern analysis."""
    patterns: list[DatingPattern] = field(default_factory=list)
    core_fear: str = ""  # the ONE fear driving their dating behavior
    authentic_strength: str = ""  # what they're actually good at in love
    repeated_cycle: str = ""  # the cycle they keep repeating
    soul_resource: str = ""  # positive evidence from Soul for breaking the cycle


# Pattern definitions — each maps to a real romantic dysfunction
_DATING_PATTERNS = [
    {
        "id": "attracted_to_unavailable",
        "label": "追不可追",
        "triggers": {
            "attachment": ["anxious"],
            "connection": ["toward"],
            "fragility": ["reactive", "anxious"],
        },
        "description": "You're attracted to people who can't or won't fully show up. The chase feels like love, but it's actually anxiety dressed up as passion.",
        "root_cause": "Anxious attachment: the uncertainty IS the attraction. When someone is fully available, it feels 'boring' — because your nervous system confuses calm with disinterest.",
        "blind_spot": "你不是被他们吸引 — 你是被那种不确定感吸引。稳定的人让你觉得'没感觉'，因为你把焦虑当成了心动。",
        "reframe": "你其实知道什么是真的好 — [soul_evidence] 就是证据。问题不是你不懂爱，是你的雷达把'安全'标记成了'无聊'。",
        "first_step": "下次遇到一个让你觉得'还行但没有心跳加速'的人，给自己三次约会的机会。心动不是第一次就该出现的。",
    },
    {
        "id": "performer",
        "label": "完美面具",
        "triggers": {
            "fragility": ["masked", "performative"],
            "conflict": ["avoid", "accommodate"],
            "attachment": ["anxious", "fearful"],
        },
        "description": "You perform a version of yourself on dates — funnier, cooler, more agreeable than you really are. And then you're exhausted, and they fall in love with someone who doesn't exist.",
        "root_cause": "Masked fragility: you believe the real you isn't enough. So you build a character. The tragedy: the mask works — they like the character. And you're trapped.",
        "blind_spot": "你以为是他们不够好所以你们分手。其实是你累了 — 演一个角色太累了。你需要的不是更好的对象，是放下面具的勇气。",
        "reframe": "你的Soul里有真实的你 — [soul_evidence]。那个人比你的面具有趣多了。你不需要表演，你需要被看见。",
        "first_step": "下次约会，故意说一件你觉得'不够酷'的事。看看对方的反应。真正的连接从不完美开始。",
    },
    {
        "id": "fear_of_rejection",
        "label": "先拒绝的人赢",
        "triggers": {
            "attachment": ["avoidant", "fearful"],
            "connection": ["away"],
            "fragility": ["avoidant", "masked"],
        },
        "description": "You never make the first move. You wait for clear signals. You'd rather miss a connection than risk rejection. You tell yourself 'if they liked me they'd say something.'",
        "root_cause": "Avoidant pattern: rejection feels like annihilation, not just disappointment. So you build a wall of 'I don't really care anyway' to protect yourself.",
        "blind_spot": "你不是'不主动'的人 — 你是'太害怕被拒绝'的人。区别很大。你有喜欢人的能力 — [soul_evidence] — 你只是把这个能力锁起来了。",
        "reframe": "你的Soul说你其实很渴望连接 — [soul_evidence]。你不需要变得勇敢，你需要接受：被拒绝不会杀了你。",
        "first_step": "这周，对一个你觉得还不错的人说'我想更了解你'。不是暗示，不是试探，直接说。最坏的结果：他们说不。然后呢？你还活着。",
    },
    {
        "id": "serial_dater",
        "label": "永远的下一个",
        "triggers": {
            "attachment": ["avoidant", "disorganized"],
            "conflict": ["avoid"],
            "fragility": ["avoidant"],
        },
        "description": "Three months in, you start finding flaws. Six months, you're already looking. You leave before it gets real because 'real' is where it hurts.",
        "root_cause": "Commitment avoidance: the beginning is intoxicating because it's all projection. When the real person shows up — flaws and all — the fantasy breaks. And you'd rather start a new fantasy than accept a real person.",
        "blind_spot": "你不是'还没遇到对的人' — 你是在对的人出现的时候逃跑。你找的不是完美的人，你找的是永远不必脆弱的借口。",
        "reframe": "你的Soul里有持久的东西 — [soul_evidence]。你能坚持，你能深入。你只是还没在恋爱里允许自己这样做。",
        "first_step": "下次你想离开的时候，问自己：'我是真的不喜欢他们了，还是我害怕了？'如果答案是害怕 — 再多待一个月。",
    },
    {
        "id": "love_bomber",
        "label": "爱的洪流",
        "triggers": {
            "attachment": ["anxious", "disorganized"],
            "connection": ["toward"],
            "conflict": ["escalating", "compete"],
        },
        "description": "You love hard and fast. Texts all day. Plans the future on the second date. Your intensity is real — but it overwhelms people. They pull back, and you interpret the pullback as rejection, so you love HARDER.",
        "root_cause": "Anxious overcompensation: you believe that if you love enough, they can't leave. But intensity without space suffocates. The more you grip, the more they slip.",
        "blind_spot": "你的爱是真的 — 但你的音量是错的。你不需要少爱一点，你需要学会安静地爱。[soul_evidence] 说明你其实会。",
        "reframe": "你的热情是礼物 — [soul_evidence]。问题不是你爱得太多，是你爱得太快。真正的连接需要空间长出来。",
        "first_step": "下次你想发第三条消息的时候，停下来。不是玩欲擒故纵 — 是给你的爱一个安静的形状。等他们回了再发。",
    },
    {
        "id": "ghost",
        "label": "消失的人",
        "triggers": {
            "attachment": ["avoidant", "disorganized", "fearful"],
            "connection": ["away"],
            "fragility": ["avoidant", "frozen"],
        },
        "description": "When feelings get real, you disappear. You stop replying. You find a reason to be busy. You're not cruel — you're terrified. Feelings that deep feel like drowning.",
        "root_cause": "Emotional overwhelm: intimacy triggers a shutdown response. Your nervous system reads 'closeness' as 'danger' and hits the eject button. By the time you want to come back, it's too late.",
        "blind_spot": "你不是冷漠的人。你消失是因为你感觉太多，不是太少。[soul_evidence] 说明你有非常深的感情 — 你只是不知道怎么在不逃跑的情况下承受它。",
        "reframe": "你的Soul说你其实很深情 — [soul_evidence]。你不需要学会感觉更多，你需要学会留下来。",
        "first_step": "下次你想消失的时候，发一条消息：'我需要一点时间，但我没有走。'这三秒钟的勇气比消失三天容易多了。",
    },
]


class DatingPatternDetector:
    """Detects romantic patterns from Soul signals — zero LLM.

    Usage:
        detector = DatingPatternDetector()
        insight = detector.analyze(
            signals={"attachment_style": "anxious", ...},
            focus_items=[SoulItem(text="I always fall for the wrong type", ...)],
            deep_items=[SoulItem(text="My first love ghosted me", ...)],
        )
    """

    def analyze(
        self,
        signals: dict,
        focus_items: list[SoulItem] | None = None,
        deep_items: list[SoulItem] | None = None,
        memory_items: list[SoulItem] | None = None,
    ) -> DatingInsight:
        """Analyze one person's Soul for dating patterns."""
        patterns = self._detect_patterns(signals, focus_items or [], deep_items or [], memory_items or [])
        core_fear = self._infer_core_fear(signals)
        strength = self._infer_authentic_strength(signals, deep_items or [])
        cycle = self._infer_repeated_cycle(patterns)
        resource = self._find_soul_resource(deep_items or [], memory_items or [])

        return DatingInsight(
            patterns=patterns,
            core_fear=core_fear,
            authentic_strength=strength,
            repeated_cycle=cycle,
            soul_resource=resource,
        )

    def _detect_patterns(self, signals, focus, deep, memory) -> list[DatingPattern]:
        """Match Soul signals to dating patterns."""
        detected = []
        all_items = focus + deep + (memory or [])

        for p in _DATING_PATTERNS:
            score = 0
            triggers = p["triggers"]

            for signal_key, trigger_values in triggers.items():
                if signal_key == "attachment":
                    if signals.get("attachment_style") in trigger_values:
                        score += 1
                elif signal_key == "connection":
                    if signals.get("connection_response") in trigger_values:
                        score += 1
                elif signal_key == "conflict":
                    if signals.get("conflict_style") in trigger_values:
                        score += 1
                elif signal_key == "fragility":
                    if signals.get("fragility_pattern") in trigger_values:
                        score += 1

            if score >= 2:  # Need at least 2 matching triggers
                # Find Soul evidence
                evidence = []
                for item in all_items:
                    if item.emotional_valence in ("negative", "extreme") and item.activation >= 0.3:
                        evidence.append(item.text[:80])
                    if len(evidence) >= 2:
                        break

                # Find positive resource for reframe
                resource = ""
                for item in deep + (memory or []):
                    if item.emotional_valence in ("positive",):
                        resource = item.text[:80]
                        break

                reframe = p["reframe"].replace("[soul_evidence]", resource or "your past experiences")
                blind_spot = p["blind_spot"].replace("[soul_evidence]", resource or "your past")

                detected.append(DatingPattern(
                    pattern_id=p["id"],
                    label=p["label"],
                    description=p["description"],
                    root_cause=p["root_cause"],
                    soul_evidence=evidence,
                    blind_spot=blind_spot,
                    reframe=reframe,
                    first_step=p["first_step"],
                ))

        return detected[:3]  # Top 3 patterns

    def _infer_core_fear(self, signals) -> str:
        attach = signals.get("attachment_style", "")
        if attach == "anxious":
            return "被抛弃 — 你最怕的不是单身，是被选择之后又被放弃"
        elif attach == "avoidant":
            return "被看穿 — 你最怕的不是孤独，是有人真正走近你然后失望"
        elif attach == "disorganized":
            return "失控 — 你既渴望靠近又害怕靠近，两种恐惧同时存在"
        elif attach == "fearful":
            return "被摧毁 — 你觉得爱到最深处一定会受伤"
        return "不被看见 — 你怕的是真实的自己不值得被爱"

    def _infer_authentic_strength(self, signals, deep_items) -> str:
        attach = signals.get("attachment_style", "")
        if attach == "anxious":
            return "你爱得比大多数人都深。这不是弱点，这是天赋。你需要的不是少爱一点，是找到一个配得上这份深度的人。"
        elif attach == "avoidant":
            return "你有极强的自我。在关系里不迷失自己是很多人做不到的。你需要的不是打开城墙，是在城墙里开一扇门。"
        elif attach == "disorganized":
            return "你同时理解爱的光明和黑暗面。这种深度让你能真正理解另一个人。你需要的不是变得简单，是找到一个能承接你复杂性的人。"
        # Default: look at deep items for clues
        for item in deep_items:
            if item.emotional_valence == "positive":
                return f"你的Soul里有这个: '{item.text[:60]}' — 这说明你知道什么是真正的连接。"
        return "你对爱是认真的。这本身就是你最大的优势。"

    def _infer_repeated_cycle(self, patterns) -> str:
        if not patterns:
            return ""
        ids = [p.pattern_id for p in patterns]
        if "attracted_to_unavailable" in ids and "love_bomber" in ids:
            return "追 → 得到 → 窒息 → 被甩 → 再追。你在用力证明自己值得被爱，但越用力越把人推远。"
        if "performer" in ids and "ghost" in ids:
            return "表演 → 疲惫 → 消失 → 孤独 → 重新表演。你在面具和逃跑之间循环。"
        if "fear_of_rejection" in ids and "serial_dater" in ids:
            return "观望 → 终于开始 → 发现不完美 → 离开。你在用'挑剔'代替'勇敢'。"
        if "attracted_to_unavailable" in ids:
            return "喜欢 → 追 → 对方不回应 → 更喜欢 → 受伤。你把得不到当成了值得追。"
        if "ghost" in ids:
            return "靠近 → 感觉太多 → 逃跑 → 后悔 → 但已经太晚了。你在逃避你最想要的东西。"
        return f"你的{patterns[0].label}模式在重复。每段关系看起来不同，但脚本是一样的。"

    def _find_soul_resource(self, deep, memory) -> str:
        for item in deep + (memory or []):
            if item.emotional_valence == "positive" and item.activation < 0.3:
                return item.text
        for item in deep:
            if item.emotional_valence == "positive":
                return item.text
        return ""


# ---------------------------------------------------------------------------
# Dating Engine — runs coaching dialogue
# ---------------------------------------------------------------------------

@dataclass
class DatingTurn:
    """One exchange in a dating coaching session."""
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class DatingSession:
    """Complete dating coaching session."""
    client_id: str
    insight: DatingInsight | None = None
    turns: list[DatingTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)

    @property
    def pattern_recognized(self) -> bool:
        """Did the client recognize at least one pattern?"""
        return self.insights_gained >= 2 and any(
            t.client_resistance <= 0.3 and t.client_insight for t in self.turns[-3:]
        ) if self.turns else False


class DatingEngine:
    """Runs dating coaching sessions.

    Key difference from other engines:
    - Therapy: reduce pain
    - Growth: amplify potential
    - Relationship: reveal relational pattern
    - Dating: reveal ROMANTIC pattern + show authentic path to connection

    Tone: friend-like, direct, sometimes funny. Not clinical.
    "你又喜欢上一个不回消息的人了？让我猜猜为什么..."
    """

    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._session_engine = session_engine
        self._patient = patient_simulator
        self._detector = DatingPatternDetector()
        self._persuasion = PersuasionPlanner()
        self._tone = ToneAdapter()

    def run(
        self,
        client_profile: PatientProfile,
        signals: dict,
        focus_items: list[SoulItem],
        deep_items: list[SoulItem],
        memory_items: list[SoulItem] | None = None,
        num_turns: int = 5,
    ) -> DatingSession:
        """Run a dating coaching session."""
        num_turns = min(num_turns, 15)
        t0 = time.time()

        # Step 1: Detect dating patterns
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)

        session = DatingSession(client_id=client_profile.character_id, insight=insight)

        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        # Step 2: Generate persuasion strategy
        strategy = self._persuasion.plan(
            focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see your {insight.patterns[0].label} pattern clearly",
            memory_items=memory_items,
        )

        # Step 3: Build dating coach context
        pattern_section = "\n".join(
            f"- PATTERN: {p.label} — {p.description[:100]}\n"
            f"  Root cause: {p.root_cause[:100]}\n"
            f"  Blind spot: {p.blind_spot[:100]}\n"
            f"  Reframe: {p.reframe[:100]}\n"
            f"  First step: {p.first_step[:100]}"
            for p in insight.patterns[:2]
        )

        cycle_section = f"\nREPEATED CYCLE: {insight.repeated_cycle}" if insight.repeated_cycle else ""

        coach_context = (
            f"{client_profile.soul_context}\n\n"
            f"DATING PATTERNS DETECTED:\n{pattern_section}\n"
            f"CORE FEAR: {insight.core_fear}\n"
            f"AUTHENTIC STRENGTH: {insight.authentic_strength}"
            f"{cycle_section}\n\n"
            f"SOUL RESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION:\n"
            f"  Deep need: {strategy.deep_need}\n"
            f"  USE: {', '.join(strategy.use_words[:5])}\n"
            f"  AVOID: {', '.join(strategy.avoid_words[:5])}\n\n"
            f"YOUR APPROACH: Dating coach. Friend-like, direct, sometimes funny.\n"
            f"1. Talk like a smart friend, NOT a therapist. '你又来了...' not '我注意到一个模式...'\n"
            f"2. Use their own words and Soul evidence to show the pattern\n"
            f"3. Core message: '你已经知道怎么吸引对的人了 — Soul 里有证据'\n"
            f"4. Reframe: it's not about learning tricks, it's about being authentically YOU\n"
            f"5. End with ONE concrete step — not advice, a challenge\n"
            f"NEVER be preachy. NEVER list rules. Think 'cool older sibling' not 'relationship therapist'."
        )

        # Adapt tone: dating coach is casual, warm, slightly provocative
        tone = self._tone.adapt(signals=signals, technique_family="relationship")
        tone.dos = [
            "Be a friend who happens to see patterns clearly — warm, direct, occasionally funny",
            "Use their language and cultural references",
            "Challenge them gently — 'are you sure about that?'",
            "Mix Chinese and English naturally if they do",
        ] + tone.dos[:2]
        tone.donts = [
            "NEVER sound clinical or therapeutic — no '我注意到' or 'pattern' language",
            "NEVER give generic dating advice — everything must come from THEIR Soul",
            "NEVER blame their exes or past partners",
        ] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        conversation_history: list[dict] = []
        current_pattern_idx = 0

        for turn_num in range(1, num_turns + 1):
            current_pattern = insight.patterns[min(current_pattern_idx, len(insight.patterns) - 1)]

            # Build plan
            if turn_num == 1:
                plan_text = (
                    f"TECHNIQUE: Dating Coach — Pattern Discovery\n"
                    f"GOAL: introduce | DEPTH: surface | PACING: casual\n"
                    f"FOCUS: Start with their dating complaint. Listen. Then drop a teaser: "
                    f"'有意思... 你有没有注意到你每次喜欢的人都有一个共同点？' "
                    f"Plant the seed of {current_pattern.label} without naming it. Be curious, not diagnostic."
                )
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                current_pattern_idx = min(current_pattern_idx + 1, len(insight.patterns) - 1)
                current_pattern = insight.patterns[current_pattern_idx]
                plan_text = (
                    f"TECHNIQUE: Dating Coach — Pivot\n"
                    f"GOAL: build_rapport | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: They're defensive. Back off and be lighter. "
                    f"Ask about a time they felt truly connected to someone — a good memory. "
                    f"Then approach {current_pattern.label} from the positive side."
                )
            elif session.turns and session.turns[-1].client_insight:
                plan_text = (
                    f"TECHNIQUE: Dating Coach — Reframe\n"
                    f"GOAL: deepen | DEPTH: deep | PACING: push\n"
                    f"FOCUS: They see the pattern! Now reframe: '{current_pattern.reframe[:80]}'. "
                    f"Core message: the problem isn't that you can't love — your Soul proves you CAN. "
                    f"The problem is what you DO with that love. Challenge: '{current_pattern.first_step[:80]}'"
                )
            else:
                plan_text = (
                    f"TECHNIQUE: Dating Coach — Reveal\n"
                    f"GOAL: deepen | DEPTH: medium | PACING: normal\n"
                    f"FOCUS: Show the pattern using their own evidence: "
                    f"'{current_pattern.blind_spot[:80]}'. "
                    f"Don't lecture — ask a question that makes them see it themselves."
                )

            # Build context
            context_lines = [f"{'Coach' if e['role'] == 'therapist' else 'Client'}: {e['content'][:200]}"
                           for e in conversation_history[-4:]]
            context = "\n".join(context_lines)

            # Generate coach reply
            coach_resp = self._session_engine.generate_reply(
                plan_text=plan_text, tone_text=tone_text,
                context=context, soul_context=coach_context,
            )

            conversation_history.append({"role": "therapist", "content": coach_resp.reply_text})

            # Client responds
            client_resp = self._patient.respond(
                profile=client_profile,
                therapist_message=coach_resp.reply_text,
                conversation_history=conversation_history[:-1],
            )

            conversation_history.append({"role": "patient", "content": client_resp.text})

            session.turns.append(DatingTurn(
                turn_number=turn_num,
                coach_text=coach_resp.reply_text,
                client_text=client_resp.text,
                client_internal_state=client_resp.internal_state,
                client_resistance=client_resp.resistance_level,
                client_resistance_reason=client_resp.resistance_reason,
                client_insight=client_resp.insight_gained,
                pattern_addressed=current_pattern.label,
            ))


        session.total_time_seconds = time.time() - t0
        return session
