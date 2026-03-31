"""Soul Layer Classifier — determines which Soul layer a statement belongs to.

The most critical module in the system. A wrong layer = wrong API = wrong star.

Rules:
  Surface (表层): Literal, present-tense, immediate needs
    → Physical world APIs (places, food, weather, directions, medicine)
    Signal: "I am...", "I need...", "right now", "help me", "where is..."

  Middle (中层): Recurring patterns, interests, gradual growth
    → Growth APIs (books, courses, communities, podcasts, skills)
    Signal: Topic appears 3+ times across sessions

  Deep (底层): Vows, beliefs, contradictions, hidden desires
    → Wisdom APIs (poetry, philosophy, reflection, spiritual, Compass)
    Signal: "never", "always", "swear", "I will", "I must", contradictions

The key test:
  "I'm hungry" → Surface (literal, right now) → find restaurant
  "I'll never be hungry again" → Deep (vow, life principle) → Stoic wisdom about resilience
  "I keep thinking about food" (over weeks) → Middle (recurring) → cooking class
"""

from __future__ import annotations

import re
import time
from typing import Any


class SoulLayer:
    SURFACE = "surface"  # 表层: 当下即时需求 → 物理世界
    MIDDLE = "middle"    # 中层: 历史持续关注 → 学习世界
    DEEP = "deep"        # 底层: 核心信念/隐藏 → 智慧世界


# ── Deep Layer Markers ───────────────────────────────────────────────────────

# These words signal a DEEP statement (vow, belief, life principle)
_DEEP_MARKERS = {
    # Vows and absolutes
    "never", "always", "forever", "i swear", "i promise", "i vow",
    "i will never", "i'll never", "not ever", "no one will ever",
    "i must", "i have to", "i refuse to",
    # Existential
    "who am i", "what's the point", "meaning of life", "why do i exist",
    "what kind of person", "i don't know who i am",
    # Beliefs
    "i believe", "i know that", "the truth is", "deep down",
    "fundamentally", "at my core", "in my heart",
    # Denial masking depth
    "i don't care about", "doesn't matter to me", "i'm over",
    "moved on from", "i'm fine with",
    # Life declarations
    "from now on", "this changes everything", "the old me is dead",
    "i am not", "i will become", "tomorrow is another day",
    # Chinese deep markers
    "永远", "绝不", "我发誓", "我必须", "从此以后", "我不在乎",
    "意义", "我是谁", "在我心里", "我相信",
    # Arabic deep markers
    "أبداً", "دائماً", "أقسم", "يجب أن", "لن أكون", "في قلبي",
}

# Past tense and reflection markers (not immediate need)
_REFLECTION_MARKERS = {
    "i used to", "looking back", "i remember when", "years ago",
    "when i was young", "before the war", "back then", "once upon",
    "曾经", "以前", "回忆", "那时候",
}

# ── Surface Layer Markers ────────────────────────────────────────────────────

# These signal IMMEDIATE, LITERAL, PRESENT needs
_SURFACE_MARKERS = {
    # Present tense urgency
    "right now", "help me", "i need to find", "where is",
    "i'm having a", "i can't breathe", "emergency",
    "currently", "at this moment", "i am currently",
    # Direct requests
    "find me", "show me", "take me to", "how do i get to",
    "is there a", "nearest", "closest", "nearby",
    # Physical state
    "i'm starving", "i'm freezing", "i'm burning up",
    "i'm bleeding", "i'm sick", "i feel dizzy",
    # Chinese surface
    "现在", "马上", "紧急", "帮我找", "附近有", "我在",
    # Arabic surface
    "الآن", "ساعدني", "أين", "أقرب",
}


