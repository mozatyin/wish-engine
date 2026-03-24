"""Tests for match reason generator."""

from wish_engine.match_reason import generate_match_reason, _CAPABILITY_TEXT
from wish_engine.marketplace import Match


def _make_match():
    return Match(
        need_request_id="req_1",
        response_request_id="req_2",
        agent_a_id="a1",
        agent_b_id="b1",
        capability_overlap=0.8,
    )


class TestTemplateReason:
    """Template-based reason generation (zero LLM)."""

    def test_english_shared_capability(self):
        reason = generate_match_reason(
            _make_match(),
            need_seeking=["empathy", "willing_to_listen"],
            offer_capabilities=["empathy", "good_listener"],
            language="en",
        )
        assert len(reason) > 0
        assert "AI" not in reason
        assert "algorithm" not in reason

    def test_chinese_shared_capability(self):
        reason = generate_match_reason(
            _make_match(),
            need_seeking=["entrepreneurial_experience"],
            offer_capabilities=["entrepreneurial_experience", "high_benevolence"],
            language="zh",
        )
        assert "从零开始" in reason or "经历" in reason or "星星" in reason

    def test_arabic_shared_capability(self):
        reason = generate_match_reason(
            _make_match(),
            need_seeking=["empathy"],
            offer_capabilities=["empathy"],
            language="ar",
        )
        assert len(reason) > 0

    def test_no_shared_no_api_generic(self):
        """No shared capabilities, no API key → generic reason."""
        reason = generate_match_reason(
            _make_match(),
            need_seeking=["rare_trait"],
            offer_capabilities=["other_trait"],
            language="en",
            api_key="",
        )
        assert "stars" in reason.lower()

    def test_zero_ai_language(self):
        """All reasons must comply with Zero-AI language."""
        for cap in _CAPABILITY_TEXT:
            reason = generate_match_reason(
                _make_match(),
                need_seeking=[cap],
                offer_capabilities=[cap],
                language="en",
            )
            import re
            banned = [r"\bAI\b", r"\balgorithm\b", r"\bmatch(?:ed|ing)?\b", r"\bsystem\b", r"\bcompute\b", r"\bdetect\b"]
            for pattern in banned:
                assert not re.search(pattern, reason, re.IGNORECASE), f"Banned pattern '{pattern}' in: {reason}"
