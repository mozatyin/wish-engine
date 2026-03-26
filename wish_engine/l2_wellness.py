"""WellnessFulfiller — local-compute wellness recommendation with emotion + fragility matching.

18-activity curated catalog across 6 groups (Sleep, Anxiety, Exercise, Nutrition,
Relaxation, Emotional). Zero LLM. Keyword matching (English/Chinese/Arabic) routes
wish text to relevant tag categories, then PersonalityFilter scores and ranks.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    ReminderOption,
)

# ── Wellness Catalog (18 entries) ────────────────────────────────────────────

WELLNESS_CATALOG: list[dict] = [
    # ── Sleep (3) ────────────────────────────────────────────────────────────
    {
        "title": "Sleep Hygiene Routine",
        "description": "Establish a consistent bedtime routine: dim lights, cool room, no screens 1 hour before bed.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sleep", "relaxation", "calming", "practical", "self-paced"],
    },
    {
        "title": "Guided Sleep Meditation",
        "description": "A 20-minute body scan meditation designed to ease you into deep, restful sleep.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sleep", "relaxation", "calming", "quiet", "self-paced"],
    },
    {
        "title": "CBT for Insomnia (CBT-I)",
        "description": "Cognitive behavioral techniques to retrain your brain for healthy sleep patterns.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sleep", "calming", "practical", "quiet", "theory"],
    },
    # ── Anxiety (3) ──────────────────────────────────────────────────────────
    {
        "title": "Box Breathing Exercise",
        "description": "4-4-4-4 breathing technique used by Navy SEALs to reduce anxiety in minutes.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["anxiety", "calming", "practical", "quiet", "self-paced"],
    },
    {
        "title": "Progressive Muscle Relaxation (PMR)",
        "description": "Systematically tense and release muscle groups to dissolve physical tension.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["anxiety", "relaxation", "calming", "practical", "quiet"],
    },
    {
        "title": "Anxiety Journaling",
        "description": "Write down worries and reframe them with evidence-based prompts to regain perspective.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["anxiety", "emotions", "calming", "practical", "self-paced"],
    },
    # ── Exercise (5) ─────────────────────────────────────────────────────────
    {
        "title": "Gentle Yoga Flow",
        "description": "A 30-minute gentle yoga sequence focusing on flexibility, breath, and calm.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["exercise", "movement", "calming", "quiet", "self-paced"],
    },
    {
        "title": "Walking Meditation",
        "description": "Combine mindful walking with breath awareness — 20 minutes in nature or indoors.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["exercise", "movement", "calming", "quiet", "self-paced"],
    },
    {
        "title": "Swimming for Wellness",
        "description": "Low-impact full-body exercise that reduces stress and improves cardiovascular health.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["exercise", "movement", "fitness", "calming", "self-paced"],
    },
    {
        "title": "Daily Running Routine",
        "description": "Start with a 15-minute jog and build up — running releases endorphins and clears the mind.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["exercise", "movement", "fitness", "calming", "self-paced"],
    },
    {
        "title": "Group Fitness Class",
        "description": "High-energy group workout — HIIT, dance, or circuit training for motivation and social connection.",
        "category": "wellness",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["exercise", "movement", "fitness", "social"],
    },
    # ── Nutrition (2) ────────────────────────────────────────────────────────
    {
        "title": "Mindful Eating Practice",
        "description": "Slow down meals, savor each bite, and reconnect with hunger and fullness signals.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nutrition", "calming", "practical", "self-paced"],
    },
    {
        "title": "Anti-Inflammatory Diet Guide",
        "description": "Focus on whole foods, omega-3s, and colorful vegetables to reduce inflammation and boost mood.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nutrition", "calming", "practical", "self-paced"],
    },
    # ── Relaxation (3) ───────────────────────────────────────────────────────
    {
        "title": "Nature Therapy (Forest Bathing)",
        "description": "Spend 30+ minutes in a natural setting — proven to lower cortisol and blood pressure.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["relaxation", "calming", "quiet", "self-paced"],
    },
    {
        "title": "Aromatherapy Routine",
        "description": "Use lavender, chamomile, or eucalyptus essential oils to promote relaxation and sleep.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["relaxation", "sleep", "calming", "quiet", "self-paced"],
    },
    {
        "title": "Digital Detox Challenge",
        "description": "Set screen-free hours each day to reduce cognitive overload and improve sleep quality.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["relaxation", "sleep", "calming", "practical", "self-paced"],
    },
    # ── Emotional (2) ────────────────────────────────────────────────────────
    {
        "title": "Gratitude Practice",
        "description": "Write three things you are grateful for each morning — rewires the brain for positivity.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["emotions", "calming", "practical", "quiet", "self-paced"],
    },
    {
        "title": "Art Therapy Expression",
        "description": "Use drawing, painting, or collage to process and express difficult emotions nonverbally.",
        "category": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["emotions", "calming", "quiet", "self-paced"],
    },
]


# ── Keyword → Tag Category Mapping ──────────────────────────────────────────

_WELLNESS_KEYWORDS: dict[str, list[str]] = {
    # sleep
    "sleep": ["sleep"],
    "insomnia": ["sleep"],
    "失眠": ["sleep"],
    "睡眠": ["sleep"],
    "睡不着": ["sleep"],
    "نوم": ["sleep"],
    "أرق": ["sleep"],
    # anxiety
    "anxiety": ["anxiety"],
    "anxious": ["anxiety"],
    "worry": ["anxiety"],
    "panic": ["anxiety"],
    "焦虑": ["anxiety"],
    "紧张": ["anxiety"],
    "不安": ["anxiety"],
    "قلق": ["anxiety"],
    "توتر": ["anxiety"],
    # exercise / movement
    "exercise": ["exercise", "movement"],
    "workout": ["exercise", "movement"],
    "运动": ["exercise", "movement"],
    "锻炼": ["exercise", "movement"],
    "健身": ["exercise", "fitness"],
    "yoga": ["exercise", "movement"],
    "瑜伽": ["exercise", "movement"],
    "run": ["exercise", "movement", "fitness"],
    "running": ["exercise", "movement", "fitness"],
    "swim": ["exercise", "movement", "fitness"],
    "跑步": ["exercise", "movement", "fitness"],
    "游泳": ["exercise", "movement", "fitness"],
    "رياضة": ["exercise", "movement"],
    "تمارين": ["exercise", "movement"],
    # nutrition
    "nutrition": ["nutrition"],
    "diet": ["nutrition"],
    "eating": ["nutrition"],
    "饮食": ["nutrition"],
    "营养": ["nutrition"],
    "吃": ["nutrition"],
    "تغذية": ["nutrition"],
    "طعام": ["nutrition"],
    # relaxation
    "relax": ["relaxation"],
    "relaxation": ["relaxation"],
    "nature": ["relaxation"],
    "detox": ["relaxation"],
    "放松": ["relaxation"],
    "自然": ["relaxation"],
    "استرخاء": ["relaxation"],
    "طبيعة": ["relaxation"],
    # emotions
    "emotion": ["emotions"],
    "emotions": ["emotions"],
    "gratitude": ["emotions"],
    "art therapy": ["emotions"],
    "情绪": ["emotions"],
    "感恩": ["emotions"],
    "مشاعر": ["emotions"],
    "امتنان": ["emotions"],
    # broad wellness terms → multiple categories
    "wellness": ["sleep", "relaxation", "emotions"],
    "health": ["exercise", "nutrition"],
    "stress": ["anxiety", "relaxation"],
    "健康": ["exercise", "nutrition"],
    "压力": ["anxiety", "relaxation"],
    "صحة": ["exercise", "nutrition"],
    "ضغط": ["anxiety", "relaxation"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text via keyword lookup.

    Returns deduplicated list of tag category strings. If no keywords match,
    returns empty list (caller should fall back to full catalog).
    """
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _WELLNESS_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


