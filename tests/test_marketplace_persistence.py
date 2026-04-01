"""Tests for Marketplace SQLite persistence."""
import tempfile
import os

import pytest

from wish_engine.marketplace import Marketplace, AgentTrustLevel, MatchState
from wish_engine.models import WishType


class TestInMemoryStillWorks:
    def test_default_in_memory(self):
        m = Marketplace()
        assert m._db is None
        m.register_agent("a1")
        assert "a1" in m._agents

    def test_full_flow_in_memory(self):
        m = Marketplace()
        m.register_agent("a1")
        m.register_agent("a2")
        need = m.post_need("a1", WishType.FIND_COMPANION, seeking=["empathy"])
        m.post_response("a2", in_response_to=need.request_id, offering=["empathy"])
        matches = m.create_matches()
        assert len(matches) == 1


class TestSQLitePersistence:
    def test_persist_and_reload_request(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            # Session 1: create and post
            m1 = Marketplace(db_path=db_path)
            m1.register_agent("a1")
            need = m1.post_need("a1", WishType.FIND_COMPANION, seeking=["empathy"])
            m1.close()

            # Session 2: reload
            m2 = Marketplace(db_path=db_path)
            assert need.request_id in m2._requests
            loaded = m2._requests[need.request_id]
            assert loaded.agent_id == "a1"
            assert loaded.seeking == ["empathy"]
            m2.close()
        finally:
            os.unlink(db_path)

    def test_agent_persists(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            m1 = Marketplace(db_path=db_path)
            m1.register_agent("agent_xyz", language="zh")
            m1.close()

            m2 = Marketplace(db_path=db_path)
            assert "agent_xyz" in m2._agents
            assert m2._agents["agent_xyz"].language == "zh"
            m2.close()
        finally:
            os.unlink(db_path)

    def test_match_persists(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            m1 = Marketplace(db_path=db_path)
            m1.register_agent("a1")
            m1.register_agent("a2")
            need = m1.post_need("a1", WishType.EMOTIONAL_SUPPORT, seeking=["good_listener"])
            m1.post_response("a2", in_response_to=need.request_id, offering=["good_listener"])
            matches = m1.create_matches()
            assert len(matches) == 1
            match_id = matches[0].match_id
            m1.close()

            m2 = Marketplace(db_path=db_path)
            assert match_id in m2._matches
            m2.close()
        finally:
            os.unlink(db_path)

    def test_trust_level_persists(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            m1 = Marketplace(db_path=db_path)
            m1.register_agent("a1")
            m1.suspend_agent("a1")
            m1.close()

            m2 = Marketplace(db_path=db_path)
            assert m2._agents["a1"].trust_level == AgentTrustLevel.SUSPENDED
            m2.close()
        finally:
            os.unlink(db_path)

    def test_declined_count_persists_through_verify(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            m1 = Marketplace(db_path=db_path)
            m1.register_agent("a1")
            m1.register_agent("a2")
            need = m1.post_need("a1", WishType.FIND_COMPANION, seeking=["empathy"])
            m1.post_response("a2", in_response_to=need.request_id, offering=["empathy"])
            matches = m1.create_matches()
            match_id = matches[0].match_id
            m1.verify(match_id, "a1", approved=False)
            m1.close()

            m2 = Marketplace(db_path=db_path)
            assert m2._matches[match_id].state == MatchState.A_DECLINED
            m2.close()
        finally:
            os.unlink(db_path)
