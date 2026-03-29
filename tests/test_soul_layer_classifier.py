"""Tests for Soul Layer Classifier — determines Surface/Middle/Deep."""

import pytest
from wish_engine.soul_layer_classifier import (
    classify_layer,
    filter_actions_by_layer,
    classify_and_filter,
    SoulLayer,
)


class TestSurfaceClassification:
    def test_im_hungry(self):
        layer, _ = classify_layer("I'm hungry")
        assert layer == SoulLayer.SURFACE

    def test_help_me(self):
        layer, _ = classify_layer("Help me find a pharmacy right now")
        assert layer == SoulLayer.SURFACE

    def test_where_is(self):
        layer, _ = classify_layer("Where is the nearest cafe?")
        assert layer == SoulLayer.SURFACE

    def test_im_sick(self):
        layer, _ = classify_layer("I'm sick and need medicine")
        assert layer == SoulLayer.SURFACE

    def test_cant_breathe(self):
        layer, _ = classify_layer("I can't breathe, help me")
        assert layer == SoulLayer.SURFACE

    def test_chinese_surface(self):
        layer, _ = classify_layer("帮我找附近有什么餐厅")
        assert layer == SoulLayer.SURFACE


class TestDeepClassification:
    def test_never_hungry_again(self):
        """THE critical test — Scarlett's vow is DEEP, not Surface."""
        layer, _ = classify_layer("I'll never be hungry again")
        assert layer == SoulLayer.DEEP

    def test_i_swear(self):
        layer, _ = classify_layer("I swear I will make them pay")
        assert layer == SoulLayer.DEEP

    def test_always(self):
        layer, _ = classify_layer("I will always love you")
        assert layer == SoulLayer.DEEP

    def test_who_am_i(self):
        layer, _ = classify_layer("Who am I really?")
        assert layer == SoulLayer.DEEP

    def test_dont_care_denial(self):
        layer, _ = classify_layer("I don't care about him anymore")
        assert layer == SoulLayer.DEEP

    def test_tomorrow_another_day(self):
        layer, _ = classify_layer("After all, tomorrow is another day")
        assert layer == SoulLayer.DEEP

    def test_from_now_on(self):
        layer, _ = classify_layer("From now on, I will be different")
        assert layer == SoulLayer.DEEP

    def test_meaning(self):
        layer, _ = classify_layer("What's the meaning of life?")
        assert layer == SoulLayer.DEEP

    def test_i_believe(self):
        layer, _ = classify_layer("I believe that people are fundamentally good")
        assert layer == SoulLayer.DEEP

    def test_chinese_deep(self):
        layer, _ = classify_layer("我发誓我永远不会再让自己这么脆弱")
        assert layer == SoulLayer.DEEP

    def test_reflection(self):
        layer, _ = classify_layer("Looking back, I realize I was wrong about everything")
        assert layer == SoulLayer.DEEP


class TestMiddleClassification:
    def test_recurring_topic(self):
        layer, _ = classify_layer("I was thinking about yoga today", topic_history={"yoga": 8})
        assert layer == SoulLayer.MIDDLE

    def test_low_count_not_middle(self):
        layer, _ = classify_layer("I tried yoga once", topic_history={"yoga": 1})
        assert layer != SoulLayer.MIDDLE


class TestFilterActions:
    def test_surface_blocks_wisdom(self):
        actions = [
            {"cat": "food", "fn": "meal"},
            {"cat": "wisdom", "fn": "quote"},
            {"cat": "place", "fn": "search"},
        ]
        filtered = filter_actions_by_layer(actions, SoulLayer.SURFACE)
        cats = [a["cat"] for a in filtered]
        assert "food" in cats
        assert "place" in cats
        assert "wisdom" not in cats

    def test_deep_blocks_food(self):
        actions = [
            {"cat": "food", "fn": "meal"},
            {"cat": "wisdom", "fn": "quote"},
            {"cat": "poetry", "fn": "poem"},
        ]
        filtered = filter_actions_by_layer(actions, SoulLayer.DEEP)
        cats = [a["cat"] for a in filtered]
        assert "food" not in cats
        assert "wisdom" in cats
        assert "poetry" in cats

    def test_middle_allows_books(self):
        actions = [
            {"cat": "books", "fn": "search"},
            {"cat": "crisis", "fn": "hotline"},
        ]
        filtered = filter_actions_by_layer(actions, SoulLayer.MIDDLE)
        cats = [a["cat"] for a in filtered]
        assert "books" in cats
        assert "crisis" not in cats


class TestClassifyAndFilter:
    def test_hungry_gets_food_not_wisdom(self):
        actions = [{"cat": "food"}, {"cat": "wisdom"}, {"cat": "place"}]
        layer, _, filtered = classify_and_filter("I'm hungry right now", actions)
        assert layer == SoulLayer.SURFACE
        assert any(a["cat"] == "food" for a in filtered)
        assert not any(a["cat"] == "wisdom" for a in filtered)

    def test_never_hungry_gets_wisdom_not_food(self):
        actions = [{"cat": "food"}, {"cat": "wisdom"}, {"cat": "poetry"}]
        layer, _, filtered = classify_and_filter("I'll never be hungry again", actions)
        assert layer == SoulLayer.DEEP
        assert not any(a["cat"] == "food" for a in filtered)
        assert any(a["cat"] == "wisdom" for a in filtered)
