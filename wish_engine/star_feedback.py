"""Star Feedback Loop — tracks which stars users engage with.

When a star is shown but never clicked, the system learns:
  - This attention type → weak match
  - This API → low value for this user

When clicked:
  - This attention → strong match → boost priority
  - This API → high value → prefer in future

Philosophy: The stars reflect the soul, but only user action reveals truth.
王阳明: 知行合一 — what matters is what you actually do, not what you say.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StarRecord:
    """Lifetime engagement stats for a specific attention type."""
    attention: str
    impressions: int = 0
    clicks: int = 0
    dismissals: int = 0

    @property
    def ctr(self) -> float:
        """Click-through rate (0.0 to 1.0)."""
        return self.clicks / self.impressions if self.impressions > 0 else 0.5

    @property
    def weight(self) -> float:
        """Priority multiplier for future recommendations (0.3 to 2.0).

        Starts at 1.0 (neutral). High CTR → up to 2.0. Low CTR + dismissals → 0.3.
        Requires 3+ impressions to deviate significantly from 1.0.
        """
        if self.impressions < 3:
            return 1.0  # Not enough data

        base = self.ctr * 2.0  # 0.0 → 2.0
        dismissal_penalty = min(0.5, self.dismissals / self.impressions)
        raw = base - dismissal_penalty
        return max(0.3, min(2.0, raw))


class StarFeedbackStore:
    """Accumulates engagement signals across sessions.

    Usage:
        store = StarFeedbackStore()
        store.impression("hungry")       # star was shown
        store.click("hungry")            # user tapped it
        store.dismiss("anxious")         # user swiped away

        weight = store.weight("hungry")  # → 1.8 (high engagement)
        weight = store.weight("anxious") # → 0.4 (user doesn't want this)
    """

    def __init__(self):
        self._records: dict[str, StarRecord] = {}

    def _get(self, attention: str) -> StarRecord:
        if attention not in self._records:
            self._records[attention] = StarRecord(attention=attention)
        return self._records[attention]

    def impression(self, attention: str) -> None:
        """Record that a star for this attention type was shown."""
        self._get(attention).impressions += 1

    def click(self, attention: str) -> None:
        """Record that the user tapped/engaged with this star."""
        r = self._get(attention)
        r.clicks += 1
        r.impressions = max(r.impressions, r.clicks)  # Guard against out-of-order

    def dismiss(self, attention: str) -> None:
        """Record that the user explicitly dismissed this star."""
        r = self._get(attention)
        r.dismissals += 1
        r.impressions = max(r.impressions, r.dismissals)

    def weight(self, attention: str) -> float:
        """Priority multiplier for this attention type (0.3 to 2.0)."""
        return self._get(attention).weight

    def top_attentions(self, n: int = 5) -> list[tuple[str, float]]:
        """Return the top N attention types by weight, sorted descending."""
        records = [(att, r.weight) for att, r in self._records.items() if r.impressions >= 3]
        return sorted(records, key=lambda x: -x[1])[:n]

    def weak_attentions(self, threshold: float = 0.5) -> list[str]:
        """Return attention types the user consistently ignores."""
        return [
            att for att, r in self._records.items()
            if r.impressions >= 3 and r.weight < threshold
        ]

    def stats(self) -> dict[str, dict]:
        """Full stats for all tracked attentions."""
        return {
            att: {
                "impressions": r.impressions,
                "clicks": r.clicks,
                "dismissals": r.dismissals,
                "ctr": round(r.ctr, 3),
                "weight": round(r.weight, 3),
            }
            for att, r in self._records.items()
        }

    def sort_actions_by_weight(self, actions: list[dict]) -> list[dict]:
        """Re-rank a list of API actions by engagement weight.

        Actions with high past engagement float to the top.
        """
        def _score(action: dict) -> float:
            attention = action.get("attention", action.get("cat", ""))
            return self.weight(attention)

        return sorted(actions, key=_score, reverse=True)