def classify_layer(text: str, topic_history: dict[str, int] | None = None) -> tuple[str, str]:
    """Classify which Soul layer a statement belongs to.

    Returns:
        (layer, reason) — e.g., ("deep", "contains vow marker 'never'")
    """
    text_lower = text.lower()

    # ── Check DEEP first (vows/beliefs override surface keywords) ────
    for marker in _DEEP_MARKERS:
        if marker in text_lower:
            return SoulLayer.DEEP, f"vow/belief marker: '{marker}'"

    # ── Check REFLECTION (past tense = not immediate) ────────────────
    for marker in _REFLECTION_MARKERS:
        if marker in text_lower:
            return SoulLayer.DEEP, f"reflection marker: '{marker}'"

    # ── Check SURFACE (immediate, present, literal) ──────────────────
    for marker in _SURFACE_MARKERS:
        if marker in text_lower:
            return SoulLayer.SURFACE, f"immediate marker: '{marker}'"

    # ── Present tense "I am [state]" = Surface ───────────────────────
    if re.search(r"\bi(?:'m| am)\s+(hungry|thirsty|tired|cold|hot|sick|scared|lost|lonely|angry)\b", text_lower):
        return SoulLayer.SURFACE, "present-tense state: 'I am [state]'"

    # ── Check MIDDLE (topic in history 3+ times) ─────────────────────
    if topic_history:
        words = set(text_lower.split())
        for topic, count in topic_history.items():
            if count >= 3 and topic.lower() in text_lower:
                return SoulLayer.MIDDLE, f"recurring topic '{topic}' ({count}x)"

    # ── Default: Surface unless explicit Deep markers were found above ────────
    # Long messages are NOT Deep by default — a user describing their hunger
    # or relationship pain in many words is still a Surface need.
    # Deep requires explicit vow/belief language or Compass-level signals.
    return SoulLayer.SURFACE, "default (no deep markers detected)"


# ── Layer → API Category Rules ───────────────────────────────────────────────

# What TYPE of API each layer should call
LAYER_API_CATEGORIES = {
    SoulLayer.SURFACE: {
        "allowed": ["place", "food", "drink", "health", "safety", "weather", "crisis",
                     "utility", "prayer", "calm", "exercise", "sleep"],
        "description": "Physical world — places, food, weather, immediate help",
        "forbidden": ["wisdom", "poetry", "reflection", "philosophy", "meaning"],
    },
    SoulLayer.MIDDLE: {
        "allowed": ["books", "learning", "art", "music", "social", "exercise",
                     "work", "confidence", "culture", "explore", "fun"],
        "description": "Growth world — books, courses, communities, skills",
        "forbidden": ["crisis", "medicine", "weather"],
    },
    SoulLayer.DEEP: {
        "allowed": ["wisdom", "poetry", "reflection", "meaning", "mindfulness",
                     "grief", "healing", "confidence"],
        "description": "Wisdom world — poetry, philosophy, self-reflection, spiritual",
        "forbidden": ["food", "drink", "place", "weather", "utility", "finance"],
    },
}


def filter_actions_by_layer(actions: list[dict], layer: str) -> list[dict]:
    """Filter API actions to only those appropriate for the Soul layer."""
    rules = LAYER_API_CATEGORIES.get(layer)
    if not rules:
        return actions

    allowed = set(rules["allowed"])
    forbidden = set(rules["forbidden"])

    filtered = []
    for action in actions:
        cat = action.get("cat", "")
        if cat in forbidden:
            continue
        if cat in allowed:
            filtered.append(action)
            continue
        # If not in allowed or forbidden, let it through (permissive for unknown categories)
        filtered.append(action)

    return filtered


def classify_and_filter(text: str, actions: list[dict], topic_history: dict[str, int] | None = None) -> tuple[str, str, list[dict]]:
    """Classify layer and filter actions in one call.

    Returns:
        (layer, reason, filtered_actions)
    """
    layer, reason = classify_layer(text, topic_history)
    filtered = filter_actions_by_layer(actions, layer)
    return layer, reason, filtered


# ── Cross-Layer Suppression ───────────────────────────────────────────────────

