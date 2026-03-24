"""WishEngine — unified facade that wires all modules together.

Single entry point: engine.process(soul_items, detector_results, ...) → WishEngineResult

Pipeline:
  SoulItem[] ──→ Adapter ──→ DetectedWish[]
                                │
  raw text ───→ Detector ──→ DetectedWish[] (merge)
                                │
                          Deduplicator
                                │
                          Classifier
                                │
                    ┌───────────┼───────────┐
                    L1          L2          L3
                    │           │           │
              L1 Fulfiller   (future)   Marketplace
                    │                       │
                 Queue ◄────────────────────┘
                    │
                Renderer → RenderOutput[]
"""

from __future__ import annotations

import json
import os
from typing import Any

from wish_engine.models import (
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
from wish_engine.adapter import detect_from_soul_items
from wish_engine.detector import detect_wishes
from wish_engine.classifier import classify
from wish_engine.deduplicator import deduplicate
from wish_engine.l1_fulfiller import fulfill
from wish_engine.renderer import render
from wish_engine.queue import WishQueue, WishPriority, QueuedWish
from wish_engine.marketplace import Marketplace


class WishEngineResult:
    """Result of processing a session through the Wish Engine."""

    def __init__(self):
        self.detected: list[DetectedWish] = []
        self.classified: list[ClassifiedWish] = []
        self.l1_wishes: list[ClassifiedWish] = []
        self.l2_wishes: list[ClassifiedWish] = []
        self.l3_wishes: list[ClassifiedWish] = []
        self.fulfillments: dict[str, L1FulfillmentResult] = {}  # wish_text → result
        self.renders: list[RenderOutput] = []
        self.queued: list[QueuedWish] = []
        self.marketplace_needs_posted: int = 0
        self.errors: list[str] = []

    @property
    def total_wishes(self) -> int:
        return len(self.classified)

    @property
    def has_chocolate_moment(self) -> bool:
        """True if any wish was fulfilled in this cycle."""
        return len(self.fulfillments) > 0

    def summary(self) -> dict[str, Any]:
        return {
            "detected": len(self.detected),
            "classified": len(self.classified),
            "l1": len(self.l1_wishes),
            "l2": len(self.l2_wishes),
            "l3": len(self.l3_wishes),
            "fulfilled": len(self.fulfillments),
            "renders": len(self.renders),
            "queued": len(self.queued),
            "marketplace_posted": self.marketplace_needs_posted,
            "errors": self.errors,
        }


# Profile sufficiency — minimum dimensions needed for L1 fulfillment
_MIN_DIMENSIONS_FOR_FULFILLMENT = 3


def _count_profile_dimensions(detector_results: DetectorResults) -> int:
    """Count how many detector dimensions have data."""
    count = 0
    if detector_results.emotion.get("emotions"):
        count += 1
    if detector_results.conflict.get("style"):
        count += 1
    if detector_results.mbti.get("type"):
        count += 1
    if detector_results.attachment.get("style"):
        count += 1
    if detector_results.values.get("top_values"):
        count += 1
    if detector_results.fragility.get("pattern"):
        count += 1
    if detector_results.eq.get("overall") is not None:
        count += 1
    if detector_results.communication_dna.get("dominant_style"):
        count += 1
    if detector_results.humor.get("style"):
        count += 1
    if detector_results.love_language.get("primary"):
        count += 1
    return count


# L3 wish type → marketplace capability mapping
_L3_CAPABILITY_MAP: dict[WishType, list[str]] = {
    WishType.FIND_COMPANION: ["empathy", "shared_experience", "willing_to_listen"],
    WishType.FIND_MENTOR: ["domain_expertise", "mentoring_experience", "guidance"],
    WishType.SKILL_EXCHANGE: ["skill_teaching", "skill_learning", "patience"],
    WishType.SHARED_EXPERIENCE: ["shared_activity", "availability", "compatible_interests"],
    WishType.EMOTIONAL_SUPPORT: ["empathy", "non_judgmental", "active_listening"],
}


class WishEngine:
    """Unified facade for the Wish Engine pipeline.

    Usage:
        engine = WishEngine(api_key="sk-or-...", marketplace=marketplace)

        # Process a session
        result = engine.process(
            soul_items=soul_items_from_soulgraph,
            raw_wishes=["想理解自己"],  # optional direct wishes
            detector_results=detector_results,
            emotion_state=emotion_state,
            cross_detector_patterns=patterns,
            soul_type={"name": "Hidden Depths"},
            session_id="s1",
            user_id="u1",
            agent_id="agent_u1",
        )

        # Check results
        print(result.summary())
        for r in result.renders:
            print(f"Star: {r.star_state} {r.color} {r.animation}")
    """

    def __init__(
        self,
        api_key: str | None = None,
        marketplace: Marketplace | None = None,
        queue: WishQueue | None = None,
        fulfill_l1: bool = True,
        post_l3: bool = True,
    ):
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._marketplace = marketplace
        self._queue = queue or WishQueue()
        self._fulfill_l1 = fulfill_l1
        self._post_l3 = post_l3

    @property
    def queue(self) -> WishQueue:
        return self._queue

    @property
    def marketplace(self) -> Marketplace | None:
        return self._marketplace

    def process(
        self,
        soul_items: list[dict[str, Any]] | None = None,
        raw_wishes: list[str] | None = None,
        detector_results: DetectorResults | None = None,
        emotion_state: EmotionState | None = None,
        cross_detector_patterns: list[CrossDetectorPattern] | None = None,
        soul_type: dict[str, Any] | None = None,
        life_chapter: dict[str, Any] | None = None,
        session_id: str = "",
        user_id: str = "",
        agent_id: str = "",
    ) -> WishEngineResult:
        """Process a session through the full pipeline.

        Args:
            soul_items: SoulGraph SoulItem dicts (Path A — structured detection)
            raw_wishes: Direct wish texts from "Make a wish" (Path B — regex detection)
            detector_results: All 16 detector results (for L1 fulfillment)
            emotion_state: Current emotion snapshot
            cross_detector_patterns: Cross-detector synthesized patterns
            soul_type: Soul type dict
            life_chapter: Current life chapter
            session_id: Current session ID
            user_id: User ID
            agent_id: Agent ID (for marketplace)

        Returns:
            WishEngineResult with all pipeline outputs.
        """
        result = WishEngineResult()
        det_results = detector_results or DetectorResults()

        # ── Step 1: Detect wishes from both paths ────────────────────────

        all_wishes: list[DetectedWish] = []

        # Path A: SoulItem structured detection
        if soul_items:
            path_a = detect_from_soul_items(soul_items)
            all_wishes.extend(path_a)

        # Path B: Raw text regex detection
        if raw_wishes:
            intentions = [
                Intention(id=f"raw_{i}", text=text)
                for i, text in enumerate(raw_wishes)
            ]
            path_b = detect_wishes(
                intentions,
                emotion_state=emotion_state,
                cross_detector_patterns=cross_detector_patterns,
            )
            all_wishes.extend(path_b)

        if not all_wishes:
            return result

        # ── Step 2: Deduplicate ──────────────────────────────────────────

        all_wishes = deduplicate(all_wishes)
        result.detected = all_wishes

        # ── Step 3: Classify ─────────────────────────────────────────────

        for wish in all_wishes:
            classified = classify(wish)
            result.classified.append(classified)

            if classified.level == WishLevel.L1:
                result.l1_wishes.append(classified)
            elif classified.level == WishLevel.L2:
                result.l2_wishes.append(classified)
            elif classified.level == WishLevel.L3:
                result.l3_wishes.append(classified)

        # ── Step 4: Route by level ───────────────────────────────────────

        distress = emotion_state.distress if emotion_state else 0.0
        profile_dims = _count_profile_dimensions(det_results)

        # L1: Always queue and render, fulfill only if enabled + sufficient data
        if result.l1_wishes:
            for wish in result.l1_wishes:
                try:
                    # Enqueue first (Born state)
                    qw = self._queue.enqueue(
                        wish, session_id=session_id, user_id=user_id, distress=distress,
                    )
                    result.queued.append(qw)

                    # Profile sufficiency gate
                    if not self._fulfill_l1 or profile_dims < _MIN_DIMENSIONS_FOR_FULFILLMENT:
                        # Not fulfilling or not enough data → star stays in BORN
                        born_render = render(WishState.BORN, wish=wish)
                        result.renders.append(born_render)
                        continue

                    # Mark searching
                    self._queue.mark_searching(qw.wish_id)

                    # Fulfill
                    if self._api_key:
                        fulfillment = fulfill(
                            wish=wish,
                            detector_results=det_results,
                            cross_detector_patterns=cross_detector_patterns,
                            soul_type=soul_type,
                            life_chapter=life_chapter,
                            api_key=self._api_key,
                        )
                        result.fulfillments[wish.wish_text] = fulfillment

                        # Compute delay for chocolate moment
                        delay = self._queue.compute_delay(qw.priority)
                        self._queue.mark_found(qw.wish_id, fulfillment, delay_seconds=delay)

                        # Render found state
                        found_render = render(WishState.FOUND, wish=wish, fulfillment=fulfillment)
                        result.renders.append(found_render)
                    else:
                        # No API key → can't fulfill, render searching
                        searching_render = render(WishState.SEARCHING, wish=wish)
                        result.renders.append(searching_render)

                except Exception as e:
                    result.errors.append(f"L1 fulfillment error: {e}")
                    born_render = render(WishState.BORN, wish=wish)
                    result.renders.append(born_render)

        # L2: Queue only (fulfillment is future Phase 2)
        for wish in result.l2_wishes:
            try:
                qw = self._queue.enqueue(
                    wish, session_id=session_id, user_id=user_id, distress=distress,
                )
                result.queued.append(qw)
                born_render = render(WishState.BORN, wish=wish)
                result.renders.append(born_render)
            except Exception as e:
                result.errors.append(f"L2 queue error: {e}")

        # L3: Post to marketplace
        if self._post_l3 and self._marketplace and agent_id:
            for wish in result.l3_wishes:
                try:
                    seeking = _L3_CAPABILITY_MAP.get(wish.wish_type, ["general_connection"])
                    self._marketplace.post_need(
                        agent_id=agent_id,
                        wish_type=wish.wish_type,
                        seeking=seeking,
                    )
                    result.marketplace_needs_posted += 1

                    # Also queue for tracking
                    qw = self._queue.enqueue(
                        wish, session_id=session_id, user_id=user_id, distress=distress,
                    )
                    self._queue.mark_searching(qw.wish_id)
                    result.queued.append(qw)

                    searching_render = render(WishState.SEARCHING, wish=wish)
                    result.renders.append(searching_render)
                except Exception as e:
                    result.errors.append(f"L3 marketplace error: {e}")

        return result

    def get_ready_reveals(self, user_id: str) -> list[RenderOutput]:
        """Get wishes ready to reveal to the user (chocolate moments).

        Call this when user opens the app.
        """
        ready = self._queue.get_ready_to_reveal(user_id)
        renders: list[RenderOutput] = []
        for qw in ready:
            self._queue.mark_recommended(qw.wish_id)
            r = render(
                WishState.RECOMMENDED,
                wish=qw.wish,
                fulfillment=qw.fulfillment,
            )
            renders.append(r)
        return renders

    def confirm_wish(self, wish_id: str) -> RenderOutput | None:
        """User confirms they want to see the fulfillment."""
        qw = self._queue.get_by_id(wish_id)
        if not qw:
            return None
        self._queue.mark_confirmed(wish_id)
        self._queue.mark_fulfilled(wish_id)
        return render(
            WishState.FULFILLED,
            wish=qw.wish,
            fulfillment=qw.fulfillment,
        )

    def archive_wish(self, wish_id: str) -> None:
        """Archive a fulfilled or dismissed wish."""
        self._queue.mark_archived(wish_id)
