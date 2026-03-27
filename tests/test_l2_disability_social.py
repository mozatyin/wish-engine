"""Tests for DisabilitySocialFulfiller."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_disability_social import DisabilitySocialFulfiller, DISABILITY_SOCIAL_CATALOG


class TestDisabilitySocialCatalog:
    def test_catalog_has_12_entries(self):
        assert len(DISABILITY_SOCIAL_CATALOG) == 12

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags"}
        for item in DISABILITY_SOCIAL_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"


class TestDisabilitySocialFulfiller:
    def _make_wish(self, text="disability social activities") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.FIND_RESOURCE,
            level=WishLevel.L2, fulfillment_strategy="disability_social",
        )

    def test_returns_l2_result(self):
        f = DisabilitySocialFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3_recommendations(self):
        f = DisabilitySocialFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_wheelchair_keyword(self):
        f = DisabilitySocialFulfiller()
        result = f.fulfill(self._make_wish("wheelchair sports"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "wheelchair" in tags or "adaptive" in tags

    def test_has_reminder(self):
        f = DisabilitySocialFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None

    def test_relevance_reason_not_empty(self):
        f = DisabilitySocialFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        for r in result.recommendations:
            assert len(r.relevance_reason) > 5

    def test_deaf_keyword(self):
        f = DisabilitySocialFulfiller()
        result = f.fulfill(self._make_wish("deaf community events"), DetectorResults())
        tags = []
        for r in result.recommendations:
            tags.extend(r.tags)
        assert "deaf" in tags or "sign_language" in tags
