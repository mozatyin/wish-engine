"""L2 Fulfiller — local-compute recommendation engine with personality filtering.

Routes L2 wishes to domain-specific fulfillers. Each fulfiller has a curated
knowledge base and applies personality-based filtering. Zero LLM.

8 fulfillment types:
  a) Place search (parks, cafes, meditation centers, gyms)
  b) Book recommendation (values + MBTI matching)
  c) Course recommendation (cognitive style matching)
  d) Career direction (values + MBTI career mapping)
  e) Wellness recommendation (emotion + fragility matching)
  f) Safe route / safe space (time + gender + personality safety)
  g) Deals / discounts (values → deal preference mapping)
  h) Prayer times (astronomical local computation)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
    WishLevel,
    WishType,
)
from wish_engine.personalization import personalize_reason


class PersonalityFilter:
    """Applies personality-based filtering and scoring to recommendation candidates.

    Hard filters (exclude):
      - MBTI I + introversion > 0.6 -> exclude noisy/crowded
      - emotion anxiety > 0.5 -> exclude high-stimulation
      - fragility defensive -> exclude confrontational

    Soft filters (score boost):
      - values tradition -> boost traditional
      - values self-direction -> boost autonomous
      - attachment anxious -> boost calming/structured
      - MBTI N -> boost theory-heavy
      - MBTI S -> boost practical/hands-on
    """

    def __init__(self, detector_results: DetectorResults):
        self._det = detector_results

    @property
    def _is_introvert(self) -> bool:
        mbti = self._det.mbti
        if not mbti.get("type"):
            return False
        ei = mbti.get("dimensions", {}).get("E_I", 0.5)
        return ei < 0.4

    @property
    def _anxiety_level(self) -> float:
        return self._det.emotion.get("emotions", {}).get("anxiety", 0.0)

    @property
    def _fragility_pattern(self) -> str:
        return self._det.fragility.get("pattern", "")

    @property
    def _top_values(self) -> list[str]:
        return self._det.values.get("top_values", [])

    @property
    def _mbti_type(self) -> str:
        return self._det.mbti.get("type", "")

    @property
    def _attachment_style(self) -> str:
        return self._det.attachment.get("style", "")

    def apply(self, candidates: list[dict]) -> list[dict]:
        """Apply hard exclusion filters. Returns surviving candidates."""
        result = []
        for c in candidates:
            if self._is_introvert and c.get("noise") == "loud" and c.get("social") == "high":
                continue
            if self._anxiety_level > 0.5 and c.get("mood") == "intense":
                continue
            if self._fragility_pattern == "defensive" and c.get("mood") == "confrontational":
                continue
            result.append(c)
        return result

    def score(self, candidates: list[dict]) -> list[dict]:
        """Add _personality_score to each candidate based on trait alignment."""
        for c in candidates:
            s = 0.5
            tags = set(c.get("tags", []))

            # Value-based boosts
            if "tradition" in self._top_values and "traditional" in tags:
                s += 0.15
            if "self-direction" in self._top_values and ("self-paced" in tags or "autonomous" in tags):
                s += 0.15
            if "benevolence" in self._top_values and "helping" in tags:
                s += 0.10

            # MBTI-based boosts
            if len(self._mbti_type) == 4:
                if self._mbti_type[1] == "N" and "theory" in tags:
                    s += 0.10
                if self._mbti_type[1] == "S" and "practical" in tags:
                    s += 0.10
                if self._mbti_type[0] == "I" and "quiet" in tags:
                    s += 0.10
                if self._mbti_type[0] == "E" and "social" in tags:
                    s += 0.10

            # Attachment-based boosts
            if self._attachment_style == "anxious" and "calming" in tags:
                s += 0.10

            # Emotion-based boosts
            if self._anxiety_level > 0.5 and "calming" in tags:
                s += 0.10

            c["_personality_score"] = min(s, 1.0)
        return candidates

    def filter_and_rank(self, candidates: list[dict], max_results: int = 3) -> list[dict]:
        """Apply hard filter, score, sort descending, return top N."""
        filtered = self.apply(candidates)
        scored = self.score(filtered)
        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        return scored[:max_results]


# Categories that are safety-critical — PersonalityFilter MUST be bypassed.
# Crisis hotlines and resources must always appear in their original priority
# order regardless of user personality traits (MBTI, attachment, etc.).
SAFETY_CRITICAL_CATEGORIES: frozenset[str] = frozenset({
    "suicide_prevention",
    "domestic_violence",
    "crisis",
})


class L2Fulfiller(ABC):
    """Base class for L2 domain-specific fulfillers.

    Subclasses can set ``safety_critical = True`` to bypass PersonalityFilter
    entirely — crisis resources are returned in their original priority order.
    """

    # Override in subclass to skip PersonalityFilter
    safety_critical: bool = False

    @abstractmethod
    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        ...

    def _build_recommendations(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list[Recommendation]:
        """Filter, score, and convert candidates to Recommendation models.

        Safety-critical fulfillers bypass PersonalityFilter entirely — crisis
        resources are returned in their original priority order so that
        hotlines always appear first regardless of user personality.
        """
        if self.safety_critical:
            # No filtering, no reranking — preserve original priority order
            ranked = candidates[:max_results]
        else:
            pf = PersonalityFilter(detector_results)
            ranked = pf.filter_and_rank(candidates, max_results=max_results)

        results: list[Recommendation] = []
        for c in ranked:
            tags = c.get("tags", [])
            if self.safety_critical:
                # Use the pre-set relevance reason for crisis resources
                reason = c.get("relevance_reason", "Help is available")
            else:
                reason = personalize_reason(
                    recommendation_title=c["title"],
                    recommendation_tags=tags,
                    detector_results=detector_results,
                )
            results.append(
                Recommendation(
                    title=c["title"],
                    description=c["description"],
                    category=c["category"],
                    relevance_reason=reason,
                    score=c.get("_personality_score", 0.5),
                    action_url=c.get("action_url"),
                    tags=tags,
                )
            )
        return results


def _get_fulfiller(wish_type: WishType, wish_text: str = "") -> L2Fulfiller:
    """Get the fulfiller instance for a wish type using score-based routing."""
    from wish_engine.l2_router import get_fulfiller_instance
    return get_fulfiller_instance(wish_text, wish_type)


def fulfill_l2(
    wish: ClassifiedWish,
    detector_results: DetectorResults,
) -> L2FulfillmentResult:
    """Route an L2 wish to the appropriate fulfiller and return recommendations.

    Zero LLM — all local-compute with curated knowledge bases.
    """
    if wish.level != WishLevel.L2:
        raise ValueError(f"L2Fulfiller only handles L2 wishes, got {wish.level}")

    fulfiller = _get_fulfiller(wish.wish_type, wish_text=wish.wish_text)
    return fulfiller.fulfill(wish, detector_results)
