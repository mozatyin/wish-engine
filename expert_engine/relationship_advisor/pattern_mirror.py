"""Pattern Mirror — reveals hidden relationship patterns from one person's Soul.

Not analyzing the other person. Only showing THIS person what THEIR Soul reveals
about how they relate, what they repeat, and what they actually need.

Zero LLM. Rule-based pattern detection from Soul items.

Key insight: people's relationship complaints about others are usually
projections of their own unmet needs or repeated patterns from childhood.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from expert_engine.goal_generator import SoulItem


@dataclass
class RelationshipPattern:
    """A relationship pattern — named as a STRENGTH, not a dysfunction."""
    pattern_name: str  # "deep_reader", "all_in_lover" — positive capability name
    capability: str  # The hidden strength this pattern reveals
    description: str  # The gift + its shadow side
    origin: str  # Where it comes from
    current_manifestation: str  # How it shows up NOW
    soul_evidence: list[str]  # Quotes from Soul items
    blind_spot: str  # What they can't see
    reframe: str  # The "you already are" reframe
    action_step: str  # Concrete thing to do THIS WEEK


@dataclass
class RelationshipInsight:
    """Complete relationship self-insight report."""
    patterns: list[RelationshipPattern] = field(default_factory=list)
    core_need: str = ""  # The ONE thing they actually need (not what they say)
    giving_style: str = ""  # How they express love
    receiving_need: str = ""  # How they need to receive love
    mismatch: str = ""  # The gap between giving and needing
    soul_resource: str = ""  # The positive evidence in Soul for resolution


# Pattern detection rules
# Each pattern is STRENGTH-BASED: names the hidden capability, not the dysfunction.
# Includes concrete action_step for immediate behavior change.
_PATTERNS = [
    {
        "name": "deep_reader",  # was: waiting_to_be_asked
        "triggers": {
            "attachment": ["anxious"],
            "connection": ["toward"],
            "conflict": ["accommodate", "avoid"],
        },
        "capability": "You read people's emotions better than anyone. You know exactly what others need — sometimes before they know it themselves.",
        "description": "Your gift is emotional attunement. The shadow side: you wait for others to read YOU the way you read them.",
        "blind_spot": "You're waiting to be seen the way you see others. But your superpower works outward, not inward — people can't read you back because you never show them how.",
        "reframe": "You already know how to connect — [soul_evidence] proves it. The gap isn't your ability to love. It's that you haven't said 'this is what I need' out loud.",
        "action_step": "This week: ONE time, tell someone exactly what you need. Not hint. Say: 'I need you to ask me how my day was.' Watch what happens.",
    },
    {
        "name": "all_in_lover",  # was: pursuit_withdrawal
        "triggers": {
            "attachment": ["anxious"],
            "connection": ["toward"],
            "conflict": ["escalating", "compete"],
        },
        "capability": "You love with your entire being. When you're in, you're ALL in. This intensity is rare and beautiful.",
        "description": "Your gift is total devotion. The shadow side: your intensity can overwhelm the other person, and their retreat feels like death.",
        "blind_spot": "Your love isn't the problem. The VOLUME is. You're playing a symphony in a room built for a whisper. Your Soul shows you can also love quietly — [soul_evidence].",
        "reframe": "You already know how to love gently — you did it with [soul_evidence]. The question isn't whether to love less, but whether you can trust that quiet love still counts.",
        "action_step": "This week: when you want to text them, wait 10 minutes. Not to play games — to let your love find a gentler volume. Notice: does the urge change shape?",
    },
    {
        "name": "natural_healer",  # was: caretaker_trap
        "triggers": {
            "attachment": ["anxious", "secure"],
            "conflict": ["accommodate"],
            "values": ["benevolence"],
        },
        "capability": "You have an extraordinary gift for nurturing. People feel safe around you because your care is genuine, not performed.",
        "description": "Your gift is deep care. The shadow side: you give so much that you forget to receive, and the resentment builds silently.",
        "blind_spot": "You give love the way you needed it as a child. That's not a flaw — it's wisdom. But the other person might need something completely different.",
        "reframe": "Your care is real. But care without receiving becomes a one-way door. Your Soul shows you once let someone care for YOU — [soul_evidence]. That felt different, didn't it?",
        "action_step": "This week: when someone offers help, say YES instead of 'I'm fine.' Just once. Let them give to you the way you give to them.",
    },
    {
        "name": "self_sovereign",  # was: avoidant_fortress
        "triggers": {
            "attachment": ["avoidant"],
            "connection": ["away"],
            "fragility": ["masked", "avoidant"],
        },
        "capability": "You have an unshakeable inner core. You can stand alone when others crumble. This self-sufficiency is genuine strength.",
        "description": "Your gift is independence. The shadow side: you've made it a fortress instead of a launchpad.",
        "blind_spot": "You think you don't need anyone. But your Soul remembers [soul_evidence] — a moment you let someone in and it didn't destroy you. It actually made you MORE yourself.",
        "reframe": "Your independence isn't the problem. It's your greatest asset. The question is: can you be independent AND connected? Your Soul says yes — [soul_evidence].",
        "action_step": "This week: share ONE thing you're struggling with — with anyone. Not to get fixed. Just to be known. Notice: does it feel as dangerous as you expected?",
    },
    {
        "name": "fierce_protector",  # was: control_as_love
        "triggers": {
            "conflict": ["compete", "escalating"],
            "fragility": ["defensive", "masked"],
            "attachment": ["avoidant", "disorganized"],
        },
        "capability": "You protect the people you love with extraordinary fierceness. You see threats before anyone else and you ACT.",
        "description": "Your gift is protective instinct. The shadow side: protection that isn't asked for feels like control to the person receiving it.",
        "blind_spot": "You're trying to PROTECT them — that impulse is love. But they experience it as 'you don't trust me to handle this.' The fix isn't less love, it's asking first.",
        "reframe": "Your Soul shows you CAN let go — [soul_evidence]. That moment of release was when you were MOST connected, not least.",
        "action_step": "This week: when you see a problem they haven't noticed, ASK before fixing: 'Do you want my help with this, or do you want me to just listen?' Then honor their answer.",
    },
    {
        "name": "old_soul_lover",  # was: ghost_of_parent
        "triggers": {
            "attachment": ["anxious", "disorganized", "fearful"],
            "fragility": ["reactive"],
        },
        "capability": "You understand love at a depth most people never reach. You've felt its absence so completely that you recognize its presence instantly.",
        "description": "Your gift is emotional depth. The shadow side: you sometimes see your parent's face in your partner's eyes.",
        "blind_spot": "You're not fighting with your partner. You're completing a conversation you started with your parent decades ago. Recognizing this is the first step to freedom.",
        "reframe": "Your Soul holds both: the old wound ([origin_evidence]) AND proof you've already started healing ([soul_evidence]). You're not stuck in the past — you're working your way out.",
        "action_step": "This week: when you feel triggered by your partner, pause and ask: 'Am I reacting to what THEY just did, or to what someone else did years ago?' Just the question changes everything.",
    },
    {
        "name": "loyalty_architect",  # was: test_and_reject
        "triggers": {
            "attachment": ["disorganized", "fearful"],
            "connection": ["against"],
            "fragility": ["reactive", "defensive"],
        },
        "capability": "You value loyalty above everything. You'd rather be alone than with someone who isn't truly committed.",
        "description": "Your gift is fierce standards for authenticity. The shadow side: you create impossible tests because you're more afraid of being loved than being alone.",
        "blind_spot": "You're not testing if they love you. You already know they do — [soul_evidence]. The real test is whether YOU can tolerate being loved without sabotaging it.",
        "reframe": "Someone already proved their loyalty to you — [soul_evidence]. You didn't destroy that bond. You CAN let someone stay.",
        "action_step": "This week: when you feel the urge to test them (pick a fight, withdraw, create a crisis) — name it silently: 'This is a test.' Then don't send that text. Wait an hour. See if the urge passes.",
    },
    {
        "name": "bilingual_heart",  # was: love_language_mismatch
        "triggers": {
            "love_language_mismatch": [True],
        },
        "capability": "You have a strong, clear way of expressing love. It's genuine and consistent — people can count on how you show up.",
        "description": "Your gift is reliability in love. The gap: you speak one love dialect fluently but the person you love speaks a different one.",
        "blind_spot": "You show love the way you WISH you were loved. That's beautiful — but they can't hear it because it's in your language, not theirs.",
        "reframe": "You already know how to love deeply. Learning their language doesn't replace yours — it makes you bilingual. You already have the hardest part: the heart. Now add the translation.",
        "action_step": "This week: ask them directly: 'What makes you feel most loved?' Listen without defending your own way. Then do ONE thing in THEIR language, not yours.",
    },
]


class PatternMirror:
    """Reveals hidden relationship patterns from one person's Soul.

    Usage:
        mirror = PatternMirror()
        insight = mirror.analyze(
            signals={"attachment_style": "anxious", "conflict_style": "accommodate", ...},
            focus_items=[SoulItem(text="He never asks how my day was", ...)],
            deep_items=[SoulItem(text="Mom was always working", ...)],
        )
    """

    def analyze(
        self,
        signals: dict,
        focus_items: list[SoulItem] | None = None,
        deep_items: list[SoulItem] | None = None,
        memory_items: list[SoulItem] | None = None,
    ) -> RelationshipInsight:
        """Analyze one person's Soul for relationship patterns."""

        patterns = self._detect_patterns(signals, focus_items or [], deep_items or [], memory_items or [])
        core_need = self._infer_core_need(signals)
        giving = self._infer_giving_style(signals)
        receiving = self._infer_receiving_need(signals)
        mismatch = self._identify_mismatch(giving, receiving)
        resource = self._find_soul_resource(deep_items or [], memory_items or [])

        return RelationshipInsight(
            patterns=patterns,
            core_need=core_need,
            giving_style=giving,
            receiving_need=receiving,
            mismatch=mismatch,
            soul_resource=resource,
        )

    def _detect_patterns(self, signals, focus, deep, memory) -> list[RelationshipPattern]:
        """Match Soul signals to relationship patterns."""
        detected = []
        all_items = focus + deep + (memory or [])

        for p in _PATTERNS:
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
                elif signal_key == "values":
                    if signals.get("values_dominant") in trigger_values:
                        score += 1
                elif signal_key == "love_language_mismatch":
                    if signals.get("love_language_mismatch") in trigger_values:
                        score += 1

            if score >= 2:  # Need at least 2 matching triggers
                # Find Soul evidence
                evidence = []
                for item in all_items:
                    if item.emotional_valence in ("negative", "extreme") and item.activation >= 0.4:
                        evidence.append(item.text[:60])
                    if len(evidence) >= 2:
                        break

                # Find origin (from deep/memory items about childhood/parents)
                origin = ""
                origin_keywords = {"mother", "father", "parent", "child", "grew up", "family", "mama", "papa", "妈", "爸", "小时候"}
                for item in deep + (memory or []):
                    if any(kw in item.text.lower() for kw in origin_keywords):
                        origin = item.text[:60]
                        break

                # Find positive resource
                resource = ""
                for item in deep + (memory or []):
                    if item.emotional_valence in ("positive", "neutral") and "connection" in (item.tags or []):
                        resource = item.text[:60]
                        break
                if not resource:
                    for item in deep:
                        if item.emotional_valence in ("positive",):
                            resource = item.text[:60]
                            break

                reframe = p["reframe"].replace("[soul_evidence]", resource or "a moment in your past")
                reframe = reframe.replace("[origin_evidence]", origin or "your earliest relationships")

                blind_spot = p["blind_spot"].replace("[soul_evidence]", resource or "a moment")
                blind_spot = blind_spot.replace("[origin_evidence]", origin or "your earliest relationships")

                detected.append(RelationshipPattern(
                    pattern_name=p["name"],
                    capability=p.get("capability", ""),
                    description=p["description"],
                    origin=origin or "early relationship patterns",
                    current_manifestation=evidence[0] if evidence else "current relationship difficulty",
                    soul_evidence=evidence,
                    blind_spot=blind_spot,
                    reframe=reframe,
                    action_step=p.get("action_step", ""),
                ))

        return detected[:3]  # Top 3 patterns

    def _infer_core_need(self, signals) -> str:
        attach = signals.get("attachment_style", "")
        if attach == "anxious":
            return "to be chosen — actively, visibly, repeatedly"
        elif attach == "avoidant":
            return "to be accepted without having to perform vulnerability"
        elif attach == "disorganized":
            return "to be safe AND close at the same time (which feels impossible)"
        elif attach == "fearful":
            return "to trust without being destroyed"
        return "to be seen as they truly are"

    def _infer_giving_style(self, signals) -> str:
        ll = signals.get("love_language_primary", "")
        if ll: return f"gives love through {ll.replace('_', ' ')}"
        conflict = signals.get("conflict_style", "")
        if conflict == "accommodate": return "gives love through sacrifice and service"
        if conflict == "compete": return "gives love through protection and providing"
        if conflict == "avoid": return "gives love through space and non-interference"
        return "gives love through presence"

    def _infer_receiving_need(self, signals) -> str:
        attach = signals.get("attachment_style", "")
        if attach == "anxious": return "needs to hear 'I choose you' in words, often"
        if attach == "avoidant": return "needs love expressed through respect for boundaries"
        if attach == "disorganized": return "needs consistency more than intensity"
        return "needs genuine attention and curiosity"

    def _identify_mismatch(self, giving, receiving) -> str:
        if giving and receiving and giving != receiving:
            return f"You {giving}, but you {receiving}. This gap is probably the same gap your partner feels."
        return ""

    def _find_soul_resource(self, deep, memory) -> str:
        for item in deep + (memory or []):
            if item.emotional_valence == "positive" and item.activation < 0.3:
                return item.text
        return ""
