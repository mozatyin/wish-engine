"""DisabilitySocialFulfiller — inclusive social activities for people with disabilities.

12-entry catalog of adaptive, inclusive social and recreational activities.
Personality-filtered. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Catalog (12 entries) ─────────────────────────────────────────────────────

DISABILITY_SOCIAL_CATALOG: list[dict] = [
    {
        "title": "Adaptive Sports Programs",
        "description": "Find adaptive sports near you — sit-ski, hand-cycling, adaptive surfing, and more.",
        "category": "adaptive_sports",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["sports", "adaptive", "physical", "community", "active"],
    },
    {
        "title": "Disability Meetup Groups",
        "description": "Local meetups for people with disabilities — social events, outings, and friendship.",
        "category": "disability_meetup",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["meetup", "social", "community", "friendship"],
    },
    {
        "title": "Inclusive Dance Classes",
        "description": "Dance classes welcoming all abilities — seated dance, movement therapy, creative expression.",
        "category": "inclusive_dance",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["dance", "inclusive", "creative", "movement", "adaptive"],
    },
    {
        "title": "Wheelchair Basketball League",
        "description": "Competitive and recreational wheelchair basketball — teamwork, fitness, and fun.",
        "category": "wheelchair_basketball",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["basketball", "wheelchair", "sports", "competitive", "active"],
    },
    {
        "title": "Blind Community Network",
        "description": "Social groups, tech resources, and peer mentoring for blind and low-vision individuals.",
        "category": "blind_community",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["blind", "vision", "community", "support", "calming"],
    },
    {
        "title": "Deaf Community Hub",
        "description": "Deaf culture events, sign language socials, and community gatherings.",
        "category": "deaf_community",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["deaf", "sign_language", "community", "culture", "calming"],
    },
    {
        "title": "Neurodivergent Social Group",
        "description": "Low-pressure social gatherings designed for autistic and neurodivergent adults.",
        "category": "neurodivergent_group",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["neurodivergent", "autism", "social", "calming", "gentle"],
    },
    {
        "title": "Disability Art Collective",
        "description": "Art workshops, exhibitions, and creative expression for artists with disabilities.",
        "category": "disability_art",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["art", "creative", "inclusive", "community", "calming"],
    },
    {
        "title": "Adaptive Yoga Classes",
        "description": "Chair yoga, wheelchair yoga, and modified poses — movement for every body.",
        "category": "adaptive_yoga",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["yoga", "adaptive", "gentle", "calming", "self-paced"],
    },
    {
        "title": "Disability Dating Community",
        "description": "Inclusive dating spaces where disability is understood, not a barrier.",
        "category": "disability_dating",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["dating", "inclusive", "social", "calming"],
    },
    {
        "title": "Accessible Travel Group",
        "description": "Travel companions and accessible destination reviews from travelers with disabilities.",
        "category": "accessible_travel_group",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["travel", "accessible", "community", "adventure"],
    },
    {
        "title": "Disability Advocacy Network",
        "description": "Get involved in disability rights — policy advocacy, awareness campaigns, and peer support.",
        "category": "disability_advocacy",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["advocacy", "rights", "community", "empowerment"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_DISABILITY_SOCIAL_KEYWORDS: dict[str, list[str]] = {
    "残障社交": [],
    "disability": [],
    "disabled": [],
    "残疾": [],
    "إعاقة": [],
    "inclusive": ["inclusive"],
    "adaptive": ["adaptive"],
    "wheelchair": ["wheelchair", "adaptive"],
    "轮椅": ["wheelchair", "adaptive"],
    "blind": ["blind", "vision"],
    "视障": ["blind", "vision"],
    "deaf": ["deaf", "sign_language"],
    "听障": ["deaf", "sign_language"],
    "neurodivergent": ["neurodivergent", "autism"],
    "自闭": ["neurodivergent", "autism"],
    "sports": ["sports", "active"],
    "dance": ["dance", "creative"],
    "art": ["art", "creative"],
    "yoga": ["yoga", "gentle"],
    "advocacy": ["advocacy", "rights"],
}


def _match_disability_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _DISABILITY_SOCIAL_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class DisabilitySocialFulfiller(L2Fulfiller):
    """L2 fulfiller for disability social activities — inclusive, adaptive.

    12 curated entries for adaptive sports, community, and social activities. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_disability_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in DISABILITY_SOCIAL_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in DISABILITY_SOCIAL_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in DISABILITY_SOCIAL_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Inclusive communities are waiting for you. Check back for new events!",
                delay_hours=48,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "adaptive" in tags:
        return "Designed to be fully accessible and adaptive"
    if "community" in tags:
        return "Connect with a welcoming, understanding community"
    if "creative" in tags:
        return "Express yourself through inclusive creative activities"
    if "active" in tags:
        return "Stay active with adaptive sports programs"
    return "Inclusive activity designed for every ability"