# ── Physical activity tags that warrant map data ─────────────────────────────

_PHYSICAL_TAGS = {"exercise", "movement", "fitness"}


class WellnessFulfiller(L2Fulfiller):
    """L2 fulfiller for HEALTH_WELLNESS wishes — wellness activity recommendations.

    Uses keyword matching to narrow down the 18-activity catalog, then applies
    PersonalityFilter for scoring and ranking. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match tag categories from wish text
        matched_categories = _match_categories(wish.wish_text)

        # 2. Filter catalog to items that have at least one matching tag
        if matched_categories:
            matched_set = set(matched_categories)
            candidates = [
                dict(item) for item in WELLNESS_CATALOG
                if matched_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in WELLNESS_CATALOG]

        # 3. If filtering left nothing, fall back to full catalog
        if not candidates:
            candidates = [dict(item) for item in WELLNESS_CATALOG]

        # 4. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        # 5. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        # 6. Determine if map data is needed (physical activities)
        rec_tags = set()
        for r in recommendations:
            rec_tags.update(r.tags)
        map_data = (
            MapData(place_type="gym", radius_km=5.0)
            if rec_tags & _PHYSICAL_TAGS
            else None
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=map_data,
            reminder_option=ReminderOption(
                text="Try this wellness activity today?",
                delay_hours=12,
            ),
        )


def _build_relevance_reason(item: dict, detector_results: DetectorResults) -> str:
    """Build a personalized relevance reason based on detector results."""
    parts: list[str] = []

    # Emotion-based reasons
    emotions = detector_results.emotion.get("emotions", {})
    anxiety = emotions.get("anxiety", 0.0)
    if anxiety > 0.5 and "calming" in item.get("tags", []):
        parts.append("Helps reduce anxiety with a calming approach")

    sadness = emotions.get("sadness", 0.0)
    if sadness > 0.5 and "emotions" in item.get("tags", []):
        parts.append("Supports emotional processing and healing")

    # Fragility-based reasons
    fragility_pattern = detector_results.fragility.get("pattern", "")
    if fragility_pattern == "avoidant" and "quiet" in item.get("tags", []):
        parts.append("Gentle activity you can do at your own pace")
    if fragility_pattern == "overwhelmed" and "self-paced" in item.get("tags", []):
        parts.append("Self-paced so you stay in control")

    # Attachment-based reasons
    attachment_style = detector_results.attachment.get("style", "")
    if attachment_style == "anxious" and "calming" in item.get("tags", []):
        parts.append("Calming practice to soothe attachment anxiety")

    if not parts:
        tags = item.get("tags", [])
        if "sleep" in tags:
            parts.append("Supports better sleep quality")
        elif "exercise" in tags:
            parts.append("Boosts mood through physical activity")
        elif "relaxation" in tags:
            parts.append("Promotes deep relaxation")
        elif "emotions" in tags:
            parts.append("Supports emotional well-being")
        elif "nutrition" in tags:
            parts.append("Nourishes body and mind")
        else:
            parts.append("Recommended for your wellness journey")

    return ". ".join(parts)
