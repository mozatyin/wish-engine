"""Tests for SocialJusticeFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_social_justice import SocialJusticeFulfiller, SOCIAL_JUSTICE_CATALOG


class TestSocialJusticeCatalog:
    def test_catalog_has_12_entries(self):
        assert len(SOCIAL_JUSTICE_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in SOCIAL_JUSTICE_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestSocialJusticeFulfiller:
    def _make_wish(self, text="social justice activism") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="social_justice",
        )

    def test_returns_l2_result(self):
        f = SocialJusticeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = SocialJusticeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_protest_keyword(self):
        f = SocialJusticeFulfiller()
        result = f.fulfill(self._make_wish("protest safety guide"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "protest" in tags or "safety" in tags

    def test_vote_keyword(self):
        f = SocialJusticeFulfiller()
        result = f.fulfill(self._make_wish("how to vote register"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "voting" in tags or "registration" in tags

    def test_has_reminder(self):
        f = SocialJusticeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = SocialJusticeFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
