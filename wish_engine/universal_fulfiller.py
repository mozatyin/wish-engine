"""UniversalFulfiller — one fulfiller for all catalogs.

Replaces 140 individual l2_*.py fulfillers with a single pipeline:
  Router → CatalogStore.search() → PersonalityRanker → Personalizer → Result

External interface (fulfill_l2) unchanged.
"""

from __future__ import annotations

from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
    WishLevel,
)
from wish_engine.catalog_store import search as catalog_search, get_catalog
from wish_engine.l2_fulfiller import PersonalityFilter, SAFETY_CRITICAL_CATEGORIES
from wish_engine.personalization import personalize_reason


# Catalogs that should include map data
_MAP_CATALOGS = {
    "places", "food", "hometown_food", "medical", "pet_friendly", "coworking",
    "events", "safe_spaces", "parking", "ev_charging", "late_night", "noise_map",
    "kids_activities", "elderly_care", "family_dining", "nature_healing",
    "rainy_day", "photo_spots",
}

# Catalog → reminder text
_REMINDER_TEXTS = {
    "food": "Try this restaurant today?",
    "events": "Want a reminder before the event?",
    "places": "Visit this spot this weekend?",
    "sleep_env": "Try this tonight before bed",
    "mindfulness": "Start your practice today?",
    "habit_tracker": "Track your habit today?",
    "courses": "Start this course today?",
    "books": "Start reading this week?",
    "volunteer": "Sign up for volunteering?",
    "nature_healing": "Visit this nature spot soon?",
}
_DEFAULT_REMINDER = "Save this for later?"


def universal_fulfill(
    catalog_id: str,
    wish: ClassifiedWish,
    detector_results: DetectorResults,
) -> L2FulfillmentResult:
    """Universal fulfillment: catalog search → personality rank → personalize.

    Args:
        catalog_id: Which catalog to search (from Router)
        wish: The classified wish
        detector_results: User's 16-dimension profile

    Returns:
        L2FulfillmentResult with personalized recommendations
    """
    is_safety_critical = catalog_id in SAFETY_CRITICAL_CATEGORIES

    # Step 1: SEARCH — get candidates from catalog
    keywords = wish.wish_text.lower().split()[:5]  # simple keyword extraction
    candidates = catalog_search(catalog_id, keywords)

    if not candidates:
        # Fallback: get full catalog
        candidates = get_catalog(catalog_id)

    if not candidates:
        # Ultimate fallback: generic recommendation
        candidates = [
            {
                "title": "Explore options",
                "description": "We're looking for the best match for you",
                "category": "general",
                "tags": ["calming"],
                "noise": "quiet",
                "social": "low",
                "mood": "calming",
            }
        ]

    # Step 2: RANK — safety-critical catalogs bypass PersonalityFilter entirely
    if is_safety_critical:
        ranked = candidates[:3]
    else:
        pf = PersonalityFilter(detector_results)
        ranked = pf.filter_and_rank(candidates, max_results=3)

    # Step 3: PRESENT — build personalized recommendations
    recommendations = []
    for item in ranked:
        if is_safety_critical:
            reason = item.get("relevance_reason", "Help is available")
        else:
            reason = personalize_reason(
                recommendation_title=item.get("title", ""),
                recommendation_tags=item.get("tags", []),
                detector_results=detector_results,
                wish_text=wish.wish_text,
            )
        recommendations.append(Recommendation(
            title=item["title"],
            description=item.get("description", ""),
            category=item.get("category", catalog_id),
            relevance_reason=reason,
            score=item.get("_personality_score", 0.5),
            action_url=item.get("action_url"),
            tags=item.get("tags", []),
        ))

    if not recommendations:
        # Should not happen, but safety net
        recommendations = [Recommendation(
            title="Exploring options for you",
            description="We're finding the best match",
            category=catalog_id,
            relevance_reason="Based on your profile",
            score=0.5,
        )]

    # Step 4: Map data + reminder
    map_data = None
    if catalog_id in _MAP_CATALOGS:
        primary_cat = recommendations[0].category if recommendations else catalog_id
        map_data = MapData(place_type=primary_cat, radius_km=5.0)

    reminder_text = _REMINDER_TEXTS.get(catalog_id, _DEFAULT_REMINDER)

    return L2FulfillmentResult(
        recommendations=recommendations,
        map_data=map_data,
        reminder_option=ReminderOption(text=reminder_text, delay_hours=24),
    )
