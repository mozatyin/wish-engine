"""Tests for UniversalFulfiller — the single pipeline replacing 140 fulfillers."""

import pytest
from wish_engine.models import ClassifiedWish, DetectorResults, L2FulfillmentResult, WishLevel, WishType
from wish_engine.universal_fulfiller import universal_fulfill


class TestUniversalFulfill:
    def test_food_returns_result(self):
        wish = ClassifiedWish(wish_text="I want comfort food", wish_type=WishType.FIND_PLACE, level=WishLevel.L2, fulfillment_strategy="test")
        result = universal_fulfill("food", wish, DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_suicide_prevention_returns_result(self):
        wish = ClassifiedWish(wish_text="I don't want to live", wish_type=WishType.HEALTH_WELLNESS, level=WishLevel.L2, fulfillment_strategy="test")
        result = universal_fulfill("suicide_prevention", wish, DetectorResults())
        assert len(result.recommendations) >= 1

    def test_suicide_prevention_bypasses_personality_filter(self):
        """Crisis catalogs must preserve original priority order — no personality reranking."""
        wish = ClassifiedWish(wish_text="I want to die", wish_type=WishType.HEALTH_WELLNESS, level=WishLevel.L2, fulfillment_strategy="test")
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.1}})
        result = universal_fulfill("suicide_prevention", wish, det)
        assert result.recommendations[0].title == "Crisis Hotline — Call Now"

    def test_unknown_catalog_still_returns(self):
        wish = ClassifiedWish(wish_text="something random", wish_type=WishType.FIND_RESOURCE, level=WishLevel.L2, fulfillment_strategy="test")
        result = universal_fulfill("nonexistent_catalog", wish, DetectorResults())
        assert len(result.recommendations) >= 1  # fallback works

    def test_personality_filter_applied(self):
        """Introvert should not get noisy recommendations."""
        wish = ClassifiedWish(wish_text="I want to go somewhere", wish_type=WishType.FIND_PLACE, level=WishLevel.L2, fulfillment_strategy="test")
        det = DetectorResults(mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}})
        result = universal_fulfill("places", wish, det)
        for rec in result.recommendations:
            # PersonalityFilter excludes items with noise=loud AND social=high for introverts
            assert not (rec.tags and "noisy" in rec.tags)

    def test_personalized_reason(self):
        """Reason should mention personality traits."""
        wish = ClassifiedWish(wish_text="quiet study", wish_type=WishType.FIND_PLACE, level=WishLevel.L2, fulfillment_strategy="test")
        det = DetectorResults(mbti={"type": "INTJ", "dimensions": {"E_I": 0.2}}, values={"top_values": ["self-direction"]})
        result = universal_fulfill("places", wish, det)
        reasons = [r.relevance_reason for r in result.recommendations]
        assert any("INTJ" in r or "quiet" in r or "independent" in r for r in reasons)

    def test_map_data_for_place_catalogs(self):
        wish = ClassifiedWish(wish_text="find a place", wish_type=WishType.FIND_PLACE, level=WishLevel.L2, fulfillment_strategy="test")
        result = universal_fulfill("food", wish, DetectorResults())
        assert result.map_data is not None

    def test_no_map_data_for_non_place(self):
        wish = ClassifiedWish(wish_text="read a book", wish_type=WishType.FIND_RESOURCE, level=WishLevel.L2, fulfillment_strategy="test")
        result = universal_fulfill("books", wish, DetectorResults())
        assert result.map_data is None

    def test_has_reminder(self):
        wish = ClassifiedWish(wish_text="test", wish_type=WishType.FIND_RESOURCE, level=WishLevel.L2, fulfillment_strategy="test")
        result = universal_fulfill("food", wish, DetectorResults())
        assert result.reminder_option is not None

    def test_max_3_recommendations(self):
        wish = ClassifiedWish(wish_text="test", wish_type=WishType.FIND_PLACE, level=WishLevel.L2, fulfillment_strategy="test")
        result = universal_fulfill("places", wish, DetectorResults())
        assert len(result.recommendations) <= 3

    def test_domestic_violence_is_safety_critical(self):
        wish = ClassifiedWish(wish_text="I'm being abused", wish_type=WishType.HEALTH_WELLNESS, level=WishLevel.L2, fulfillment_strategy="test")
        result = universal_fulfill("domestic_violence", wish, DetectorResults())
        assert len(result.recommendations) >= 1


class TestFulfillL2Integration:
    """Test that fulfill_l2() still works through the universal pipeline."""

    def test_basic_wish(self):
        from wish_engine.l2_fulfiller import fulfill_l2
        wish = ClassifiedWish(wish_text="I need comfort food for dinner", wish_type=WishType.FIND_PLACE, level=WishLevel.L2, fulfillment_strategy="test")
        result = fulfill_l2(wish, DetectorResults())
        assert isinstance(result, L2FulfillmentResult)
        assert len(result.recommendations) >= 1

    def test_crisis_wish(self):
        from wish_engine.l2_fulfiller import fulfill_l2
        wish = ClassifiedWish(wish_text="I'm thinking about suicide", wish_type=WishType.HEALTH_WELLNESS, level=WishLevel.L2, fulfillment_strategy="test")
        result = fulfill_l2(wish, DetectorResults())
        assert len(result.recommendations) >= 1

    def test_l1_wish_raises(self):
        from wish_engine.l2_fulfiller import fulfill_l2
        wish = ClassifiedWish(wish_text="test", wish_type=WishType.SELF_UNDERSTANDING, level=WishLevel.L1, fulfillment_strategy="test")
        with pytest.raises(ValueError):
            fulfill_l2(wish, DetectorResults())
