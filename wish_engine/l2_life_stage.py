"""LifeStageFulfiller — local-compute life stage transition recommendation.

15-entry curated catalog covering all major life transitions. Zero LLM.
Keyword matching (English/Chinese/Arabic) routes wish text to relevant
categories, then PersonalityFilter scores and ranks candidates.

Tags: milestone/career/family/retirement/planning.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    Recommendation,
    ReminderOption,
)

# ── Life Stage Catalog (15 entries) ───────────────────────────────────────────

LIFE_STAGE_CATALOG: list[dict] = [
    {
        "title": "Graduation Planning",
        "description": "Cap-and-gown to career — plan your graduation milestone and next steps.",
        "category": "graduation_planning",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["milestone", "planning", "calming", "social", "structured"],
    },
    {
        "title": "First Job Preparation",
        "description": "Resume, interview prep, and workplace tips for your first career step.",
        "category": "first_job_prep",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["career", "planning", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Moving Out Guide",
        "description": "Your first apartment — budgeting, furnishing, and living independently.",
        "category": "moving_out",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["milestone", "planning", "quiet", "calming", "practical"],
    },
    {
        "title": "Engagement Planning",
        "description": "Ring, proposal ideas, and celebration planning for the big question.",
        "category": "engagement_planning",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["milestone", "planning", "calming", "social", "celebration"],
    },
    {
        "title": "First Home Guide",
        "description": "Buying your first home — mortgages, inspections, and neighborhood tips.",
        "category": "first_home",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["milestone", "planning", "quiet", "calming", "practical"],
    },
    {
        "title": "Career Pivot Resources",
        "description": "Changing careers — skills assessment, retraining, and transition planning.",
        "category": "career_pivot",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["career", "planning", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Midlife Exploration",
        "description": "Rediscovering passions and purpose in the middle of life's journey.",
        "category": "midlife_exploration",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["milestone", "quiet", "calming", "self-paced", "reflection"],
    },
    {
        "title": "Empty Nest Adjustment",
        "description": "Kids have left — rediscover yourself, your partner, and your passions.",
        "category": "empty_nest",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["family", "quiet", "calming", "social", "reflection"],
    },
    {
        "title": "Pre-Retirement Planning",
        "description": "Financial planning, health prep, and lifestyle design before retirement.",
        "category": "pre_retirement",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["retirement", "planning", "quiet", "calming", "practical"],
    },
    {
        "title": "Retirement Community",
        "description": "Active retirement communities with social activities and care options.",
        "category": "retirement_community",
        "noise": "quiet",
        "social": "high",
        "mood": "calming",
        "tags": ["retirement", "social", "calming", "structured", "community"],
    },
    {
        "title": "Second Career Launch",
        "description": "Start something new after retirement — consulting, teaching, or volunteering.",
        "category": "second_career",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["career", "retirement", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Legacy Planning",
        "description": "Wills, trusts, and legacy projects — leave something meaningful behind.",
        "category": "legacy_planning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["planning", "quiet", "calming", "practical", "reflection"],
    },
    {
        "title": "Bucket List for Seniors",
        "description": "Adventures and experiences to check off — it is never too late.",
        "category": "bucket_list_senior",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["milestone", "social", "calming", "self-paced", "adventure"],
    },
    {
        "title": "Grandparent Activities",
        "description": "Fun things to do with grandchildren — bonding across generations.",
        "category": "grandparent_activities",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["family", "social", "calming", "outdoor", "indoor"],
    },
    {
        "title": "Life Review",
        "description": "Reflect on your journey — memoir writing, photo books, and storytelling.",
        "category": "life_review",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["reflection", "quiet", "calming", "self-paced", "creative"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

LIFE_STAGE_KEYWORDS: set[str] = {
    "人生阶段", "life stage", "毕业", "graduation", "退休", "retirement",
    "مرحلة", "milestone", "transition", "转折", "career change",
    "first job", "moving out", "engagement", "empty nest",
    "搬家", "结婚", "订婚", "خطوبة", "تقاعد",
}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "graduation_planning": ["graduation", "毕业", "تخرج", "graduate"],
    "first_job_prep": ["first job", "第一份工作", "وظيفة أولى", "career start"],
    "moving_out": ["moving out", "搬出", "apartment", "独立", "استقلال"],
    "engagement_planning": ["engagement", "propose", "订婚", "خطوبة", "ring"],
    "first_home": ["first home", "买房", "mortgage", "بيت أول"],
    "career_pivot": ["career change", "转行", "pivot", "تحول مهني"],
    "midlife_exploration": ["midlife", "中年", "منتصف العمر", "purpose"],
    "empty_nest": ["empty nest", "孩子离家", "عش فارغ"],
    "pre_retirement": ["pre-retirement", "退休准备", "ما قبل التقاعد"],
    "retirement_community": ["retirement community", "养老", "مجتمع التقاعد"],
    "second_career": ["second career", "再就业", "مهنة ثانية"],
    "legacy_planning": ["legacy", "will", "遗嘱", "وصية", "trust"],
    "bucket_list_senior": ["bucket list", "心愿清单", "قائمة أمنيات"],
    "grandparent_activities": ["grandparent", "grandchild", "孙子", "أحفاد"],
    "life_review": ["life review", "memoir", "回忆录", "مذكرات", "reflect"],
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    for item in LIFE_STAGE_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0

        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.25

        # Planning/practical boost
        if any(kw in text_lower for kw in ["plan", "planning", "准备", "تخطيط"]):
            if "planning" in item.get("tags", []):
                score_boost += 0.1

        # Social/connection boost
        if any(kw in text_lower for kw in ["connect", "community", "社区", "مجتمع"]):
            if "social" in item.get("tags", []):
                score_boost += 0.1

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


def _build_relevance(item: dict) -> str:
    """Build a relevance reason for life stage recommendations."""
    reasons = {
        "graduation_planning": "Celebrate and plan your next chapter",
        "first_job_prep": "Ready for your first career step",
        "moving_out": "Your independence journey starts here",
        "engagement_planning": "Make the big moment unforgettable",
        "first_home": "Your first home — a huge milestone",
        "career_pivot": "It is brave to start fresh — here is how",
        "midlife_exploration": "Rediscover what matters to you now",
        "empty_nest": "A new chapter for you",
        "pre_retirement": "Plan now to enjoy later",
        "retirement_community": "Active, social, and supported retirement",
        "second_career": "Your experience is an asset — use it",
        "legacy_planning": "Leave something meaningful behind",
        "bucket_list_senior": "It is never too late for adventure",
        "grandparent_activities": "Making memories across generations",
        "life_review": "Your story deserves to be told",
    }
    return reasons.get(item["category"], "A life stage resource for you")


class LifeStageFulfiller(L2Fulfiller):
    """L2 fulfiller for life stage transition wishes.

    15-entry curated catalog covering all major life transitions.
    Tags: milestone/career/family/retirement/planning. Zero LLM.
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
                relevance_reason=c.get("relevance_reason", "A life stage resource for you"),
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
        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Life transitions take time — check back in a week?",
                delay_hours=168,
            ),
        )
