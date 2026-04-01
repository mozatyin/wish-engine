"""Agent Marketplace — stock exchange model for L3 wish matching.

PRIVACY MODEL:
- Agents ONLY post requests (needs), NEVER host information
- Agent has permission to: post_request, respond_to_request, verify_match
- Agent does NOT have permission to: post_host_profile, reveal_host_identity
- Exchange NEVER sees user profiles — only anonymous requests
- Compatibility is computed by each Agent LOCALLY, not by Exchange
- Exchange only validates: is this agent registered? is it behaving normally?

Flow:
    Agent A detects host wish → posts anonymous request to Exchange
    Exchange broadcasts request → all Agents scan
    Agent B decides locally: "my host matches this" → posts response
    Exchange connects A and B agents
    Agents verify each other bilaterally (through Exchange as relay)
    Both pass → notify humans

    Agent A                  Exchange                   Agent B
      │                        │                          │
      ├─ post_request ────────►│                          │
      │  (need only,           │─── broadcast ───────────►│
      │   no host info)        │                          │
      │                        │     [B checks locally:   │
      │                        │      does my host match?]│
      │                        │                          │
      │                        │◄──── respond_to_request ─┤
      │                        │      (capability only,   │
      │                        │       no host info)      │
      │                        │                          │
      │◄── match_proposal ─────┤──── match_proposal ─────►│
      │                        │                          │
      │  [A checks locally:    │     [B checks locally:   │
      │   is B safe for host?] │      is A safe for host?]│
      │                        │                          │
      ├─ verify(pass) ─────────┤◄──── verify(pass) ───────┤
      │                        │                          │
      │                   [MUTUAL]                        │
      │                        │                          │
      ├─ notify_human ─────────┤──────── notify_human ────┤

Zero LLM for matching. 1× Haiku only for match_reason text (post-mutual).
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from wish_engine.models import WishType


# ═══════════════════════════════════════════════════════════════════════════════
# Request — what agents post (ONLY needs/capabilities, NO host info)
# ═══════════════════════════════════════════════════════════════════════════════


class RequestType(str, Enum):
    NEED = "need"        # "Seeking someone who..." (买单)
    RESPONSE = "response"  # "I can help with this" (卖单)


class RequestState(str, Enum):
    OPEN = "open"
    MATCHED = "matched"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Request(BaseModel):
    """An anonymous request posted by an agent.

    Contains ONLY:
    - What is needed (wish_type + capability description)
    - What is offered (capability tags)
    NEVER contains: host profile, scores, personal data
    """

    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    agent_id: str  # opaque token, not traceable to user
    request_type: RequestType
    wish_type: WishType
    state: RequestState = RequestState.OPEN
    created_at: float = Field(default_factory=time.time)

    # Need: what is being sought (abstract capabilities, no personal data)
    seeking: list[str] = Field(default_factory=list)
    # e.g., ["entrepreneurial_experience", "willing_to_listen", "similar_struggle"]

    # Response: what is being offered (abstract capabilities)
    offering: list[str] = Field(default_factory=list)
    # e.g., ["entrepreneurial_experience", "high_benevolence", "good_listener"]

    # The need/response pair this responds to (for responses only)
    in_response_to: str | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# Match — connecting two agents
# ═══════════════════════════════════════════════════════════════════════════════


class MatchState(str, Enum):
    PROPOSED = "proposed"
    A_VERIFIED = "a_verified"
    B_VERIFIED = "b_verified"
    MUTUAL = "mutual"
    A_DECLINED = "a_declined"
    B_DECLINED = "b_declined"
    EXPIRED = "expired"


class Match(BaseModel):
    """A proposed match between two agents."""

    match_id: str = Field(default_factory=lambda: f"match_{uuid.uuid4().hex[:8]}")
    need_request_id: str
    response_request_id: str
    agent_a_id: str  # the one with the need
    agent_b_id: str  # the one who responded
    state: MatchState = MatchState.PROPOSED
    created_at: float = Field(default_factory=time.time)
    verified_at: float = 0.0

    # Capability overlap (computed by Exchange from request tags only)
    capability_overlap: float = 0.0

    # Match reason (generated post-mutual, 1× Haiku)
    match_reason: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# Agent Behavior Validator — Exchange's trust layer
# ═══════════════════════════════════════════════════════════════════════════════


class AgentTrustLevel(str, Enum):
    TRUSTED = "trusted"
    PROBATION = "probation"  # new agent, limited posting
    SUSPENDED = "suspended"  # abnormal behavior detected


class AgentRecord(BaseModel):
    """Exchange's record of an agent (behavior tracking, NOT profile)."""

    agent_id: str
    trust_level: AgentTrustLevel = AgentTrustLevel.PROBATION
    registered_at: float = Field(default_factory=time.time)
    total_requests: int = 0
    total_responses: int = 0
    total_matches: int = 0
    declined_count: int = 0
    language: str = "en"  # for broadcasting to same-language agents


