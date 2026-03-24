"""Tests for WishQueue — async lifecycle management."""

import time
import pytest

from wish_engine.models import (
    CardType, ClassifiedWish, L1FulfillmentResult, WishLevel, WishState, WishType,
)
from wish_engine.queue import WishQueue, WishPriority, QueuedWish


def _make_wish(wish_type=WishType.SELF_UNDERSTANDING, level=WishLevel.L1):
    return ClassifiedWish(
        wish_text="test wish",
        wish_type=wish_type,
        level=level,
        fulfillment_strategy="test",
    )


def _make_fulfillment():
    return L1FulfillmentResult(
        fulfillment_text="Your insight here.",
        related_stars=["conflict:avoiding"],
        card_type=CardType.INSIGHT,
    )


class TestEnqueue:
    def test_basic_enqueue(self):
        q = WishQueue()
        wish = _make_wish()
        qw = q.enqueue(wish, session_id="s1", user_id="u1")
        assert qw.state == WishState.BORN
        assert qw.wish_id.startswith("wish_")
        assert qw.session_id == "s1"
        assert qw.user_id == "u1"
        assert qw.created_at > 0

    def test_sequential_ids(self):
        q = WishQueue()
        w1 = q.enqueue(_make_wish(), user_id="u1")
        w2 = q.enqueue(_make_wish(), user_id="u1")
        assert w1.wish_id != w2.wish_id

    def test_priority_urgent_high_distress(self):
        q = WishQueue()
        wish = _make_wish(wish_type=WishType.EMOTIONAL_PROCESSING)
        qw = q.enqueue(wish, distress=0.7)
        assert qw.priority == WishPriority.URGENT

    def test_priority_normal(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), distress=0.3)
        assert qw.priority == WishPriority.NORMAL

    def test_priority_low_reflection(self):
        q = WishQueue()
        wish = _make_wish(wish_type=WishType.LIFE_REFLECTION)
        qw = q.enqueue(wish, distress=0.2)
        assert qw.priority == WishPriority.LOW


