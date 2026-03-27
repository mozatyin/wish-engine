"""DocumentaryFulfiller — emotion-matched documentary recommendations.

15-genre curated catalog with emotion-based routing: curious→science,
inspired→biography, anxious→nature. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Emotion → Genre Mapping ──────────────────────────────────────────────────

EMOTION_GENRE_MAP: dict[str, list[str]] = {
    "curious": ["science", "technology", "space", "psychology"],
    "inspired": ["social_justice", "sports", "history"],
    "anxious": ["nature", "art", "food"],
    "sad": ["music", "philosophy", "culture"],
    "bored": ["true_crime", "sports", "environment"],
    "joyful": ["food", "music", "culture"],
}

# ── Documentary Catalog (15 entries) ─────────────────────────────────────────

DOCUMENTARY_CATALOG: list[dict] = [
    {
        "title": "Nature & Wildlife Documentaries",
        "description": "Planet Earth, Blue Planet, and more — breathtaking footage of the natural world.",
        "category": "nature",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nature", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Science Frontiers",
        "description": "Quantum physics, neuroscience, and the cutting edge — expand your mind.",
        "category": "science",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["science", "quiet", "calming", "theory", "self-paced"],
    },
    {
        "title": "History Uncovered",
        "description": "Ancient civilizations, world wars, and forgotten stories — history brought to life.",
        "category": "history",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["history", "quiet", "calming", "traditional", "theory"],
    },
    {
        "title": "Social Justice Stories",
        "description": "Powerful stories of change — civil rights, activism, and human resilience.",
        "category": "social_justice",
        "noise": "quiet",
        "social": "low",
        "mood": "intense",
        "tags": ["social_justice", "theory", "helping"],
    },
    {
        "title": "Music Documentaries",
        "description": "Behind the music — artist stories, live recordings, and musical journeys.",
        "category": "music",
        "noise": "moderate",
        "social": "low",
        "mood": "calming",
        "tags": ["music", "calming", "self-paced"],
    },
    {
        "title": "Art & Design Films",
        "description": "Painters, architects, and designers — creative minds and their masterworks.",
        "category": "art",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["art", "quiet", "calming", "theory"],
    },
    {
        "title": "Food & Cuisine Journeys",
        "description": "Street food, fine dining, and culinary traditions from around the world.",
        "category": "food",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["food", "calming", "traditional", "self-paced"],
    },
    {
        "title": "Technology & Innovation",
        "description": "AI, space tech, and digital futures — how technology shapes our world.",
        "category": "technology",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["technology", "quiet", "calming", "theory", "self-paced"],
    },
    {
        "title": "Psychology & Human Behavior",
        "description": "Why we do what we do — cognitive biases, social experiments, and the mind.",
        "category": "psychology",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["psychology", "quiet", "calming", "theory"],
    },
    {
        "title": "True Crime Investigations",
        "description": "Unsolved cases, forensic breakthroughs, and courtroom drama.",
        "category": "true_crime",
        "noise": "quiet",
        "social": "low",
        "mood": "intense",
        "tags": ["true_crime", "quiet", "self-paced"],
    },
    {
        "title": "Sports Legends & Stories",
        "description": "Athletic feats, underdog stories, and the spirit of competition.",
        "category": "sports",
        "noise": "moderate",
        "social": "medium",
        "mood": "intense",
        "tags": ["sports", "social", "adventure"],
    },
    {
        "title": "Environment & Climate",
        "description": "Climate change, ocean conservation, and sustainability — urgent stories of our time.",
        "category": "environment",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["environment", "quiet", "calming", "helping"],
    },
    {
        "title": "Space & Astronomy",
        "description": "Black holes, Mars missions, and the cosmos — explore the universe from your couch.",
        "category": "space",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["space", "quiet", "calming", "theory", "self-paced"],
    },
    {
        "title": "Philosophy & Big Questions",
        "description": "Free will, consciousness, and meaning — documentaries that make you think.",
        "category": "philosophy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["philosophy", "quiet", "calming", "theory"],
    },
    {
        "title": "World Cultures & Traditions",
        "description": "Rituals, festivals, and daily life — diverse cultures explored with respect.",
        "category": "culture",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["culture", "quiet", "calming", "traditional"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_DOC_KEYWORDS: dict[str, list[str]] = {
    "纪录片": ["documentary"],
    "documentary": ["documentary"],
    "وثائقي": ["documentary"],
    "film": ["documentary"],
    "doc": ["documentary"],
    "nature": ["nature"],
    "自然": ["nature"],
    "science": ["science"],
    "科学": ["science"],
    "history": ["history"],
    "历史": ["history"],
    "true crime": ["true_crime"],
    "犯罪": ["true_crime"],
    "space": ["space"],
    "太空": ["space"],
    "宇宙": ["space"],
    "psychology": ["psychology"],
    "心理": ["psychology"],
    "food": ["food"],
    "美食": ["food"],
    "music": ["music"],
    "音乐": ["music"],
    "art": ["art"],
    "艺术": ["art"],
    "technology": ["technology"],
    "科技": ["technology"],
    "philosophy": ["philosophy"],
    "哲学": ["philosophy"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _DOC_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _emotion_to_genre_tags(emotions: dict) -> list[str]:
    """Map dominant emotion to preferred documentary genres."""
    if not emotions:
        return []
    # Find dominant emotion
    dominant = max(emotions, key=emotions.get, default=None)
    if dominant:
        return EMOTION_GENRE_MAP.get(dominant, [])
    return []


def _build_relevance_reason(item: dict, dominant_emotion: str) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")

    if dominant_emotion:
        emotion_reasons = {
            ("curious", "science"): "Feed your curiosity with cutting-edge science",
            ("curious", "technology"): "Explore the innovations shaping our future",
            ("anxious", "nature"): "Let nature calm your mind",
            ("inspired", "social_justice"): "Stories of change to fuel your inspiration",
            ("sad", "music"): "Music stories that heal and connect",
        }
        key = (dominant_emotion, category)
        if key in emotion_reasons:
            return emotion_reasons[key]

    reason_map = {
        "nature": "Breathtaking footage of the natural world",
        "science": "Expand your mind with the latest discoveries",
        "history": "Understand the present through the past",
        "social_justice": "Powerful stories of human resilience",
        "music": "Behind the music you love",
        "art": "Creative minds and their masterworks",
        "food": "A delicious journey around the world",
        "technology": "How innovation shapes tomorrow",
        "psychology": "Understand why we do what we do",
        "true_crime": "Gripping investigations and mysteries",
        "sports": "Stories of grit and glory",
        "environment": "Our planet's most urgent stories",
        "space": "Explore the cosmos from your couch",
        "philosophy": "Big questions that make you think",
        "culture": "Diverse traditions and perspectives",
    }
    return reason_map.get(category, "A great documentary picked for you")


class DocumentaryFulfiller(L2Fulfiller):
    """L2 fulfiller for documentary wishes — emotion-matched recommendations.

    Uses keyword matching + emotion→genre mapping to select from 15-genre catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Add emotion-based genre preferences
        emotions = detector_results.emotion.get("emotions", {})
        emotion_tags = _emotion_to_genre_tags(emotions)
        dominant_emotion = max(emotions, key=emotions.get, default="") if emotions else ""

        all_tags = list(matched_categories)
        for t in emotion_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in DOCUMENTARY_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in DOCUMENTARY_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in DOCUMENTARY_CATALOG]

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, dominant_emotion)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New documentary picks every week — check back!",
                delay_hours=72,
            ),
        )
