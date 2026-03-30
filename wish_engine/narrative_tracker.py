"""Life Narrative Arc Tracker — understands which phase of life a user is in.

Phases (in order):
  survival  → immediate needs dominate (food, safety, health, crisis)
  stability → needs met, building routine (habit, sleep, work)
  growth    → seeking improvement (learning, books, community, skill)
  meaning   → existential questions, legacy (purpose, wisdom, identity)

Why this matters:
  Scarlett in Chapter 1 (survival) needs the Noodle House.
  Scarlett in Chapter 12 (meaning) needs Marcus Aurelius.
  Same hunger keyword → different response depending on narrative phase.

王阳明: 知行合一。The system should act from where the heart truly is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LifePhase(str, Enum):
    SURVIVAL  = "survival"   # 生存: 当下危机，立刻需要帮助
    STABILITY = "stability"  # 稳定: 需求已满，建立日常
    GROWTH    = "growth"     # 成长: 主动追求进步
    MEANING   = "meaning"    # 意义: 探索人生目的


# Signal keywords that push toward each phase
_PHASE_SIGNALS: dict[LifePhase, list[str]] = {
    LifePhase.SURVIVAL: [
        "hungry", "starving", "sick", "emergency", "help me", "can't breathe",
        "bleeding", "homeless", "no money", "desperate", "scared", "i'm lost",
        "danger", "crisis", "survive", "alive", "need medicine", "no food",
        "饿", "紧急", "帮我", "危险", "没有钱",
    ],
    LifePhase.STABILITY: [
        "routine", "habit", "sleep better", "going to work", "my apartment",
        "weekly", "schedule", "regular", "stable", "settled", "everyday",
        "morning routine", "after work", "healthy habits",
        "规律", "日常", "习惯", "稳定",
    ],
    LifePhase.GROWTH: [
        "learn", "course", "improve", "skill", "better at", "practice",
        "goal", "progress", "challenge myself", "reading", "study",
        "workout", "achieve", "level up", "build", "project",
        "学习", "进步", "目标", "提升",
    ],
    LifePhase.MEANING: [
        "who am i", "meaning", "purpose", "legacy", "life is", "why do i",
        "what's the point", "i believe", "i swear", "never again", "always",
        "from now on", "the rest of my life", "i realize", "looking back",
        "what matters", "at the end", "soul", "destiny",
        "意义", "人生", "我是谁", "相信", "永远",
    ],
}

# How phase shapes recommendations
_PHASE_RECOMMENDATION_WEIGHTS: dict[LifePhase, dict[str, float]] = {
    LifePhase.SURVIVAL: {
        "surface_weight": 2.0,   # Heavily favor immediate needs
        "middle_weight":  0.3,   # Rarely offer growth content
        "deep_weight":    0.2,   # Almost never wisdom (except anchoring)
        "wisdom_ok":      False, # Don't offer philosophy when in crisis
    },
    LifePhase.STABILITY: {
        "surface_weight": 1.2,
        "middle_weight":  1.0,
        "deep_weight":    0.5,
        "wisdom_ok":      True,
    },
    LifePhase.GROWTH: {
        "surface_weight": 0.8,
        "middle_weight":  1.5,   # Growth content is primary
        "deep_weight":    0.8,
        "wisdom_ok":      True,
    },
    LifePhase.MEANING: {
        "surface_weight": 0.5,   # Practical needs take back seat
        "middle_weight":  0.8,
        "deep_weight":    2.0,   # Wisdom and reflection are primary
        "wisdom_ok":      True,
    },
}

# Phase transition messages (shown to user when phase changes)
_PHASE_TRANSITIONS: dict[tuple[LifePhase, LifePhase], str] = {
    (LifePhase.SURVIVAL, LifePhase.STABILITY): "你已经度过了最难的时刻。现在可以想想怎么把生活稳定下来了。",
    (LifePhase.STABILITY, LifePhase.GROWTH):   "你的生活已经稳定了。是时候想想往哪里成长了。",
    (LifePhase.GROWTH, LifePhase.MEANING):     "你一直在进步。现在有时间问更大的问题了——你真正想要什么？",
    (LifePhase.MEANING, LifePhase.GROWTH):     "想清楚了吗？是时候把你的想法变成行动了。",
    (LifePhase.STABILITY, LifePhase.SURVIVAL): "你现在面对一个紧急情况。先处理眼前的问题。",
}


@dataclass
class NarrativeTracker:
    """Accumulates signals across sessions to determine the user's life phase.

    Usage:
        tracker = NarrativeTracker()
        tracker.update(["I'm so hungry", "No money left"])  # → survival
        tracker.update(["I'm taking a yoga class now"])     # → stability
        phase = tracker.current_phase  # → LifePhase.STABILITY
    """
    # Phase signal counts (accumulated across all sessions)
    _scores: dict[LifePhase, float] = field(
        default_factory=lambda: {p: 0.0 for p in LifePhase}
    )
    _phase_history: list[LifePhase] = field(default_factory=list)
    _session_count: int = 0

    @property
    def current_phase(self) -> LifePhase:
        """The life phase with the highest accumulated score."""
        return max(self._scores, key=lambda p: self._scores[p])

    @property
    def weights(self) -> dict[str, float]:
        """Recommendation weights for the current phase."""
        return _PHASE_RECOMMENDATION_WEIGHTS[self.current_phase]

    def update(self, texts: list[str], decay: float = 0.95) -> LifePhase | None:
        """Process new texts and update phase scores.

        Older signals decay so recent context dominates.
        Returns the new phase if a transition occurred, else None.
        """
        prev_phase = self.current_phase

        # Decay all existing scores
        for p in self._scores:
            self._scores[p] *= decay

        # Score new texts
        combined = " ".join(texts).lower()
        for phase, keywords in _PHASE_SIGNALS.items():
            hits = sum(1 for kw in keywords if kw in combined)
            self._scores[phase] += hits

        self._session_count += 1
        new_phase = self.current_phase
        self._phase_history.append(new_phase)

        # Return transition if phase changed
        if new_phase != prev_phase:
            return new_phase
        return None

    def transition_message(self, from_phase: LifePhase, to_phase: LifePhase) -> str | None:
        """Get the message to show when a phase transition occurs."""
        return _PHASE_TRANSITIONS.get((from_phase, to_phase))

    def phase_scores(self) -> dict[str, float]:
        """Return current phase scores for debugging."""
        return {p.value: round(score, 2) for p, score in self._scores.items()}

    def recent_phases(self, n: int = 5) -> list[str]:
        """Return the last N phase labels."""
        return [p.value for p in self._phase_history[-n:]]

    def should_show_wisdom(self) -> bool:
        """Whether the current phase welcomes wisdom/reflection content."""
        return self.weights.get("wisdom_ok", True)

    def summary(self) -> str:
        phase = self.current_phase
        scores = self.phase_scores()
        return f"[{phase.value.upper()}] scores={scores} sessions={self._session_count}"
