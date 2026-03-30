"""Tests for Star Feedback Loop (Improvement #3)."""
import pytest
from wish_engine.star_feedback import StarFeedbackStore, StarRecord


class TestStarRecord:
    def test_ctr_zero_with_no_clicks(self):
        r = StarRecord(attention="hungry", impressions=5, clicks=0)
        assert r.ctr == 0.0

    def test_ctr_one_with_all_clicks(self):
        r = StarRecord(attention="hungry", impressions=5, clicks=5)
        assert r.ctr == 1.0

    def test_ctr_half(self):
        r = StarRecord(attention="hungry", impressions=10, clicks=5)
        assert r.ctr == 0.5

    def test_ctr_default_when_no_impressions(self):
        r = StarRecord(attention="hungry")
        assert r.ctr == 0.5  # Neutral default

    def test_weight_neutral_with_few_impressions(self):
        r = StarRecord(attention="hungry", impressions=2, clicks=2)
        assert r.weight == 1.0  # Not enough data

    def test_weight_high_with_high_ctr(self):
        r = StarRecord(attention="hungry", impressions=10, clicks=9)
        assert r.weight > 1.5

    def test_weight_low_with_low_ctr_and_dismissals(self):
        r = StarRecord(attention="hungry", impressions=10, clicks=0, dismissals=8)
        assert r.weight < 0.5

    def test_weight_clamped_between_03_and_20(self):
        r = StarRecord(attention="hungry", impressions=100, clicks=100)
        assert 0.3 <= r.weight <= 2.0
        r2 = StarRecord(attention="hungry", impressions=100, clicks=0, dismissals=100)
        assert 0.3 <= r2.weight <= 2.0


class TestStarFeedbackStore:
    def test_impression_recorded(self):
        store = StarFeedbackStore()
        store.impression("hungry")
        assert store.stats()["hungry"]["impressions"] == 1

    def test_click_recorded(self):
        store = StarFeedbackStore()
        store.impression("hungry")
        store.click("hungry")
        assert store.stats()["hungry"]["clicks"] == 1

    def test_dismiss_recorded(self):
        store = StarFeedbackStore()
        store.impression("anxious")
        store.dismiss("anxious")
        assert store.stats()["anxious"]["dismissals"] == 1

    def test_weight_neutral_with_few_data(self):
        store = StarFeedbackStore()
        store.impression("new_attention")
        assert store.weight("new_attention") == 1.0

    def test_weight_increases_with_clicks(self):
        store = StarFeedbackStore()
        for _ in range(10):
            store.impression("hungry")
            store.click("hungry")
        assert store.weight("hungry") > 1.2

    def test_weight_decreases_with_dismissals(self):
        store = StarFeedbackStore()
        for _ in range(10):
            store.impression("anxious")
            store.dismiss("anxious")
        assert store.weight("anxious") < 0.8

    def test_unknown_attention_returns_neutral(self):
        store = StarFeedbackStore()
        assert store.weight("never_seen") == 1.0

    def test_top_attentions(self):
        store = StarFeedbackStore()
        # Make "hungry" high engagement
        for _ in range(5):
            store.impression("hungry")
            store.click("hungry")
        # Make "anxious" low engagement
        for _ in range(5):
            store.impression("anxious")
        top = store.top_attentions(n=1)
        assert top[0][0] == "hungry"

    def test_weak_attentions(self):
        store = StarFeedbackStore()
        for _ in range(5):
            store.impression("anxious")
            store.dismiss("anxious")
        weak = store.weak_attentions(threshold=0.8)
        assert "anxious" in weak

    def test_sort_actions_by_weight(self):
        store = StarFeedbackStore()
        # Make "hungry" high engagement
        for _ in range(5):
            store.impression("hungry")
            store.click("hungry")

        actions = [
            {"cat": "food", "attention": "anxious"},
            {"cat": "place", "attention": "hungry"},
        ]
        sorted_actions = store.sort_actions_by_weight(actions)
        # hungry should come first (higher weight)
        assert sorted_actions[0]["attention"] == "hungry"

    def test_click_before_impression_guards(self):
        """Click without impression shouldn't crash."""
        store = StarFeedbackStore()
        store.click("hungry")  # Out of order — should not crash
        assert store.stats()["hungry"]["clicks"] == 1
