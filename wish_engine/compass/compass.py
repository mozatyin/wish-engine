"""WishCompass — unified facade for the Compass pipeline.

Usage:
    compass = WishCompass()

    # After each session
    result = compass.scan(topics=[...], detector_results=det, session_id="s1")

    # During conversation (check if should surface a shell)
    revelation = compass.check_trigger(current_text="...", session_id="s1", distress=0.2, topics_mentioned=[...])

    # After user feedback
    compass.record_feedback(shell_id, "confirm")

    # For star map rendering
    stars = compass.get_star_renders()
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from wish_engine.compass.contradiction import ContradictionDetector
from wish_engine.compass.models import (
    InteractionType,
    ShellStage,
)
from wish_engine.compass.revelation import Revelation, RevelationRenderer
from wish_engine.compass.star_render import CompassStarOutput, render_shell_star
from wish_engine.compass.trigger import TriggerEngine
from wish_engine.compass.vault import SecretVault
from wish_engine.models import DetectorResults


# Shell pattern → wish text templates
_SHELL_WISH_TEMPLATES: dict[str, str] = {
    "emotion_anomaly": "想更了解自己对{topic}的真实感受",
    "mouth_hard_heart_soft": "想面对自己对{topic}的真实态度",
    "say_one_do_other": "想理解自己为什么嘴上否认{topic}但行动上在靠近",
    "repeated_probing": "想认真想想{topic}对自己到底意味着什么",
    "value_conflict": "想理解自己内心的价值矛盾",
    "avoidance_signal": "想面对自己一直在回避的{topic}",
    "growth_gap": "想让自己的行动跟上内心的成长",
}


def _shell_to_wish_text(shell) -> str:
    template = _SHELL_WISH_TEMPLATES.get(shell.pattern.value, "想了解自己内心隐藏的渴望")
    return template.format(topic=shell.topic)


class ScanResult(BaseModel):
    """Result of a compass scan."""

    new_shells: int = 0
    updated_shells: int = 0
    total_shells: int = 0


class WishCompass:
    """Unified facade for the Wish Compass pipeline."""

    def __init__(self):
        self.vault = SecretVault()
        self._detector = ContradictionDetector()
        self._trigger = TriggerEngine()
        self._renderer = RevelationRenderer()
        self._history: dict[str, Any] = {
            "average_arousal": 0.35,
            "entity_history": {},
        }

    def scan(
        self,
        topics: list[dict[str, Any]],
        detector_results: DetectorResults,
        session_id: str = "",
        known_wishes: list[dict[str, Any]] | None = None,
    ) -> ScanResult:
        """Run daily scan on session data to discover new shells.

        Args:
            topics: List of discussed topics with entity, sentiment, arousal, mentions.
            detector_results: Current 16-dimension detector results.
            session_id: Current session ID.
            known_wishes: Already expressed wishes to filter out.

        Returns:
            ScanResult with counts of new/updated shells.
        """
        self.vault.apply_decay()

        signals = {
            "topics": topics,
            "detector_results": detector_results,
            "session_id": session_id,
        }
        shells = self._detector.detect(signals, self._history, known_wishes or [])

        new_count = 0
        updated_count = 0
        for shell in shells:
            existing = self.vault.get_by_topic(shell.topic)
            if existing:
                self.vault.merge_or_add(shell)
                updated_count += 1
            else:
                self.vault.add(shell)
                new_count += 1

        # Update history with entity info for future scans
        for topic in topics:
            entity = topic.get("entity", "")
            if entity:
                ent_hist = self._history["entity_history"].setdefault(entity, {
                    "session_count": 0,
                    "avg_sentiment": "",
                    "avg_arousal": 0.0,
                })
                ent_hist["session_count"] += 1
                ent_hist["avg_sentiment"] = topic.get("sentiment", "")
                ent_hist["avg_arousal"] = topic.get("arousal", 0.0)

        return ScanResult(
            new_shells=new_count,
            updated_shells=updated_count,
            total_shells=len(self.vault.all_shells),
        )

    def check_trigger(
        self,
        current_text: str,
        session_id: str,
        distress: float = 0.0,
        topics_mentioned: list[str] | None = None,
    ) -> Revelation | None:
        """Check if any shell should be surfaced in current context.

        Returns Revelation if triggered, None otherwise.
        """
        context = {
            "current_text": current_text,
            "session_id": session_id,
            "distress": distress,
            "topics_mentioned": topics_mentioned or [],
        }

        # Check all bud+ shells for trigger
        for shell in self.vault.visible_shells:
            event = self._trigger.should_trigger(shell, context)
            if event:
                self._trigger.mark_triggered(session_id)
                revelation = self._renderer.render(shell)
                shell.trigger_history.append(event)
                return revelation
        return None

    def record_feedback(self, shell_id: str, feedback: str) -> None:
        """Record user feedback on a revelation.

        Args:
            shell_id: The shell that was revealed.
            feedback: "confirm", "deny", or "ignore".
        """
        type_map = {
            "confirm": InteractionType.CONFIRM,
            "deny": InteractionType.DENY,
            "ignore": InteractionType.IGNORE,
        }
        itype = type_map.get(feedback, InteractionType.IGNORE)
        self.vault.record_interaction(shell_id, itype)

    def get_star_renders(self) -> list[CompassStarOutput]:
        """Get star map renders for all visible shells."""
        renders = []
        for shell in self.vault.visible_shells:
            star = render_shell_star(shell)
            if star:
                renders.append(star)
        return renders

    def harvest_blooms(self) -> list[dict]:
        """Convert bloom-stage shells to wish-like dicts for Engine fulfillment.

        Returns list of dicts compatible with Wish Engine raw_wishes input.
        Each bloom shell is harvested once (marked with related_wishes entry).
        """
        harvested = []
        for shell in self.vault.bloom_shells:
            if "harvested" in shell.related_wishes:
                continue  # already harvested
            # Convert shell topic + pattern to a wish text
            wish_text = _shell_to_wish_text(shell)
            harvested.append({
                "wish_text": wish_text,
                "shell_id": shell.id,
                "shell_topic": shell.topic,
                "shell_pattern": shell.pattern.value,
                "confidence": shell.confidence,
            })
            shell.related_wishes.append("harvested")
        return harvested

    def summary(self) -> dict[str, int]:
        """Summary of compass state."""
        shells = self.vault.all_shells
        return {
            "total_shells": len(shells),
            "seeds": sum(1 for s in shells if s.stage == ShellStage.SEED),
            "sprouts": sum(1 for s in shells if s.stage == ShellStage.SPROUT),
            "buds": sum(1 for s in shells if s.stage == ShellStage.BUD),
            "blooms": sum(1 for s in shells if s.stage == ShellStage.BLOOM),
        }
