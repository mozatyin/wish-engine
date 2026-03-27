"""Tests for IdentityExplorationFulfiller — compass-integrated identity exploration."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.l2_identity_exploration import IdentityExplorationFulfiller, IDENTITY_CATALOG


class TestIdentityCatalog:
    def test_catalog_has_15_entries(self):
        assert len(IDENTITY_CATALOG) == 15

    def test_each_entry_has_required_fields(self):
        required = {"title", "description", "category", "tags", "difficulty"}
        for item in IDENTITY_CATALOG:
            missing = required - set(item.keys())
            assert not missing, f"{item['title']} missing: {missing}"

    def test_15_categories(self):
        cats = {item["category"] for item in IDENTITY_CATALOG}
        assert len(cats) == 15


class TestIdentityExplorationFulfiller:
    def _make_wish(self, text="我是谁") -> ClassifiedWish:
        return ClassifiedWish(
            wish_text=text, wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2, fulfillment_strategy="identity_exploration",
        )

    def test_returns_l2_result(self):
        f = IdentityExplorationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_max_3(self):
        f = IdentityExplorationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert len(result.recommendations) <= 3

    def test_career_keyword_targets_career(self):
        f = IdentityExplorationFulfiller()
        result = f.fulfill(self._make_wish("I want to explore my career identity"), DetectorResults())
        cats = [r.category for r in result.recommendations]
        assert "career_identity" in cats

    def test_avoidant_attachment_targets_attachment(self):
        f = IdentityExplorationFulfiller()
        det = DetectorResults(attachment={"style": "avoidant"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        assert "attachment_understanding" in cats

    def test_tradition_values_target_heritage(self):
        f = IdentityExplorationFulfiller()
        det = DetectorResults(values={"top_values": ["tradition"]})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        assert "heritage_connection" in cats

    def test_fragile_avoids_bold(self):
        f = IdentityExplorationFulfiller()
        det = DetectorResults(fragility={"pattern": "fragile"})
        result = f.fulfill(self._make_wish(), det)
        cats = [r.category for r in result.recommendations]
        assert "attachment_understanding" not in cats  # bold difficulty

    def test_has_reminder(self):
        f = IdentityExplorationFulfiller()
        result = f.fulfill(self._make_wish(), DetectorResults())
        assert result.reminder_option is not None
