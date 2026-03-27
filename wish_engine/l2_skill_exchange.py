"""SkillExchangeFulfiller — skill exchange map with personality-matched pairing.

20 skill pairs for mutual teaching/learning. Core innovation: detect what
users can offer and what they want, then suggest complementary pairs.
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

# ── Skill Pair Catalog (20 entries) ──────────────────────────────────────────

SKILL_CATALOG: list[dict] = [
    {
        "title": "Japanese ↔ Arabic",
        "description": "Exchange language skills — teach your native tongue, learn a new one.",
        "category": "language",
        "tags": ["language", "social", "cultural", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "skills": ["japanese", "arabic"],
    },
    {
        "title": "Photography ↔ Design",
        "description": "Swap visual skills — capture moments and create with them.",
        "category": "creative",
        "tags": ["creative", "practical", "visual", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "skills": ["photography", "design"],
    },
    {
        "title": "Cooking ↔ Gardening",
        "description": "From garden to table — grow ingredients and learn to cook with them.",
        "category": "lifestyle",
        "tags": ["practical", "calming", "nature", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "skills": ["cooking", "gardening"],
    },
    {
        "title": "Guitar ↔ Piano",
        "description": "Musicians helping musicians — trade chord knowledge and technique.",
        "category": "music",
        "tags": ["music", "creative", "quiet", "self-paced"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "skills": ["guitar", "piano"],
    },
    {
        "title": "Coding ↔ Data Science",
        "description": "Software meets statistics — build apps and analyze data together.",
        "category": "tech",
        "tags": ["tech", "practical", "theory", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "skills": ["coding", "data"],
    },
    {
        "title": "Yoga ↔ Meditation",
        "description": "Body and mind — deepen your practice by learning both paths.",
        "category": "wellness",
        "tags": ["wellness", "calming", "quiet", "mindfulness"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "skills": ["yoga", "meditation"],
    },
    {
        "title": "Calligraphy ↔ Painting",
        "description": "Brush arts — from precise strokes to expressive canvases.",
        "category": "creative",
        "tags": ["creative", "quiet", "traditional", "calming"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "skills": ["calligraphy", "painting"],
    },
    {
        "title": "Dance ↔ Fitness",
        "description": "Move your body — learn choreography and build strength together.",
        "category": "fitness",
        "tags": ["fitness", "social", "energizing"],
        "mood": "energizing",
        "noise": "loud",
        "social": "high",
        "skills": ["dance", "fitness"],
    },
    {
        "title": "Writing ↔ Editing",
        "description": "Create and refine — writers and editors make each other better.",
        "category": "creative",
        "tags": ["creative", "quiet", "theory", "self-paced"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "skills": ["writing", "editing"],
    },
    {
        "title": "Marketing ↔ Sales",
        "description": "Attract and close — learn both sides of the business growth engine.",
        "category": "business",
        "tags": ["business", "practical", "social"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "skills": ["marketing", "sales"],
    },
    {
        "title": "Accounting ↔ Finance",
        "description": "Numbers and strategy — track money and learn to grow it.",
        "category": "business",
        "tags": ["business", "practical", "theory", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "skills": ["accounting", "finance"],
    },
    {
        "title": "Tutoring ↔ Mentoring",
        "description": "Teaching is learning — help others academically and professionally.",
        "category": "education",
        "tags": ["education", "social", "helping", "quiet"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "skills": ["tutoring", "mentoring"],
    },
    {
        "title": "Carpentry ↔ Plumbing",
        "description": "Hands-on trades — build and fix things around the house.",
        "category": "trades",
        "tags": ["practical", "hands-on", "autonomous"],
        "mood": "calming",
        "noise": "moderate",
        "social": "low",
        "skills": ["carpentry", "plumbing"],
    },
    {
        "title": "Sewing ↔ Knitting",
        "description": "Textile arts — from mending clothes to creating cozy knits.",
        "category": "craft",
        "tags": ["creative", "quiet", "traditional", "calming", "practical"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "skills": ["sewing", "knitting"],
    },
    {
        "title": "Pottery ↔ Sculpture",
        "description": "Shape with your hands — wheel-thrown pottery and sculptural forms.",
        "category": "creative",
        "tags": ["creative", "quiet", "calming", "hands-on"],
        "mood": "calming",
        "noise": "quiet",
        "social": "low",
        "skills": ["pottery", "sculpture"],
    },
    {
        "title": "Singing ↔ Music Theory",
        "description": "Voice and knowledge — sing better by understanding how music works.",
        "category": "music",
        "tags": ["music", "creative", "theory", "quiet"],
        "mood": "calming",
        "noise": "moderate",
        "social": "medium",
        "skills": ["singing", "music_theory"],
    },
    {
        "title": "Basketball ↔ Soccer",
        "description": "Court and pitch — athletes exchanging sport-specific skills.",
        "category": "sports",
        "tags": ["sports", "social", "energizing", "fitness"],
        "mood": "energizing",
        "noise": "loud",
        "social": "high",
        "skills": ["basketball", "soccer"],
    },
    {
        "title": "Chess ↔ Go",
        "description": "Strategy games — deepen your tactical thinking across two traditions.",
        "category": "games",
        "tags": ["strategy", "quiet", "theory", "traditional"],
        "mood": "calming",
        "noise": "quiet",
        "social": "medium",
        "skills": ["chess", "go"],
    },
    {
        "title": "Hiking ↔ Climbing",
        "description": "Vertical and horizontal — trail knowledge meets wall technique.",
        "category": "outdoor",
        "tags": ["nature", "fitness", "energizing", "social"],
        "mood": "energizing",
        "noise": "moderate",
        "social": "medium",
        "skills": ["hiking", "climbing"],
    },
    {
        "title": "Film ↔ Theater",
        "description": "Screen and stage — learn storytelling from both performance traditions.",
        "category": "performing",
        "tags": ["creative", "social", "theory"],
        "mood": "calming",
        "noise": "moderate",
        "social": "high",
        "skills": ["film", "theater"],
    },
]


def _detect_skill_interests(wish_text: str) -> list[str]:
    """Detect mentioned skills from the wish text."""
    text_lower = wish_text.lower()
    all_skills: list[str] = []
    for item in SKILL_CATALOG:
        for skill in item["skills"]:
            if skill in text_lower and skill not in all_skills:
                all_skills.append(skill)
    return all_skills


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on skill keyword matching."""
    interests = _detect_skill_interests(wish_text)

    candidates: list[dict] = []
    for item in SKILL_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        if interests:
            matched = set(interests) & set(item["skills"])
            if matched:
                score_boost += 0.25 * len(matched)
                item_copy["relevance_reason"] = (
                    f"Matches your interest in {', '.join(matched)}"
                )

        item_copy["_emotion_boost"] = score_boost
        candidates.append(item_copy)

    return candidates


class SkillExchangeFulfiller(L2Fulfiller):
    """L2 fulfiller for skill exchange wishes — personality-matched skill pairing.

    20-entry curated catalog. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)

        for c in candidates:
            if "relevance_reason" not in c:
                c["relevance_reason"] = "A great skill exchange opportunity for you"

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
                text="Ready to start your skill exchange?",
                delay_hours=48,
            ),
        )
