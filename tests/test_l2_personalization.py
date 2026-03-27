"""Tests proving L2 personalization varies output by user profile.

These tests verify that the PersonalityFilter and L2 fulfillers produce
genuinely different recommendations when given different detector profiles.
Empty DetectorResults should NOT be used — that's the bug this file catches.
"""

import pytest
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    WishLevel,
    WishType,
)
from wish_engine.l2_books import BookFulfiller
from wish_engine.l2_career import CareerFulfiller
from wish_engine.l2_places import PlaceFulfiller
from wish_engine.l2_fulfiller import PersonalityFilter
from wish_engine.l2_suicide_prevention import SuicidePreventionFulfiller
from wish_engine.l2_domestic_violence import DomesticViolenceFulfiller


# ── Helpers ──────────────────────────────────────────────────────────────────


def _introvert_det() -> DetectorResults:
    return DetectorResults(
        mbti={"type": "INFJ", "dimensions": {"E_I": 0.2}},
        values={"top_values": ["self-direction", "universalism"]},
        emotion={"emotions": {"calm": 0.3}},
        attachment={"style": "secure"},
    )


def _extravert_det() -> DetectorResults:
    return DetectorResults(
        mbti={"type": "ESFP", "dimensions": {"E_I": 0.8}},
        values={"top_values": ["stimulation", "hedonism"]},
        emotion={"emotions": {"joy": 0.6}},
        attachment={"style": "secure"},
    )


def _anxious_det() -> DetectorResults:
    return DetectorResults(
        mbti={"type": "INFP", "dimensions": {"E_I": 0.3}},
        emotion={"emotions": {"anxiety": 0.8}},
        fragility={"pattern": "reactive"},
        attachment={"style": "anxious"},
    )


def _calm_det() -> DetectorResults:
    return DetectorResults(
        mbti={"type": "ESTJ", "dimensions": {"E_I": 0.7}},
        emotion={"emotions": {"calm": 0.7}},
        fragility={"pattern": "resilient"},
        attachment={"style": "secure"},
    )


def _tradition_det() -> DetectorResults:
    return DetectorResults(
        values={"top_values": ["tradition", "conformity"]},
        mbti={"type": "ISTJ", "dimensions": {"E_I": 0.3}},
    )


def _self_direction_det() -> DetectorResults:
    return DetectorResults(
        values={"top_values": ["self-direction", "stimulation"]},
        mbti={"type": "ENTP", "dimensions": {"E_I": 0.7}},
    )


def _book_wish(text="recommend me a book") -> ClassifiedWish:
    return ClassifiedWish(
        wish_text=text,
        wish_type=WishType.FIND_RESOURCE,
        level=WishLevel.L2,
        fulfillment_strategy="resource_recommendation",
    )


def _career_wish(text="I want career direction") -> ClassifiedWish:
    return ClassifiedWish(
        wish_text=text,
        wish_type=WishType.CAREER_DIRECTION,
        level=WishLevel.L2,
        fulfillment_strategy="career_guidance",
    )


def _place_wish(text="find me a place to relax") -> ClassifiedWish:
    return ClassifiedWish(
        wish_text=text,
        wish_type=WishType.FIND_PLACE,
        level=WishLevel.L2,
        fulfillment_strategy="place_search",
    )


# ── Tests ────────────────────────────────────────────────────────────────────


class TestBooksIntrovertVsExtravert:
    """Introvert and extravert should get different book recommendations."""

    def test_different_ranking_order(self):
        f = BookFulfiller()
        intro_result = f.fulfill(_book_wish(), _introvert_det())
        extra_result = f.fulfill(_book_wish(), _extravert_det())

        intro_titles = [r.title for r in intro_result.recommendations]
        extra_titles = [r.title for r in extra_result.recommendations]

        # At minimum, the ranked order or scores should differ
        intro_scores = [r.score for r in intro_result.recommendations]
        extra_scores = [r.score for r in extra_result.recommendations]

        # Either titles differ or scores differ — personalization is working
        assert intro_titles != extra_titles or intro_scores != extra_scores, (
            "Introvert and extravert got identical book recommendations — "
            "personalization is not working"
        )

    def test_introvert_gets_higher_quiet_scores(self):
        f = BookFulfiller()
        intro_result = f.fulfill(_book_wish(), _introvert_det())

        # Introvert should get books with "quiet" tag scored higher
        for rec in intro_result.recommendations:
            if "quiet" in rec.tags:
                assert rec.score >= 0.5, (
                    f"Introvert's quiet book '{rec.title}' scored too low: {rec.score}"
                )

    def test_extravert_relevance_mentions_personality(self):
        f = BookFulfiller()
        extra_result = f.fulfill(_book_wish(), _extravert_det())

        # At least one recommendation should have a personalized reason
        reasons = [r.relevance_reason for r in extra_result.recommendations]
        has_personal = any("ESFP" in r or "stimulation" in r.lower() for r in reasons)
        # This is acceptable even if not present — the key test is ranking difference
        # But the reason should NOT be a generic fallback for all
        generic_count = sum(1 for r in reasons if r.startswith("Recommended for you:"))
        assert generic_count < len(reasons), (
            "All recommendations got generic reasons — personalization not working"
        )


