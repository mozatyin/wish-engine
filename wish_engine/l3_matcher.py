"""L3Matcher — multi-dimensional match scoring for user-to-user connections.

Match Score = 0.3×Wish Alignment + 0.25×Soul Compatibility + 0.2×Emotional Safety
              + 0.15×Availability + 0.1×Novelty

All computation is local and deterministic. Zero LLM.

Privacy: operates on AgentProfile (dimension scores only), never on conversation content.
Safety: crisis users excluded, distress>0.6 delayed.
"""

from __future__ import annotations

import re

from wish_engine.models import AgentProfile, WishType

# Common stopwords to ignore in semantic alignment
_STOPWORDS: frozenset[str] = frozenset({
    "i", "a", "an", "the", "is", "it", "to", "of", "and", "or", "in",
    "my", "me", "we", "you", "he", "she", "they", "have", "has", "do",
    "did", "can", "will", "want", "need", "feel", "be", "am", "are",
    "was", "were", "been", "for", "on", "at", "by", "as", "this", "that",
})


# ── Compatibility tables (zero LLM, lookup only) ────────────────────────────

# Attachment style compatibility: secure is universally safe;
# anxious-avoidant is volatile; same-insecure can be supportive short-term
_ATTACHMENT_HARMONY: dict[tuple[str, str], float] = {
    ("secure", "secure"): 0.9,
    ("secure", "anxious"): 0.7,
    ("secure", "avoidant"): 0.7,
    ("secure", "fearful"): 0.6,
    ("anxious", "secure"): 0.7,
    ("avoidant", "secure"): 0.7,
    ("fearful", "secure"): 0.6,
    ("anxious", "anxious"): 0.4,
    ("avoidant", "avoidant"): 0.5,
    ("anxious", "avoidant"): 0.2,  # volatile pair
    ("avoidant", "anxious"): 0.2,
    ("fearful", "fearful"): 0.3,
    ("fearful", "anxious"): 0.3,
    ("anxious", "fearful"): 0.3,
    ("fearful", "avoidant"): 0.3,
    ("avoidant", "fearful"): 0.3,
}

# Conflict style compatibility
_CONFLICT_HARMONY: dict[tuple[str, str], float] = {
    ("collaborating", "collaborating"): 0.9,
    ("collaborating", "compromising"): 0.8,
    ("collaborating", "accommodating"): 0.7,
    ("collaborating", "avoiding"): 0.5,
    ("collaborating", "competing"): 0.4,
    ("compromising", "collaborating"): 0.8,
    ("compromising", "compromising"): 0.7,
    ("compromising", "accommodating"): 0.7,
    ("compromising", "avoiding"): 0.5,
    ("compromising", "competing"): 0.4,
    ("accommodating", "collaborating"): 0.7,
    ("accommodating", "compromising"): 0.7,
    ("accommodating", "accommodating"): 0.6,
    ("accommodating", "avoiding"): 0.5,
    ("accommodating", "competing"): 0.3,
    ("avoiding", "collaborating"): 0.5,
    ("avoiding", "compromising"): 0.5,
    ("avoiding", "accommodating"): 0.5,
    ("avoiding", "avoiding"): 0.4,
    ("avoiding", "competing"): 0.2,
    ("competing", "collaborating"): 0.4,
    ("competing", "compromising"): 0.4,
    ("competing", "accommodating"): 0.3,
    ("competing", "avoiding"): 0.2,
    ("competing", "competing"): 0.1,
}

# MBTI function stack complementarity (simplified: same or adjacent types = higher)
_MBTI_HARMONY: dict[str, set[str]] = {
    # Idealist pairs — NF types connect naturally
    "INFJ": {"ENFP", "INFP", "ENFJ", "INTJ"},
    "INFP": {"ENFJ", "INFJ", "ENFP", "ISFP"},
    "ENFJ": {"INFP", "INFJ", "ENFP", "ENTJ"},
    "ENFP": {"INFJ", "INTJ", "INFP", "ENFJ"},
    # Analyst pairs — NT types
    "INTJ": {"ENFP", "ENTP", "INFJ", "ENTJ"},
    "INTP": {"ENTJ", "ENTP", "INFJ", "INTJ"},
    "ENTJ": {"INTP", "INFP", "INTJ", "ENFJ"},
    "ENTP": {"INFJ", "INTJ", "INTP", "ENFP"},
    # Sentinel pairs — SJ types
    "ISTJ": {"ESFJ", "ISFJ", "ESTJ", "ISTP"},
    "ISFJ": {"ESFP", "ESTP", "ISTJ", "ESFJ"},
    "ESTJ": {"ISFP", "ISTP", "ISTJ", "ESFJ"},
    "ESFJ": {"ISTP", "ISFP", "ISTJ", "ISFJ"},
    # Explorer pairs — SP types
    "ISTP": {"ESFJ", "ESTJ", "ESTP", "ISFP"},
    "ISFP": {"ENTJ", "ESTJ", "ESFJ", "INFP"},
    "ESTP": {"ISFJ", "ISTJ", "ISTP", "ESFP"},
    "ESFP": {"ISFJ", "ISTJ", "ESTP", "ISFP"},
}

