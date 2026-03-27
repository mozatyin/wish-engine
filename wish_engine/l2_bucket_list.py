"""BucketListFulfiller — life experiment list with location awareness.

25 life experiments with "nearby first" logic. Personality-matched suggestions.
Multilingual keyword routing (EN/ZH/AR).
Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Bucket List Catalog (25 entries) ─────────────────────────────────────────

BUCKET_LIST_CATALOG: list[dict] = [
    {
        "title": "Solo Travel",
        "description": "Take a trip alone — discover yourself in an unfamiliar place.",
        "category": "solo_travel",
        "tags": ["travel", "autonomous", "energizing"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "low",
        "nearby": False,
    },
    {
        "title": "Learn an Instrument",
        "description": "Guitar, piano, ukulele — make music with your own hands.",
        "category": "learn_instrument",
        "tags": ["creative", "self-paced", "quiet", "music"],
        "mood": "calming",
        "noise": "moderate",
        "social": "low",
        "nearby": True,
    },
    {
        "title": "Write a Book",
        "description": "Everyone has one book in them — start yours today.",
        "category": "write_a_book",
        "tags": ["creative", "quiet", "self-paced", "autonomous"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "nearby": True,
    },
    {
        "title": "Run a Marathon",
        "description": "42.195 km — the ultimate endurance challenge. Start with a 5K.",
        "category": "run_marathon",
        "tags": ["fitness", "energizing", "practical"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "medium",
        "nearby": True,
    },
    {
        "title": "Learn to Cook",
        "description": "Master 10 dishes from scratch — feed yourself and impress others.",
        "category": "learn_to_cook",
        "tags": ["practical", "creative", "calming", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "nearby": True,
    },
    {
        "title": "Start a Blog",
        "description": "Share your thoughts with the world — writing is thinking made visible.",
        "category": "start_a_blog",
        "tags": ["creative", "quiet", "self-paced", "autonomous"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "nearby": True,
    },
    {
        "title": "Volunteer Abroad",
        "description": "Give your time in another country — impact lives, including your own.",
        "category": "volunteer_abroad",
        "tags": ["travel", "helping", "social", "energizing"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "high",
        "nearby": False,
    },
    {
        "title": "Learn a New Language",
        "description": "Open a door to another culture — every word is a new connection.",
        "category": "learn_new_language",
        "tags": ["language", "self-paced", "quiet", "theory"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "nearby": True,
    },
    {
        "title": "Take a Class",
        "description": "Pottery, dance, cooking, art — learn something completely new.",
        "category": "take_a_class",
        "tags": ["creative", "social", "practical"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "nearby": True,
    },
    {
        "title": "Go Camping",
        "description": "Sleep under the stars — disconnect from everything, reconnect with nature.",
        "category": "go_camping",
        "tags": ["nature", "quiet", "autonomous"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "nearby": False,
    },
    {
        "title": "Attend a Festival",
        "description": "Music, food, or culture — immerse yourself in collective joy.",
        "category": "attend_a_festival",
        "tags": ["social", "energizing", "fun"],
        "mood": "energizing",
        "noise": "loud",
        "social": "high",
        "nearby": True,
    },
    {
        "title": "Try Meditation Retreat",
        "description": "3-7 days of silence — the deepest reset you've never tried.",
        "category": "try_meditation",
        "tags": ["calming", "quiet", "mindfulness", "autonomous"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "nearby": False,
    },
    {
        "title": "Join a Club",
        "description": "Book club, hiking club, board game club — find your people.",
        "category": "join_a_club",
        "tags": ["social", "calming"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "nearby": True,
    },
    {
        "title": "Give a Speech",
        "description": "Stand up and speak — Toastmasters, open mic, or just a toast at dinner.",
        "category": "give_a_speech",
        "tags": ["social", "energizing", "practical"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "high",
        "nearby": True,
    },
    {
        "title": "Learn to Dance",
        "description": "Salsa, tango, or hip-hop — your body wants to move.",
        "category": "learn_to_dance",
        "tags": ["creative", "social", "fitness", "energizing"],
        "mood": "energizing",
        "noise": "loud",
        "social": "medium",
        "nearby": True,
    },
    {
        "title": "Visit 10 Countries",
        "description": "See the world — each country changes how you see home.",
        "category": "visit_10_countries",
        "tags": ["travel", "energizing", "autonomous"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "medium",
        "nearby": False,
    },
    {
        "title": "Read 50 Books",
        "description": "One book a week for a year — transform your mind through reading.",
        "category": "read_50_books",
        "tags": ["quiet", "self-paced", "theory", "autonomous"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "nearby": True,
    },
    {
        "title": "Start a Business",
        "description": "Turn an idea into reality — even a side project counts.",
        "category": "start_a_business",
        "tags": ["practical", "autonomous", "energizing"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "medium",
        "nearby": True,
    },
    {
        "title": "Mentor Someone",
        "description": "Share what you know — teaching is the best way to deepen mastery.",
        "category": "mentor_someone",
        "tags": ["social", "helping", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "nearby": True,
    },
    {
        "title": "Plant a Garden",
        "description": "Grow something living — herbs, flowers, or vegetables on your balcony.",
        "category": "plant_a_garden",
        "tags": ["nature", "calming", "quiet", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "nearby": True,
    },
    {
        "title": "Make a Short Film",
        "description": "Phone camera + story + editing app — you're a filmmaker now.",
        "category": "make_a_film",
        "tags": ["creative", "practical", "self-paced"],
        "mood": "calming",
        "noise": "moderate",
        "social": "low",
        "nearby": True,
    },
    {
        "title": "Learn Calligraphy",
        "description": "The art of beautiful writing — slow, meditative, and deeply satisfying.",
        "category": "learn_calligraphy",
        "tags": ["creative", "quiet", "calming", "traditional"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "nearby": True,
    },
    {
        "title": "Swim in the Ocean",
        "description": "Feel the salt water — there's nothing quite like the open sea.",
        "category": "swim_in_ocean",
        "tags": ["nature", "energizing", "fitness"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "low",
        "nearby": False,
    },
    {
        "title": "Watch a Sunrise",
        "description": "Wake up early once — watch the sky change colors. Worth it.",
        "category": "watch_sunrise",
        "tags": ["nature", "quiet", "calming", "simple"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "nearby": True,
    },
    {
        "title": "Host a Dinner Party",
        "description": "Cook for friends — set the table, light candles, make memories.",
        "category": "host_a_dinner",
        "tags": ["social", "creative", "warm", "practical"],
        "mood": "calming",
        "noise": "moderate",
        "social": "high",
        "nearby": True,
    },
]


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select candidates with nearby-first logic."""
    text_lower = wish_text.lower()

    # Detect "nearby" preference
    nearby_pref = any(
        kw in text_lower
        for kw in ["附近", "nearby", "local", "能做", "قريب", "here"]
    )

    candidates: list[dict] = []
    for item in BUCKET_LIST_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        # Nearby-first logic
        if nearby_pref and item.get("nearby"):
            score_boost += 0.2
            item_copy["relevance_reason"] = "You can start this one right where you are"
        elif nearby_pref and not item.get("nearby"):
            score_boost -= 0.1

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


class BucketListFulfiller(L2Fulfiller):
    """L2 fulfiller for bucket list wishes — location-aware life experiments.

    25-entry curated catalog. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "A life experiment worth trying"

        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:3]

        from wish_engine.models import Recommendation

        recommendations = [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "Matches your profile"),
                score=c.get("_personality_score", 0.5),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Ready to check something off your bucket list?",
                delay_hours=72,
            ),
        )
