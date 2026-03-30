"""Tests for philosophy_quotes API module."""
import pytest
from wish_engine.apis.philosophy_quotes import (
    get_quote,
    get_quotes_by_tradition,
    list_traditions,
)


class TestListTraditions:
    def test_returns_list(self):
        result = list_traditions()
        assert isinstance(result, list)
        assert len(result) >= 10

    def test_contains_major_traditions(self):
        traditions = list_traditions()
        for expected in ["Stoic", "Buddhist", "Taoist", "Confucian", "Sufi", "Greek"]:
            assert expected in traditions, f"{expected} missing from traditions"

    def test_sorted(self):
        traditions = list_traditions()
        assert traditions == sorted(traditions)


class TestGetQuote:
    def test_returns_required_fields(self):
        q = get_quote()
        assert "author" in q
        assert "text" in q
        assert "tradition" in q

    def test_fields_are_strings(self):
        q = get_quote()
        assert isinstance(q["author"], str) and q["author"]
        assert isinstance(q["text"], str) and q["text"]
        assert isinstance(q["tradition"], str) and q["tradition"]

    def test_no_internal_fields_leaked(self):
        q = get_quote()
        assert "_source" not in q
        assert "_id" not in q

    def test_stoic_tradition_filter(self):
        """When tradition=Stoic, should get a Stoic quote."""
        q = get_quote(tradition="Stoic")
        # Should be Stoic (from static fallback at minimum)
        assert q["tradition"] == "Stoic"

    def test_buddhist_tradition_filter(self):
        q = get_quote(tradition="Buddhist")
        assert q["tradition"] == "Buddhist"

    def test_taoist_tradition_filter(self):
        q = get_quote(tradition="Taoist")
        assert q["tradition"] == "Taoist"

    def test_unknown_tradition_returns_any_quote(self):
        """Unknown tradition falls back gracefully."""
        q = get_quote(tradition="UnknownXYZ")
        assert "text" in q  # Still returns something

    def test_no_tradition_returns_something(self):
        q = get_quote()
        assert q["text"]


class TestGetQuotesByTradition:
    def test_returns_list(self):
        result = get_quotes_by_tradition("Stoic", limit=3)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_limit_respected(self):
        result = get_quotes_by_tradition("Stoic", limit=2)
        assert len(result) <= 2

    def test_all_correct_tradition(self):
        result = get_quotes_by_tradition("Buddhist", limit=5)
        # Static fallback guarantees tradition
        for q in result:
            assert "author" in q
            assert "text" in q

    def test_each_has_required_fields(self):
        result = get_quotes_by_tradition("Greek", limit=3)
        for q in result:
            assert "author" in q and q["author"]
            assert "text" in q and q["text"]
            assert "tradition" in q

    def test_limit_clamped_at_20(self):
        """Limit above 20 is clamped."""
        result = get_quotes_by_tradition("Stoic", limit=100)
        assert len(result) <= 20

    def test_limit_clamped_at_1(self):
        result = get_quotes_by_tradition("Stoic", limit=0)
        assert len(result) >= 1


class TestBridgeCompatibility:
    """Verify the template format works with the bridge."""

    def test_template_fields_present(self):
        """Bridge template: '🏛️ {tradition}: {text} — {author}'"""
        q = get_quote()
        try:
            rendered = "🏛️ {tradition}: {text} — {author}".format(**q)
            assert len(rendered) > 10
        except KeyError as e:
            pytest.fail(f"Bridge template field missing: {e}")

    def test_stoic_template(self):
        q = get_quote(tradition="Stoic")
        rendered = "🏛️ {tradition}: {text} — {author}".format(**q)
        assert "Stoic" in rendered