# Wish type → which dimensions matter most for matching
_WISH_DIMENSION_WEIGHTS: dict[WishType, dict[str, float]] = {
    WishType.FIND_COMPANION: {
        "attachment": 0.3, "values": 0.3, "conflict": 0.2, "mbti": 0.2,
    },
    WishType.FIND_MENTOR: {
        "eq": 0.3, "communication": 0.3, "values": 0.2, "conflict": 0.2,
    },
    WishType.SKILL_EXCHANGE: {
        "communication": 0.3, "humor": 0.2, "values": 0.2, "mbti": 0.3,
    },
    WishType.SHARED_EXPERIENCE: {
        "values": 0.3, "humor": 0.3, "mbti": 0.2, "attachment": 0.2,
    },
    WishType.EMOTIONAL_SUPPORT: {
        "attachment": 0.35, "eq": 0.30, "conflict": 0.20, "fragility": 0.15,
    },
}


# ── Score components ─────────────────────────────────────────────────────────


def _text_alignment(text_a: str, text_b: str) -> float:
    """Keyword Jaccard similarity between two wish-text summaries.

    Tokenizes, removes stopwords, computes |intersection| / |union|.
    Returns 0.0 for empty inputs.
    """
    def _tokens(text: str) -> set[str]:
        return {t for t in re.split(r"[^a-zA-Z]+", text.lower()) if t and t not in _STOPWORDS}

    a_tokens = _tokens(text_a)
    b_tokens = _tokens(text_b)
    if not a_tokens or not b_tokens:
        return 0.0
    union = a_tokens | b_tokens
    return len(a_tokens & b_tokens) / len(union)


def _wish_alignment(
    wish_type: WishType,
    seeking: list[str],
    offering: list[str],
) -> float:
    """How well B's offering aligns with A's need. Jaccard on capability tags."""
    if not seeking:
        return 0.0
    seek_set = set(seeking)
    offer_set = set(offering)
    matched = len(seek_set & offer_set)
    return matched / len(seek_set)


def _values_overlap(a_values: list[str], b_values: list[str]) -> float:
    """Shared value dimensions (Jaccard)."""
    if not a_values or not b_values:
        return 0.5  # neutral if unknown
    a_set = set(v.lower() for v in a_values)
    b_set = set(v.lower() for v in b_values)
    union = a_set | b_set
    if not union:
        return 0.5
    return len(a_set & b_set) / len(union)


def _soul_compatibility(
    a: AgentProfile,
    b: AgentProfile,
    wish_type: WishType,
) -> float:
    """Weighted soul compatibility based on wish-type-relevant dimensions."""
    weights = _WISH_DIMENSION_WEIGHTS.get(wish_type, {
        "attachment": 0.25, "values": 0.25, "conflict": 0.25, "mbti": 0.25,
    })

    scores: dict[str, float] = {}

    # Attachment harmony
    if "attachment" in weights:
        a_att = a.attachment_style.lower().split("-")[0] if a.attachment_style else ""
        b_att = b.attachment_style.lower().split("-")[0] if b.attachment_style else ""
        if a_att and b_att:
            scores["attachment"] = _ATTACHMENT_HARMONY.get((a_att, b_att), 0.5)
        else:
            scores["attachment"] = 0.5

    # Conflict harmony
    if "conflict" in weights:
        a_con = a.conflict_style.lower() if a.conflict_style else ""
        b_con = b.conflict_style.lower() if b.conflict_style else ""
        if a_con and b_con:
            scores["conflict"] = _CONFLICT_HARMONY.get((a_con, b_con), 0.5)
        else:
            scores["conflict"] = 0.5

    # MBTI complementarity
    if "mbti" in weights:
        a_mbti = a.mbti.upper() if a.mbti else ""
        b_mbti = b.mbti.upper() if b.mbti else ""
        if a_mbti and b_mbti:
            compatible = _MBTI_HARMONY.get(a_mbti, set())
            scores["mbti"] = 0.8 if b_mbti in compatible else 0.4
        else:
            scores["mbti"] = 0.5

    # Values overlap
    if "values" in weights:
        scores["values"] = _values_overlap(a.values, b.values)

    # EQ (for mentor/emotional support: B should have higher EQ)
    if "eq" in weights:
        if b.eq_score > 0:
            scores["eq"] = min(b.eq_score, 1.0)
        else:
            scores["eq"] = 0.5

    # Communication style compatibility (same = good for shared experience)
    if "communication" in weights:
        if a.communication_style and b.communication_style:
            scores["communication"] = 0.7 if a.communication_style == b.communication_style else 0.5
        else:
            scores["communication"] = 0.5

    # Humor style (same humor = bonding)
    if "humor" in weights:
        if a.humor_style and b.humor_style:
            scores["humor"] = 0.8 if a.humor_style == b.humor_style else 0.4
        else:
            scores["humor"] = 0.5

    # Fragility (for emotional support: avoid pairing two highly fragile users)
    if "fragility" in weights:
        a_frag = 1.0 if a.fragility_pattern else 0.0
        b_frag = 1.0 if b.fragility_pattern else 0.0
        # One fragile + one stable = ok; both fragile = risky
        if a_frag and b_frag:
            scores["fragility"] = 0.3
        elif not a_frag and not b_frag:
            scores["fragility"] = 0.7
        else:
            scores["fragility"] = 0.6

    # Weighted average
    total = 0.0
    total_weight = 0.0
    for dim, weight in weights.items():
        if dim in scores:
            total += scores[dim] * weight
            total_weight += weight

    return total / total_weight if total_weight > 0 else 0.5


