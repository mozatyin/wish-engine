"""Tests for Cross-Layer Vow Suppressor (Improvement #2)."""
import time
import pytest
from wish_engine.soul_layer_classifier import VowSuppressor, SoulLayer


class TestVowSuppressionBasics:
    def test_deep_vow_records_food_suppression(self):
        sup = VowSuppressor()
        topic = sup.record("I'll never be hungry again", SoulLayer.DEEP)
        assert topic == "food"

    def test_surface_statement_does_not_record(self):
        sup = VowSuppressor()
        topic = sup.record("I'm hungry right now", SoulLayer.SURFACE)
        assert topic is None

    def test_food_suppresses_food_cat(self):
        sup = VowSuppressor()
        sup.record("I'll never be hungry again", SoulLayer.DEEP)
        assert sup.is_suppressed("food") is True

    def test_food_suppresses_drink_cat(self):
        sup = VowSuppressor()
        sup.record("I'll never be hungry again", SoulLayer.DEEP)
        assert sup.is_suppressed("drink") is True

    def test_food_does_not_suppress_wisdom(self):
        sup = VowSuppressor()
        sup.record("I'll never be hungry again", SoulLayer.DEEP)
        assert sup.is_suppressed("wisdom") is False

    def test_food_does_not_suppress_place(self):
        sup = VowSuppressor()
        sup.record("I'll never be hungry again", SoulLayer.DEEP)
        assert sup.is_suppressed("place") is False

    def test_love_suppresses_social_dating(self):
        sup = VowSuppressor()
        sup.record("I will always love you", SoulLayer.DEEP)
        assert sup.is_suppressed("social") is True
        assert sup.is_suppressed("dating") is True

    def test_love_does_not_suppress_food(self):
        sup = VowSuppressor()
        sup.record("I will always love you", SoulLayer.DEEP)
        assert sup.is_suppressed("food") is False

    def test_anger_vow_suppresses_calm(self):
        sup = VowSuppressor()
        sup.record("I swear I will make them pay", SoulLayer.DEEP)
        assert sup.is_suppressed("calm") is True
        assert sup.is_suppressed("mindfulness") is True

    def test_no_suppression_when_empty(self):
        sup = VowSuppressor()
        assert sup.is_suppressed("food") is False
        assert sup.is_suppressed("wisdom") is False


class TestVowSuppressionExpiry:
    def test_suppression_expires_after_duration(self):
        sup = VowSuppressor()
        # Record with very short duration (0.001 hours = 3.6 seconds)
        sup.record("I'll never be hungry again", SoulLayer.DEEP, hours=0)
        # Wait a tiny bit
        time.sleep(0.01)
        # Should be expired and cleaned up
        assert sup.is_suppressed("food") is False

    def test_active_suppressions_shows_remaining_hours(self):
        sup = VowSuppressor()
        sup.record("I'll never be hungry again", SoulLayer.DEEP, hours=24)
        active = sup.active_suppressions()
        assert "food" in active
        assert 0 < active["food"] <= 24

    def test_clear_removes_all(self):
        sup = VowSuppressor()
        sup.record("I'll never be hungry again", SoulLayer.DEEP)
        sup.clear()
        assert sup.is_suppressed("food") is False
        assert sup.active_suppressions() == {}


class TestVowTopicExtraction:
    def test_chinese_hunger_vow(self):
        sup = VowSuppressor()
        topic = sup.record("我发誓我永远不会再让自己挨饿", SoulLayer.DEEP)
        assert topic == "food"

    def test_chinese_love_vow(self):
        sup = VowSuppressor()
        topic = sup.record("我永远不会再爱了", SoulLayer.DEEP)
        assert topic == "love"

    def test_pain_topic_detected(self):
        sup = VowSuppressor()
        topic = sup.record("I'll never let grief destroy me again", SoulLayer.DEEP)
        assert topic == "pain"

    def test_multiple_vows_stack(self):
        """Multiple vows can be active simultaneously."""
        sup = VowSuppressor()
        sup.record("I'll never be hungry again", SoulLayer.DEEP)
        sup.record("I swear I will make them pay", SoulLayer.DEEP)
        assert sup.is_suppressed("food") is True
        assert sup.is_suppressed("calm") is True
