"""Progress Tracker — computes dimension changes between sessions and scores improvement."""
from __future__ import annotations


class ProgressTracker:
    """Tracks progress across therapy dimensions between sessions."""

    # Dimensions where DECREASE means improvement
    NEGATIVE_DIMENSIONS = {
        "emotion_intensity",
        "crisis_level",
        "fragility_confidence",
        "self_criticism_score",
    }
    # Dimensions where INCREASE means improvement
    POSITIVE_DIMENSIONS = {
        "eq_score",
        "connection_confidence",
    }

    def compute_changes(
        self, before: dict[str, float], after: dict[str, float]
    ) -> dict[str, float]:
        """Compute delta for each dimension present in both snapshots.
        Returns {dimension: after - before}.
        """
        shared = before.keys() & after.keys()
        return {dim: after[dim] - before[dim] for dim in shared}

    def improvement_score(self, changes: dict[str, float]) -> float:
        """Compute overall improvement score from dimension changes.

        Positive = improvement, negative = worsening, 0 = no change.
        For NEGATIVE_DIMENSIONS: decrease is improvement (invert sign).
        For POSITIVE_DIMENSIONS: increase is improvement (keep sign).
        Average all contributing dimensions.
        """
        if not changes:
            return 0.0

        scores: list[float] = []
        for dim, delta in changes.items():
            if dim in self.NEGATIVE_DIMENSIONS:
                # Decrease is good → invert sign so negative delta → positive score
                scores.append(-delta)
            elif dim in self.POSITIVE_DIMENSIONS:
                # Increase is good → keep sign
                scores.append(delta)
            else:
                # Unknown dimension — treat increase as improvement by default
                scores.append(delta)

        return sum(scores) / len(scores) if scores else 0.0

    def format_changes(self, changes: dict[str, float]) -> str:
        """Format changes for prompt injection.

        E.g.: 'emotion_intensity: ↓ 0.20 (improved), eq_score: ↑ 0.10 (improved)'
        """
        if not changes:
            return "No significant changes"

        parts: list[str] = []
        for dim, delta in sorted(changes.items()):
            arrow = "↑" if delta > 0 else "↓" if delta < 0 else "→"
            abs_delta = abs(delta)

            # Determine if this change is an improvement
            if dim in self.NEGATIVE_DIMENSIONS:
                label = "improved" if delta < 0 else "worsened" if delta > 0 else "unchanged"
            elif dim in self.POSITIVE_DIMENSIONS:
                label = "improved" if delta > 0 else "worsened" if delta < 0 else "unchanged"
            else:
                label = "increased" if delta > 0 else "decreased" if delta < 0 else "unchanged"

            parts.append(f"{dim}: {arrow} {abs_delta:.2f} ({label})")

        return ", ".join(parts)