class TestLifecycleTransitions:
    def test_full_lifecycle(self):
        q = WishQueue()
        wish = _make_wish()
        fulfillment = _make_fulfillment()

        qw = q.enqueue(wish, user_id="u1")
        assert qw.state == WishState.BORN

        q.mark_searching(qw.wish_id)
        assert q.get_by_id(qw.wish_id).state == WishState.SEARCHING

        q.mark_found(qw.wish_id, fulfillment, delay_seconds=0)
        qw = q.get_by_id(qw.wish_id)
        assert qw.state == WishState.FOUND
        assert qw.fulfillment is not None

        q.mark_recommended(qw.wish_id)
        assert q.get_by_id(qw.wish_id).state == WishState.RECOMMENDED

        q.mark_confirmed(qw.wish_id)
        assert q.get_by_id(qw.wish_id).state == WishState.CONFIRMED

        q.mark_fulfilled(qw.wish_id)
        assert q.get_by_id(qw.wish_id).state == WishState.FULFILLED

        q.mark_archived(qw.wish_id)
        assert q.get_by_id(qw.wish_id).state == WishState.ARCHIVED

    def test_timestamps_set(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        assert qw.created_at > 0
        assert qw.searching_at == 0

        q.mark_searching(qw.wish_id)
        qw = q.get_by_id(qw.wish_id)
        assert qw.searching_at > 0


class TestRevealTiming:
    def test_immediate_reveal(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        q.mark_searching(qw.wish_id)
        q.mark_found(qw.wish_id, _make_fulfillment(), delay_seconds=0)

        ready = q.get_ready_to_reveal("u1")
        assert len(ready) == 1

    def test_delayed_reveal_not_ready(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        q.mark_searching(qw.wish_id)
        q.mark_found(qw.wish_id, _make_fulfillment(), delay_seconds=9999)

        ready = q.get_ready_to_reveal("u1")
        assert len(ready) == 0  # Not ready yet

    def test_priority_ordering(self):
        q = WishQueue()

        # Normal priority wish
        w1 = q.enqueue(_make_wish(), user_id="u1", distress=0.3)
        q.mark_searching(w1.wish_id)
        q.mark_found(w1.wish_id, _make_fulfillment(), delay_seconds=0)

        # Urgent priority wish
        w2 = q.enqueue(
            _make_wish(wish_type=WishType.EMOTIONAL_PROCESSING),
            user_id="u1", distress=0.8,
        )
        q.mark_searching(w2.wish_id)
        q.mark_found(w2.wish_id, _make_fulfillment(), delay_seconds=0)

        ready = q.get_ready_to_reveal("u1")
        assert len(ready) == 2
        assert ready[0].priority == WishPriority.URGENT  # Urgent first

    def test_only_found_state_revealed(self):
        q = WishQueue()

        # BORN wish — not ready
        q.enqueue(_make_wish(), user_id="u1")

        # SEARCHING wish — not ready
        w2 = q.enqueue(_make_wish(), user_id="u1")
        q.mark_searching(w2.wish_id)

        # FOUND wish — ready
        w3 = q.enqueue(_make_wish(), user_id="u1")
        q.mark_searching(w3.wish_id)
        q.mark_found(w3.wish_id, _make_fulfillment(), delay_seconds=0)

        # FULFILLED wish — already delivered, not in ready
        w4 = q.enqueue(_make_wish(), user_id="u1")
        q.mark_searching(w4.wish_id)
        q.mark_found(w4.wish_id, _make_fulfillment(), delay_seconds=0)
        q.mark_recommended(w4.wish_id)
        q.mark_confirmed(w4.wish_id)
        q.mark_fulfilled(w4.wish_id)

        ready = q.get_ready_to_reveal("u1")
        assert len(ready) == 1  # Only the FOUND wish


class TestUserQueries:
    def test_get_user_wishes(self):
        q = WishQueue()
        q.enqueue(_make_wish(), user_id="u1")
        q.enqueue(_make_wish(), user_id="u1")
        q.enqueue(_make_wish(), user_id="u2")

        assert len(q.get_user_wishes("u1")) == 2
        assert len(q.get_user_wishes("u2")) == 1

    def test_active_count(self):
        q = WishQueue()
        w1 = q.enqueue(_make_wish(), user_id="u1")
        w2 = q.enqueue(_make_wish(), user_id="u1")

        assert q.get_active_count("u1") == 2

        # Archive one
        q.mark_searching(w1.wish_id)
        q.mark_found(w1.wish_id, _make_fulfillment(), delay_seconds=0)
        q.mark_recommended(w1.wish_id)
        q.mark_confirmed(w1.wish_id)
        q.mark_fulfilled(w1.wish_id)
        q.mark_archived(w1.wish_id)

        assert q.get_active_count("u1") == 1

    def test_get_by_id(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        assert q.get_by_id(qw.wish_id) is not None
        assert q.get_by_id("nonexistent") is None


class TestComputeDelay:
    def test_urgent_immediate(self):
        q = WishQueue()
        assert q.compute_delay(WishPriority.URGENT) == 0

    def test_normal_one_hour(self):
        q = WishQueue()
        assert q.compute_delay(WishPriority.NORMAL) == 3600

    def test_low_six_hours(self):
        q = WishQueue()
        assert q.compute_delay(WishPriority.LOW) == 21600


class TestStateValidation:
    """State transitions must follow valid paths."""

    def test_valid_born_to_searching(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        q.mark_searching(qw.wish_id)  # Should not raise

    def test_invalid_born_to_fulfilled(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        with pytest.raises(ValueError, match="Invalid transition"):
            q.mark_fulfilled(qw.wish_id)

    def test_invalid_fulfilled_to_searching(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        q.mark_searching(qw.wish_id)
        q.mark_found(qw.wish_id, _make_fulfillment(), delay_seconds=0)
        q.mark_recommended(qw.wish_id)
        q.mark_confirmed(qw.wish_id)
        q.mark_fulfilled(qw.wish_id)
        with pytest.raises(ValueError, match="Invalid transition"):
            q.mark_searching(qw.wish_id)

    def test_cancel_from_born(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        q.cancel(qw.wish_id)
        assert q.get_by_id(qw.wish_id).state == WishState.ARCHIVED

    def test_cancel_from_searching(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        q.mark_searching(qw.wish_id)
        q.cancel(qw.wish_id)
        assert q.get_by_id(qw.wish_id).state == WishState.ARCHIVED

    def test_cancel_from_recommended(self):
        """User dismisses a recommendation."""
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        q.mark_searching(qw.wish_id)
        q.mark_found(qw.wish_id, _make_fulfillment(), delay_seconds=0)
        q.mark_recommended(qw.wish_id)
        q.cancel(qw.wish_id)
        assert q.get_by_id(qw.wish_id).state == WishState.ARCHIVED


class TestMaxWishes:
    def test_max_wishes_enforced(self):
        q = WishQueue()
        for i in range(q.MAX_ACTIVE_WISHES_PER_USER):
            q.enqueue(_make_wish(), user_id="u1")
        with pytest.raises(ValueError, match="active wishes"):
            q.enqueue(_make_wish(), user_id="u1")

    def test_archived_dont_count(self):
        q = WishQueue()
        for i in range(q.MAX_ACTIVE_WISHES_PER_USER):
            qw = q.enqueue(_make_wish(), user_id="u1")
        # Archive one
        first_id = list(q._wishes.keys())[0]
        q.cancel(first_id)
        # Now can add one more
        q.enqueue(_make_wish(), user_id="u1")  # Should not raise

    def test_different_users_independent(self):
        q = WishQueue()
        for i in range(q.MAX_ACTIVE_WISHES_PER_USER):
            q.enqueue(_make_wish(), user_id="u1")
        # u2 is unaffected
        q.enqueue(_make_wish(), user_id="u2")  # Should not raise


class TestExpiry:
    def test_expire_stale(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        # Manually backdate creation
        q._wishes[qw.wish_id].created_at = time.time() - q.WISH_EXPIRY_SECONDS - 1
        expired = q.expire_stale()
        assert qw.wish_id in expired
        assert q.get_by_id(qw.wish_id).state == WishState.ARCHIVED

    def test_recent_not_expired(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        expired = q.expire_stale()
        assert len(expired) == 0

    def test_fulfilled_not_expired(self):
        q = WishQueue()
        qw = q.enqueue(_make_wish(), user_id="u1")
        q.mark_searching(qw.wish_id)
        q.mark_found(qw.wish_id, _make_fulfillment(), delay_seconds=0)
        q.mark_recommended(qw.wish_id)
        q.mark_confirmed(qw.wish_id)
        q.mark_fulfilled(qw.wish_id)
        # Backdate
        q._wishes[qw.wish_id].created_at = time.time() - q.WISH_EXPIRY_SECONDS - 1
        expired = q.expire_stale()
        assert len(expired) == 0  # Already fulfilled, don't expire