# ═══════════════════════════════════════════════════════════════════════════════
# Marketplace — the exchange itself
# ═══════════════════════════════════════════════════════════════════════════════


def _compute_capability_overlap(seeking: list[str], offering: list[str]) -> float:
    """Compute overlap between what's sought and what's offered.

    This is the Exchange's ONLY scoring — based on capability tags only.
    Detailed compatibility is computed by agents locally.
    """
    if not seeking or not offering:
        return 0.0
    seek_set = set(seeking)
    offer_set = set(offering)
    matched = len(seek_set & offer_set)
    return matched / len(seek_set) if seek_set else 0.0


class Marketplace:
    """Agent Marketplace — stock exchange for L3 wish matching.

    Privacy guarantees:
    - Exchange NEVER stores or sees user profiles
    - Exchange only sees: agent_id + request type + capability tags
    - Compatibility scoring: capability overlap only (not personality matching)
    - Personality/safety matching happens at the Agent level, not here

    Usage:
        market = Marketplace()

        # Agents register (Exchange only tracks behavior, not profiles)
        market.register_agent("agent_A", language="zh")
        market.register_agent("agent_B", language="zh")

        # Agent A posts a need (no host info)
        need = market.post_need(
            "agent_A",
            wish_type=WishType.FIND_COMPANION,
            seeking=["entrepreneurial_experience", "willing_to_listen"],
        )

        # Exchange broadcasts to all agents
        broadcast = market.get_open_needs()  # Agents poll this

        # Agent B decides locally it can help, posts response
        resp = market.post_response(
            "agent_B",
            in_response_to=need.request_id,
            offering=["entrepreneurial_experience", "high_benevolence"],
        )

        # Exchange creates match
        matches = market.create_matches()

        # Bilateral verification (each agent checks locally)
        market.verify("match_id", "agent_A", approved=True)
        market.verify("match_id", "agent_B", approved=True)

        # Both passed → mutual
        mutual = market.get_mutual_matches()
    """

    CAPABILITY_THRESHOLD = 0.3  # Minimum capability overlap
    MAX_ACTIVE_NEEDS_PER_AGENT = 5
    MAX_RESPONSES_PER_NEED = 10
    MATCH_EXPIRY_HOURS = 72

    def __init__(self, db_path: str | None = None):
        self._agents: dict[str, AgentRecord] = {}
        self._requests: dict[str, Request] = {}
        self._matches: dict[str, Match] = {}
        self._db: sqlite3.Connection | None = None
        if db_path:
            self._db = sqlite3.connect(db_path)
            self._db_init()
            self._load_from_db()

    def _db_init(self) -> None:
        assert self._db
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY, data TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS requests (
                request_id TEXT PRIMARY KEY, data TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY, data TEXT NOT NULL
            );
        """)
        self._db.commit()

    def _load_from_db(self) -> None:
        assert self._db
        for (data,) in self._db.execute("SELECT data FROM agents"):
            rec = AgentRecord(**json.loads(data))
            self._agents[rec.agent_id] = rec
        for (data,) in self._db.execute("SELECT data FROM requests"):
            req = Request(**json.loads(data))
            self._requests[req.request_id] = req
        for (data,) in self._db.execute("SELECT data FROM matches"):
            m = Match(**json.loads(data))
            self._matches[m.match_id] = m

    def _save_agent(self, record: AgentRecord) -> None:
        if self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO agents (agent_id, data) VALUES (?, ?)",
                (record.agent_id, record.model_dump_json()),
            )
            self._db.commit()

    def _save_request(self, req: Request) -> None:
        if self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO requests (request_id, data) VALUES (?, ?)",
                (req.request_id, req.model_dump_json()),
            )
            self._db.commit()

    def _save_match(self, match: Match) -> None:
        if self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO matches (match_id, data) VALUES (?, ?)",
                (match.match_id, match.model_dump_json()),
            )
            self._db.commit()

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._db:
            self._db.close()
            self._db = None

    # ── Agent registration ───────────────────────────────────────────────

    def register_agent(self, agent_id: str, language: str = "en") -> AgentRecord:
        """Register an agent. Exchange only tracks behavior, not profile."""
        if agent_id in self._agents:
            return self._agents[agent_id]
        record = AgentRecord(agent_id=agent_id, language=language)
        self._agents[agent_id] = record
        self._save_agent(record)
        return record

    def _check_agent(self, agent_id: str) -> AgentRecord:
        """Get agent record, raise if not registered or suspended."""
        record = self._agents.get(agent_id)
        if not record:
            raise ValueError(f"Agent {agent_id} not registered")
        if record.trust_level == AgentTrustLevel.SUSPENDED:
            raise ValueError(f"Agent {agent_id} is suspended")
        return record

    # ── Posting needs ────────────────────────────────────────────────────

    def post_need(
        self,
        agent_id: str,
        wish_type: WishType,
        seeking: list[str],
    ) -> Request:
        """Agent posts a need (buy order). Contains ONLY what is sought."""
        record = self._check_agent(agent_id)

        # Rate limit
        active = sum(
            1 for r in self._requests.values()
            if r.agent_id == agent_id
            and r.request_type == RequestType.NEED
            and r.state == RequestState.OPEN
        )
        if active >= self.MAX_ACTIVE_NEEDS_PER_AGENT:
            raise ValueError(f"Agent {agent_id} has too many active needs")

        req = Request(
            agent_id=agent_id,
            request_type=RequestType.NEED,
            wish_type=wish_type,
            seeking=seeking,
        )
        self._requests[req.request_id] = req
        record.total_requests += 1
        self._save_request(req)
        self._save_agent(record)
        return req

    # ── Posting responses ────────────────────────────────────────────────

    def post_response(
        self,
        agent_id: str,
        in_response_to: str,
        offering: list[str],
    ) -> Request:
        """Agent responds to a need (sell order). Contains ONLY what is offered."""
        record = self._check_agent(agent_id)

        need = self._requests.get(in_response_to)
        if not need:
            raise ValueError(f"Need {in_response_to} not found")
        if need.state != RequestState.OPEN:
            raise ValueError(f"Need {in_response_to} is not open")
        if need.agent_id == agent_id:
            raise ValueError("Cannot respond to your own need")

        # Check response limit
        existing = sum(
            1 for r in self._requests.values()
            if r.in_response_to == in_response_to
            and r.state == RequestState.OPEN
        )
        if existing >= self.MAX_RESPONSES_PER_NEED:
            raise ValueError(f"Need {in_response_to} has too many responses")

        resp = Request(
            agent_id=agent_id,
            request_type=RequestType.RESPONSE,
            wish_type=need.wish_type,
            offering=offering,
            in_response_to=in_response_to,
        )
        self._requests[resp.request_id] = resp
        record.total_responses += 1
        self._save_request(resp)
        self._save_agent(record)
        return resp

    # ── Match creation ───────────────────────────────────────────────────

    def create_matches(self) -> list[Match]:
        """Create matches from need-response pairs above threshold.

        Exchange computes capability overlap ONLY — does not access profiles.
        """
        responses = [
            r for r in self._requests.values()
            if r.request_type == RequestType.RESPONSE and r.state == RequestState.OPEN
        ]

        new_matches: list[Match] = []
        for resp in responses:
            need = self._requests.get(resp.in_response_to or "")
            if not need or need.state != RequestState.OPEN:
                continue

            overlap = _compute_capability_overlap(need.seeking, resp.offering)
            if overlap >= self.CAPABILITY_THRESHOLD:
                match = Match(
                    need_request_id=need.request_id,
                    response_request_id=resp.request_id,
                    agent_a_id=need.agent_id,
                    agent_b_id=resp.agent_id,
                    capability_overlap=overlap,
                )
                self._matches[match.match_id] = match
                need.state = RequestState.MATCHED
                resp.state = RequestState.MATCHED
                new_matches.append(match)
                self._save_match(match)
                self._save_request(need)
                self._save_request(resp)

                # Update records
                for aid in (need.agent_id, resp.agent_id):
                    if aid in self._agents:
                        self._agents[aid].total_matches += 1
                        self._save_agent(self._agents[aid])

        return new_matches

    # ── Verification ─────────────────────────────────────────────────────

    def verify(self, match_id: str, agent_id: str, approved: bool) -> Match:
        """Agent verifies a proposed match.

        Each agent checks LOCALLY whether the match is safe for their host.
        Exchange doesn't know WHY they approved/declined — just the result.
        """
        match = self._matches.get(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")
        if agent_id not in (match.agent_a_id, match.agent_b_id):
            raise ValueError(f"Agent {agent_id} not part of match {match_id}")

        if not approved:
            if agent_id == match.agent_a_id:
                match.state = MatchState.A_DECLINED
            else:
                match.state = MatchState.B_DECLINED
            if agent_id in self._agents:
                self._agents[agent_id].declined_count += 1
                self._save_agent(self._agents[agent_id])
            self._save_match(match)
            return match

        if agent_id == match.agent_a_id:
            if match.state == MatchState.PROPOSED:
                match.state = MatchState.A_VERIFIED
            elif match.state == MatchState.B_VERIFIED:
                match.state = MatchState.MUTUAL
                match.verified_at = time.time()
        elif agent_id == match.agent_b_id:
            if match.state == MatchState.PROPOSED:
                match.state = MatchState.B_VERIFIED
            elif match.state == MatchState.A_VERIFIED:
                match.state = MatchState.MUTUAL
                match.verified_at = time.time()

        self._save_match(match)
        return match

    # ── Queries ──────────────────────────────────────────────────────────

    def get_open_needs(self, language: str | None = None) -> list[Request]:
        """Get all open needs — agents poll this to find matches.

        Optionally filter by language for same-language matching.
        """
        needs = [
            r for r in self._requests.values()
            if r.request_type == RequestType.NEED and r.state == RequestState.OPEN
        ]
        if language:
            needs = [
                n for n in needs
                if self._agents.get(n.agent_id, AgentRecord(agent_id="")).language == language
            ]
        return needs

    def get_mutual_matches(self) -> list[Match]:
        """Get matches where both agents verified — ready for human notification."""
        return [m for m in self._matches.values() if m.state == MatchState.MUTUAL]

    def get_agent_matches(self, agent_id: str) -> list[Match]:
        """Get all matches involving this agent."""
        return [
            m for m in self._matches.values()
            if m.agent_a_id == agent_id or m.agent_b_id == agent_id
        ]

    def get_stats(self) -> dict[str, Any]:
        """Marketplace statistics — like exchange market data."""
        return {
            "agents": len(self._agents),
            "open_needs": sum(1 for r in self._requests.values()
                             if r.request_type == RequestType.NEED and r.state == RequestState.OPEN),
            "open_responses": sum(1 for r in self._requests.values()
                                 if r.request_type == RequestType.RESPONSE and r.state == RequestState.OPEN),
            "total_matches": len(self._matches),
            "mutual_matches": sum(1 for m in self._matches.values() if m.state == MatchState.MUTUAL),
            "declined": sum(1 for m in self._matches.values()
                          if m.state in (MatchState.A_DECLINED, MatchState.B_DECLINED)),
        }

    # ── Trust management ─────────────────────────────────────────────────

    def promote_agent(self, agent_id: str) -> None:
        """Promote agent from probation to trusted after good behavior."""
        record = self._agents.get(agent_id)
        if record and record.trust_level == AgentTrustLevel.PROBATION:
            if record.total_matches >= 3 and record.declined_count <= 1:
                record.trust_level = AgentTrustLevel.TRUSTED
                self._save_agent(record)

    def suspend_agent(self, agent_id: str) -> None:
        """Suspend agent for abnormal behavior."""
        record = self._agents.get(agent_id)
        if record:
            record.trust_level = AgentTrustLevel.SUSPENDED
            self._save_agent(record)

    # ── Expiry ───────────────────────────────────────────────────────────

    def expire_stale(self) -> int:
        """Expire old unverified matches."""
        now = time.time()
        expired = 0
        cutoff = self.MATCH_EXPIRY_HOURS * 3600
        for match in self._matches.values():
            if match.state in (MatchState.PROPOSED, MatchState.A_VERIFIED, MatchState.B_VERIFIED):
                if now - match.created_at > cutoff:
                    match.state = MatchState.EXPIRED
                    expired += 1
                    self._save_match(match)
        return expired
