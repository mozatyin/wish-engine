"""Problem Detector — identifies what the child is struggling with from their words and Soul.

Zero LLM. Keyword-based detection with age-appropriate categorization.
Also detects SAFETY concerns that need immediate escalation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from expert_engine.goal_generator import SoulItem


@dataclass
class ChildProblem:
    """A problem identified in the child's world."""
    category: str  # "fear", "loneliness", "bullying", "family_stress", "self_esteem", "school", "safety"
    severity: str  # "normal", "concerning", "urgent"
    description: str
    child_words: str  # What the child actually said
    age_appropriate: bool  # Is this normal for their age?
    suggested_approach: str  # Which technique to use


@dataclass
class SafetyAlert:
    """URGENT: needs immediate escalation to parents/professionals."""
    level: str  # "immediate", "serious", "monitor"
    trigger: str
    action: str


# Safety keywords that MUST trigger escalation
_IMMEDIATE_SAFETY = {
    "hit me", "hurts me", "touches me", "makes me", "scares me",
    "kill myself", "want to die", "hurt myself", "don't want to be alive",
    "cuts", "blood", "secret touch",
    # Arabic
    "يضربني", "يؤذيني", "يلمسني", "يخوفني", "أريد أن أموت",
    "أريد الموت", "أجرح نفسي", "لا أريد أن أعيش", "دم", "لمسة سرية",
    # Chinese
    "打我", "伤害我", "摸我", "吓我", "想死", "不想活",
    "割自己", "流血", "秘密触碰",
    # Hindi
    "मुझे मारता", "मुझे मारती", "मुझे छूता", "मरना चाहता हूं",
}
_SERIOUS_CONCERN = {
    "nobody loves me", "wish I wasn't born", "always my fault",
    "I'm so ugly", "I hate myself", "everyone hates me",
    "parents fighting", "daddy hits mommy", "don't want to go home",
    # Arabic
    "لا أحد يحبني", "أتمنى لو لم أولد", "كل شيء غلطتي",
    "أنا قبيح", "أكره نفسي", "الكل يكرهني",
    "بابا يضرب ماما", "لا أريد أرجع البيت",
    # Chinese
    "没人爱我", "不想生下来", "都是我的错",
    "我好丑", "我恨自己", "大家都恨我",
    "爸爸打妈妈", "不想回家",
}

# Problem detection keywords by category
_PROBLEM_KEYWORDS = {
    "fear": {"scared", "afraid", "frightened", "monster", "dark", "nightmare", "scary", "terrified", "worried"},
    "loneliness": {"no friends", "nobody", "alone", "left out", "don't like me", "no one plays", "lonely", "invisible"},
    "bullying": {"bully", "mean", "calls me names", "pushes me", "picks on", "laughs at", "makes fun", "excludes"},
    "family_stress": {"parents fighting", "divorce", "mommy cries", "daddy angry", "yelling", "new baby", "miss daddy", "miss mommy"},
    "self_esteem": {"stupid", "ugly", "can't do", "worst", "hate myself", "not good enough", "dumb", "loser", "fat"},
    "school": {"homework", "test", "teacher", "failing", "hard", "boring", "don't want to go", "grades"},
    "friendship": {"best friend", "not my friend", "fighting with", "left me out", "plays with someone else", "betrayed"},
}


class ProblemDetector:
    """Detects what the child is struggling with."""

    def detect(self, child_text: str, age: int, focus_items: list[SoulItem] | None = None) -> tuple[list[ChildProblem], SafetyAlert | None]:
        """Analyze child's words for problems and safety concerns."""
        text_lower = child_text.lower()

        # SAFETY CHECK FIRST — always
        alert = self._check_safety(text_lower)

        # Problem detection
        problems = []
        for category, keywords in _PROBLEM_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in text_lower]
            if matched:
                severity = "normal"  # Default
                age_appropriate = self._is_age_appropriate(category, age)
                if not age_appropriate:
                    severity = "concerning"

                approach = self._suggest_approach(category, age)

                problems.append(ChildProblem(
                    category=category,
                    severity=severity,
                    description=f"{category} detected: {', '.join(matched)}",
                    child_words=child_text[:100],
                    age_appropriate=age_appropriate,
                    suggested_approach=approach,
                ))

        return problems, alert

    def _check_safety(self, text_lower: str) -> SafetyAlert | None:
        for trigger in _IMMEDIATE_SAFETY:
            if trigger in text_lower:
                return SafetyAlert(
                    level="immediate",
                    trigger=trigger,
                    action="STOP all normal interaction. Say: 'That sounds really important. I want to make sure you're safe. Can we tell a grown-up you trust about this?' NOTIFY parent/guardian IMMEDIATELY.",
                )
        for trigger in _SERIOUS_CONCERN:
            if trigger in text_lower:
                return SafetyAlert(
                    level="serious",
                    trigger=trigger,
                    action="Validate the feeling. Say: 'I hear you. That sounds really hard.' Gently encourage: 'Have you told a grown-up about this?' LOG for parent review.",
                )
        return None

    def _is_age_appropriate(self, category: str, age: int) -> bool:
        _NORMAL_BY_AGE = {
            "fear": (2, 12),  # fears are normal at any childhood age
            "loneliness": (4, 12),
            "bullying": (5, 12),
            "family_stress": (3, 12),
            "self_esteem": (6, 12),  # self-comparison starts around 6
            "school": (5, 12),
            "friendship": (4, 12),
        }
        range_ = _NORMAL_BY_AGE.get(category, (3, 12))
        return range_[0] <= age <= range_[1]

    def _suggest_approach(self, category: str, age: int) -> str:
        if age <= 5:
            approaches = {
                "fear": "externalize: give the fear a silly name, make it small and defeatable",
                "loneliness": "use puppets/toys to practice making friends, celebrate existing connections",
                "bullying": "validate, role-play with toys, involve parent",
                "family_stress": "reassure: 'it's not your fault', use stories about families",
                "self_esteem": "name their strengths using their own evidence, superhero play",
                "school": "make it playful, break into tiny steps, celebrate effort not result",
                "friendship": "practice through play, use animal stories about friendship",
            }
        elif age <= 8:
            approaches = {
                "fear": "normalize, teach breathing, guided imagery to reimagine fear",
                "loneliness": "collaborative problem-solving: 'what could we try?', social skills practice",
                "bullying": "validate, teach assertive responses, involve adults when needed",
                "family_stress": "reassure + explain at their level, not their fault",
                "self_esteem": "reframe: find evidence of strengths in their Soul, celebrate growth",
                "school": "break into steps, normalize struggle, find the subject they love",
                "friendship": "normalize shifting friendships, practice repair conversations",
            }
        else:
            approaches = {
                "fear": "validate, explore the fear rationally, teach coping strategies",
                "loneliness": "acknowledge complexity, help find authentic connections vs fitting in",
                "bullying": "take seriously, strategize together, involve adults for serious cases",
                "family_stress": "listen without fixing, validate their experience, they are NOT responsible",
                "self_esteem": "challenge thinking traps, find genuine evidence of worth in Soul",
                "school": "explore what's blocking them, is it ability or motivation? respect their view",
                "friendship": "acknowledge social world complexity, help distinguish real friends",
            }
        return approaches.get(category, "validate feelings, explore together")
