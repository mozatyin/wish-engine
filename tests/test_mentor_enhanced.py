"""Tests for MentorFulfiller — enhanced mentor matching."""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_mentor_enhanced import (
    MentorFulfiller,
    MENTOR_CATALOG,
    _match_mentor_domain,
)


class TestMentorCatalog:
    def test_catalog_has_15_entries(self):
        assert len(MENTOR_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "domain", "noise", "social", "mood", "tags"}
        for item in MENTOR_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_catalog_has_diverse_domains(self):
        domains = {item["domain"] for item in MENTOR_CATALOG}
        assert len(domains) == 15  # all unique domains


class TestMentorFulfiller:
    def _make_wish(self, text="I need a mentor") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_MENTOR,
            level=WishLevel.L2, fulfillment_strategy="mentor",
        )

    def test_returns_l2_result(self):
        f = MentorFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_career_keyword_matches_career_domain(self):
        assert _match_mentor_domain("I need a career mentor") == "career"

    def test_tech_keyword_matches_tech_domain(self):
        assert _match_mentor_domain("想找技术导师") == "tech"

    def test_max_3(self):
        f = MentorFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_has_reminder(self):
        f = MentorFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_has_map_data(self):
        f = MentorFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.map_data is not None

    def test_no_domain_returns_results(self):
        f = MentorFulfiller()
        result = f.fulfill(self._make_wish("help me grow"), DetectorResults())
        assert len(result.recommendations) >= 1