# When a Deep vow fires, these Surface categories are suppressed for N hours.
# "I'll never be hungry again" → suppress food/drink/restaurant for 72h
_VOW_TOPIC_CATEGORIES: dict[str, set[str]] = {
    "food":         {"food", "drink"},
    "love":         {"social", "dating"},
    "pain":         {"fun", "celebration", "party"},
    "money":        {"shopping", "luxury", "finance"},
    "anger":        {"calm", "mindfulness"},   # anger vow → don't soothe, empower
    "identity":     {"place", "utility"},      # "who am I" → no quick errands
}

# Keyword → vow topic mapping
_VOW_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "food":     ["hungry", "hunger", "food", "eat", "eating", "starving", "fed", "fed up", "饥饿", "吃", "挨饿", "饿"],
    "love":     ["love", "loved", "lover", "heart", "him", "her", "rhett", "ashley", "relationship",
                 "爱", "他", "她", "感情"],
    "pain":     ["hurt", "pain", "cry", "tears", "grief", "loss", "die", "dead", "suffer", "痛", "哭"],
    "money":    ["money", "poor", "rich", "dollar", "afford", "debt", "broke", "钱", "穷", "富"],
    "anger":    ["pay", "revenge", "hate", "fury", "furious", "make them", "恨", "报复"],
    "identity": ["who i am", "who am i", "myself", "person i", "我是谁", "我自己"],
}


def _extract_vow_topic(text: str) -> str | None:
    """Extract the primary topic of a Deep vow statement."""
    text_lower = text.lower()
    for topic, keywords in _VOW_TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return topic
    return None


class VowSuppressor:
    """Tracks active Deep vows and blocks conflicting Surface API categories.

    When "I'll never be hungry again" fires as a Deep vow, food and drink
    recommendations are suppressed for 72 hours — Scarlett doesn't need a
    restaurant suggestion right after making her life-defining vow.
    """

    def __init__(self, default_hours: int = 72):
        self._default_hours = default_hours
        # topic → unix expiry timestamp
        self._suppressions: dict[str, float] = {}

    def record(self, text: str, layer: str, hours: int | None = None) -> str | None:
        """If layer is DEEP, extract topic and start suppression. Returns topic or None."""
        if layer != SoulLayer.DEEP:
            return None
        topic = _extract_vow_topic(text)
        if topic:
            duration = hours if hours is not None else self._default_hours
            self._suppressions[topic] = time.time() + duration * 3600
        return topic

    # Urgent physical attentions that override vow suppression for their category.
    # "I'll never eat junk food again" is a vow — but if the user is genuinely
    # hungry the next day, the restaurant recommendation must still fire.
    _URGENCY_OVERRIDE: dict[str, frozenset[str]] = {
        "food":   frozenset({"hungry", "starving", "famished"}),
        "drink":  frozenset({"thirsty", "dehydrated"}),
        "health": frozenset({"need_medicine", "headache", "panicking"}),
        "crisis": frozenset({"panicking", "scared"}),
    }

    def is_suppressed(self, cat: str, current_attentions: list[str] | None = None) -> bool:
        """Return True if this API category is currently blocked by an active vow.

        Args:
            cat:                API category string (e.g. "food", "drink").
            current_attentions: Surface attentions detected right now.
                                If an urgent physical need is present for this
                                category, the suppression is bypassed.
        """
        # Urgency override: real physical need beats a prior vow
        if current_attentions:
            urgent = self._URGENCY_OVERRIDE.get(cat, frozenset())
            if urgent & set(current_attentions):
                return False

        now = time.time()
        expired = [t for t, exp in self._suppressions.items() if exp < now]
        for t in expired:
            del self._suppressions[t]

        for topic, expiry in self._suppressions.items():
            if expiry >= now and cat in _VOW_TOPIC_CATEGORIES.get(topic, set()):
                return True
        return False

    def active_suppressions(self) -> dict[str, float]:
        """Return {topic: hours_remaining} for active suppressions."""
        now = time.time()
        return {
            topic: (expiry - now) / 3600
            for topic, expiry in self._suppressions.items()
            if expiry > now
        }

    def clear(self) -> None:
        self._suppressions.clear()
