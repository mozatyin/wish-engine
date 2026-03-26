"""Tests for L2Fulfiller base class, personality filter, and router."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    Recommendation,
    WishLevel,
    WishType,
)
from wish_engine.l2_fulfiller import (
    L2Fulfiller,
    PersonalityFilter,
    fulfill_l2,
)


class TestPersonalityFilter:
    def _make_candidate(self, **overrides) -> dict:
        base = {
            "title": "Test Place",
            "description": "A test",
            "category": "park",
            "tags": [],
            "noise": "quiet",
            "social": "low",
            "mood": "calming",
            "cognitive_style": "any",
        }
        base.update(overrides)
        return base

    def test_introvert_excludes_noisy(self):
        pf = PersonalityFilter(DetectorResults(
            mbti={"type": "INFJ", "dimensions": {"E_I": 0.3}},
        ))
        candidates = [
            self._make_candidate(title="Loud Bar", noise="loud", social="high"),
            self._make_candidate(title="Quiet Park", noise="quiet", social="low"),
        ]
        filtered = pf.apply(candidates)
        titles = [c["title"] for c in filtered]
        assert "Quiet Park" in titles
        assert "Loud Bar" not in titles

    def test_extrovert_keeps_noisy(self):
        pf = PersonalityFilter(DetectorResults(
            mbti={"type": "ENFP", "dimensions": {"E_I": 0.8}},
        ))
        candidates = [
            self._make_candidate(title="Loud Bar", noise="loud", social="high"),
            self._make_candidate(title="Quiet Park", noise="quiet", social="low"),
        ]
        filtered = pf.apply(candidates)
        assert len(filtered) == 2

    def test_anxiety_excludes_high_stimulation(self):
        pf = PersonalityFilter(DetectorResults(
            emotion={"emotions": {"anxiety": 0.7}},
        ))
        candidates = [
            self._make_candidate(title="Intense Bootcamp", mood="intense"),
            self._make_candidate(title="Gentle Yoga", mood="calming"),
        ]
        filtered = pf.apply(candidates)
        titles = [c["title"] for c in filtered]
        assert "Gentle Yoga" in titles
        assert "Intense Bootcamp" not in titles

    def test_no_anxiety_keeps_intense(self):
        pf = PersonalityFilter(DetectorResults(
            emotion={"emotions": {"joy": 0.8}},
        ))
        candidates = [
            self._make_candidate(title="Intense Bootcamp", mood="intense"),
        ]
        assert len(pf.apply(candidates)) == 1

    def test_tradition_boosts_traditional(self):
        pf = PersonalityFilter(DetectorResults(
            values={"top_values": ["tradition", "conformity"]},
        ))
        candidates = [
            self._make_candidate(title="Traditional Meditation", tags=["traditional"]),
            self._make_candidate(title="Modern Mindfulness App", tags=["modern"]),
        ]
        scored = pf.score(candidates)
        trad = next(s for s in scored if s["title"] == "Traditional Meditation")
        modern = next(s for s in scored if s["title"] == "Modern Mindfulness App")
        assert trad["_personality_score"] > modern["_personality_score"]

    def test_self_direction_boosts_autonomous(self):
        pf = PersonalityFilter(DetectorResults(
            values={"top_values": ["self-direction", "stimulation"]},
        ))
        candidates = [
            self._make_candidate(title="Self-Paced Course", tags=["self-paced", "autonomous"]),
            self._make_candidate(title="Structured Classroom", tags=["structured", "group"]),
        ]
        scored = pf.score(candidates)
        sp = next(s for s in scored if s["title"] == "Self-Paced Course")
        sc = next(s for s in scored if s["title"] == "Structured Classroom")
        assert sp["_personality_score"] > sc["_personality_score"]

    def test_empty_detector_results_passes_all(self):
        pf = PersonalityFilter(DetectorResults())
        candidates = [self._make_candidate(), self._make_candidate(title="Another")]
        assert len(pf.apply(candidates)) == 2

    def test_defensive_fragility_excludes_confrontational(self):
        pf = PersonalityFilter(DetectorResults(
            fragility={"pattern": "defensive"},
        ))
        candidates = [
            self._make_candidate(title="Assertiveness Workshop", mood="confrontational"),
            self._make_candidate(title="Gentle Journaling", mood="calming"),
        ]
        filtered = pf.apply(candidates)
        titles = [c["title"] for c in filtered]
        assert "Assertiveness Workshop" not in titles
        assert "Gentle Journaling" in titles


class TestFulfillL2Router:
    def _make_wish(self, wish_type: WishType) -> ClassifiedWish:
        return ClassifiedWish(
            wish_text="test wish",
            wish_type=wish_type,
            level=WishLevel.L2,
            fulfillment_strategy="test",
        )

    def test_l1_wish_raises(self):
        wish = ClassifiedWish(
            wish_text="test", wish_type=WishType.SELF_UNDERSTANDING,
            level=WishLevel.L1, fulfillment_strategy="test",
        )
        with pytest.raises(ValueError, match="L2"):
            fulfill_l2(wish, DetectorResults())
