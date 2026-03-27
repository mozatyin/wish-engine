"""VolunteerFulfiller — values-driven volunteer opportunity matching.

15-type curated catalog of volunteer activities with values-based personality
mapping (benevolence→direct helping, universalism→systemic change). Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Values → Volunteer Type Mapping ──────────────────────────────────────────

VALUES_VOLUNTEER_MAP: dict[str, list[str]] = {
    "benevolence": ["teaching", "elderly_care", "hospital", "food_bank", "mentoring_youth"],
    "universalism": ["environmental", "refugee_support", "coding_for_good", "disaster_relief"],
    "tradition": ["community_garden", "library", "charity_run"],
    "stimulation": ["disaster_relief", "charity_run", "art_therapy"],
    "self-direction": ["coding_for_good", "mentoring_youth", "art_therapy"],
    "conformity": ["blood_donation", "food_bank", "library"],
    "security": ["community_garden", "hospital", "elderly_care"],
}

# ── Volunteer Catalog (15 entries) ───────────────────────────────────────────

VOLUNTEER_CATALOG: list[dict] = [
    {
        "title": "Teaching & Tutoring",
        "description": "Teach reading, math, or languages to underserved children and adults.",
        "category": "teaching",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["teaching", "helping", "practical", "social"],
    },
    {
        "title": "Environmental Conservation",
        "description": "Beach cleanups, tree planting, and wildlife habitat restoration.",
        "category": "environmental",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["environmental", "nature", "social"],
    },
    {
        "title": "Animal Shelter Volunteering",
        "description": "Walk dogs, socialize cats, and help abandoned animals find homes.",
        "category": "animal_shelter",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["animal_shelter", "calming", "helping"],
    },
    {
        "title": "Elderly Care & Companionship",
        "description": "Visit nursing homes, share stories, and bring warmth to seniors.",
        "category": "elderly_care",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["elderly_care", "helping", "calming", "quiet"],
    },
    {
        "title": "Food Bank & Meal Service",
        "description": "Sort donations, pack meals, and serve food to those in need.",
        "category": "food_bank",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["food_bank", "helping", "social", "practical"],
    },
    {
        "title": "Disaster Relief Support",
        "description": "Emergency response, supply distribution, and rebuilding communities.",
        "category": "disaster_relief",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["disaster_relief", "social"],
    },
    {
        "title": "Youth Mentoring Program",
        "description": "Guide young people through academic challenges and life skills.",
        "category": "mentoring_youth",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["mentoring_youth", "helping", "practical"],
    },
    {
        "title": "Hospital Volunteering",
        "description": "Comfort patients, assist staff, and bring cheer to hospital wards.",
        "category": "hospital",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["hospital", "helping", "calming", "quiet"],
    },
    {
        "title": "Library & Literacy Programs",
        "description": "Read to children, organize books, and promote literacy in your community.",
        "category": "library",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["library", "quiet", "traditional", "helping"],
    },
    {
        "title": "Community Garden Projects",
        "description": "Grow food together — urban gardening, composting, and green spaces.",
        "category": "community_garden",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["community_garden", "nature", "calming", "traditional"],
    },
    {
        "title": "Refugee Support Services",
        "description": "Language help, cultural orientation, and resettlement assistance.",
        "category": "refugee_support",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["refugee_support", "helping", "social"],
    },
    {
        "title": "Blood Donation Drives",
        "description": "Organize or participate in blood donation — save lives in under an hour.",
        "category": "blood_donation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["blood_donation", "practical", "helping"],
    },
    {
        "title": "Charity Run & Walkathon",
        "description": "Run or walk for a cause — fundraising through fitness events.",
        "category": "charity_run",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["charity_run", "social"],
    },
    {
        "title": "Coding for Good",
        "description": "Build websites, apps, and tools for nonprofits and social enterprises.",
        "category": "coding_for_good",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["coding_for_good", "practical", "quiet", "autonomous"],
    },
    {
        "title": "Art Therapy Volunteering",
        "description": "Facilitate creative sessions for at-risk youth, patients, or seniors.",
        "category": "art_therapy",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["art_therapy", "helping", "calming", "social"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_VOLUNTEER_KEYWORDS: dict[str, list[str]] = {
    "志愿": ["volunteer"],
    "volunteer": ["volunteer"],
    "公益": ["volunteer", "helping"],
    "charity": ["volunteer", "helping"],
    "متطوع": ["volunteer"],
    "خيري": ["volunteer", "helping"],
    "donate": ["blood_donation", "helping"],
    "捐": ["blood_donation", "helping"],
    "teach": ["teaching"],
    "支教": ["teaching"],
    "环保": ["environmental"],
    "environment": ["environmental"],
    "animal": ["animal_shelter"],
    "动物": ["animal_shelter"],
    "mentor": ["mentoring_youth"],
    "refugee": ["refugee_support"],
    "disaster": ["disaster_relief"],
    "garden": ["community_garden"],
    "coding for good": ["coding_for_good"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _VOLUNTEER_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _values_to_volunteer_tags(top_values: list[str]) -> list[str]:
    """Map user's top values to preferred volunteer types."""
    tags: list[str] = []
    for value in top_values:
        for tag in VALUES_VOLUNTEER_MAP.get(value, []):
            if tag not in tags:
                tags.append(tag)
    return tags


def _build_relevance_reason(item: dict, top_values: list[str]) -> str:
    """Build a personalized relevance reason based on values."""
    tags = set(item.get("tags", []))

    for value in top_values:
        if value == "benevolence" and "helping" in tags:
            return "A direct way to help others — matches your caring nature"
        if value == "universalism" and tags & {"environmental", "refugee_support"}:
            return "Making a systemic difference in the world"
        if value == "tradition" and "traditional" in tags:
            return "Strengthen your community through time-honored service"
        if value == "self-direction" and tags & {"autonomous", "practical"}:
            return "Use your skills independently for meaningful impact"

    category = item.get("category", "")
    reason_map = {
        "teaching": "Share knowledge and change a life",
        "environmental": "Protect the planet for future generations",
        "animal_shelter": "Give love to animals who need it most",
        "elderly_care": "Bring warmth and companionship to seniors",
        "food_bank": "Ensure no one in your community goes hungry",
        "coding_for_good": "Your tech skills can change the world",
        "art_therapy": "Heal through creativity",
    }
    return reason_map.get(category, "Give back and make a difference")


class VolunteerFulfiller(L2Fulfiller):
    """L2 fulfiller for volunteer/charity wishes — values-driven matching.

    Uses keyword matching + values→volunteer mapping to select from 15-type
    catalog, then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Add values-based categories
        top_values = detector_results.values.get("top_values", [])
        values_tags = _values_to_volunteer_tags(top_values)

        all_tags = list(matched_categories)
        for t in values_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in VOLUNTEER_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in VOLUNTEER_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in VOLUNTEER_CATALOG]

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, top_values)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New volunteer opportunities near you — check back soon!",
                delay_hours=48,
            ),
        )
