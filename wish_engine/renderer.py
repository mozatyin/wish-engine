"""Wish Renderer — generates star map visual state for wishes. Zero LLM.

Produces frontend animation instructions based on wish state and level.
"""

from __future__ import annotations

import re
from typing import Any

from wish_engine.models import (
    CardType,
    ClassifiedWish,
    L1FulfillmentResult,
    L2FulfillmentResult,
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
    l2_fulfillment: L2FulfillmentResult | None = None,
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

    if l2_fulfillment:
        card["recommendations"] = [
            {
                "title": r.title,
                "description": r.description,
                "category": r.category,
                "relevance_reason": r.relevance_reason,
                "score": r.score,
                "tags": r.tags,
            }
            for r in l2_fulfillment.recommendations
        ]
        if l2_fulfillment.map_data:
            card["map_data"] = {
                "place_type": l2_fulfillment.map_data.place_type,
                "radius_km": l2_fulfillment.map_data.radius_km,
            }
        if l2_fulfillment.reminder_option:
            card["reminder"] = {
                "text": l2_fulfillment.reminder_option.text,
                "delay_hours": l2_fulfillment.reminder_option.delay_hours,
            }

    # Chocolate moment text — multilingual, Zero-AI language (V10 §7.2)
    # Detect language from wish text for reveal text
    if wish and re.search(r"[\u4e00-\u9fff]", wish.wish_text):
        reveal_lang = "zh"
    elif wish and re.search(r"[\u0600-\u06ff]", wish.wish_text):
        reveal_lang = "ar"
    else:
        reveal_lang = "en"

    _REVEAL_TEXT = {
        WishState.FOUND: {
            "en": "A wish is coming true...",
            "zh": "一个愿望正在实现...",
            "ar": "...أمنية على وشك التحقق",
        },
        WishState.FULFILLED: {
            "en": "Your stars have an answer",
            "zh": "你的星星有了答案",
            "ar": "نجومك وجدت إجابة",
        },
        WishState.RECOMMENDED: {
            "en": "Something appeared for your wish",
            "zh": "你的愿望有了回应",
            "ar": "ظهر شيء لأمنيتك",
        },
    }

    if state in _REVEAL_TEXT:
        card["reveal_text"] = _REVEAL_TEXT[state].get(reveal_lang, _REVEAL_TEXT[state]["en"])
    elif state == WishState.BORN:
        card["reveal_text"] = None

    # Animation timing (ms) — frontend uses these for sequencing
    _ANIMATION_DURATION = {
        WishState.BORN: 2000,
        WishState.SEARCHING: 3000,
        WishState.FOUND: 1500,
        WishState.RECOMMENDED: 1000,
        WishState.CONFIRMED: 800,
        WishState.FULFILLED: 2500,
        WishState.ARCHIVED: 1000,
    }
    card["animation_duration_ms"] = _ANIMATION_DURATION.get(state, 1000)
    card["animation_easing"] = "ease-in-out" if state != WishState.FULFILLED else "ease-out"

    return card


def render(
    state: WishState,
    wish: ClassifiedWish | None = None,
    fulfillment: L1FulfillmentResult | None = None,
    l2_fulfillment: L2FulfillmentResult | None = None,
) -> RenderOutput:
    """Render star map visual state for a wish.

    Zero LLM — pure state→visual mapping.

    Args:
        state: Current wish lifecycle state.
        wish: Classified wish (needed for level-dependent colors).
        fulfillment: L1 fulfillment result (included in card_data if present).
        l2_fulfillment: L2 fulfillment result (included in card_data if present).

    Returns:
        RenderOutput with star_state, color, animation, and card_data.
    """
    level = wish.level if wish else None
    color = _get_color(state, level)
    animation = _get_animation(state, level)
    card_data = _build_card_data(wish, fulfillment, state, l2_fulfillment=l2_fulfillment)

    return RenderOutput(
        star_state=state,
        color=color,
        animation=animation,
        card_data=card_data,
    )


def render_lifecycle(
    wish: ClassifiedWish,
    fulfillment: L1FulfillmentResult | None = None,
    l2_fulfillment: L2FulfillmentResult | None = None,
) -> list[RenderOutput]:
    """Render all lifecycle states for a wish (for animation sequencing).

    Returns ordered list from BORN through current state.
    """
    states = [WishState.BORN, WishState.SEARCHING, WishState.FOUND]
    if fulfillment or l2_fulfillment:
        states.extend([WishState.RECOMMENDED, WishState.CONFIRMED, WishState.FULFILLED])

    return [
        render(
            s, wish,
            fulfillment if s == WishState.FULFILLED else None,
            l2_fulfillment=l2_fulfillment if s == WishState.FULFILLED else None,
        )
        for s in states
    ]
