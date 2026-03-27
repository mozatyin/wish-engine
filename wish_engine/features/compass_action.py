"""Compass Action — full Conversation -> Scan -> Trigger -> Fulfill pipeline.

Wires together DialogueScanner, WishCompass, and UniversalFulfiller into
a single process_conversation() call that returns what happened.

Zero LLM for the pipeline itself (individual components may use LLM).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from wish_engine.compass.compass import WishCompass, ScanResult
from wish_engine.compass.scanner import DialogueScanner
from wish_engine.compass.revelation import Revelation
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishState,
    WishType,
)
from wish_engine.universal_fulfiller import universal_fulfill


# ── Result Model ────────────────────────────────────────────────────────────

@dataclass
class CompassActionResult:
    """Result of the full conversation -> action pipeline."""

    scan: ScanResult | None = None
    shells: list[dict[str, Any]] = field(default_factory=list)
    revelation: Revelation | None = None
    fulfillment: L2FulfillmentResult | None = None
    action_taken: str = "scan_only"  # "scan_only" | "revelation_triggered" | "bloom_fulfilled"


# ── Shell -> Catalog mapping ────────────────────────────────────────────────

_PATTERN_CATALOG_MAP: dict[str, str] = {
    "emotion_anomaly": "mindfulness",
    "mouth_hard_heart_soft": "personality_growth",
    "say_one_do_other": "personality_growth",
    "repeated_probing": "deep_social",
    "value_conflict": "mindfulness",
    "avoidance_signal": "confidence",
    "growth_gap": "courses",
}


def _route_bloom(bloom: dict[str, Any]) -> str:
    """Route a harvested bloom to a catalog_id."""
    pattern = bloom.get("shell_pattern", "")
    return _PATTERN_CATALOG_MAP.get(pattern, "mindfulness")


# ── Public API ──────────────────────────────────────────────────────────────

def process_conversation(
    compass: WishCompass,
    text: str,
    detector_results: DetectorResults,
    session_id: str = "",
    entity_names: dict[str, list[str]] | None = None,
    distress: float = 0.0,
) -> CompassActionResult:
    """Process a conversation turn through the full Compass -> Action pipeline.

    Step 1: DialogueScanner extracts topics -> compass.scan()
    Step 2: compass.check_trigger() for revelations
    Step 3: compass.harvest_blooms() -> route -> universal_fulfill()

    Args:
        compass: WishCompass instance (maintains state across turns).
        text: Current conversation text.
        detector_results: User's 16-dimension profile.
        session_id: Current session ID.
        entity_names: Optional entity name -> aliases mapping.
        distress: Current distress level (0-1).

    Returns:
        CompassActionResult describing what happened.
    """
    result = CompassActionResult()

    # Step 1: Scan — extract topics and feed to compass
    scanner = DialogueScanner(entity_names=entity_names)
    topics = scanner.scan_dialogue(text, session_id=session_id)
    scan_result = compass.scan(
        topics=topics,
        detector_results=detector_results,
        session_id=session_id,
    )
    result.scan = scan_result

    # Capture current shells for visibility
    result.shells = [
        {"id": s.id, "topic": s.topic, "stage": s.stage.value, "confidence": s.confidence}
        for s in compass.vault.all_shells
    ]

    # Step 2: Check trigger — maybe surface a revelation
    revelation = compass.check_trigger(
        current_text=text,
        session_id=session_id,
        distress=distress,
        topics_mentioned=[t.get("entity", "") for t in topics if t.get("entity")],
    )
    if revelation:
        result.revelation = revelation
        result.action_taken = "revelation_triggered"
        return result

    # Step 3: Harvest blooms — convert ripe shells to wishes and fulfill
    blooms = compass.harvest_blooms()
    if blooms:
        # Fulfill the first bloom (one at a time, not overwhelming)
        bloom = blooms[0]
        catalog_id = _route_bloom(bloom)
        wish = ClassifiedWish(
            wish_text=bloom.get("wish_text", ""),
            wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2,
            fulfillment_strategy=catalog_id,
            state=WishState.SEARCHING,
            confidence=bloom.get("confidence", 0.5),
        )
        fulfillment = universal_fulfill(catalog_id, wish, detector_results)
        result.fulfillment = fulfillment
        result.action_taken = "bloom_fulfilled"
        return result

    return result
