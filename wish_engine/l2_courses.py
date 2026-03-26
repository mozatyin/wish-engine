"""CourseFulfiller — local-compute course recommendation with cognitive style matching.

27-course curated catalog across 9 topics. Zero LLM. Keyword matching
(English/Chinese/Arabic) routes wish text to relevant topics, then
PersonalityFilter scores and ranks candidates by MBTI cognitive style.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Course Catalog (27 entries) ──────────────────────────────────────────────

COURSE_CATALOG: list[dict] = [
    # psychology (3)
    {
        "title": "Introduction to Psychology",
        "description": "Comprehensive overview of psychological principles, from cognition to social behavior.",
        "category": "course",
        "topic": "psychology",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["psychology", "theory", "self-paced", "quiet"],
    },
    {
        "title": "Positive Psychology: Resilience Skills",
        "description": "Evidence-based techniques for building mental resilience and well-being.",
        "category": "course",
        "topic": "psychology",
        "format": "interactive",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["psychology", "practical", "self-paced", "calming"],
    },
    {
        "title": "Social Psychology",
        "description": "How other people influence our thoughts, feelings, and behavior.",
        "category": "course",
        "topic": "psychology",
        "format": "video",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["psychology", "theory", "social"],
    },
    # meditation (3)
    {
        "title": "Mindfulness Meditation for Beginners",
        "description": "Guided 8-week program to build a daily meditation practice from scratch.",
        "category": "course",
        "topic": "meditation",
        "format": "guided",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meditation", "practical", "self-paced", "calming", "quiet"],
    },
    {
        "title": "The Science of Meditation",
        "description": "Neuroscience research behind meditation, breathwork, and contemplative practices.",
        "category": "course",
        "topic": "meditation",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meditation", "theory", "self-paced", "quiet", "calming"],
    },
    {
        "title": "Yoga & Meditation Retreat Online",
        "description": "Live group sessions combining yoga flow with guided meditation.",
        "category": "course",
        "topic": "meditation",
        "format": "group",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["meditation", "practical", "social", "group", "calming"],
    },
    # programming (3)
    {
        "title": "Python for Everybody",
        "description": "Learn Python programming from zero — variables, loops, data structures, and web scraping.",
        "category": "course",
        "topic": "programming",
        "format": "interactive",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["programming", "practical", "self-paced", "quiet", "coding", "tech"],
    },
    {
        "title": "CS50: Introduction to Computer Science",
        "description": "Harvard's legendary intro CS course covering algorithms, data structures, and web development.",
        "category": "course",
        "topic": "programming",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["programming", "theory", "self-paced", "quiet", "coding", "tech"],
    },
    {
        "title": "Full-Stack Web Development Bootcamp",
        "description": "Intensive hands-on bootcamp: HTML, CSS, JavaScript, React, Node.js, and databases.",
        "category": "course",
        "topic": "programming",
        "format": "bootcamp",
        "noise": "moderate",
        "social": "medium",
        "mood": "intense",
        "tags": ["programming", "practical", "coding", "tech"],
    },
    # art (3)
    {
        "title": "Drawing Fundamentals",
        "description": "Master pencil sketching, shading, and perspective — no prior experience needed.",
        "category": "course",
        "topic": "art",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["art", "practical", "self-paced", "quiet", "calming"],
    },
    {
        "title": "Art History: Renaissance to Modern",
        "description": "Explore art movements, major works, and the ideas that shaped visual culture.",
        "category": "course",
        "topic": "art",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["art", "theory", "self-paced", "quiet"],
    },
    {
        "title": "Digital Illustration Workshop",
        "description": "Create digital art with Procreate and Photoshop in a collaborative workshop.",
        "category": "course",
        "topic": "art",
        "format": "group",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["art", "practical", "social", "group"],
    },
    # language (3)
    {
        "title": "Conversational English",
        "description": "Build everyday English speaking and listening confidence through practice dialogues.",
        "category": "course",
        "topic": "language",
        "format": "interactive",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["language", "practical", "social"],
    },
    {
        "title": "Arabic for Beginners",
        "description": "Learn Modern Standard Arabic — alphabet, grammar, and everyday phrases.",
        "category": "course",
        "topic": "language",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["language", "practical", "self-paced", "quiet"],
    },
    {
        "title": "Linguistics: The Science of Language",
        "description": "Understand phonetics, syntax, and semantics — how human language works.",
        "category": "course",
        "topic": "language",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["language", "theory", "self-paced", "quiet"],
    },
    # business (3)
    {
        "title": "Entrepreneurship Essentials",
        "description": "From idea validation to business model canvas — launch your first venture.",
        "category": "course",
        "topic": "business",
        "format": "interactive",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["business", "practical", "social"],
    },
    {
        "title": "Financial Literacy & Personal Finance",
        "description": "Budgeting, investing, and building wealth — practical money management skills.",
        "category": "course",
        "topic": "business",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["business", "practical", "self-paced", "quiet"],
    },
    {
        "title": "Behavioral Economics",
        "description": "How psychology shapes economic decisions — biases, nudges, and market behavior.",
        "category": "course",
        "topic": "business",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["business", "theory", "self-paced", "quiet"],
    },
    # wellness (3)
    {
        "title": "Sleep Science & Better Rest",
        "description": "Understand circadian rhythms and build habits for deeper, restorative sleep.",
        "category": "course",
        "topic": "wellness",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wellness", "practical", "self-paced", "calming", "quiet"],
    },
    {
        "title": "Nutrition Fundamentals",
        "description": "Evidence-based nutrition science — macros, micros, and meal planning.",
        "category": "course",
        "topic": "wellness",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wellness", "practical", "self-paced", "quiet"],
    },
    {
        "title": "Stress Management & Resilience",
        "description": "CBT and mindfulness techniques for managing stress and building emotional resilience.",
        "category": "course",
        "topic": "wellness",
        "format": "guided",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wellness", "practical", "self-paced", "calming", "quiet"],
    },
    # music (3)
    {
        "title": "Music Theory from Scratch",
        "description": "Notes, scales, chords, and harmony — the building blocks of music.",
        "category": "course",
        "topic": "music",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["music", "theory", "self-paced", "quiet"],
    },
    {
        "title": "Guitar for Beginners",
        "description": "Learn to play guitar — chords, strumming patterns, and your first songs.",
        "category": "course",
        "topic": "music",
        "format": "interactive",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["music", "practical", "self-paced"],
    },
    {
        "title": "Electronic Music Production",
        "description": "Create beats and tracks with Ableton — from sound design to full arrangements.",
        "category": "course",
        "topic": "music",
        "format": "interactive",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["music", "practical", "self-paced", "tech"],
    },
    # cooking (3)
    {
        "title": "Home Cooking Basics",
        "description": "Knife skills, sauces, and essential techniques for confident everyday cooking.",
        "category": "course",
        "topic": "cooking",
        "format": "video",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["cooking", "practical", "self-paced"],
    },
    {
        "title": "The Science of Cooking",
        "description": "Understand Maillard reactions, emulsification, and the chemistry behind great food.",
        "category": "course",
        "topic": "cooking",
        "format": "video",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cooking", "theory", "self-paced", "quiet"],
    },
    {
        "title": "World Cuisines: A Culinary Journey",
        "description": "Cook signature dishes from Italy, Japan, India, Mexico, and the Middle East.",
        "category": "course",
        "topic": "cooking",
        "format": "group",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["cooking", "practical", "social", "group"],
    },
]


# ── Keyword → Topic Mapping ─────────────────────────────────────────────────

_COURSE_KEYWORDS: dict[str, list[str]] = {
    # psychology
    "psychology": ["psychology"],
    "心理学": ["psychology"],
    "心理": ["psychology"],
    "علم النفس": ["psychology"],
    "نفسي": ["psychology"],
    # meditation
    "meditation": ["meditation"],
    "meditate": ["meditation"],
    "mindfulness": ["meditation"],
    "冥想": ["meditation"],
    "正念": ["meditation"],
    "تأمل": ["meditation"],
    # programming
    "programming": ["programming"],
    "coding": ["programming"],
    "code": ["programming"],
    "python": ["programming"],
    "编程": ["programming"],
    "代码": ["programming"],
    "برمجة": ["programming"],
    # art
    "art": ["art"],
    "drawing": ["art"],
    "painting": ["art"],
    "illustration": ["art"],
    "绘画": ["art"],
    "画画": ["art"],
    "美术": ["art"],
    "رسم": ["art"],
    "فن": ["art"],
    # language
    "language": ["language"],
    "english": ["language"],
    "arabic": ["language"],
    "语言": ["language"],
    "英语": ["language"],
    "لغة": ["language"],
    # business
    "business": ["business"],
    "entrepreneurship": ["business"],
    "finance": ["business"],
    "创业": ["business"],
    "理财": ["business"],
    "商业": ["business"],
    "أعمال": ["business"],
    "مالية": ["business"],
    # wellness
    "wellness": ["wellness"],
    "health": ["wellness"],
    "sleep": ["wellness"],
    "stress": ["wellness"],
    "nutrition": ["wellness"],
    "健康": ["wellness"],
    "睡眠": ["wellness"],
    "压力": ["wellness"],
    "营养": ["wellness"],
    "صحة": ["wellness"],
    # music
    "music": ["music"],
    "guitar": ["music"],
    "piano": ["music"],
    "音乐": ["music"],
    "吉他": ["music"],
    "موسيقى": ["music"],
    # cooking
    "cooking": ["cooking"],
    "cook": ["cooking"],
    "cuisine": ["cooking"],
    "baking": ["cooking"],
    "做饭": ["cooking"],
    "烹饪": ["cooking"],
    "烘焙": ["cooking"],
    "طبخ": ["cooking"],
    # broad / learning wishes
    "learn": ["psychology", "programming", "language"],
    "学": ["psychology", "programming", "language"],
    "تعلم": ["psychology", "programming", "language"],
    "course": ["psychology", "business", "programming"],
    "课程": ["psychology", "business", "programming"],
    "دورة": ["psychology", "business", "programming"],
}


def _match_topics(wish_text: str) -> dict[str, int]:
    """Extract matching course topics from wish text via keyword lookup.

    Returns dict mapping topic -> match count. Topics matched by more
    keywords are considered more relevant. If no keywords match,
    returns empty dict (caller should fall back to full catalog).
    """
    text_lower = wish_text.lower()
    counts: dict[str, int] = {}
    for keyword, topics in _COURSE_KEYWORDS.items():
        if keyword in text_lower:
            for topic in topics:
                counts[topic] = counts.get(topic, 0) + 1
    return counts


def _build_relevance_reason(course: dict, detector_results: DetectorResults) -> str:
    """Build a personalized relevance reason based on detector results."""
    parts: list[str] = []

    mbti_type = detector_results.mbti.get("type", "")
    if len(mbti_type) == 4:
        if mbti_type[1] == "N" and "theory" in course.get("tags", []):
            parts.append("Matches your intuitive, theory-oriented learning style")
        elif mbti_type[1] == "S" and "practical" in course.get("tags", []):
            parts.append("Matches your practical, hands-on learning style")
        if mbti_type[0] == "I" and "self-paced" in course.get("tags", []):
            parts.append("Self-paced format suits your independent study preference")

    top_values = detector_results.values.get("top_values", [])
    if top_values:
        tags = set(course.get("tags", []))
        if "self-direction" in top_values and "self-paced" in tags:
            parts.append("Supports your self-directed learning style")
        if "benevolence" in top_values and "social" in tags:
            parts.append("Collaborative format aligns with your social values")

    if not parts:
        topic = course.get("topic", "learning")
        parts.append(f"A highly-rated course on {topic}")

    return ". ".join(parts)


class CourseFulfiller(L2Fulfiller):
    """L2 fulfiller for LEARN_SKILL wishes — course recommendations.

    Uses keyword matching to narrow down the 27-course catalog, then applies
    PersonalityFilter for MBTI cognitive style scoring and ranking. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match topics from wish text (topic -> keyword hit count)
        topic_counts = _match_topics(wish.wish_text)

        # 2. Filter catalog to matched topics (or use full catalog)
        if topic_counts:
            candidates = [
                dict(c) for c in COURSE_CATALOG
                if c["topic"] in topic_counts
            ]
        else:
            candidates = [dict(c) for c in COURSE_CATALOG]

        # 3. If filtering left nothing, fall back to full catalog
        if not candidates:
            candidates = [dict(c) for c in COURSE_CATALOG]

        # 4. Add personalized relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        # 5. Sort candidates by topic relevance (more keyword hits = first)
        #    Stable sort ensures personality filter tie-breaking favors relevant topics
        if topic_counts:
            candidates.sort(
                key=lambda c: topic_counts.get(c["topic"], 0),
                reverse=True,
            )

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=None,
            reminder_option=ReminderOption(
                text="Start this course this week?",
                delay_hours=48,
            ),
        )
