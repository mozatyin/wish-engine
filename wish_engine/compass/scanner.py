"""DialogueScanner — extracts topic signals from dialogue text.

Detects entity mentions, estimates sentiment and arousal from lexical cues.
Replaces ad-hoc topic simulation with a reusable, testable component.
Zero LLM.
"""

from __future__ import annotations

import re
from typing import Any


# Emotion word lists for arousal/sentiment estimation
_NEGATIVE_WORDS = {
    "hate", "horrible", "fool", "cad", "furious", "anger", "despise",
    "disgusting", "terrible", "awful", "loathe", "resent", "bitter",
    "jealous", "envy", "humiliation", "shame", "guilt", "worthless",
    "pathetic", "weak", "failure", "betray", "abandon", "reject",
    "damn", "hell", "kill", "destroy", "rage", "contempt",
}
_POSITIVE_WORDS = {
    "love", "adore", "beautiful", "wonderful", "admire", "joy", "happy",
    "delight", "treasure", "cherish", "brilliant", "magnificent", "perfect",
    "trust", "respect", "grateful", "hope", "dream", "desire", "want",
    "need", "miss", "long", "yearn", "care", "devoted",
}
_HIGH_AROUSAL_WORDS = {
    "extraordinary", "obsess", "desperate", "cannot stop", "burning",
    "intoxicat", "fever", "madness", "wild", "overwhelm", "tremble",
    "heart", "pulse", "breathless", "electri", "consumed", "haunt",
    "possess", "torment", "agony", "ecstasy", "fire", "blaze",
    "signal fire", "demolish", "empire", "power", "invincible",
    "everything", "nothing", "forever", "never", "always",
}
_DENIAL_WORDS = {
    "don't care", "doesn't matter", "not important", "I'm fine",
    "don't need", "not interested", "over it", "moved on",
    "couldn't care less", "irrelevant", "meaningless",
}


class DialogueScanner:
    """Extracts topic signals from dialogue text for Compass consumption."""

    def __init__(self, entity_names: dict[str, list[str]] | None = None):
        """
        Args:
            entity_names: Optional dict mapping canonical entity name to aliases.
                e.g. {"Rhett": ["rhett", "butler", "captain butler"],
                       "Ashley": ["ashley", "wilkes"]}
        """
        self._entities = entity_names or {}

    def scan_dialogue(self, text: str, session_id: str = "") -> list[dict[str, Any]]:
        """Extract topic signals from a single dialogue line.

        Returns list of topic dicts with: entity, sentiment, arousal, mentions.
        """
        text_lower = text.lower()
        topics = []

        for entity_name, aliases in self._entities.items():
            if any(alias in text_lower for alias in aliases):
                sentiment = self._estimate_sentiment(text_lower)
                arousal = self._estimate_arousal(text_lower)
                topics.append({
                    "entity": entity_name,
                    "sentiment": sentiment,
                    "arousal": arousal,
                    "mentions": sum(1 for a in aliases if a in text_lower),
                })

        return topics

    def scan_batch(self, dialogues: list[dict], session_id: str = "") -> list[dict[str, Any]]:
        """Scan multiple dialogue lines, aggregate per entity."""
        entity_signals: dict[str, dict] = {}
        for d in dialogues:
            text = d.get("text", "")
            for topic in self.scan_dialogue(text, session_id):
                entity = topic["entity"]
                if entity in entity_signals:
                    existing = entity_signals[entity]
                    existing["arousal"] = max(existing["arousal"], topic["arousal"])
                    existing["mentions"] += topic["mentions"]
                    # Sentiment: if any negative with high arousal, mark as negative
                    if topic["sentiment"] == "negative" and topic["arousal"] > 0.5:
                        existing["sentiment"] = "negative"
                else:
                    entity_signals[entity] = dict(topic)
        return list(entity_signals.values())

    def _estimate_sentiment(self, text: str) -> str:
        neg = sum(1 for w in _NEGATIVE_WORDS if w in text)
        pos = sum(1 for w in _POSITIVE_WORDS if w in text)
        denial = any(d in text for d in _DENIAL_WORDS)
        if denial:
            return "denial"
        if neg > pos:
            return "negative"
        if pos > neg:
            return "positive"
        return "mixed"

    def _estimate_arousal(self, text: str) -> float:
        """Estimate arousal from 0.0 to 1.0 based on lexical cues."""
        base = 0.3
        neg = sum(1 for w in _NEGATIVE_WORDS if w in text)
        pos = sum(1 for w in _POSITIVE_WORDS if w in text)
        high = sum(1 for w in _HIGH_AROUSAL_WORDS if w in text)

        # More emotion words = higher arousal
        word_count = neg + pos + high
        if word_count >= 3:
            base += 0.3
        elif word_count >= 2:
            base += 0.2
        elif word_count >= 1:
            base += 0.1

        # High arousal words boost significantly
        base += high * 0.1

        # Exclamation marks and caps indicate intensity
        if "!" in text:
            base += 0.05
        if text != text.lower() and any(c.isupper() for c in text[1:]):
            base += 0.05

        return min(base, 0.95)
