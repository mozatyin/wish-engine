"""BookFulfiller — local-compute book recommendation with personality filtering.

32-book curated catalog across 11 topics. Zero LLM. Keyword matching
(English/Chinese/Arabic) routes wish text to relevant topics, then
PersonalityFilter scores and ranks candidates.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Book Catalog (32 entries) ────────────────────────────────────────────────

BOOK_CATALOG: list[dict] = [
    # attachment (3)
    {
        "title": "Attached",
        "author": "Amir Levine & Rachel Heller",
        "description": "Science of adult attachment and how it shapes relationships.",
        "category": "book",
        "topic": "attachment",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["attachment", "relationships", "practical", "calming"],
    },
    {
        "title": "Hold Me Tight",
        "author": "Sue Johnson",
        "description": "Emotionally focused therapy conversations for deeper bonds.",
        "category": "book",
        "topic": "attachment",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["attachment", "relationships", "theory", "calming", "quiet"],
    },
    {
        "title": "Wired for Love",
        "author": "Stan Tatkin",
        "description": "Neuroscience-based guide for creating secure relationships.",
        "category": "book",
        "topic": "attachment",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["attachment", "relationships", "practical", "quiet"],
    },
    # meditation / mindfulness (3)
    {
        "title": "Wherever You Go, There You Are",
        "author": "Jon Kabat-Zinn",
        "description": "Mindfulness meditation for everyday life.",
        "category": "book",
        "topic": "meditation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meditation", "mindfulness", "practical", "calming", "quiet"],
    },
    {
        "title": "The Miracle of Mindfulness",
        "author": "Thich Nhat Hanh",
        "description": "A gentle introduction to meditation from a Zen master.",
        "category": "book",
        "topic": "meditation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meditation", "mindfulness", "traditional", "calming", "quiet"],
    },
    {
        "title": "Radical Acceptance",
        "author": "Tara Brach",
        "description": "Embracing your life with Buddhist psychology and meditation.",
        "category": "book",
        "topic": "meditation",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["meditation", "mindfulness", "traditional", "calming", "quiet", "self-paced"],
    },
    # psychology (3)
    {
        "title": "Thinking, Fast and Slow",
        "author": "Daniel Kahneman",
        "description": "Two systems that drive the way we think and decide.",
        "category": "book",
        "topic": "psychology",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["psychology", "theory", "quiet", "calming"],
    },
    {
        "title": "The Body Keeps the Score",
        "author": "Bessel van der Kolk",
        "description": "How trauma reshapes the body and brain, and paths to recovery.",
        "category": "book",
        "topic": "psychology",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["psychology", "theory", "calming", "quiet"],
    },
    {
        "title": "Emotional Intelligence",
        "author": "Daniel Goleman",
        "description": "Why EQ matters more than IQ for success and well-being.",
        "category": "book",
        "topic": "psychology",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["psychology", "practical", "calming", "quiet"],
    },
    # conflict (3)
    {
        "title": "Nonviolent Communication",
        "author": "Marshall B. Rosenberg",
        "description": "A language of compassion for resolving conflicts peacefully.",
        "category": "book",
        "topic": "conflict",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["conflict", "relationships", "practical", "calming", "quiet"],
    },
    {
        "title": "Crucial Conversations",
        "author": "Kerry Patterson et al.",
        "description": "Tools for talking when stakes are high and emotions run strong.",
        "category": "book",
        "topic": "conflict",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["conflict", "practical", "calming"],
    },
    {
        "title": "Difficult Conversations",
        "author": "Douglas Stone et al.",
        "description": "Harvard Negotiation Project methods for the hardest talks.",
        "category": "book",
        "topic": "conflict",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["conflict", "practical", "theory", "calming", "quiet"],
    },
    # relationships (3)
    {
        "title": "The Seven Principles for Making Marriage Work",
        "author": "John Gottman",
        "description": "Research-backed strategies for lasting relationships.",
        "category": "book",
        "topic": "relationships",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["relationships", "practical", "calming", "quiet"],
    },
    {
        "title": "The Five Love Languages",
        "author": "Gary Chapman",
        "description": "Discover how you and your partner express and receive love.",
        "category": "book",
        "topic": "relationships",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["relationships", "practical", "calming", "traditional"],
    },
    {
        "title": "Mating in Captivity",
        "author": "Esther Perel",
        "description": "Balancing intimacy and desire in long-term relationships.",
        "category": "book",
        "topic": "relationships",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["relationships", "theory", "calming", "quiet"],
    },
    # growth (3)
    {
        "title": "Mindset",
        "author": "Carol S. Dweck",
        "description": "How a growth mindset unlocks potential in every area of life.",
        "category": "book",
        "topic": "growth",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["growth", "practical", "calming", "quiet"],
    },
    {
        "title": "Atomic Habits",
        "author": "James Clear",
        "description": "Tiny changes, remarkable results — a system for building good habits.",
        "category": "book",
        "topic": "growth",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["growth", "practical", "calming", "self-paced"],
    },
    {
        "title": "The Power of Now",
        "author": "Eckhart Tolle",
        "description": "A guide to spiritual enlightenment through present-moment awareness.",
        "category": "book",
        "topic": "growth",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["growth", "mindfulness", "traditional", "calming", "quiet"],
    },
    # career (3)
    {
        "title": "Designing Your Life",
        "author": "Bill Burnett & Dave Evans",
        "description": "Apply design thinking to build a joyful, fulfilling career.",
        "category": "book",
        "topic": "career",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["career", "practical", "calming", "self-paced"],
    },
    {
        "title": "So Good They Can't Ignore You",
        "author": "Cal Newport",
        "description": "Why skills trump passion in the quest for work you love.",
        "category": "book",
        "topic": "career",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["career", "practical", "calming", "quiet"],
    },
    {
        "title": "Range",
        "author": "David Epstein",
        "description": "Why generalists triumph in a specialized world.",
        "category": "book",
        "topic": "career",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["career", "theory", "calming", "quiet"],
    },
    # anxiety (3)
    {
        "title": "Feeling Good",
        "author": "David D. Burns",
        "description": "Clinically proven CBT techniques for overcoming depression and anxiety.",
        "category": "book",
        "topic": "anxiety",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["anxiety", "practical", "calming", "quiet", "self-paced"],
    },
    {
        "title": "Dare",
        "author": "Barry McDonagh",
        "description": "A breakthrough approach to ending anxiety and panic attacks.",
        "category": "book",
        "topic": "anxiety",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["anxiety", "practical", "calming", "quiet"],
    },
    {
        "title": "The Anxiety and Phobia Workbook",
        "author": "Edmund J. Bourne",
        "description": "Step-by-step exercises for managing anxiety and phobias.",
        "category": "book",
        "topic": "anxiety",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["anxiety", "practical", "calming", "self-paced", "quiet"],
    },
    # wellness (3)
    {
        "title": "Why We Sleep",
        "author": "Matthew Walker",
        "description": "The science of sleep and how it transforms health and performance.",
        "category": "book",
        "topic": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wellness", "theory", "calming", "quiet"],
    },
    {
        "title": "Breath",
        "author": "James Nestor",
        "description": "The science of breathing and its impact on health and well-being.",
        "category": "book",
        "topic": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wellness", "practical", "calming", "quiet"],
    },
    {
        "title": "The Upside of Stress",
        "author": "Kelly McGonigal",
        "description": "How to harness stress as a positive force for growth.",
        "category": "book",
        "topic": "wellness",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wellness", "practical", "calming", "quiet", "growth"],
    },
    # creativity (3)
    {
        "title": "The Artist's Way",
        "author": "Julia Cameron",
        "description": "A 12-week program to recover and nurture your creative self.",
        "category": "book",
        "topic": "creativity",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creativity", "practical", "self-paced", "calming", "quiet"],
    },
    {
        "title": "Big Magic",
        "author": "Elizabeth Gilbert",
        "description": "Creative living beyond fear — embrace curiosity over courage.",
        "category": "book",
        "topic": "creativity",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creativity", "calming", "quiet"],
    },
    {
        "title": "Steal Like an Artist",
        "author": "Austin Kleon",
        "description": "10 things nobody told you about being creative.",
        "category": "book",
        "topic": "creativity",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creativity", "practical", "calming", "quiet"],
    },
    # philosophy (2)
    {
        "title": "Meditations",
        "author": "Marcus Aurelius",
        "description": "Timeless Stoic reflections on life, duty, and inner peace.",
        "category": "book",
        "topic": "philosophy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["philosophy", "traditional", "calming", "quiet", "theory"],
    },
    {
        "title": "Man's Search for Meaning",
        "author": "Viktor E. Frankl",
        "description": "Finding purpose even in the darkest circumstances.",
        "category": "book",
        "topic": "philosophy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["philosophy", "traditional", "calming", "quiet", "growth"],
    },
]


# ── Keyword → Topic Mapping ─────────────────────────────────────────────────

_BOOK_KEYWORDS: dict[str, list[str]] = {
    # attachment
    "attachment": ["attachment"],
    "依恋": ["attachment"],
    "依附": ["attachment"],
    "تعلق": ["attachment"],
    # meditation / mindfulness
    "meditation": ["meditation"],
    "meditate": ["meditation"],
    "mindfulness": ["meditation"],
    "冥想": ["meditation"],
    "正念": ["meditation"],
    "تأمل": ["meditation"],
    # psychology
    "psychology": ["psychology"],
    "心理学": ["psychology"],
    "心理": ["psychology"],
    "علم النفس": ["psychology"],
    "نفسي": ["psychology"],
    # conflict
    "conflict": ["conflict"],
    "冲突": ["conflict"],
    "吵架": ["conflict"],
    "صراع": ["conflict"],
    "خلاف": ["conflict"],
    # relationships
    "relationship": ["relationships"],
    "relationships": ["relationships"],
    "marriage": ["relationships"],
    "love": ["relationships"],
    "关系": ["relationships"],
    "婚姻": ["relationships"],
    "恋爱": ["relationships"],
    "علاقة": ["relationships"],
    "حب": ["relationships"],
    "زواج": ["relationships"],
    # growth
    "growth": ["growth"],
    "habit": ["growth"],
    "habits": ["growth"],
    "成长": ["growth"],
    "习惯": ["growth"],
    "نمو": ["growth"],
    "عادات": ["growth"],
    # career
    "career": ["career"],
    "job": ["career"],
    "work": ["career"],
    "职业": ["career"],
    "工作": ["career"],
    "مهنة": ["career"],
    "وظيفة": ["career"],
    # anxiety
    "anxiety": ["anxiety"],
    "anxious": ["anxiety"],
    "panic": ["anxiety"],
    "焦虑": ["anxiety"],
    "恐慌": ["anxiety"],
    "قلق": ["anxiety"],
    # wellness
    "wellness": ["wellness"],
    "health": ["wellness"],
    "sleep": ["wellness"],
    "stress": ["wellness"],
    "breathing": ["wellness"],
    "健康": ["wellness"],
    "睡眠": ["wellness"],
    "压力": ["wellness"],
    "صحة": ["wellness"],
    "نوم": ["wellness"],
    # creativity
    "creativity": ["creativity"],
    "creative": ["creativity"],
    "art": ["creativity"],
    "创造": ["creativity"],
    "创意": ["creativity"],
    "إبداع": ["creativity"],
    # philosophy
    "philosophy": ["philosophy"],
    "meaning": ["philosophy"],
    "stoic": ["philosophy"],
    "哲学": ["philosophy"],
    "意义": ["philosophy"],
    "فلسفة": ["philosophy"],
    # broad / book-reading wishes
    "book": ["psychology", "growth", "philosophy"],
    "书": ["psychology", "growth", "philosophy"],
    "读": ["psychology", "growth", "philosophy"],
    "كتاب": ["psychology", "growth", "philosophy"],
}


def _match_topics(wish_text: str) -> list[str]:
    """Extract matching book topics from wish text via keyword lookup.

    Returns deduplicated list of topic strings. If no keywords match,
    returns empty list (caller should fall back to full catalog).
    """
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, topics in _BOOK_KEYWORDS.items():
        if keyword in text_lower:
            for topic in topics:
                if topic not in matched:
                    matched.append(topic)
    return matched


def _build_relevance_reason(book: dict, detector_results: DetectorResults) -> str:
    """Build a personalized relevance reason based on detector results.

    Mentions attachment style, values, or MBTI when available.
    """
    parts: list[str] = []

    attachment_style = detector_results.attachment.get("style", "")
    if attachment_style and book["topic"] == "attachment":
        parts.append(f"Especially relevant for your {attachment_style} attachment style")

    top_values = detector_results.values.get("top_values", [])
    if top_values:
        tags = set(book.get("tags", []))
        if "tradition" in top_values and "traditional" in tags:
            parts.append("Aligns with your traditional values")
        if "self-direction" in top_values and "self-paced" in tags:
            parts.append("Supports your self-directed learning style")
        if "benevolence" in top_values and "relationships" in tags:
            parts.append("Resonates with your care for relationships")

    mbti_type = detector_results.mbti.get("type", "")
    if len(mbti_type) == 4:
        if mbti_type[1] == "N" and "theory" in book.get("tags", []):
            parts.append("Matches your intuitive, theory-oriented thinking")
        elif mbti_type[1] == "S" and "practical" in book.get("tags", []):
            parts.append("Matches your practical, hands-on approach")

    if not parts:
        topic = book.get("topic", "growth")
        parts.append(f"A well-regarded resource on {topic}")

    return ". ".join(parts)


class BookFulfiller(L2Fulfiller):
    """L2 fulfiller for FIND_RESOURCE wishes — book recommendations.

    Uses keyword matching to narrow down the 32-book catalog, then applies
    PersonalityFilter for scoring and ranking. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match topics from wish text
        matched_topics = _match_topics(wish.wish_text)

        # 2. Filter catalog to matched topics (or use full catalog)
        if matched_topics:
            candidates = [
                dict(b) for b in BOOK_CATALOG
                if b["topic"] in matched_topics
            ]
        else:
            candidates = [dict(b) for b in BOOK_CATALOG]

        # 3. If filtering left nothing, fall back to full catalog
        if not candidates:
            candidates = [dict(b) for b in BOOK_CATALOG]

        # 4. Add personalized relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        # 5. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=None,
            reminder_option=ReminderOption(
                text="Start reading this book this week?",
                delay_hours=72,
            ),
        )
