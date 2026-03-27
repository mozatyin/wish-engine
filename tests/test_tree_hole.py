"""Tests for Tree Hole (匿名树洞) — private journal → Compass signals."""

import time

from wish_engine.compass.tree_hole import TreeHole, TreeHoleEntry, TREE_HOLE_SIGNAL_WEIGHT


class TestTreeHoleEntry:
    def test_entry_has_id_and_timestamp(self):
        entry = TreeHoleEntry(text="I feel lonely")
        assert entry.id.startswith("th_")
        assert entry.timestamp > 0
        assert entry.text == "I feel lonely"

    def test_entry_with_emotion_snapshot(self):
        entry = TreeHoleEntry(
            text="nobody understands me",
            emotion_snapshot={"sadness": 0.8, "loneliness": 0.9},
            session_id="sess_001",
        )
        assert entry.emotion_snapshot["sadness"] == 0.8
        assert entry.session_id == "sess_001"


class TestTreeHoleAddRetrieve:
    def test_add_and_retrieve(self):
        th = TreeHole()
        th.add_entry("I miss my old life")
        th.add_entry("Why can't I be honest with people")
        assert th.count == 2
        entries = th.get_entries()
        assert len(entries) == 2

    def test_entries_ordered_newest_first(self):
        th = TreeHole()
        e1 = th.add_entry("first entry")
        time.sleep(0.01)
        e2 = th.add_entry("second entry")
        entries = th.get_entries()
        assert entries[0].id == e2.id
        assert entries[1].id == e1.id

    def test_get_entries_respects_limit(self):
        th = TreeHole()
        for i in range(30):
            th.add_entry(f"entry {i}")
        entries = th.get_entries(limit=5)
        assert len(entries) == 5

    def test_empty_tree_hole(self):
        th = TreeHole()
        assert th.count == 0
        assert th.get_entries() == []


class TestTreeHoleSignals:
    def test_extract_signals_empty(self):
        th = TreeHole()
        assert th.extract_signals() == []

    def test_extract_signals_detects_emotions(self):
        th = TreeHole()
        th.add_entry("I feel so lonely and scared")
        signals = th.extract_signals()
        topics = [s.topic for s in signals]
        assert "loneliness" in topics
        assert "fear" in topics

    def test_signals_have_higher_weight(self):
        th = TreeHole()
        th.add_entry("I want to be free")
        signals = th.extract_signals()
        for s in signals:
            assert s.data["weight"] == TREE_HOLE_SIGNAL_WEIGHT

    def test_signals_valid_format(self):
        th = TreeHole()
        th.add_entry("I dream of a different life", session_id="sess_x")
        signals = th.extract_signals()
        assert len(signals) > 0
        for s in signals:
            assert s.signal_type.startswith("tree_hole_")
            assert s.topic
            assert s.session_id == "sess_x"
            assert s.timestamp > 0

    def test_no_emotion_produces_raw_signal(self):
        th = TreeHole()
        th.add_entry("just a random thought about nothing")
        signals = th.extract_signals()
        assert len(signals) == 1
        assert signals[0].signal_type == "tree_hole_raw"
        assert signals[0].topic == "private_thought"
