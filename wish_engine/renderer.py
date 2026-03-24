"""Wish Renderer — generates star map visual state for wishes. Zero LLM.

Produces frontend animation instructions based on wish state and level.
"""

from __future__ import annotations

from typing import Any

from wish_engine.models import (
    CardType,
    ClassifiedWish,
    L1FulfillmentResult,
    RenderOutput,
    WishLevel,
    WishState,
)

# ── Color palette (from V10 design doc §5.2) ────────────────────────────────

_STATE_COLORS: dict[tuple[WishState, WishLevel | None], str] = {
    # Born: always pale purple
    (WishState.BORN, None): "#8B7BA8",
    # Searching: always silver-white
    (WishState.SEARCHING, None): "#C0C0D0",
    # Found: depends on level
    (WishState.FOUND, WishLevel.L1): "#D4A853",  # gold
    (WishState.FOUND, WishLevel.L2): "#4A90D9",  # star blue
    (WishState.FOUND, WishLevel.L3): "#9B59B6",  # purple
    # Recommended/Confirmed: same as Found
    (WishState.RECOMMENDED, WishLevel.L1): "#D4A853",
    (WishState.RECOMMENDED, WishLevel.L2): "#4A90D9",
    (WishState.RECOMMENDED, WishLevel.L3): "#9B59B6",
    (WishState.CONFIRMED, WishLevel.L1): "#D4A853",
    (WishState.CONFIRMED, WishLevel.L2): "#4A90D9",
    (WishState.CONFIRMED, WishLevel.L3): "#9B59B6",
    # Fulfilled: warm gold
    (WishState.FULFILLED, None): "#F4C542",
    # Archived: dimmed gold
    (WishState.ARCHIVED, None): "#B8A040",
}

# ── Animation types ──────────────────────────────────────────────────────────

_STATE_ANIMATIONS: dict[WishState, str] = {
    WishState.BORN: "pulse_dim",
    WishState.SEARCHING: "rotate_slow",
    WishState.FOUND: "brighten_halo",
    WishState.RECOMMENDED: "glow_steady",
    WishState.CONFIRMED: "glow_expand",
    WishState.FULFILLED: "burst_gold_particles",
    WishState.ARCHIVED: "fade_permanent",
}

# Level-specific animation overrides for FOUND state
_FOUND_ANIMATIONS: dict[WishLevel, str] = {
    WishLevel.L1: "brighten_gold_halo",
    WishLevel.L2: "pulse_blue_wave",
    WishLevel.L3: "glow_purple_extend",
}


def _get_color(state: WishState, level: WishLevel | None) -> str:
    """Resolve star color from state + level."""
    # Try exact (state, level) match first
    if level is not None:
        color = _STATE_COLORS.get((state, level))
        if color:
            return color
    # Fall back to (state, None)
    return _STATE_COLORS.get((state, None), "#8B7BA8")


def _get_animation(state: WishState, level: WishLevel | None) -> str:
    """Resolve animation type from state + level."""
    if state == WishState.FOUND and level is not None:
        return _FOUND_ANIMATIONS.get(level, _STATE_ANIMATIONS[WishState.FOUND])
    return _STATE_ANIMATIONS.get(state, "pulse_dim")


def _build_card_data(
    wish: ClassifiedWish | None,
    fulfillment: L1FulfillmentResult | None,
    state: WishState,
) -> dict[str, Any]:
    """Build frontend card data payload."""
    card: dict[str, Any] = {}

    if wish:
        card["wish_text"] = wish.wish_text
        card["wish_type"] = wish.wish_type.value
        card["level"] = wish.level.value

    if fulfillment:
        card["fulfillment_text"] = fulfillment.fulfillment_text
        card["card_type"] = fulfillment.card_type.value
        card["related_stars"] = fulfillment.related_stars

    # Chocolate moment text (Zero-AI language)
    if state == WishState.FOUND:
        card["reveal_text"] = "A wish is coming true..."
    elif state == WishState.FULFILLED:
        card["reveal_text"] = "Your stars have an answer"
    elif state == WishState.BORN:
        card["reveal_text"] = None  # no text for born stars

    return card


def render(
    state: WishState,
    wish: ClassifiedWish | None = None,
    fulfillment: L1FulfillmentResult | None = None,
) -> RenderOutput:
    """Render star map visual state for a wish.

    Zero LLM — pure state→visual mapping.

    Args:
        state: Current wish lifecycle state.
        wish: Classified wish (needed for level-dependent colors).
        fulfillment: L1 fulfillment result (included in card_data if present).

    Returns:
        RenderOutput with star_state, color, animation, and card_data.
    """
    level = wish.level if wish else None
    color = _get_color(state, level)
    animation = _get_animation(state, level)
    card_data = _build_card_data(wish, fulfillment, state)

    return RenderOutput(
        star_state=state,
        color=color,
        animation=animation,
        card_data=card_data,
    )


def render_lifecycle(
    wish: ClassifiedWish,
    fulfillment: L1FulfillmentResult | None = None,
) -> list[RenderOutput]:
    """Render all lifecycle states for a wish (for animation sequencing).

    Returns ordered list from BORN through current state.
    """
    states = [WishState.BORN, WishState.SEARCHING, WishState.FOUND]
    if fulfillment:
        states.extend([WishState.RECOMMENDED, WishState.CONFIRMED, WishState.FULFILLED])

    return [render(s, wish, fulfillment if s == WishState.FULFILLED else None) for s in states]
