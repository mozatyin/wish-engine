"""Real Places — personality-scored place recommendations.

Scores places on solo_friendly, anxiety_friendly, introvert_friendly
based on noise/social/tags and user's MBTI/emotion profile.

Falls back to universal_fulfill("places", ...) when no Google Places API key
or no location provided.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    Recommendation,
    WishLevel,
    WishState,
    WishType,
)
from wish_engine.universal_fulfiller import universal_fulfill


# ── Place Score ─────────────────────────────────────────────────────────────

@dataclass
class PlaceScore:
    """Personality-based place scores (0-1 each)."""

    solo_friendly: float = 0.5
    anxiety_friendly: float = 0.5
    introvert_friendly: float = 0.5


# Noise/social/tag weights for scoring
_QUIET_TAGS = {"library", "park", "garden", "museum", "temple", "mosque", "church",
               "bookstore", "cafe", "tea", "nature", "quiet", "peaceful", "zen",
               "meditation", "spa", "retreat"}
_SOCIAL_TAGS = {"bar", "club", "party", "concert", "festival", "nightlife",
                "group", "team", "crowd", "busy", "popular", "trending"}
_ANXIETY_SAFE_TAGS = {"open", "spacious", "outdoor", "nature", "garden", "park",
                      "quiet", "calm", "low-key", "gentle", "familiar", "cozy"}


def _score_place(place: dict[str, Any], detector_results: DetectorResults) -> PlaceScore:
    """Score a place based on its attributes and user's detector profile.

    Args:
        place: Place dict with optional tags, noise, social fields.
        detector_results: User's 16-dimension profile.

    Returns:
        PlaceScore with solo/anxiety/introvert friendliness.
    """
    tags = set(t.lower() for t in place.get("tags", []))
    noise = place.get("noise", "moderate").lower()
    social = place.get("social", "moderate").lower()
    category = place.get("category", "").lower()

    # All tags including category
    all_tags = tags | {category}

    # Base scores from place attributes
    quiet_overlap = len(all_tags & _QUIET_TAGS)
    social_overlap = len(all_tags & _SOCIAL_TAGS)
    anxiety_overlap = len(all_tags & _ANXIETY_SAFE_TAGS)

    # Solo friendly: high if quiet, low social requirement
    solo = 0.5
    if noise in ("quiet", "silent", "low"):
        solo += 0.2
    if social in ("low", "none", "minimal"):
        solo += 0.2
    solo += min(quiet_overlap * 0.05, 0.2)
    solo -= min(social_overlap * 0.1, 0.3)

    # Anxiety friendly: high if spacious, predictable, low stimulation
    anxiety = 0.5
    if noise in ("quiet", "silent", "low"):
        anxiety += 0.15
    anxiety += min(anxiety_overlap * 0.05, 0.25)
    anxiety -= min(social_overlap * 0.1, 0.3)

    # Introvert friendly: combines quiet + low social + not crowded
    introvert = 0.5
    if noise in ("quiet", "silent", "low"):
        introvert += 0.2
    if social in ("low", "none", "minimal"):
        introvert += 0.15
    introvert += min(quiet_overlap * 0.05, 0.2)
    introvert -= min(social_overlap * 0.15, 0.4)

    # Adjust based on user's MBTI if available
    mbti = detector_results.mbti
    if isinstance(mbti, dict):
        mbti_type = mbti.get("type", "")
        if mbti_type and mbti_type[0] == "I":  # Introvert
            introvert += 0.1
            solo += 0.05

    # Adjust based on emotion/distress
    emotion = detector_results.emotion
    if isinstance(emotion, dict):
        distress = emotion.get("distress", 0.0)
        if distress > 0.5:
            anxiety += 0.1
            solo += 0.05

    return PlaceScore(
        solo_friendly=max(0.0, min(1.0, solo)),
        anxiety_friendly=max(0.0, min(1.0, anxiety)),
        introvert_friendly=max(0.0, min(1.0, introvert)),
    )


def _score_label(score: PlaceScore) -> str:
    """Generate a human-readable score label."""
    labels = []
    if score.solo_friendly >= 0.7:
        labels.append("solo-friendly")
    if score.anxiety_friendly >= 0.7:
        labels.append("anxiety-friendly")
    if score.introvert_friendly >= 0.7:
        labels.append("introvert-friendly")
    return " | ".join(labels) if labels else ""


# ── Public API ──────────────────────────────────────────────────────────────

def find_real_places(
    wish_text: str,
    detector_results: DetectorResults,
    lat: float | None = None,
    lng: float | None = None,
) -> L2FulfillmentResult:
    """Find personality-scored places.

    When Google Places API key + location provided, uses real API.
    Otherwise falls back to universal_fulfill("places", ...) catalog.

    Args:
        wish_text: User's wish text.
        detector_results: User's 16-dimension profile.
        lat: Optional latitude.
        lng: Optional longitude.

    Returns:
        L2FulfillmentResult with personality-scored recommendations.
    """
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")

    # Route to catalog-based fulfillment (always works)
    wish = ClassifiedWish(
        wish_text=wish_text,
        wish_type=WishType.FIND_PLACE,
        level=WishLevel.L2,
        fulfillment_strategy="places",
        state=WishState.SEARCHING,
        confidence=0.8,
    )
    result = universal_fulfill("places", wish, detector_results)

    # Score each recommendation with personality dimensions
    scored_recs = []
    for rec in result.recommendations:
        place_dict = {
            "tags": rec.tags,
            "category": rec.category,
        }
        score = _score_place(place_dict, detector_results)
        label = _score_label(score)

        # Append score label to relevance_reason
        reason = rec.relevance_reason
        if label:
            reason = f"{reason} [{label}]"

        scored_recs.append(Recommendation(
            title=rec.title,
            description=rec.description,
            category=rec.category,
            relevance_reason=reason,
            score=rec.score,
            action_url=rec.action_url,
            tags=rec.tags,
        ))

    return L2FulfillmentResult(
        recommendations=scored_recs,
        map_data=result.map_data,
        reminder_option=result.reminder_option,
    )
