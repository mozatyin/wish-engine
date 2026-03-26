"""AgentNegotiator — agent-to-agent negotiation protocol for L3 matching.

Flow:
    Agent A propose → Agent B evaluate(状态/能力/负载) → accept/delay/decline

Safety gates:
    - Crisis users: never enter negotiation (excluded at pool level)
    - distress > 0.6: auto-delay (agent defers on behalf of user)
    - load >= 5: auto-delay (too many active connections)

Privacy:
    - Negotiation is between agents, not users
    - Agents evaluate locally using dimension data only
    - No conversation content is exchanged during negotiation

Zero LLM — all decisions are rule-based.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from wish_engine.models import (
    AgentProfile,
    L3MatchResult,
    NegotiationProposal,
    NegotiationResponse,
    NegotiationState,
    WishType,
)
from wish_engine.l3_matcher import L3Matcher, L3MatchScore, MATCH_THRESHOLD


# Default delay when user is in distress (24 hours)
DISTRESS_DELAY_SECONDS = 24 * 3600
# Default delay when load is high (6 hours)
LOAD_DELAY_SECONDS = 6 * 3600
# Maximum active negotiations per agent
MAX_ACTIVE_NEGOTIATIONS = 3
# Negotiation expiry (48 hours)
NEGOTIATION_EXPIRY_SECONDS = 48 * 3600


class AgentNegotiator:
    """Agent-to-agent negotiation protocol for L3 wish matching.

    Each agent runs a negotiator instance locally. The negotiator:
    1. Creates proposals (when agent finds a match for its user)
    2. Evaluates incoming proposals (checks user safety/availability)
    3. Tracks negotiation state

    Usage:
        negotiator = AgentNegotiator(matcher=L3Matcher())

        # Agent A proposes to Agent B
        proposal = negotiator.propose(
            from_profile=profile_a,
            to_profile=profile_b,
            match_id="match_123",
            wish_type=WishType.FIND_COMPANION,
            seeking=["empathy"],
            offering=["empathy"],
        )

        # Agent B evaluates
        response = negotiator.evaluate(
            proposal=proposal,
            local_profile=profile_b,
        )

        # Check result
        if response.state == NegotiationState.ACCEPTED:
            # Create L3MatchResult
            result = negotiator.finalize(proposal, profile_a, profile_b)
    """

    def __init__(self, matcher: L3Matcher | None = None):
        self._matcher = matcher or L3Matcher()
        self._proposals: dict[str, NegotiationProposal] = {}
        self._responses: dict[str, NegotiationResponse] = {}
        self._active_negotiations: dict[str, int] = {}  # agent_id → count

    @property
    def matcher(self) -> L3Matcher:
        return self._matcher

    def propose(
        self,
        from_profile: AgentProfile,
        to_profile: AgentProfile,
        match_id: str,
        wish_type: WishType,
        seeking: list[str] | None = None,
        offering: list[str] | None = None,
    ) -> NegotiationProposal | None:
        """Agent A creates a proposal for Agent B.

        Returns None if:
        - Either user fails safety gate
        - Match score below threshold
        - Agent A has too many active negotiations
        """
        # Safety: crisis users never propose
        safe_a, _ = self._matcher.is_safe_for_pool(from_profile)
        if not safe_a:
            return None
        safe_b, _ = self._matcher.is_safe_for_pool(to_profile)
        if not safe_b:
            return None

        # Rate limit: max active negotiations
        a_active = self._active_negotiations.get(from_profile.agent_id, 0)
        if a_active >= MAX_ACTIVE_NEGOTIATIONS:
            return None

        # Compute match score
        score = self._matcher.score(
            from_profile, to_profile, wish_type,
            seeking=seeking, offering=offering,
        )
        if not score or score.total < self._matcher.threshold:
            return None

        proposal_id = f"neg_{uuid.uuid4().hex[:8]}"
        proposal = NegotiationProposal(
            proposal_id=proposal_id,
            match_id=match_id,
            from_agent_id=from_profile.agent_id,
            to_agent_id=to_profile.agent_id,
            wish_type=wish_type,
            match_score=round(score.total, 3),
            score_breakdown=score.to_dict(),
        )
        self._proposals[proposal_id] = proposal
        self._active_negotiations[from_profile.agent_id] = a_active + 1
        return proposal

    def evaluate(
        self,
        proposal: NegotiationProposal,
        local_profile: AgentProfile,
    ) -> NegotiationResponse:
        """Agent B evaluates an incoming proposal.

        Decision logic (all local, zero LLM):
        1. Crisis → decline (should never reach here, but defense-in-depth)
        2. distress > 0.6 → delay (24h)
        3. load >= 5 → delay (6h)
        4. Not available → decline
        5. Match score below threshold → decline
        6. Otherwise → accept
        """
        # Defense-in-depth: crisis check
        if local_profile.is_crisis:
            return NegotiationResponse(
                proposal_id=proposal.proposal_id,
                agent_id=local_profile.agent_id,
                state=NegotiationState.DECLINED,
                reason="crisis",
            )

        # Distress gate: delay matching
        if local_profile.distress > 0.6:
            delay_until = time.time() + DISTRESS_DELAY_SECONDS
            response = NegotiationResponse(
                proposal_id=proposal.proposal_id,
                agent_id=local_profile.agent_id,
                state=NegotiationState.DELAYED,
                reason="high_distress",
                delay_until=delay_until,
            )
            self._responses[proposal.proposal_id] = response
            return response

        # Load gate: delay if overloaded
        if local_profile.load >= 5:
            delay_until = time.time() + LOAD_DELAY_SECONDS
            response = NegotiationResponse(
                proposal_id=proposal.proposal_id,
                agent_id=local_profile.agent_id,
                state=NegotiationState.DELAYED,
                reason="load_limit",
                delay_until=delay_until,
            )
            self._responses[proposal.proposal_id] = response
            return response

        # Availability gate
        if not local_profile.available:
            response = NegotiationResponse(
                proposal_id=proposal.proposal_id,
                agent_id=local_profile.agent_id,
                state=NegotiationState.DECLINED,
                reason="unavailable",
            )
            self._responses[proposal.proposal_id] = response
            return response

        # Score gate: verify the match score is acceptable
        if proposal.match_score < self._matcher.threshold:
            response = NegotiationResponse(
                proposal_id=proposal.proposal_id,
                agent_id=local_profile.agent_id,
                state=NegotiationState.DECLINED,
                reason="below_threshold",
            )
            self._responses[proposal.proposal_id] = response
            return response

        # All gates passed → accept
        response = NegotiationResponse(
            proposal_id=proposal.proposal_id,
            agent_id=local_profile.agent_id,
            state=NegotiationState.ACCEPTED,
        )
        self._responses[proposal.proposal_id] = response
        b_active = self._active_negotiations.get(local_profile.agent_id, 0)
        self._active_negotiations[local_profile.agent_id] = b_active + 1
        return response

    def finalize(
        self,
        proposal: NegotiationProposal,
        a_profile: AgentProfile,
        b_profile: AgentProfile,
        is_mutual: bool = False,
    ) -> L3MatchResult:
        """Create final L3MatchResult after successful negotiation.

        Call this after both agents have accepted (or after mutual detection).
        """
        match_text = (
            "Your stars found each other"
            if is_mutual
            else "Someone's star resonates with yours"
        )

        return L3MatchResult(
            match_id=proposal.match_id,
            agent_a_id=a_profile.agent_id,
            agent_b_id=b_profile.agent_id,
            wish_type=proposal.wish_type,
            match_score=proposal.match_score,
            score_breakdown=proposal.score_breakdown,
            is_mutual=is_mutual,
            match_text=match_text,
        )

    def negotiate_full(
        self,
        a_profile: AgentProfile,
        b_profile: AgentProfile,
        match_id: str,
        wish_type: WishType,
        seeking: list[str] | None = None,
        offering: list[str] | None = None,
    ) -> tuple[L3MatchResult | None, NegotiationResponse | None]:
        """Run full negotiation: propose → evaluate → finalize.

        Convenience method for synchronous negotiation.

        Returns:
            (L3MatchResult, None) if accepted
            (None, NegotiationResponse) if delayed/declined
            (None, None) if proposal failed safety gates
        """
        proposal = self.propose(
            from_profile=a_profile,
            to_profile=b_profile,
            match_id=match_id,
            wish_type=wish_type,
            seeking=seeking,
            offering=offering,
        )
        if not proposal:
            return None, None

        response = self.evaluate(proposal, local_profile=b_profile)

        if response.state == NegotiationState.ACCEPTED:
            result = self.finalize(proposal, a_profile, b_profile)
            return result, response

        return None, response

    def negotiate_mutual(
        self,
        a_profile: AgentProfile,
        b_profile: AgentProfile,
        match_id: str,
        a_wish_type: WishType,
        b_wish_type: WishType,
        a_seeking: list[str] | None = None,
        a_offering: list[str] | None = None,
        b_seeking: list[str] | None = None,
        b_offering: list[str] | None = None,
    ) -> L3MatchResult | None:
        """Detect and negotiate mutual matches.

        If both A and B have complementary wishes, create a mutual match
        with "Your stars found each other".

        Returns L3MatchResult with is_mutual=True if both directions pass.
        """
        # Check mutual complementarity
        is_mutual = self._matcher.detect_mutual(
            a_profile, b_profile,
            a_wish_type, b_wish_type,
            a_seeking=a_seeking,
            a_offering=a_offering,
            b_seeking=b_seeking,
            b_offering=b_offering,
        )
        if not is_mutual:
            return None

        # Both directions pass threshold — run safety evaluation for both
        # A evaluates B's direction
        proposal_ab = NegotiationProposal(
            proposal_id=f"neg_{uuid.uuid4().hex[:8]}",
            match_id=match_id,
            from_agent_id=a_profile.agent_id,
            to_agent_id=b_profile.agent_id,
            wish_type=a_wish_type,
            match_score=1.0,  # already verified above threshold
        )
        resp_b = self.evaluate(proposal_ab, local_profile=b_profile)
        if resp_b.state != NegotiationState.ACCEPTED:
            return None

        # B evaluates A's direction
        proposal_ba = NegotiationProposal(
            proposal_id=f"neg_{uuid.uuid4().hex[:8]}",
            match_id=f"{match_id}_reverse",
            from_agent_id=b_profile.agent_id,
            to_agent_id=a_profile.agent_id,
            wish_type=b_wish_type,
            match_score=1.0,
        )
        resp_a = self.evaluate(proposal_ba, local_profile=a_profile)
        if resp_a.state != NegotiationState.ACCEPTED:
            return None

        # Both accepted — compute actual score for A→B direction
        score = self._matcher.score(
            a_profile, b_profile, a_wish_type,
            seeking=a_seeking, offering=a_offering,
        )

        return L3MatchResult(
            match_id=match_id,
            agent_a_id=a_profile.agent_id,
            agent_b_id=b_profile.agent_id,
            wish_type=a_wish_type,
            match_score=round(score.total, 3) if score else 0.0,
            score_breakdown=score.to_dict() if score else {},
            is_mutual=True,
            match_text="Your stars found each other",
        )

    def get_proposal(self, proposal_id: str) -> NegotiationProposal | None:
        return self._proposals.get(proposal_id)

    def get_response(self, proposal_id: str) -> NegotiationResponse | None:
        return self._responses.get(proposal_id)

    def get_active_count(self, agent_id: str) -> int:
        return self._active_negotiations.get(agent_id, 0)

    def expire_stale(self) -> int:
        """Expire negotiations older than NEGOTIATION_EXPIRY_SECONDS."""
        now = time.time()
        expired = 0
        cutoff = now - NEGOTIATION_EXPIRY_SECONDS
        for pid, proposal in list(self._proposals.items()):
            if proposal.created_at < cutoff:
                # Decrement active counts
                a_count = self._active_negotiations.get(proposal.from_agent_id, 0)
                if a_count > 0:
                    self._active_negotiations[proposal.from_agent_id] = a_count - 1
                resp = self._responses.get(pid)
                if resp and resp.state == NegotiationState.ACCEPTED:
                    b_count = self._active_negotiations.get(resp.agent_id, 0)
                    if b_count > 0:
                        self._active_negotiations[resp.agent_id] = b_count - 1
                del self._proposals[pid]
                if pid in self._responses:
                    del self._responses[pid]
                expired += 1
        return expired
