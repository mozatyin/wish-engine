"""Tests for Wish Renderer — star map visual state generation."""

import pytest

from wish_engine.models import (
    CardType,
    ClassifiedWish,
    L1FulfillmentResult,
    RenderOutput,
    WishLevel,
    WishState,
    WishType,
)
from wish_engine.renderer import render, render_lifecycle


# ── Helper factories ─────────────────────────────────────────────────────────


def _make_wish(wish_type=WishType.SELF_UNDERSTANDING, level=WishLevel.L1):
    return ClassifiedWish(
        wish_text="test wish",
        wish_type=wish_type,
        level=level,
        fulfillment_strategy="test",
    )


def _make_fulfillment():
    return L1FulfillmentResult(
        fulfillment_text="Your insight text here.",
        related_stars=["conflict:avoiding", "attachment:anxious"],
        card_type=CardType.INSIGHT,
    )


# ── Color mapping ────────────────────────────────────────────────────────────


class TestColors:
    """V10 §5.2 color palette."""

    def test_born_pale_purple(self):
        out = render(WishState.BORN)
        assert out.color == "#8B7BA8"

    def test_searching_silver(self):
        out = render(WishState.SEARCHING)
        assert out.color == "#C0C0D0"

    def test_found_l1_gold(self):
        wish = _make_wish(level=WishLevel.L1)
        out = render(WishState.FOUND, wish=wish)
        assert out.color == "#D4A853"

    def test_found_l2_blue(self):
        wish = _make_wish(wish_type=WishType.FIND_PLACE, level=WishLevel.L2)
        out = render(WishState.FOUND, wish=wish)
        assert out.color == "#4A90D9"

    def test_found_l3_purple(self):
        wish = _make_wish(wish_type=WishType.FIND_COMPANION, level=WishLevel.L3)
        out = render(WishState.FOUND, wish=wish)
        assert out.color == "#9B59B6"

    def test_fulfilled_warm_gold(self):
        out = render(WishState.FULFILLED)
        assert out.color == "#F4C542"

    def test_archived_dimmed_gold(self):
        out = render(WishState.ARCHIVED)
        assert out.color == "#B8A040"


# ── Animation mapping ────────────────────────────────────────────────────────


class TestAnimations:
    def test_born_pulse_dim(self):
        out = render(WishState.BORN)
        assert out.animation == "pulse_dim"

    def test_searching_rotate_slow(self):
        out = render(WishState.SEARCHING)
        assert out.animation == "rotate_slow"

    def test_found_l1_gold_halo(self):
        wish = _make_wish(level=WishLevel.L1)
        out = render(WishState.FOUND, wish=wish)
        assert out.animation == "brighten_gold_halo"

    def test_found_l2_blue_wave(self):
        wish = _make_wish(wish_type=WishType.FIND_PLACE, level=WishLevel.L2)
        out = render(WishState.FOUND, wish=wish)
        assert out.animation == "pulse_blue_wave"

    def test_found_l3_purple_extend(self):
        wish = _make_wish(wish_type=WishType.FIND_COMPANION, level=WishLevel.L3)
        out = render(WishState.FOUND, wish=wish)
        assert out.animation == "glow_purple_extend"

    def test_fulfilled_burst(self):
        out = render(WishState.FULFILLED)
        assert out.animation == "burst_gold_particles"

    def test_archived_fade(self):
        out = render(WishState.ARCHIVED)
        assert out.animation == "fade_permanent"


# ── Card data ────────────────────────────────────────────────────────────────


class TestCardData:
    def test_born_no_reveal_text(self):
        out = render(WishState.BORN)
        assert out.card_data.get("reveal_text") is None

    def test_found_reveal_text(self):
        wish = _make_wish()
        out = render(WishState.FOUND, wish=wish)
        assert out.card_data["reveal_text"] == "A wish is coming true..."

    def test_fulfilled_reveal_text(self):
        out = render(WishState.FULFILLED, fulfillment=_make_fulfillment())
        assert out.card_data["reveal_text"] == "Your stars have an answer"

    def test_card_data_includes_wish(self):
        wish = _make_wish()
        out = render(WishState.FOUND, wish=wish)
        assert out.card_data["wish_text"] == "test wish"
        assert out.card_data["wish_type"] == "self_understanding"
        assert out.card_data["level"] == "L1"

    def test_card_data_includes_fulfillment(self):
        fulfillment = _make_fulfillment()
        wish = _make_wish()
        out = render(WishState.FULFILLED, wish=wish, fulfillment=fulfillment)
        assert out.card_data["fulfillment_text"] == "Your insight text here."
        assert out.card_data["card_type"] == "insight"
        assert "conflict:avoiding" in out.card_data["related_stars"]


# ── Render output structure ──────────────────────────────────────────────────


class TestRenderOutputStructure:
    def test_output_is_pydantic(self):
        out = render(WishState.BORN)
        assert isinstance(out, RenderOutput)

    def test_serializable(self):
        wish = _make_wish()
        fulfillment = _make_fulfillment()
        out = render(WishState.FULFILLED, wish=wish, fulfillment=fulfillment)
        data = out.model_dump()
        assert data["star_state"] == "fulfilled"
        assert isinstance(data["card_data"], dict)


# ── Lifecycle rendering ──────────────────────────────────────────────────────


class TestRenderLifecycle:
    def test_lifecycle_without_fulfillment(self):
        wish = _make_wish()
        stages = render_lifecycle(wish)
        assert len(stages) == 3  # born, searching, found
        assert stages[0].star_state == WishState.BORN
        assert stages[1].star_state == WishState.SEARCHING
        assert stages[2].star_state == WishState.FOUND

    def test_lifecycle_with_fulfillment(self):
        wish = _make_wish()
        fulfillment = _make_fulfillment()
        stages = render_lifecycle(wish, fulfillment=fulfillment)
        assert len(stages) == 6  # born through fulfilled
        assert stages[0].star_state == WishState.BORN
        assert stages[-1].star_state == WishState.FULFILLED

    def test_lifecycle_found_has_correct_color(self):
        wish = _make_wish(level=WishLevel.L1)
        stages = render_lifecycle(wish)
        found_stage = stages[2]
        assert found_stage.color == "#D4A853"  # gold for L1

    def test_lifecycle_fulfilled_has_card_data(self):
        wish = _make_wish()
        fulfillment = _make_fulfillment()
        stages = render_lifecycle(wish, fulfillment=fulfillment)
        fulfilled_stage = stages[-1]
        assert fulfilled_stage.card_data.get("fulfillment_text") == "Your insight text here."


# ── Zero-AI language compliance ──────────────────────────────────────────────


class TestZeroAILanguage:
    """V10 §7.2: Never say AI, algorithm, model, etc."""

    def test_found_text_no_ai_terms(self):
        wish = _make_wish()
        out = render(WishState.FOUND, wish=wish)
        text = out.card_data.get("reveal_text", "")
        banned = ["AI", "algorithm", "model", "detect", "compute", "analyze", "score"]
        for word in banned:
            assert word.lower() not in text.lower()

    def test_fulfilled_text_no_ai_terms(self):
        out = render(WishState.FULFILLED, fulfillment=_make_fulfillment())
        text = out.card_data.get("reveal_text", "")
        banned = ["AI", "algorithm", "model", "detect", "compute", "analyze", "score"]
        for word in banned:
            assert word.lower() not in text.lower()
