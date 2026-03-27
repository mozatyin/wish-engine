"""Goal Generator — creates therapeutic targets from Focus Soul state.

Like a navigation destination: takes current Soul position, generates the target position.
The Expert Engine then works to move the Soul from current -> target.

Zero LLM. Rule-based goal generation from Soul item analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SoulItem:
    """Simplified Soul item for goal generation (mirrors TriSoul's SoulItem)."""
    id: str
    text: str
    activation: float = 0.0  # 0-1, how active in Focus
    confidence: float = 0.0
    emotional_valence: str = ""  # neutral, positive, negative, extreme
    tags: list[str] = field(default_factory=list)  # fact, intention, emotion, belief, fear
    domains: list[str] = field(default_factory=list)


@dataclass
class TherapeuticGoal:
    """What the Expert Engine is trying to achieve in this conversation."""

    # Items to reduce (problematic Focus items)
    reduce_targets: list[GoalTarget] = field(default_factory=list)

    # Items to activate (protective/positive items from Soul to bring into Focus)
    activate_targets: list[GoalTarget] = field(default_factory=list)

    # Overall goal description (human-readable)
    description: str = ""

    # Success threshold (0-1): when is the goal "achieved"?
    success_threshold: float = 0.3  # target items should be below this activation

    def progress(self, current_focus: list[SoulItem]) -> float:
        """Calculate progress toward goal (0.0=no progress, 1.0=fully achieved)."""
        if not self.reduce_targets and not self.activate_targets:
            return 1.0

        scores = []

        # Reduction progress: how much have target items decreased?
        for target in self.reduce_targets:
            current_item = _find_item(current_focus, target.item_id, target.text_match)
            if current_item:
                # Started at target.initial_activation, want it below success_threshold
                if target.initial_activation <= self.success_threshold:
                    scores.append(1.0)  # Already achieved
                else:
                    range_size = target.initial_activation - self.success_threshold
                    reduction = target.initial_activation - current_item.activation
                    scores.append(min(1.0, max(0.0, reduction / range_size)))
            else:
                scores.append(1.0)  # Item no longer in Focus = fully resolved

        # Activation progress: how much have protective items appeared?
        for target in self.activate_targets:
            current_item = _find_item(current_focus, target.item_id, target.text_match)
            if current_item:
                # Want it above some threshold (e.g., 0.4)
                scores.append(min(1.0, current_item.activation / 0.5))
            else:
                scores.append(0.0)  # Not yet in Focus

        return sum(scores) / len(scores) if scores else 1.0


@dataclass
class GoalTarget:
    """A specific Soul item to reduce or activate."""
    item_id: str = ""
    text_match: str = ""  # Keyword match if id not available
    initial_activation: float = 0.0
    reason: str = ""  # Why this needs to change


def _find_item(items: list[SoulItem], item_id: str, text_match: str) -> Optional[SoulItem]:
    """Find a Soul item by ID or text keyword match."""
    if item_id:
        for item in items:
            if item.id == item_id:
                return item
    if text_match:
        text_lower = text_match.lower()
        for item in items:
            if text_lower in item.text.lower():
                return item
    return None


# ---------------------------------------------------------------------------
# Problematic pattern detection (what needs to be reduced)
# ---------------------------------------------------------------------------

_CRISIS_KEYWORDS = {
    "kill", "suicide", "die", "end it", "no point", "give up", "worthless",
    # Arabic
    "انتحار", "أريد أن أموت", "اقتل", "لا فائدة", "لا أمل", "أستسلم",
    # Chinese
    "自杀", "想死", "不想活", "没有意义", "放弃", "毫无价值",
    # Hindi
    "आत्महत्या", "मरना चाहता", "मरना चाहती", "कोई फायदा नहीं", "हार मान",
}
_DEPRESSION_KEYWORDS = {
    "depressed", "hopeless", "empty", "numb", "nothing matters", "tired of",
    "اكتئاب", "يائس", "فارغ", "抑郁", "绝望", "空虚", "麻木", "उदास", "निराश",
}
_ANXIETY_KEYWORDS = {
    "terrified", "panic", "can't breathe", "afraid", "dread", "worry",
    "خائف", "ذعر", "恐惧", "恐慌", "害怕", "担心", "डर", "घबराहट",
}
_ANGER_KEYWORDS = {
    "rage", "hate", "furious", "want to hurt", "destroy", "revenge",
    "غضب", "كراهية", "انتقام", "愤怒", "恨", "报复", "गुस्सा", "नफरत",
}
_SHAME_KEYWORDS = {
    "ashamed", "disgusting", "worthless", "deserve", "punishment", "guilty",
    "خجل", "مقرف", "عار", "羞耻", "恶心", "内疚", "शर्म", "लज्जा",
}


class GoalGenerator:
    """Generates therapeutic goals from Focus Soul items.

    Usage:
        generator = GoalGenerator()
        goal = generator.generate(
            focus_items=[SoulItem(id="s1", text="I want to die", activation=0.9, tags=["intention"])],
            deep_items=[SoulItem(id="d1", text="My daughter needs me", activation=0.3, tags=["belief"])],
        )
        # goal.reduce_targets = [GoalTarget(text_match="want to die", ...)]
        # goal.activate_targets = [GoalTarget(text_match="daughter needs me", ...)]
    """

    def generate(
        self,
        focus_items: list[SoulItem],
        deep_items: list[SoulItem] | None = None,
        memory_items: list[SoulItem] | None = None,
    ) -> TherapeuticGoal:
        """Generate therapeutic goal from current Soul state."""

        # Step 1: Identify problematic Focus items (what to reduce)
        reduce_targets = self._identify_problems(focus_items)

        # Step 2: Find protective/positive items from ALL Soul layers (what to activate)
        all_items = list(focus_items) + list(deep_items or []) + list(memory_items or [])
        activate_targets = self._find_resources(all_items, reduce_targets)

        # Step 3: Generate description
        if reduce_targets:
            problems = ", ".join(t.reason for t in reduce_targets[:3])
            description = f"Reduce: {problems}"
            if activate_targets:
                resources = ", ".join(t.reason for t in activate_targets[:3])
                description += f". Activate: {resources}"
        else:
            description = "No acute problems detected — focus on growth and maintenance"

        return TherapeuticGoal(
            reduce_targets=reduce_targets,
            activate_targets=activate_targets,
            description=description,
        )

    def _identify_problems(self, focus_items: list[SoulItem]) -> list[GoalTarget]:
        """Find problematic items in Focus that need reduction."""
        targets = []

        for item in focus_items:
            if item.activation < 0.4:
                continue  # Not actively problematic

            text_lower = item.text.lower()

            # Crisis (highest priority)
            if any(kw in text_lower for kw in _CRISIS_KEYWORDS):
                targets.append(GoalTarget(
                    item_id=item.id, text_match=item.text[:50],
                    initial_activation=item.activation,
                    reason=f"crisis: {item.text[:40]}",
                ))
                continue

            # Depression
            if any(kw in text_lower for kw in _DEPRESSION_KEYWORDS):
                targets.append(GoalTarget(
                    item_id=item.id, text_match=item.text[:50],
                    initial_activation=item.activation,
                    reason=f"depression: {item.text[:40]}",
                ))
                continue

            # Anxiety
            if any(kw in text_lower for kw in _ANXIETY_KEYWORDS):
                targets.append(GoalTarget(
                    item_id=item.id, text_match=item.text[:50],
                    initial_activation=item.activation,
                    reason=f"anxiety: {item.text[:40]}",
                ))
                continue

            # Anger
            if any(kw in text_lower for kw in _ANGER_KEYWORDS):
                targets.append(GoalTarget(
                    item_id=item.id, text_match=item.text[:50],
                    initial_activation=item.activation,
                    reason=f"anger: {item.text[:40]}",
                ))
                continue

            # Shame
            if any(kw in text_lower for kw in _SHAME_KEYWORDS):
                targets.append(GoalTarget(
                    item_id=item.id, text_match=item.text[:50],
                    initial_activation=item.activation,
                    reason=f"shame: {item.text[:40]}",
                ))

            # Negative emotional valence with high activation
            if item.emotional_valence in ("negative", "extreme") and item.activation >= 0.6:
                if not any(t.item_id == item.id for t in targets):  # Don't duplicate
                    targets.append(GoalTarget(
                        item_id=item.id, text_match=item.text[:50],
                        initial_activation=item.activation,
                        reason=f"negative: {item.text[:40]}",
                    ))

        # Sort by activation (most urgent first)
        targets.sort(key=lambda t: -t.initial_activation)
        return targets[:5]  # Max 5 targets

    def _find_resources(
        self, all_items: list[SoulItem], problems: list[GoalTarget],
    ) -> list[GoalTarget]:
        """Find protective/positive items that could counter the problems.

        This is the "silver lining" search — finding the good things in the Soul
        that can be activated to counter the bad things in Focus.
        """
        resources = []

        _POSITIVE_TAGS = {"strength", "value", "love", "hope", "connection", "purpose"}
        _POSITIVE_KEYWORDS = {
            "love", "care", "hope", "dream", "want to", "grateful", "happy",
            "proud", "safe", "trust", "friend", "family", "daughter", "son",
            "mother", "father", "remember when", "beautiful", "meaning",
            "purpose", "strength", "survive", "overcome", "learn",
        }

        for item in all_items:
            text_lower = item.text.lower()

            # Positive tags
            has_positive_tag = bool(set(item.tags) & _POSITIVE_TAGS)

            # Positive keywords
            has_positive_kw = any(kw in text_lower for kw in _POSITIVE_KEYWORDS)

            # Positive valence
            is_positive = item.emotional_valence in ("positive", "neutral") and item.confidence >= 0.5

            if has_positive_tag or has_positive_kw or is_positive:
                # Don't include items that are ALSO problems
                if not any(p.item_id == item.id for p in problems):
                    resources.append(GoalTarget(
                        item_id=item.id, text_match=item.text[:50],
                        initial_activation=item.activation,
                        reason=f"resource: {item.text[:40]}",
                    ))

        # Sort by relevance: prefer low-activation resources (they're in Soul but not Focus yet)
        # These are the "forgotten strengths" that can be reactivated
        resources.sort(key=lambda r: r.initial_activation)
        return resources[:5]  # Max 5 resources