def _emotional_safety(a: AgentProfile, b: AgentProfile) -> float:
    """Emotional safety score — both users should be in a safe state."""
    score = 1.0

    # Distress penalty (either side)
    if a.distress > 0.3:
        score -= 0.2 * (a.distress - 0.3) / 0.7  # gradual
    if b.distress > 0.3:
        score -= 0.2 * (b.distress - 0.3) / 0.7

    # Attachment safety: anxious+avoidant pairing has extra risk
    a_att = a.attachment_style.lower().split("-")[0] if a.attachment_style else ""
    b_att = b.attachment_style.lower().split("-")[0] if b.attachment_style else ""
    if {a_att, b_att} == {"anxious", "avoidant"}:
        score -= 0.15

    # EQ floor: at least one should have reasonable EQ
    if a.eq_score > 0 and b.eq_score > 0:
        if max(a.eq_score, b.eq_score) < 0.4:
            score -= 0.1

    return max(0.0, min(1.0, score))


def _availability(a: AgentProfile, b: AgentProfile) -> float:
    """Availability score based on load and explicit availability flag."""
    if not a.available or not b.available:
        return 0.0

    # Load penalty: more active connections = less available
    max_load = 5
    a_load_score = max(0.0, 1.0 - a.load / max_load)
    b_load_score = max(0.0, 1.0 - b.load / max_load)
    return (a_load_score + b_load_score) / 2


def _novelty(a: AgentProfile, b: AgentProfile, past_matches: list[str] | None = None) -> float:
    """Novelty score — prefer new connections over repeated matches."""
    if past_matches is None:
        past_matches = []

    # If B was already matched with A before, reduce novelty
    if b.agent_id in past_matches or a.agent_id in past_matches:
        return 0.2
    return 1.0


# ── Main scorer ──────────────────────────────────────────────────────────────

# Weights from spec
W_WISH = 0.30
W_SOUL = 0.25
W_SAFETY = 0.20
W_AVAIL = 0.15
W_NOVELTY = 0.10

# Minimum score to proceed with negotiation
MATCH_THRESHOLD = 0.45


class L3MatchScore:
    """Computed match score with full breakdown."""

    __slots__ = (
        "total", "wish_alignment", "soul_compatibility",
        "emotional_safety", "availability", "novelty", "text_alignment",
    )

    def __init__(
        self,
        wish_alignment: float,
        soul_compatibility: float,
        emotional_safety: float,
        availability: float,
        novelty: float,
        text_alignment: float = 0.0,
    ):
        self.wish_alignment = wish_alignment
        self.soul_compatibility = soul_compatibility
        self.emotional_safety = emotional_safety
        self.availability = availability
        self.novelty = novelty
        self.text_alignment = text_alignment
        self.total = (
            W_WISH * wish_alignment
            + W_SOUL * soul_compatibility
            + W_SAFETY * emotional_safety
            + W_AVAIL * availability
            + W_NOVELTY * novelty
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "wish_alignment": round(self.wish_alignment, 3),
            "soul_compatibility": round(self.soul_compatibility, 3),
            "emotional_safety": round(self.emotional_safety, 3),
            "availability": round(self.availability, 3),
            "novelty": round(self.novelty, 3),
            "text_alignment": round(self.text_alignment, 3),
            "total": round(self.total, 3),
        }


