"""Wish Engine — SoulMap V10 wish detection, classification, fulfillment, and rendering."""

from wish_engine.models import (
    CardType,
    ClassifiedWish,
    CrossDetectorPattern,
    DetectedWish,
    DetectorResults,
    EmotionState,
    Intention,
    L1FulfillmentResult,
    RenderOutput,
    WishLevel,
    WishState,
    WishType,
)
from wish_engine.detector import detect_wishes
from wish_engine.classifier import classify, classify_batch, WISH_TYPES, FULFILLMENT_STRATEGIES
from wish_engine.l1_fulfiller import fulfill
from wish_engine.renderer import render, render_lifecycle
from wish_engine.deduplicator import deduplicate
from wish_engine.queue import WishQueue, WishPriority, QueuedWish

__all__ = [
    # Models
    "CardType",
    "ClassifiedWish",
    "CrossDetectorPattern",
    "DetectedWish",
    "DetectorResults",
    "EmotionState",
    "Intention",
    "L1FulfillmentResult",
    "RenderOutput",
    "WishLevel",
    "WishState",
    "WishType",
    # Functions
    "detect_wishes",
    "classify",
    "classify_batch",
    "fulfill",
    "render",
    "render_lifecycle",
    # Deduplicator
    "deduplicate",
    # Queue
    "WishQueue",
    "WishPriority",
    "QueuedWish",
    # Constants
    "WISH_TYPES",
    "FULFILLMENT_STRATEGIES",
]
