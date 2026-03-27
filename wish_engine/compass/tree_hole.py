"""Tree Hole (匿名树洞) — private journal that feeds raw signals into Compass.

Users say things in the tree hole they can't say to anyone.
These entries carry HIGHER signal weight because they're more honest.
Part of Compass because tree hole text is raw material for hidden desire detection.
Zero LLM.
"""

from __future__ import annotations

import re
import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

from wish_engine.compass.models import Signal


# Emotion keywords for signal extraction (multilingual)
_EMOTION_WORDS: dict[str, str] = {
    # English
    "lonely": "loneliness",
    "alone": "loneliness",
    "miss": "longing",
    "wish": "desire",
    "want": "desire",
    "hate": "anger",
    "angry": "anger",
    "scared": "fear",
    "afraid": "fear",
    "sad": "sadness",
    "happy": "joy",
    "love": "love",
    "jealous": "jealousy",
    "regret": "regret",
    "ashamed": "shame",
    "tired": "exhaustion",
    "trapped": "constraint",
    "free": "freedom",
    "dream": "aspiration",
    "hope": "hope",
    # Chinese
    "孤独": "loneliness",
    "想念": "longing",
    "想要": "desire",
    "讨厌": "anger",
    "害怕": "fear",
    "伤心": "sadness",
    "开心": "joy",
    "爱": "love",
    "后悔": "regret",
    "累": "exhaustion",
    "自由": "freedom",
    "梦想": "aspiration",
    # Arabic
    "وحيد": "loneliness",
    "أريد": "desire",
    "خائف": "fear",
    "حزين": "sadness",
    "حب": "love",
}

# Higher weight because tree hole entries are more honest than regular conversation
TREE_HOLE_SIGNAL_WEIGHT = 1.5


class TreeHoleEntry(BaseModel):
    """A single private journal entry."""

    id: str = Field(default_factory=lambda: f"th_{uuid.uuid4().hex[:8]}")
    text: str
    timestamp: float = Field(default_factory=time.time)
    emotion_snapshot: dict[str, Any] = Field(default_factory=dict)
    session_id: str = ""


class TreeHole:
    """Private journal where users record thoughts they can't share with anyone.

    Entries are stored in-memory (same pattern as SecretVault).
    The key insight: tree hole text is MORE honest than regular conversation,
    so signals extracted carry higher weight for Compass contradiction detection.
    """

    def __init__(self) -> None:
        self._entries: list[TreeHoleEntry] = []

    @property
    def count(self) -> int:
        return len(self._entries)

    def add_entry(
        self,
        text: str,
        emotion_state: dict[str, Any] | None = None,
        session_id: str = "",
    ) -> TreeHoleEntry:
        """Store a new tree hole entry.

        Args:
            text: The private journal text
            emotion_state: Optional emotion snapshot at time of writing
            session_id: Session identifier for cross-referencing

        Returns:
            The created TreeHoleEntry
        """
        entry = TreeHoleEntry(
            text=text,
            emotion_snapshot=emotion_state or {},
            session_id=session_id,
        )
        self._entries.append(entry)
        return entry

    def get_entries(self, limit: int = 20) -> list[TreeHoleEntry]:
        """Return recent entries, newest first.

        Args:
            limit: Maximum number of entries to return (default 20)

        Returns:
            List of TreeHoleEntry sorted by timestamp descending
        """
        sorted_entries = sorted(self._entries, key=lambda e: e.timestamp, reverse=True)
        return sorted_entries[:limit]

    def extract_signals(self) -> list[Signal]:
        """Convert tree hole entries into Compass topic signals.

        Scans entry text for emotion words and generates Signal objects
        that the ContradictionDetector can consume. Tree hole signals
        carry higher weight (1.5x) because they're more honest.

        Returns:
            List of Signal objects suitable for Compass processing
        """
        if not self._entries:
            return []

        signals: list[Signal] = []
        for entry in self._entries:
            detected_emotions = self._detect_emotions(entry.text)
            if not detected_emotions:
                # Even without detected emotions, the entry itself is a signal
                signals.append(
                    Signal(
                        signal_type="tree_hole_raw",
                        topic="private_thought",
                        data={
                            "text_preview": entry.text[:100],
                            "weight": TREE_HOLE_SIGNAL_WEIGHT,
                            "entry_id": entry.id,
                        },
                        session_id=entry.session_id,
                        timestamp=entry.timestamp,
                    )
                )
            else:
                for emotion_label in detected_emotions:
                    signals.append(
                        Signal(
                            signal_type="tree_hole_emotion",
                            topic=emotion_label,
                            data={
                                "text_preview": entry.text[:100],
                                "weight": TREE_HOLE_SIGNAL_WEIGHT,
                                "emotion": emotion_label,
                                "entry_id": entry.id,
                            },
                            session_id=entry.session_id,
                            timestamp=entry.timestamp,
                        )
                    )
        return signals

    @staticmethod
    def _detect_emotions(text: str) -> list[str]:
        """Detect emotion keywords in text.

        Returns deduplicated list of emotion labels found.
        """
        text_lower = text.lower()
        found: list[str] = []
        seen: set[str] = set()
        for keyword, label in _EMOTION_WORDS.items():
            if keyword in text_lower and label not in seen:
                found.append(label)
                seen.add(label)
        return found