class L3Matcher:
    """Multi-dimensional L3 match scorer.

    Computes match score between two agents based on dimension data only.
    Zero LLM — all scoring is deterministic lookup + arithmetic.

    Safety gates:
    - Crisis users are excluded (returns None)
    - distress > 0.6 returns score but flags as unsafe

    Privacy:
    - Operates on AgentProfile (dimension scores/labels only)
    - Never accesses conversation content

    Usage:
        matcher = L3Matcher()
        score = matcher.score(
            profile_a, profile_b,
            wish_type=WishType.FIND_COMPANION,
            seeking=["empathy", "shared_experience"],
            offering=["empathy", "good_listener"],
        )
        if score and score.total >= MATCH_THRESHOLD:
            # proceed to negotiation
    """

    def __init__(self, threshold: float = MATCH_THRESHOLD):
        self._threshold = threshold

    @property
    def threshold(self) -> float:
        return self._threshold

    def is_safe_for_pool(self, profile: AgentProfile) -> tuple[bool, str]:
        """Check if a user is safe to enter the matching pool.

        Returns:
            (is_safe, reason) — reason is empty if safe.
        """
        if profile.is_crisis:
            return False, "crisis"
        if not profile.available:
            return False, "unavailable"
        return True, ""

    def should_delay(self, profile: AgentProfile) -> tuple[bool, str]:
        """Check if matching should be delayed for this user.

        Returns:
            (should_delay, reason)
        """
        if profile.distress > 0.6:
            return True, "high_distress"
        if profile.load >= 5:
            return True, "load_limit"
        return False, ""

    def score(
        self,
        a: AgentProfile,
        b: AgentProfile,
        wish_type: WishType,
        seeking: list[str] | None = None,
        offering: list[str] | None = None,
        past_matches: list[str] | None = None,
    ) -> L3MatchScore | None:
        """Compute multi-dimensional match score.

        Returns None if either user fails safety gate (crisis).
        """
        # Safety gate: crisis users excluded
        safe_a, reason_a = self.is_safe_for_pool(a)
        if not safe_a:
            return None
        safe_b, reason_b = self.is_safe_for_pool(b)
        if not safe_b:
            return None

        wa = _wish_alignment(wish_type, seeking or [], offering or [])
        sc = _soul_compatibility(a, b, wish_type)
        es = _emotional_safety(a, b)
        av = _availability(a, b)
        nv = _novelty(a, b, past_matches)
        ta = _text_alignment(a.wish_text, b.wish_text)

        return L3MatchScore(
            wish_alignment=wa,
            soul_compatibility=sc,
            emotional_safety=es,
            availability=av,
            novelty=nv,
            text_alignment=ta,
        )

    def rank_candidates(
        self,
        seeker: AgentProfile,
        candidates: list[AgentProfile],
        wish_type: WishType,
        seeking: list[str] | None = None,
        offerings: dict[str, list[str]] | None = None,
        past_matches: list[str] | None = None,
    ) -> list[tuple[AgentProfile, L3MatchScore]]:
        """Rank multiple candidates by match score.

        Args:
            seeker: The user seeking a match.
            candidates: Potential match partners.
            wish_type: Type of L3 wish.
            seeking: Capability tags the seeker wants.
            offerings: agent_id → offering tags mapping.
            past_matches: List of agent_ids previously matched with seeker.

        Returns:
            Sorted list of (profile, score) tuples, highest first.
            Only includes candidates above threshold.
        """
        offerings = offerings or {}
        results: list[tuple[AgentProfile, L3MatchScore]] = []

        for candidate in candidates:
            if candidate.agent_id == seeker.agent_id:
                continue

            offering = offerings.get(candidate.agent_id, [])
            match_score = self.score(
                seeker, candidate, wish_type,
                seeking=seeking, offering=offering,
                past_matches=past_matches,
            )
            if match_score and match_score.total >= self._threshold:
                results.append((candidate, match_score))

        results.sort(key=lambda x: x[1].total, reverse=True)
        return results

    def detect_mutual(
        self,
        a: AgentProfile,
        b: AgentProfile,
        a_wish_type: WishType,
        b_wish_type: WishType,
        a_seeking: list[str] | None = None,
        a_offering: list[str] | None = None,
        b_seeking: list[str] | None = None,
        b_offering: list[str] | None = None,
    ) -> bool:
        """Detect if two users have mutual complementary wishes.

        "Your stars found each other" — both have L3 wishes that the
        other can fulfill.
        """
        # A's wish fulfilled by B
        score_ab = self.score(
            a, b, a_wish_type,
            seeking=a_seeking, offering=a_offering,
        )
        if not score_ab or score_ab.total < self._threshold:
            return False

        # B's wish fulfilled by A
        score_ba = self.score(
            b, a, b_wish_type,
            seeking=b_seeking, offering=b_offering,
        )
        if not score_ba or score_ba.total < self._threshold:
            return False

        return True