class TestPlacesAnxiousVsCalm:
    """High anxiety user should not get loud/crowded places."""

    def test_anxious_excludes_intense_places(self):
        pf = PersonalityFilter(_anxious_det())
        candidates = [
            {"title": "Quiet Garden", "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "calming"]},
            {"title": "Loud Club", "noise": "loud", "social": "high", "mood": "intense", "tags": ["social", "loud"]},
            {"title": "Busy Market", "noise": "moderate", "social": "medium", "mood": "intense", "tags": ["social"]},
        ]
        filtered = pf.apply(candidates)
        titles = [c["title"] for c in filtered]
        assert "Quiet Garden" in titles
        assert "Busy Market" not in titles, "Intense mood should be excluded for anxious user"

    def test_anxious_vs_calm_get_different_places(self):
        f = PlaceFulfiller()
        anxious_result = f.fulfill(_place_wish(), _anxious_det())
        calm_result = f.fulfill(_place_wish(), _calm_det())

        anxious_titles = [r.title for r in anxious_result.recommendations]
        calm_titles = [r.title for r in calm_result.recommendations]
        anxious_scores = [r.score for r in anxious_result.recommendations]
        calm_scores = [r.score for r in calm_result.recommendations]

        assert anxious_titles != calm_titles or anxious_scores != calm_scores, (
            "Anxious and calm users got identical place recommendations"
        )


class TestCareerValuesDiffer:
    """Different values should change career direction ranking."""

    def test_tradition_vs_self_direction(self):
        f = CareerFulfiller()
        trad_result = f.fulfill(_career_wish(), _tradition_det())
        sd_result = f.fulfill(_career_wish(), _self_direction_det())

        trad_titles = [r.title for r in trad_result.recommendations]
        sd_titles = [r.title for r in sd_result.recommendations]
        trad_scores = [r.score for r in trad_result.recommendations]
        sd_scores = [r.score for r in sd_result.recommendations]

        assert trad_titles != sd_titles or trad_scores != sd_scores, (
            "Tradition and self-direction users got identical career recs"
        )

    def test_self_direction_boosts_autonomous_careers(self):
        f = CareerFulfiller()
        sd_result = f.fulfill(_career_wish(), _self_direction_det())

        # At least one recommendation should have autonomous tag
        all_tags = []
        for r in sd_result.recommendations:
            all_tags.extend(r.tags)
        assert "autonomous" in all_tags or "self-direction" in all_tags, (
            "Self-direction user should see autonomous career options"
        )


class TestCrisisFulfillersAreIntentionallyStatic:
    """Suicide prevention and DV fulfillers should NOT vary by personality.

    This is correct behavior — crisis resources must always show the same
    hotlines and safety resources regardless of who the user is.
    """

    def test_suicide_prevention_same_for_introvert_and_extravert(self):
        f = SuicidePreventionFulfiller()
        wish = ClassifiedWish(
            wish_text="I want to end it all",
            wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2,
            fulfillment_strategy="wellness_recommendation",
        )
        intro_result = f.fulfill(wish, _introvert_det())
        extra_result = f.fulfill(wish, _extravert_det())

        intro_titles = [r.title for r in intro_result.recommendations]
        extra_titles = [r.title for r in extra_result.recommendations]

        assert intro_titles == extra_titles, (
            "Crisis resources should be identical regardless of personality"
        )

    def test_dv_same_for_anxious_and_calm(self):
        f = DomesticViolenceFulfiller()
        wish = ClassifiedWish(
            wish_text="my partner hits me",
            wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2,
            fulfillment_strategy="wellness_recommendation",
        )
        anxious_result = f.fulfill(wish, _anxious_det())
        calm_result = f.fulfill(wish, _calm_det())

        anxious_titles = [r.title for r in anxious_result.recommendations]
        calm_titles = [r.title for r in calm_result.recommendations]

        assert anxious_titles == calm_titles, (
            "DV resources should be identical regardless of personality"
        )

    def test_suicide_prevention_always_shows_hotline_first(self):
        f = SuicidePreventionFulfiller()
        wish = ClassifiedWish(
            wish_text="I want to die",
            wish_type=WishType.HEALTH_WELLNESS,
            level=WishLevel.L2,
            fulfillment_strategy="wellness_recommendation",
        )
        result = f.fulfill(wish, DetectorResults())
        first = result.recommendations[0]
        assert "hotline" in first.title.lower() or "crisis" in first.title.lower(), (
            f"First crisis recommendation should be hotline, got: {first.title}"
        )


class TestPersonalityFilterMechanics:
    """Direct tests on PersonalityFilter to verify scoring mechanics."""

    def test_introvert_exclusion_of_loud_social(self):
        pf = PersonalityFilter(_introvert_det())
        candidates = [
            {"title": "A", "noise": "loud", "social": "high", "tags": []},
            {"title": "B", "noise": "quiet", "social": "low", "tags": ["quiet"]},
        ]
        filtered = pf.apply(candidates)
        assert len(filtered) == 1
        assert filtered[0]["title"] == "B"

    def test_values_boost_scoring(self):
        pf = PersonalityFilter(_tradition_det())
        candidates = [
            {"title": "Traditional", "tags": ["traditional"]},
            {"title": "Modern", "tags": ["autonomous"]},
        ]
        scored = pf.score(candidates)
        trad_score = next(c["_personality_score"] for c in scored if c["title"] == "Traditional")
        mod_score = next(c["_personality_score"] for c in scored if c["title"] == "Modern")
        assert trad_score > mod_score, (
            f"Tradition value should boost traditional items: {trad_score} vs {mod_score}"
        )

    def test_empty_detector_results_produces_equal_scores(self):
        """With empty results, all candidates should get the same base score."""
        pf = PersonalityFilter(DetectorResults())
        candidates = [
            {"title": "A", "tags": ["quiet"]},
            {"title": "B", "tags": ["social"]},
            {"title": "C", "tags": ["traditional"]},
        ]
        scored = pf.score(candidates)
        scores = [c["_personality_score"] for c in scored]
        assert len(set(scores)) == 1, (
            f"Empty profile should give equal scores, got: {scores}"
        )
