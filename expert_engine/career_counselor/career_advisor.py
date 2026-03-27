"""Career Advisor — reveals career patterns from Soul and coaches toward true calling.

Core principle: "你每天下班后做的那件事 — 那才是你的真正职业"
(What you do AFTER work is your real calling)

Not about resume tips or interview skills. About understanding what your Soul
already knows about your true path.

Pipeline: CareerPatternDetector (zero LLM) -> CareerEngine (1x Sonnet per turn)
Communication style: wise mentor, direct, sometimes provocative. Not HR.
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
# Career Pattern Detector — zero LLM, rule-based from Soul signals
# ---------------------------------------------------------------------------

@dataclass
class CareerPattern:
    """A career pattern detected from Soul."""
    pattern_id: str
    label: str  # human-readable name
    description: str  # what this pattern looks like
    root_cause: str  # why they're stuck (from Soul)
    soul_evidence: list[str]  # quotes from Soul items
    blind_spot: str  # what they can't see about themselves
    reframe: str  # the "你已经知道了" reframe
    first_step: str  # one concrete thing to try


@dataclass
class CareerInsight:
    """Complete career pattern analysis."""
    patterns: list[CareerPattern] = field(default_factory=list)
    core_block: str = ""  # the ONE thing keeping them stuck
    hidden_strength: str = ""  # what they don't realize they're good at
    after_hours_clue: str = ""  # what they do after work = real calling
    soul_resource: str = ""  # positive evidence from Soul for making the leap


# Pattern definitions — each maps to a real career dysfunction
_CAREER_PATTERNS = [
    {
        "id": "hidden_passion",
        "label": "隐藏的热情",
        "triggers": {
            "keywords_focus": ["after work", "hobby", "dream", "wish", "free time",
                               "下班后", "业余", "梦想", "爱好", "空闲", "读书",
                               "画", "写", "做", "学", "练"],
            "keywords_deep": ["talent", "gift", "natural", "born to", "always loved",
                              "天赋", "从小", "一直", "天生", "别人说我"],
        },
        "description": "You have something you do for free that could be a career. You dismiss it as 'just a hobby' because making money from passion feels too good to be true.",
        "root_cause": "You were taught that work = suffering and passion = irresponsible. So you split yourself: the daytime worker and the nighttime dreamer. But the nighttime version is the real you.",
        "blind_spot": "你以为你的爱好'不实际' — 但你每天下班后做的那件事，就是你的真正职业。[soul_evidence] 已经证明了。",
        "reframe": "你已经在做你的真正职业了 — 只是没有人付你钱而已。[soul_evidence] 说明你的能力是真的。问题不是'能不能'，是'敢不敢'。",
        "first_step": "这周用你的'爱好'帮一个人解决一个真实问题。免费的。当你看到对方的反应，你就知道这不只是爱好了。",
    },
    {
        "id": "golden_cage",
        "label": "金笼子",
        "triggers": {
            "keywords_focus": ["hate my job", "salary", "money", "trapped", "golden handcuffs",
                               "讨厌工作", "工资", "钱", "困住", "不想干", "高薪",
                               "浪费", "才华", "委屈"],
            "keywords_deep": ["used to love", "passion died", "sell out", "compromise",
                              "曾经", "热爱", "放弃", "妥协", "为了钱"],
        },
        "description": "You're earning good money doing something that's killing your soul. You can't leave because the lifestyle depends on the salary. You're a prisoner with a nice cell.",
        "root_cause": "At some point you traded meaning for security. Maybe it was a rational choice then. But the cost compounds: every year in the cage, the real you gets smaller.",
        "blind_spot": "你以为离开意味着从零开始。其实你在笼子里积累的能力 — [soul_evidence] — 在外面更值钱。你害怕的不是贫穷，是未知。",
        "reframe": "你的才华不属于这个笼子 — [soul_evidence] 就是证据。你不需要辞职，你需要一个Plan B，然后让Plan B长大到替代Plan A。",
        "first_step": "算一笔账：你的'最低生存线'是多少？大多数人以为自己需要的钱是实际需要的3倍。那个真实的数字会让你自由很多。",
    },
    {
        "id": "imposter",
        "label": "冒充者",
        "triggers": {
            "keywords_focus": ["fraud", "imposter", "don't deserve", "luck", "found out",
                               "冒充", "不配", "运气", "被发现", "不够好",
                               "别人比我强", "假装"],
            "keywords_deep": ["actually good", "people say", "achieved", "built",
                              "其实", "别人说", "做到了", "成就", "成功"],
        },
        "description": "You're competent — maybe even brilliant — but you don't believe it. Every achievement feels like luck. Every praise feels undeserved. You're waiting to be 'found out.'",
        "root_cause": "Someone taught you that confidence = arrogance. So you discount your wins and amplify your gaps. The irony: the fact that you worry about being a fraud is proof you're not one. Real frauds don't worry.",
        "blind_spot": "你觉得自己是冒充的 — 但看看你的Soul: [soul_evidence]。这些不是运气，这是实力。你不是在假装 — 你是在否认自己的真实水平。",
        "reframe": "你不需要更多证据证明自己行 — [soul_evidence] 已经够了。你需要的是允许自己相信这些证据。",
        "first_step": "写下你做过的三件'别人做不到但你觉得没什么'的事。问三个信任的人：'你觉得我擅长什么？'他们的答案会让你震惊。",
    },
    {
        "id": "passion_died",
        "label": "热情已死",
        "triggers": {
            "keywords_focus": ["burnout", "exhausted", "used to love", "don't care", "numb",
                               "倦怠", "疲惫", "曾经热爱", "不在乎", "麻木",
                               "没意思", "提不起劲"],
            "keywords_deep": ["remember when", "first day", "why I started", "young",
                              "记得", "第一天", "为什么开始", "年轻时", "刚入行"],
        },
        "description": "You used to love this work. Now you feel nothing. The fire went out and you don't know how to relight it. You wonder if you chose wrong, but really the job changed — or you grew past it.",
        "root_cause": "Burnout isn't about working too hard — it's about working without meaning. The passion didn't die randomly; something specific killed it: a bad boss, a broken promise, the system grinding you down.",
        "blind_spot": "你以为热情死了就回不来了。其实热情不会消失 — 它只是被埋住了。[soul_evidence] 说明火种还在。你需要找到埋住它的那块石头，然后搬开。",
        "reframe": "你曾经热爱这件事 — [soul_evidence] 就是证据。你不需要找新的热情，你需要找到杀死旧热情的那个人或那件事，然后跟它告别。",
        "first_step": "回想你最后一次对工作感到兴奋是什么时候。那个时刻之后发生了什么？那就是你需要解决的问题 — 不是职业问题，是那个具体的事件。",
    },
    {
        "id": "never_chose",
        "label": "从未选择",
        "triggers": {
            "keywords_focus": ["fell into", "parents wanted", "expected", "didn't choose",
                               "family pressure", "accident",
                               "稀里糊涂", "父母要我", "期望", "没选过",
                               "家里安排", "不知道怎么就", "从来没有"],
            "keywords_deep": ["my own", "want to", "if I could", "real me",
                              "我自己", "想要", "如果可以", "真正的我", "做主"],
        },
        "description": "You never chose your career — it was chosen for you by family, circumstance, or inertia. You went along because you didn't know what you wanted. Now you do, but it feels too late.",
        "root_cause": "You were trained to be obedient, not autonomous. Choosing for yourself feels selfish or scary. But the cost of not choosing is living someone else's life.",
        "blind_spot": "你以为你'不知道自己想要什么' — 但你的Soul说得很清楚: [soul_evidence]。你不是没有方向，你是没有允许自己有方向。",
        "reframe": "你其实一直知道自己想要什么 — [soul_evidence] 就是证据。你缺的不是方向，是许可。现在我给你许可: 你有权利选择自己的人生。",
        "first_step": "完成这个句子：'如果没有任何人的期望，我明天想做的是____。'写下来。不要修改。那就是你的方向。",
    },
    {
        "id": "fear_of_leap",
        "label": "不敢跳",
        "triggers": {
            "keywords_focus": ["afraid", "risk", "what if", "fail", "too late", "age",
                               "害怕", "风险", "万一", "失败", "太晚", "年纪",
                               "不敢", "家庭责任", "房贷"],
            "keywords_deep": ["know what I want", "plan", "dream", "ready",
                              "知道想要", "计划", "准备好了", "一直想"],
        },
        "description": "You know exactly what you want to do. You've researched it. Maybe even made plans. But you can't pull the trigger. Fear of failure, financial risk, age, family responsibilities — the reasons are real but they're also excuses.",
        "root_cause": "The leap isn't the scary part — it's the identity change. Jumping means admitting you spent years on the wrong path. That's not failure, that's growth. But it doesn't feel that way.",
        "blind_spot": "你列了一百个不能跳的理由，但你没注意到: 你已经在准备了。[soul_evidence] 说明你的Soul已经做好了决定 — 只有你的大脑还在犹豫。",
        "reframe": "你不是不敢跳 — 你是已经在半空中了。[soul_evidence] 说明你早就开始了。你需要的不是勇气，是承认自己已经很勇敢了。",
        "first_step": "不要辞职。做一个最小可行实验: 用一个周末做你梦想中的工作。如果那个周末比你的一周五天都充实 — 你就有了答案。",
    },
]


class CareerPatternDetector:
    """Detects career patterns from Soul signals — zero LLM.

    Usage:
        detector = CareerPatternDetector()
        insight = detector.analyze(
            signals={"career_satisfaction": "low", ...},
            focus_items=[SoulItem(text="I hate my job", ...)],
            deep_items=[SoulItem(text="I used to paint every day", ...)],
        )
    """

    def analyze(
        self,
        signals: dict,
        focus_items: list[SoulItem] | None = None,
        deep_items: list[SoulItem] | None = None,
        memory_items: list[SoulItem] | None = None,
    ) -> CareerInsight:
        """Analyze one person's Soul for career patterns."""
        focus = focus_items or []
        deep = deep_items or []
        memory = memory_items or []

        patterns = self._detect_patterns(signals, focus, deep, memory)
        core_block = self._infer_core_block(patterns, signals)
        strength = self._infer_hidden_strength(deep, memory)
        after_hours = self._find_after_hours_clue(focus, deep, memory)
        resource = self._find_soul_resource(deep, memory)

        return CareerInsight(
            patterns=patterns,
            core_block=core_block,
            hidden_strength=strength,
            after_hours_clue=after_hours,
            soul_resource=resource,
        )

    def _detect_patterns(self, signals, focus, deep, memory) -> list[CareerPattern]:
        """Match Soul signals to career patterns via keyword matching."""
        detected = []
        all_items = focus + deep + memory

        focus_text = " ".join(item.text.lower() for item in focus)
        deep_text = " ".join(item.text.lower() for item in deep + memory)

        for p in _CAREER_PATTERNS:
            score = 0

            # Check focus keywords
            for kw in p["triggers"]["keywords_focus"]:
                if kw.lower() in focus_text:
                    score += 1
                    if score >= 2:
                        break

            # Check deep keywords
            for kw in p["triggers"]["keywords_deep"]:
                if kw.lower() in deep_text:
                    score += 1
                    if score >= 3:
                        break

            # Also check explicit signal flags
            if signals.get("career_pattern") == p["id"]:
                score += 3
            if signals.get("career_satisfaction") == "low" and p["id"] in ("golden_cage", "passion_died", "never_chose"):
                score += 1
            if signals.get("career_clarity") == "low" and p["id"] in ("never_chose", "fear_of_leap", "hidden_passion"):
                score += 1

            if score >= 2:
                # Find Soul evidence
                evidence = []
                for item in all_items:
                    if item.activation >= 0.3 or item.emotional_valence in ("negative", "extreme"):
                        evidence.append(item.text[:80])
                    if len(evidence) >= 2:
                        break

                # Find positive resource for reframe
                resource = ""
                for item in deep + memory:
                    if item.emotional_valence == "positive":
                        resource = item.text[:80]
                        break

                reframe = p["reframe"].replace("[soul_evidence]", resource or "your past experiences")
                blind_spot = p["blind_spot"].replace("[soul_evidence]", resource or "your past")

                detected.append(CareerPattern(
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

    def _infer_core_block(self, patterns: list[CareerPattern], signals: dict) -> str:
        if not patterns:
            return "不确定 — 需要更多信息"
        pid = patterns[0].pattern_id
        blocks = {
            "hidden_passion": "你不相信热爱的事情能养活你 — 所以你把它藏在下班后",
            "golden_cage": "你用薪水衡量人生 — 但你的Soul在用意义衡量",
            "imposter": "你不相信自己的能力是真的 — 每一次成功都被你标记为'运气'",
            "passion_died": "某个人或某件事杀死了你的热情 — 但你以为是你自己变了",
            "never_chose": "你从来没有允许自己选择 — 因为选择意味着可能让别人失望",
            "fear_of_leap": "你什么都准备好了，除了允许自己出发",
        }
        return blocks.get(pid, patterns[0].root_cause[:100])

    def _infer_hidden_strength(self, deep: list[SoulItem], memory: list[SoulItem]) -> str:
        for item in deep + memory:
            if item.emotional_valence == "positive" and any(
                t in (item.tags or []) for t in ("talent", "strength", "skill", "gift")
            ):
                return f"你的Soul里藏着这个: '{item.text[:60]}' — 这不是爱好，这是天赋。"
        for item in deep + memory:
            if item.emotional_valence == "positive":
                return f"你的Soul说: '{item.text[:60]}' — 这里有你还没发现的能力。"
        return "你的能力比你相信的要多。你只是还没把它们放在一起看过。"

    def _find_after_hours_clue(self, focus, deep, memory) -> str:
        """The 'after work' thing = real calling clue."""
        all_items = focus + deep + memory
        clue_keywords = [
            "after work", "hobby", "free time", "weekend", "passion",
            "下班后", "业余", "空闲", "周末", "热爱",
            "读书", "画", "写", "做", "学", "练", "跑",
        ]
        for item in all_items:
            text_lower = item.text.lower()
            for kw in clue_keywords:
                if kw in text_lower:
                    return item.text[:100]
        return ""

    def _find_soul_resource(self, deep, memory) -> str:
        for item in deep + memory:
            if item.emotional_valence == "positive" and item.activation < 0.3:
                return item.text
        for item in deep:
            if item.emotional_valence == "positive":
                return item.text
        return ""


# ---------------------------------------------------------------------------
# Career Engine — runs coaching dialogue
# ---------------------------------------------------------------------------

@dataclass
class CareerTurn:
    """One exchange in a career coaching session."""
    turn_number: int
    coach_text: str
    client_text: str
    client_internal_state: str
    client_resistance: float
    client_resistance_reason: str
    client_insight: bool
    pattern_addressed: str


@dataclass
class CareerSession:
    """Complete career coaching session."""
    client_id: str
    insight: CareerInsight | None = None
    turns: list[CareerTurn] = field(default_factory=list)
    total_time_seconds: float = 0.0

    @property
    def insights_gained(self) -> int:
        return sum(1 for t in self.turns if t.client_insight)

    @property
    def clarity_achieved(self) -> bool:
        """Did the client gain clarity about their career direction?"""
        return self.insights_gained >= 2 and any(
            t.client_resistance <= 0.3 and t.client_insight for t in self.turns[-3:]
        ) if self.turns else False


class CareerEngine:
    """Runs career coaching sessions.

    Key difference from other engines:
    - Therapy: reduce pain
    - Growth: amplify potential
    - Dating: reveal romantic pattern
    - Career: reveal CALLING + show path from where you are to where you belong

    Tone: wise mentor, direct, sometimes provocative. Not HR.
    "你每天下班后做的那件事 — 那才是你的真正职业"
    """

    def __init__(self, session_engine: SessionEngine, patient_simulator: PatientSimulator):
        self._session_engine = session_engine
        self._patient = patient_simulator
        self._detector = CareerPatternDetector()
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
    ) -> CareerSession:
        """Run a career coaching session."""
        num_turns = min(num_turns, 15)
        t0 = time.time()

        # Step 1: Detect career patterns
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)

        session = CareerSession(client_id=client_profile.character_id, insight=insight)

        if not insight.patterns:
            session.total_time_seconds = time.time() - t0
            return session

        # Step 2: Generate persuasion strategy
        strategy = self._persuasion.plan(
            focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see your {insight.patterns[0].label} pattern and find your true calling",
            memory_items=memory_items,
        )

        # Step 3: Build career coach context
        pattern_section = "\n".join(
            f"- PATTERN: {p.label} — {p.description[:100]}\n"
            f"  Root cause: {p.root_cause[:100]}\n"
            f"  Blind spot: {p.blind_spot[:100]}\n"
            f"  Reframe: {p.reframe[:100]}\n"
            f"  First step: {p.first_step[:100]}"
            for p in insight.patterns[:2]
        )

        after_hours = f"\nAFTER-HOURS CLUE: {insight.after_hours_clue}" if insight.after_hours_clue else ""

        coach_context = (
            f"{client_profile.soul_context}\n\n"
            f"CAREER PATTERNS DETECTED:\n{pattern_section}\n"
            f"CORE BLOCK: {insight.core_block}\n"
            f"HIDDEN STRENGTH: {insight.hidden_strength}"
            f"{after_hours}\n\n"
            f"SOUL RESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION:\n"
            f"  Deep need: {strategy.deep_need}\n"
            f"  USE: {', '.join(strategy.use_words[:5])}\n"
            f"  AVOID: {', '.join(strategy.avoid_words[:5])}\n\n"
            f"YOUR APPROACH: Career counselor. Wise mentor, direct, sometimes provocative.\n"
            f"1. Core principle: '你每天下班后做的那件事 — 那才是你的真正职业'\n"
            f"2. Use their Soul evidence to show they ALREADY know what they want\n"
            f"3. Don't give career advice — help them SEE what's already in their Soul\n"
            f"4. Challenge limiting beliefs: 'too late', 'too risky', 'not practical'\n"
            f"5. End with ONE concrete micro-experiment, not a life plan\n"
            f"NEVER be preachy. NEVER list steps. Think 'wise uncle/mentor' not 'career counselor'."
        )

        # Adapt tone
        tone = self._tone.adapt(signals=signals, technique_family="career")
        tone.dos = [
            "Be a wise mentor who sees their potential before they do — warm, direct, occasionally provocative",
            "Use their own Soul evidence and language",
            "Challenge gently: 'you already know the answer, don't you?'",
            "Mix Chinese and English naturally if they do",
        ] + tone.dos[:2]
        tone.donts = [
            "NEVER sound like HR or a career consultant — no 'SWOT analysis' or 'networking strategies'",
            "NEVER give generic career advice — everything must come from THEIR Soul",
            "NEVER dismiss their fears as irrational — acknowledge and then reframe",
        ] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        conversation_history: list[dict] = []
        current_pattern_idx = 0

        for turn_num in range(1, num_turns + 1):
            current_pattern = insight.patterns[min(current_pattern_idx, len(insight.patterns) - 1)]

            # Build plan
            if turn_num == 1:
                plan_text = (
                    f"TECHNIQUE: Career Counselor — Discovery\n"
                    f"GOAL: introduce | DEPTH: surface | PACING: casual\n"
                    f"FOCUS: Start with their career frustration. Listen. Then drop a teaser: "
                    f"'你有没有注意到，你说起你的工作用的是'应该'，但说起[after_hours_clue]的时候用的是'想要'？' "
                    f"Plant the seed of {current_pattern.label}. Be curious, not diagnostic."
                )
            elif session.turns and session.turns[-1].client_resistance >= 0.6:
                current_pattern_idx = min(current_pattern_idx + 1, len(insight.patterns) - 1)
                current_pattern = insight.patterns[current_pattern_idx]
                plan_text = (
                    f"TECHNIQUE: Career Counselor — Pivot\n"
                    f"GOAL: build_rapport | DEPTH: surface | PACING: slow\n"
                    f"FOCUS: They're defensive. Back off and be lighter. "
                    f"Ask about a time they felt truly alive at work — or anywhere. "
                    f"Then approach {current_pattern.label} from the positive side."
                )
            elif session.turns and session.turns[-1].client_insight:
                plan_text = (
                    f"TECHNIQUE: Career Counselor — Reframe\n"
                    f"GOAL: deepen | DEPTH: deep | PACING: push\n"
                    f"FOCUS: They see it! Now reframe: '{current_pattern.reframe[:80]}'. "
                    f"Core message: your Soul already chose — you just haven't caught up yet. "
                    f"Challenge: '{current_pattern.first_step[:80]}'"
                )
            else:
                plan_text = (
                    f"TECHNIQUE: Career Counselor — Reveal\n"
                    f"GOAL: deepen | DEPTH: medium | PACING: normal\n"
                    f"FOCUS: Show the pattern using their own evidence: "
                    f"'{current_pattern.blind_spot[:80]}'. "
                    f"Don't lecture — ask a question that makes them see it themselves."
                )

            # Build context
            context_lines = [f"{'Counselor' if e['role'] == 'therapist' else 'Client'}: {e['content'][:200]}"
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

            session.turns.append(CareerTurn(
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

    def respond(
        self,
        client_message: str,
        signals: dict,
        focus_items: list[SoulItem],
        deep_items: list[SoulItem],
        memory_items: list[SoulItem] | None = None,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        """Single-turn career coaching response for real-time dialogue. 1 LLM call.

        Same pipeline as run() but accepts a real client's message instead of
        invoking the patient simulator. No simulation involved.

        Args:
            client_message: The real client's message.
            signals: Detector signals for career pattern detection.
            focus_items: Soul Focus items.
            deep_items: Soul Deep items.
            memory_items: Soul Memory items.
            conversation_history: Previous exchanges as
                [{"role": "coach"|"client", "content": "..."}].

        Returns:
            {"reply": str, "patterns_detected": list[str], "progress_note": str}
        """
        history = conversation_history or []

        # Detect career patterns (0 LLM)
        insight = self._detector.analyze(signals, focus_items, deep_items, memory_items)

        if not insight.patterns:
            return {"reply": "", "patterns_detected": [], "progress_note": "No career patterns detected."}

        # Build persuasion strategy (0 LLM)
        strategy = self._persuasion.plan(
            focus_items=focus_items, deep_items=deep_items,
            target_suggestion=f"see your {insight.patterns[0].label} pattern and find your true calling",
            memory_items=memory_items,
        )

        # Build coach context
        pattern_section = "\n".join(
            f"- PATTERN: {p.label} — {p.description[:100]}\n"
            f"  Root cause: {p.root_cause[:100]}\n"
            f"  Blind spot: {p.blind_spot[:100]}\n"
            f"  Reframe: {p.reframe[:100]}\n"
            f"  First step: {p.first_step[:100]}"
            for p in insight.patterns[:2]
        )
        after_hours = f"\nAFTER-HOURS CLUE: {insight.after_hours_clue}" if insight.after_hours_clue else ""

        coach_context = (
            f"CAREER PATTERNS DETECTED:\n{pattern_section}\n"
            f"CORE BLOCK: {insight.core_block}\n"
            f"HIDDEN STRENGTH: {insight.hidden_strength}"
            f"{after_hours}\n\n"
            f"SOUL RESOURCE: {insight.soul_resource}\n\n"
            f"PERSUASION:\n"
            f"  Deep need: {strategy.deep_need}\n"
            f"  USE: {', '.join(strategy.use_words[:5])}\n"
            f"  AVOID: {', '.join(strategy.avoid_words[:5])}\n\n"
            f"YOUR APPROACH: Career counselor. Wise mentor, direct, sometimes provocative.\n"
            f"1. Use their Soul evidence to show they ALREADY know what they want\n"
            f"2. Challenge limiting beliefs gently\n"
            f"3. End with ONE concrete micro-experiment"
        )

        # Adapt tone (0 LLM)
        tone = self._tone.adapt(signals=signals, technique_family="career")
        tone.dos = [
            "Be a wise mentor — warm, direct, occasionally provocative",
            "Use their own Soul evidence and language",
            "Challenge gently: 'you already know the answer, don't you?'",
        ] + tone.dos[:2]
        tone.donts = [
            "NEVER sound like HR or a career consultant",
            "NEVER give generic career advice",
        ] + tone.donts[:2]
        tone_text = tone.to_prompt_lines()

        # Build plan
        turn_number = len([h for h in history if h.get("role") == "client"]) + 1
        current_pattern = insight.patterns[0]
        plan_text = (
            f"TECHNIQUE: Career Counselor — Discovery\n"
            f"GOAL: {'introduce' if turn_number == 1 else 'deepen'} | "
            f"DEPTH: {'surface' if turn_number == 1 else 'medium'} | "
            f"PACING: {'casual' if turn_number == 1 else 'normal'}\n"
            f"FOCUS: Help them see the {current_pattern.label} pattern using their own evidence."
        )

        # Build context from history + current message
        mapped_history = []
        for e in history:
            role = "therapist" if e.get("role") == "coach" else "patient"
            mapped_history.append({"role": role, "content": e.get("content", "")})
        mapped_history.append({"role": "patient", "content": client_message})

        context_lines = [
            f"{'Counselor' if e['role'] == 'therapist' else 'Client'}: {e['content'][:200]}"
            for e in mapped_history[-4:]
        ]
        context = "\n".join(context_lines)

        # Generate reply (1 LLM call)
        resp = self._session_engine.generate_reply(
            plan_text=plan_text, tone_text=tone_text,
            context=context, soul_context=coach_context,
        )

        return {
            "reply": resp.reply_text,
            "patterns_detected": [p.label for p in insight.patterns],
            "progress_note": resp.progress_note,
        }
