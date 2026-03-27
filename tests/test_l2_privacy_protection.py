"""Tests for PrivacyProtectionFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_privacy_protection import PrivacyProtectionFulfiller, PRIVACY_CATALOG


class TestPrivacyCatalog:
    def test_catalog_has_10_entries(self):
        assert len(PRIVACY_CATALOG) == 10

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in PRIVACY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestPrivacyProtectionFulfiller:
    def _make_wish(self, text="I want to protect my privacy") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="privacy_protection",
        )

    def test_returns_l2_result(self):
        f = PrivacyProtectionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = PrivacyProtectionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_password_keyword(self):
        f = PrivacyProtectionFulfiller()
        result = f.fulfill(self._make_wish("help with password security"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "password" in tags or "security" in tags

    def test_vpn_keyword(self):
        f = PrivacyProtectionFulfiller()
        result = f.fulfill(self._make_wish("do I need a vpn"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "vpn" in tags or "privacy" in tags

    def test_has_reminder(self):
        f = PrivacyProtectionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = PrivacyProtectionFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5
