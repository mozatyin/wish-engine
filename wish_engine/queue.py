"""WishQueue — async lifecycle management for wishes.

Manages the wish lifecycle for the chocolate moment experience:
- Born (instant) → Searching (async) → Found → Recommended → Confirmed → Fulfilled → Archived

Key insight from design review: timing matters more than content.
If wish is fulfilled immediately after detection, it feels like a search engine.
If it appears next time user opens the app, it's a chocolate moment.

This module manages wish state transitions and scheduling.
Zero LLM.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from wish_engine.models import (
    ClassifiedWish,
    L1FulfillmentResult,
    WishLevel,
    WishState,
)


class WishPriority(str, Enum):
    """Fulfillment priority based on distress and wish type."""
    URGENT = "urgent"      # High distress + emotional_processing → fulfill fast
    NORMAL = "normal"      # Standard wishes → delay for chocolate moment
    LOW = "low"            # Reflection/portrait → can wait longer


class QueuedWish(BaseModel):
    """A wish in the queue with lifecycle metadata."""

    wish_id: str
    wish: ClassifiedWish
    state: WishState = WishState.BORN
    priority: WishPriority = WishPriority.NORMAL

    # Timestamps (Unix epoch seconds, 0 = not yet)
    created_at: float = Field(default_factory=time.time)
    searching_at: float = 0.0
    found_at: float = 0.0
    recommended_at: float = 0.0
    confirmed_at: float = 0.0
    fulfilled_at: float = 0.0
    archived_at: float = 0.0

    # Fulfillment data (populated when Found)
    fulfillment: L1FulfillmentResult | None = None

    # Scheduling
    reveal_after: float = 0.0   # Don't reveal before this timestamp
    session_id: str = ""
    user_id: str = ""


# Valid state transitions
_VALID_TRANSITIONS: dict[WishState, set[WishState]] = {
    WishState.BORN: {WishState.SEARCHING, WishState.ARCHIVED},  # can cancel from born
    WishState.SEARCHING: {WishState.FOUND, WishState.ARCHIVED},  # can cancel from searching
    WishState.FOUND: {WishState.RECOMMENDED, WishState.ARCHIVED},
    WishState.RECOMMENDED: {WishState.CONFIRMED, WishState.ARCHIVED},  # user can dismiss
    WishState.CONFIRMED: {WishState.FULFILLED},
    WishState.FULFILLED: {WishState.ARCHIVED},
    WishState.ARCHIVED: set(),  # terminal state
}


class WishQueue:
    """Manages wish lifecycle transitions.

    Usage:
        queue = WishQueue()
        qw = queue.enqueue(classified_wish, session_id="s1", user_id="u1", distress=0.5)
        queue.mark_searching(qw.wish_id)
        queue.mark_found(qw.wish_id, fulfillment_result, delay_seconds=3600)
        # ... later, when user opens app ...
        ready = queue.get_ready_to_reveal(user_id="u1")
        queue.mark_recommended(ready[0].wish_id)
    """

    MAX_ACTIVE_WISHES_PER_USER = 10  # Prevent star map clutter
    WISH_EXPIRY_SECONDS = 7 * 86400  # 7 days — unfulfilled wishes expire

    def __init__(self):
        self._wishes: dict[str, QueuedWish] = {}
        self._counter: int = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"wish_{self._counter:04d}"

    def enqueue(
        self,
        wish: ClassifiedWish,
        session_id: str = "",
        user_id: str = "",
        distress: float = 0.0,
    ) -> QueuedWish:
        """Add a new wish to the queue. Returns QueuedWish in BORN state.

        Raises:
            ValueError: If user already has MAX_ACTIVE_WISHES_PER_USER active wishes.
        """
        if user_id and self.get_active_count(user_id) >= self.MAX_ACTIVE_WISHES_PER_USER:
            raise ValueError(
                f"User {user_id} has {self.MAX_ACTIVE_WISHES_PER_USER} active wishes. "
                "Archive or cancel some before adding more."
            )
        wish_id = self._next_id()

        # Determine priority based on distress and wish type
        priority = self._compute_priority(wish, distress)

        qw = QueuedWish(
            wish_id=wish_id,
            wish=wish,
            state=WishState.BORN,
            priority=priority,
            session_id=session_id,
            user_id=user_id,
        )
        self._wishes[wish_id] = qw
        return qw

    def _compute_priority(self, wish: ClassifiedWish, distress: float) -> WishPriority:
        """Compute fulfillment priority."""
        # High distress + emotional processing → urgent (don't make them wait)
        if distress > 0.6 and wish.wish_type.value == "emotional_processing":
            return WishPriority.URGENT
        # High distress + any L1 → urgent
        if distress > 0.7 and wish.level == WishLevel.L1:
            return WishPriority.URGENT
        # Life reflection, soul portrait → low priority (can wait)
        if wish.wish_type.value in ("life_reflection",):
            return WishPriority.LOW
        return WishPriority.NORMAL

    def _transition(self, wish_id: str, new_state: WishState) -> QueuedWish:
        """Validate and execute state transition."""
        qw = self._wishes[wish_id]
        valid = _VALID_TRANSITIONS.get(qw.state, set())
        if new_state not in valid:
            raise ValueError(
                f"Invalid transition: {qw.state.value} → {new_state.value}. "
                f"Valid: {[s.value for s in valid]}"
            )
        qw.state = new_state
        return qw

    def mark_searching(self, wish_id: str) -> QueuedWish:
        """Transition wish to SEARCHING state (agent working on it)."""
        qw = self._transition(wish_id, WishState.SEARCHING)
        qw.searching_at = time.time()
        return qw

    def mark_found(
        self,
        wish_id: str,
        fulfillment: L1FulfillmentResult,
        delay_seconds: float = 0,
    ) -> QueuedWish:
        """Transition wish to FOUND state with fulfillment data.

        Args:
            wish_id: Wish to update.
            fulfillment: Generated fulfillment content.
            delay_seconds: Delay before revealing to user (chocolate moment timing).
                          0 = reveal immediately (urgent).
                          3600 = reveal after 1 hour.
                          86400 = reveal next day.
        """
        qw = self._transition(wish_id, WishState.FOUND)
        qw.found_at = time.time()
        qw.fulfillment = fulfillment
        qw.reveal_after = time.time() + delay_seconds
        return qw

    def mark_recommended(self, wish_id: str) -> QueuedWish:
        """Transition to RECOMMENDED (shown to user, awaiting confirmation)."""
        qw = self._transition(wish_id, WishState.RECOMMENDED)
        qw.recommended_at = time.time()
        return qw

    def mark_confirmed(self, wish_id: str) -> QueuedWish:
        """User confirmed they want to see the fulfillment."""
        qw = self._transition(wish_id, WishState.CONFIRMED)
        qw.confirmed_at = time.time()
        return qw

    def mark_fulfilled(self, wish_id: str) -> QueuedWish:
        """Wish fully delivered to user."""
        qw = self._transition(wish_id, WishState.FULFILLED)
        qw.fulfilled_at = time.time()
        return qw

    def mark_archived(self, wish_id: str) -> QueuedWish:
        """Archive completed wish (moves to Life Chapter)."""
        qw = self._transition(wish_id, WishState.ARCHIVED)
        qw.archived_at = time.time()
        return qw

    def cancel(self, wish_id: str) -> QueuedWish:
        """Cancel a wish (user dismisses or wish becomes irrelevant).

        Can cancel from any non-terminal state.
        """
        qw = self._transition(wish_id, WishState.ARCHIVED)
        qw.archived_at = time.time()
        return qw

    def expire_stale(self, user_id: str | None = None) -> list[str]:
        """Expire wishes that have been unfulfilled for too long.

        Returns list of expired wish IDs.
        """
        now = time.time()
        expired: list[str] = []
        for qw in list(self._wishes.values()):
            if user_id and qw.user_id != user_id:
                continue
            if qw.state in (WishState.FULFILLED, WishState.ARCHIVED):
                continue
            age = now - qw.created_at
            if age > self.WISH_EXPIRY_SECONDS:
                qw.state = WishState.ARCHIVED
                qw.archived_at = now
                expired.append(qw.wish_id)
        return expired

    def get_ready_to_reveal(self, user_id: str) -> list[QueuedWish]:
        """Get wishes ready to reveal to a user (FOUND + past reveal_after time).

        Called when user opens the app. Returns wishes sorted by priority.
        """
        now = time.time()
        ready = [
            qw for qw in self._wishes.values()
            if qw.user_id == user_id
            and qw.state == WishState.FOUND
            and qw.reveal_after <= now
        ]
        # Sort: urgent first, then by found_at (earliest first)
        priority_order = {WishPriority.URGENT: 0, WishPriority.NORMAL: 1, WishPriority.LOW: 2}
        ready.sort(key=lambda w: (priority_order.get(w.priority, 1), w.found_at))
        return ready

    def get_user_wishes(self, user_id: str) -> list[QueuedWish]:
        """Get all wishes for a user, sorted by creation time."""
        return sorted(
            [qw for qw in self._wishes.values() if qw.user_id == user_id],
            key=lambda w: w.created_at,
        )

    def get_active_count(self, user_id: str) -> int:
        """Count non-archived wishes for a user."""
        return sum(
            1 for qw in self._wishes.values()
            if qw.user_id == user_id and qw.state != WishState.ARCHIVED
        )

    def get_by_id(self, wish_id: str) -> QueuedWish | None:
        """Get a specific wish by ID."""
        return self._wishes.get(wish_id)

    def compute_delay(self, priority: WishPriority) -> float:
        """Compute recommended delay in seconds for chocolate moment timing."""
        return {
            WishPriority.URGENT: 0,          # Immediate
            WishPriority.NORMAL: 3600,       # 1 hour
            WishPriority.LOW: 21600,         # 6 hours
        }.get(priority, 3600)
