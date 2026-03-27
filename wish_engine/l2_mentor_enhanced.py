"""MentorFulfiller — enhanced L2 mentor matching with location awareness.

15-entry curated catalog of mentorship types with personality and values matching.
Multilingual keyword routing (EN/ZH/AR). Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    ReminderOption,
)

# ── Mentor Catalog (15 entries) ──────────────────────────────────────────────

MENTOR_CATALOG: list[dict] = [
    {
        "title": "Career Mentor",
        "description": "Experienced professional to guide your career transitions and growth strategy.",
        "category": "mentor",
        "domain": "career",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "career", "quiet", "calming"],
    },
    {
        "title": "Startup Mentor",
        "description": "Founder-turned-advisor to help you validate ideas, build MVPs, and find product-market fit.",
        "category": "mentor",
        "domain": "startup",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "modern", "autonomous"],
    },
    {
        "title": "Creative Mentor",
        "description": "Artist or designer who nurtures your creative voice and pushes your boundaries.",
        "category": "mentor",
        "domain": "creative",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Academic Mentor",
        "description": "Professor or researcher to guide your thesis, publications, and academic career.",
        "category": "mentor",
        "domain": "academic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["intellectual", "theory", "quiet", "calming"],
    },
    {
        "title": "Life Coach Mentor",
        "description": "Holistic life coach to help you find balance, purpose, and direction.",
        "category": "mentor",
        "domain": "life",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "helping", "quiet", "self-paced"],
    },
    {
        "title": "Spiritual Guide",
        "description": "A spiritual mentor for meditation, mindfulness, and inner peace practices.",
        "category": "mentor",
        "domain": "spiritual",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["traditional", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Parenting Mentor",
        "description": "Experienced parent to share wisdom on raising children with confidence and love.",
        "category": "mentor",
        "domain": "parenting",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "calming", "helping", "quiet"],
    },
    {
        "title": "Tech Mentor",
        "description": "Senior engineer to guide your technical skills, architecture decisions, and career path.",
        "category": "mentor",
        "domain": "tech",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "modern", "quiet", "theory"],
    },
    {
        "title": "Finance Mentor",
        "description": "Financial advisor to help you with investing, budgeting, and wealth building.",
        "category": "mentor",
        "domain": "finance",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "quiet", "calming"],
    },
    {
        "title": "Health & Wellness Mentor",
        "description": "Certified coach for fitness, nutrition, and mental health wellness journeys.",
        "category": "mentor",
        "domain": "health",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "calming", "self-paced", "quiet"],
    },
    {
        "title": "Leadership Mentor",
        "description": "Executive coach to develop your leadership presence, communication, and decision-making.",
        "category": "mentor",
        "domain": "leadership",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "social", "calming"],
    },
    {
        "title": "Writing Mentor",
        "description": "Published author to guide your writing craft — fiction, non-fiction, or journalism.",
        "category": "mentor",
        "domain": "writing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Public Speaking Coach",
        "description": "Communication expert to help you overcome stage fright and deliver powerful talks.",
        "category": "mentor",
        "domain": "public_speaking",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "social", "calming"],
    },
    {
        "title": "Negotiation Mentor",
        "description": "Master negotiator to teach you persuasion, deal-making, and conflict resolution.",
        "category": "mentor",
        "domain": "negotiation",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["practical", "social", "calming", "theory"],
    },
    {
        "title": "Emotional Intelligence Coach",
        "description": "EQ specialist to deepen your self-awareness, empathy, and relationship skills.",
        "category": "mentor",
        "domain": "emotional_intelligence",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["calming", "helping", "quiet", "theory"],
    },
]

# ── Keywords ──────────────────────────────────────────────────────────────────

_MENTOR_KEYWORDS: set[str] = {
    "导师", "mentor", "前辈", "指导", "مرشد", "guidance", "coach",
    "advisor", "顾问", "guide",
}


def _match_mentor_domain(wish_text: str) -> str | None:
    """Detect mentor domain from wish text keywords."""
    text_lower = wish_text.lower()
    domain_keywords = {
        "career": ["career", "职业", "工作", "job", "مهنة"],
        "startup": ["startup", "创业", "founder", "شركة"],
        "creative": ["creative", "创意", "art", "design", "فن"],
        "academic": ["academic", "学术", "research", "论文", "أكاديمي"],
        "tech": ["tech", "coding", "programming", "技术", "تقنية"],
        "finance": ["finance", "investing", "理财", "投资", "مالية"],
        "health": ["health", "fitness", "健康", "صحة"],
        "writing": ["writing", "写作", "author", "كتابة"],
        "leadership": ["leadership", "领导", "management", "قيادة"],
    }
    for domain, keywords in domain_keywords.items():
        if any(kw in text_lower for kw in keywords):
            return domain
    return None


class MentorFulfiller(L2Fulfiller):
    """L2 fulfiller for mentor matching wishes — personality + values alignment.

    15-entry curated catalog. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Detect domain from wish text
        domain = _match_mentor_domain(wish.wish_text)

        # 2. Filter by domain if detected
        candidates = [dict(item) for item in MENTOR_CATALOG]
        if domain:
            domain_matches = [c for c in candidates if c.get("domain") == domain]
            if domain_matches:
                candidates = domain_matches

        # 3. Add relevance reasons
        for c in candidates:
            d = c.get("domain", "")
            c["relevance_reason"] = f"Expert {d} guidance matched to your personality"

        # 4. Personality filter and rank
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="mentor_space", radius_km=15.0),
            reminder_option=ReminderOption(
                text="Schedule a mentor session this week?",
                delay_hours=48,
            ),
        )
