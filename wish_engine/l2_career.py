"""CareerFulfiller — local-compute career direction with values + MBTI matching.

17-direction curated catalog across 7 groups. Zero LLM. PersonalityFilter
scores and ranks candidates based on values and MBTI alignment.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Career Catalog (17 entries) ──────────────────────────────────────────────

CAREER_CATALOG: list[dict] = [
    # ── Independent / Self-direction (3) ─────────────────────────────────────
    {
        "title": "Freelance Consulting",
        "description": "Build an independent practice around your expertise — set your own hours, choose your clients, grow at your pace.",
        "category": "career_direction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["self-direction", "autonomous", "practical", "quiet"],
    },
    {
        "title": "Entrepreneurship",
        "description": "Launch your own venture — from side project to startup. High autonomy, high reward.",
        "category": "career_direction",
        "noise": "moderate",
        "social": "medium",
        "mood": "intense",
        "tags": ["self-direction", "autonomous", "entrepreneurship", "achievement"],
    },
    {
        "title": "Creative Professional",
        "description": "Design, write, illustrate, or produce — turn creative skills into a sustainable career.",
        "category": "career_direction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["self-direction", "autonomous", "quiet", "theory"],
    },
    # ── Helping / Benevolence (4) ────────────────────────────────────────────
    {
        "title": "Counseling & Therapy",
        "description": "Help others navigate emotional challenges as a licensed counselor or therapist.",
        "category": "career_direction",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["benevolence", "helping", "social-impact", "quiet", "calming"],
    },
    {
        "title": "Education & Teaching",
        "description": "Shape the next generation — teach, tutor, or design learning experiences.",
        "category": "career_direction",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["benevolence", "helping", "social", "traditional", "practical"],
    },
    {
        "title": "Non-Profit Leadership",
        "description": "Lead organizations that create social change — fundraising, programs, advocacy.",
        "category": "career_direction",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["benevolence", "helping", "social-impact", "social", "achievement"],
    },
    {
        "title": "Healthcare",
        "description": "Care for people's physical well-being — nursing, public health, allied health professions.",
        "category": "career_direction",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["benevolence", "helping", "practical", "social"],
    },
    # ── Achievement / Power (3) ──────────────────────────────────────────────
    {
        "title": "Management & Leadership",
        "description": "Lead teams, set strategy, and drive organizational results.",
        "category": "career_direction",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["achievement", "social", "practical"],
    },
    {
        "title": "Finance & Investment",
        "description": "Analyze markets, manage portfolios, or advise on financial strategy.",
        "category": "career_direction",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["achievement", "practical", "theory"],
    },
    {
        "title": "Strategy Consulting",
        "description": "Solve high-stakes business problems for top organizations worldwide.",
        "category": "career_direction",
        "noise": "moderate",
        "social": "high",
        "mood": "intense",
        "tags": ["achievement", "theory", "social"],
    },
    # ── Security / Stability (2) ─────────────────────────────────────────────
    {
        "title": "Government & Public Service",
        "description": "Serve your community with stable, mission-driven work in the public sector.",
        "category": "career_direction",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["security", "traditional", "practical", "quiet"],
    },
    {
        "title": "Engineering",
        "description": "Design and build systems — civil, mechanical, electrical, or industrial engineering.",
        "category": "career_direction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["security", "practical", "quiet", "theory"],
    },
    # ── Universalism (2) ─────────────────────────────────────────────────────
    {
        "title": "Research & Academia",
        "description": "Push the boundaries of knowledge — conduct research, publish, teach at university level.",
        "category": "career_direction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["universalism", "theory", "quiet", "self-direction"],
    },
    {
        "title": "International Development",
        "description": "Work across borders on global challenges — development, diplomacy, humanitarian aid.",
        "category": "career_direction",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["universalism", "social-impact", "social", "helping"],
    },
    # ── Tech (2) ─────────────────────────────────────────────────────────────
    {
        "title": "Software Development",
        "description": "Build products and systems with code — web, mobile, backend, or infrastructure.",
        "category": "career_direction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "quiet", "self-direction", "autonomous"],
    },
    {
        "title": "Data Science & AI",
        "description": "Extract insights from data and build intelligent systems — analytics, ML, NLP.",
        "category": "career_direction",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["theory", "quiet", "practical", "self-direction"],
    },
    # ── Volunteer / Social Impact (1) ────────────────────────────────────────
    {
        "title": "Social Work & Volunteering",
        "description": "Support vulnerable communities through direct service — shelters, outreach, advocacy.",
        "category": "career_direction",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["benevolence", "helping", "social-impact", "social", "traditional"],
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _build_career_reason(career: dict, top_values: list[str]) -> str:
    """Build a personalized relevance reason based on the user's top values."""
    tags = set(career.get("tags", []))
    parts: list[str] = []

    # Value-based reasons
    if "self-direction" in top_values and ("self-direction" in tags or "autonomous" in tags):
        parts.append("Aligns with your independent, self-directed nature")
    if "benevolence" in top_values and ("benevolence" in tags or "helping" in tags):
        parts.append("Resonates with your desire to help others")
    if "achievement" in top_values and "achievement" in tags:
        parts.append("Matches your drive for achievement and impact")
    if "universalism" in top_values and ("universalism" in tags or "social-impact" in tags):
        parts.append("Supports your vision for a better world")
    if "security" in top_values and "security" in tags:
        parts.append("Offers the stability and security you value")
    if "tradition" in top_values and "traditional" in tags:
        parts.append("Rooted in time-tested, traditional paths")
    if "stimulation" in top_values and ("entrepreneurship" in tags or "self-direction" in tags):
        parts.append("Offers the variety and stimulation you crave")

    if not parts:
        parts.append(f"A promising direction: {career['title'].lower()}")

    return ". ".join(parts)


class CareerFulfiller(L2Fulfiller):
    """L2 fulfiller for CAREER_DIRECTION wishes — career direction recommendations.

    Uses a 17-entry curated catalog of career directions, then applies
    PersonalityFilter for scoring and ranking. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        top_values = detector_results.values.get("top_values", [])

        # Copy catalog so personality filter can mutate scores
        candidates = [dict(c) for c in CAREER_CATALOG]

        # Add personalized relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_career_reason(c, top_values)

        # Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=None,
            reminder_option=ReminderOption(
                text="Explore this career direction this week?",
                delay_hours=48,
            ),
        )
