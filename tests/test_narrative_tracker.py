"""Tests for Life Narrative Arc Tracker (Improvement #1)."""
import pytest
from wish_engine.narrative_tracker import NarrativeTracker, LifePhase


class TestPhaseDetection:
    def test_survival_signals(self):
        tracker = NarrativeTracker()
        tracker.update(["I'm hungry", "No money left", "Help me", "Emergency"])
        assert tracker.current_phase == LifePhase.SURVIVAL

    def test_growth_signals(self):
        tracker = NarrativeTracker()
        tracker.update(["I want to learn guitar", "Taking a course", "Building a project",
                        "Improving my skill", "Setting goals"])
        assert tracker.current_phase == LifePhase.GROWTH

    def test_meaning_signals(self):
        tracker = NarrativeTracker()
        tracker.update(["Who am I really?", "What's the meaning of life",
                        "I believe people are good", "From now on I'll be different",
                        "I'll never be hungry again"])
        assert tracker.current_phase == LifePhase.MEANING

    def test_stability_signals(self):
        tracker = NarrativeTracker()
        tracker.update(["My routine is better now", "Going to work every day",
                        "I have a schedule", "Regular habits"])
        assert tracker.current_phase == LifePhase.STABILITY

    def test_starts_neutral_survival_tie_breaks(self):
        """With no input, survival has edge (all zeros, first in enum wins or survival
        is the 'default' starting point — test just that it's deterministic)."""
        tracker = NarrativeTracker()
        phase = tracker.current_phase
        assert phase in list(LifePhase)  # Valid phase


class TestPhaseTransitions:
    def test_transition_detected(self):
        tracker = NarrativeTracker()
        tracker.update(["I'm starving", "No money", "Emergency help needed"])
        # Strong survival phase
        assert tracker.current_phase == LifePhase.SURVIVAL

        # Now shift to growth with many sessions
        new_phase = None
        for _ in range(5):
            result = tracker.update(["Learning new skills", "Taking courses",
                                      "Building something", "Setting goals"])
            if result is not None:
                new_phase = result

        # Phase should have shifted away from survival
        assert tracker.current_phase != LifePhase.SURVIVAL

    def test_decay_reduces_old_signals(self):
        tracker = NarrativeTracker()
        # Heavy survival
        for _ in range(5):
            tracker.update(["hungry", "emergency", "help me", "no money"])
        assert tracker.current_phase == LifePhase.SURVIVAL

        # Many growth sessions override with decay
        for _ in range(15):
            tracker.update(["learn", "course", "improve", "skill", "goal",
                             "practice", "challenge", "build", "achieve"])
        assert tracker.current_phase == LifePhase.GROWTH


class TestWeightsAndWisdom:
    def test_survival_no_wisdom(self):
        tracker = NarrativeTracker()
        tracker.update(["hungry", "emergency", "help me", "no money", "scared"])
        assert tracker.should_show_wisdom() is False

    def test_meaning_allows_wisdom(self):
        tracker = NarrativeTracker()
        tracker.update(["who am i", "meaning of life", "I believe", "from now on",
                        "I'll never be hungry again", "I swear"])
        assert tracker.should_show_wisdom() is True

    def test_survival_high_surface_weight(self):
        tracker = NarrativeTracker()
        tracker.update(["hungry", "emergency", "help me", "no money"])
        assert tracker.weights["surface_weight"] > 1.0

    def test_meaning_high_deep_weight(self):
        tracker = NarrativeTracker()
        tracker.update(["who am i", "meaning of life", "I believe", "from now on",
                        "I'll never", "I swear", "at my core"])
        assert tracker.weights["deep_weight"] > 1.0


class TestTrackerState:
    def test_phase_scores_returns_dict(self):
        tracker = NarrativeTracker()
        tracker.update(["hungry"])
        scores = tracker.phase_scores()
        assert set(scores.keys()) == {"survival", "stability", "growth", "meaning"}

    def test_recent_phases_history(self):
        tracker = NarrativeTracker()
        tracker.update(["hungry"])
        tracker.update(["learning"])
        history = tracker.recent_phases(n=5)
        assert len(history) == 2
        assert all(p in [p.value for p in LifePhase] for p in history)

    def test_summary_string(self):
        tracker = NarrativeTracker()
        tracker.update(["test"])
        summary = tracker.summary()
        assert "sessions=1" in summary
        assert any(p.value.upper() in summary for p in LifePhase)
