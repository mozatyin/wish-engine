"""FreeActivityFulfiller — free and low-cost activity recommendations.

20-entry curated catalog of free/budget activities. All entries tagged "free".
Personality-based filtering via MBTI and values.
Multilingual keyword routing (EN/ZH/AR).
Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    Recommendation,
    ReminderOption,
)

# ── Free Activity Catalog (20 entries) ───────────────────────────────────────

FREE_ACTIVITY_CATALOG: list[dict] = [
    {
        "title": "Free Museum Day",
        "description": "Many museums offer free admission days — explore art and history for nothing.",
        "category": "free_museum_day",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["free", "quiet", "creative", "cultural"],
    },
    {
        "title": "Park Concert",
        "description": "Live music in the open air — bring a blanket and enjoy the show.",
        "category": "park_concert",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["free", "social", "outdoor", "creative"],
    },
    {
        "title": "Library Event",
        "description": "Author talks, reading groups, and workshops — your library card is the ticket.",
        "category": "library_event",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "quiet", "practical"],
    },
    {
        "title": "Community Class",
        "description": "Free cooking, language, or art classes run by local volunteers.",
        "category": "community_class",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "social", "practical", "creative"],
    },
    {
        "title": "Volunteer Day",
        "description": "Give back to your community — meet people while making a difference.",
        "category": "volunteer_day",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["free", "social", "helping"],
    },
    {
        "title": "Street Art Walking Tour",
        "description": "Self-guided tour of murals and street art — the city is your gallery.",
        "category": "street_art_tour",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["free", "creative", "outdoor"],
    },
    {
        "title": "Free Yoga in the Park",
        "description": "Community yoga sessions in green spaces — breathe, stretch, and relax.",
        "category": "free_yoga_in_park",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "outdoor", "calming", "quiet"],
    },
    {
        "title": "Language Exchange Meetup",
        "description": "Practice a new language with native speakers — free and fun.",
        "category": "language_exchange",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["free", "social", "practical"],
    },
    {
        "title": "Book Swap Event",
        "description": "Bring a book, take a book — discover your next favorite read for free.",
        "category": "book_swap",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "quiet", "practical"],
    },
    {
        "title": "Open Mic Night",
        "description": "Share your poetry, comedy, or music — or just watch and enjoy.",
        "category": "open_mic",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["free", "social", "creative"],
    },
    {
        "title": "Community Garden",
        "description": "Dig, plant, and grow — connect with nature and neighbors.",
        "category": "community_garden",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "outdoor", "calming", "social"],
    },
    {
        "title": "Beach Cleanup",
        "description": "Clean up the coast while meeting eco-minded people — feel good doing good.",
        "category": "beach_cleanup",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["free", "outdoor", "social", "helping"],
    },
    {
        "title": "Astronomy Night",
        "description": "Stargazing with telescopes — local astronomy clubs often host free sessions.",
        "category": "astronomy_night",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "outdoor", "quiet", "creative"],
    },
    {
        "title": "Heritage Walking Tour",
        "description": "Explore your city's history on foot — free guided or self-guided walks.",
        "category": "heritage_walk",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "outdoor", "cultural", "traditional"],
    },
    {
        "title": "Sunrise Meditation",
        "description": "Greet the day with a free group meditation at sunrise — peaceful and grounding.",
        "category": "sunrise_meditation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["free", "outdoor", "calming", "quiet"],
    },
    {
        "title": "Park Tai Chi",
        "description": "Join a free morning tai chi class in the park — gentle movement for all levels.",
        "category": "park_tai_chi",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "outdoor", "calming", "quiet"],
    },
    {
        "title": "Free Film Screening",
        "description": "Outdoor or community screenings of classic and indie films — popcorn optional.",
        "category": "free_film_screening",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "social", "creative", "quiet"],
    },
    {
        "title": "Sketching Meetup",
        "description": "Bring your sketchbook and draw together — no skill level required.",
        "category": "sketching_meetup",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "creative", "quiet", "outdoor"],
    },
    {
        "title": "Photography Walk",
        "description": "Explore the city through your lens — free group walks for all camera types.",
        "category": "photography_walk",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "creative", "outdoor"],
    },
    {
        "title": "Outdoor Chess",
        "description": "Giant chess boards in the park — challenge strangers and make friends.",
        "category": "outdoor_chess",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["free", "outdoor", "quiet", "social", "practical"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

FREE_ACTIVITY_KEYWORDS: set[str] = {
    "免费", "free", "低价", "budget", "省钱", "مجاني", "no cost",
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates based on personality preferences."""
    text_lower = wish_text.lower()

    candidates: list[dict] = []
    for item in FREE_ACTIVITY_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0
        tags = set(item.get("tags", []))

        # MBTI matching
        mbti_type = detector_results.mbti.get("type", "")
        if len(mbti_type) == 4:
            if mbti_type[0] == "I" and "quiet" in tags:
                score_boost += 0.15
            elif mbti_type[0] == "E" and "social" in tags:
                score_boost += 0.15

        # Values matching
        top_values = detector_results.values.get("top_values", [])
        if "universalism" in top_values and "helping" in tags:
            score_boost += 0.1
        if "self-direction" in top_values and "creative" in tags:
            score_boost += 0.1
        if "tradition" in top_values and "traditional" in tags:
            score_boost += 0.1

        # Text preference hints
        if any(kw in text_lower for kw in ["outdoor", "户外", "park", "公园"]):
            if "outdoor" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["art", "艺术", "creative", "创意"]):
            if "creative" in tags:
                score_boost += 0.15
        if any(kw in text_lower for kw in ["volunteer", "志愿", "تطوع"]):
            if "helping" in tags:
                score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


class FreeActivityFulfiller(L2Fulfiller):
    """L2 fulfiller for free/low-cost activities — personality-matched.

    20-entry curated catalog. All entries free. Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:max_results]

        return [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "Free and fun — no cost to try"),
                score=c.get("_personality_score", 0.5),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "Free and fun — no cost to try"

        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="park", radius_km=5.0),
            reminder_option=ReminderOption(
                text="Join this free activity this weekend?",
                delay_hours=24,
            ),
        )
