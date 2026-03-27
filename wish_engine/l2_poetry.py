"""PoetryFulfiller — emotion & culture-matched poetry recommendations.

20-category curated catalog spanning world poetry traditions with emotion-based
and culture-based personality mapping. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Emotion → Poetry Category Mapping ────────────────────────────────────────

EMOTION_POETRY_MAP: dict[str, list[str]] = {
    "sadness": ["grief_poetry", "hope_poetry"],
    "anger": ["protest", "war_poetry"],
    "joy": ["love_poetry", "nature_poetry", "funny_poetry"],
    "anxiety": ["spiritual", "nature_poetry", "hope_poetry"],
    "fear": ["hope_poetry", "spiritual"],
    "love": ["love_poetry", "sufi_poetry"],
    "contempt": ["protest", "philosophical"],
    "surprise": ["modern_verse", "funny_poetry"],
}

# ── Culture → Poetry Category Mapping ────────────────────────────────────────

CULTURE_POETRY_MAP: dict[str, list[str]] = {
    "arab": ["arabic_classical", "sufi_poetry"],
    "chinese": ["chinese_tang"],
    "japanese": ["japanese_haiku"],
    "western": ["english_romantic", "modern_verse"],
    "indian": ["sufi_poetry", "spiritual"],
    "persian": ["sufi_poetry", "philosophical"],
}

# ── Poetry Catalog (20 entries) ──────────────────────────────────────────────

POETRY_CATALOG: list[dict] = [
    {
        "title": "Arabic Classical Poetry Collection",
        "description": "Pre-Islamic odes to Abbasid masterpieces — Al-Mutanabbi, Imru' al-Qais, and more.",
        "category": "arabic_classical",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["arabic_classical", "traditional", "heritage", "spiritual"],
    },
    {
        "title": "Tang Dynasty Poetry Anthology",
        "description": "Li Bai, Du Fu, Wang Wei — the golden age of Chinese poetry.",
        "category": "chinese_tang",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["chinese_tang", "traditional", "heritage", "nature"],
    },
    {
        "title": "Japanese Haiku Collection",
        "description": "Bashō, Issa, Buson — capturing seasons and moments in 17 syllables.",
        "category": "japanese_haiku",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["japanese_haiku", "nature", "quiet", "traditional"],
    },
    {
        "title": "English Romantic Poetry",
        "description": "Keats, Shelley, Byron, Wordsworth — nature, beauty, and the sublime.",
        "category": "english_romantic",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["english_romantic", "nature", "love", "traditional"],
    },
    {
        "title": "Sufi Poetry & Mystic Verse",
        "description": "Rumi, Hafiz, Ibn Arabi — divine love and spiritual ecstasy.",
        "category": "sufi_poetry",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["sufi_poetry", "spiritual", "love", "traditional", "heritage"],
    },
    {
        "title": "Modern & Contemporary Verse",
        "description": "From the Beats to slam poetry — fresh voices breaking boundaries.",
        "category": "modern_verse",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["modern_verse", "social", "theory"],
    },
    {
        "title": "Love Poetry Through the Ages",
        "description": "From Sappho to Neruda — the universal language of love in verse.",
        "category": "love_poetry",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["love_poetry", "love", "calming"],
    },
    {
        "title": "Nature Poetry & Pastoral Verse",
        "description": "Celebrating the natural world — forests, rivers, seasons, and stars.",
        "category": "nature_poetry",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["nature_poetry", "nature", "calming", "quiet"],
    },
    {
        "title": "Grief & Elegiac Poetry",
        "description": "Poems of loss, mourning, and remembrance — finding words for the unspeakable.",
        "category": "grief_poetry",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["grief_poetry", "calming", "helping"],
    },
    {
        "title": "Poetry of Hope & Resilience",
        "description": "Verses that lift the spirit — from Maya Angelou to Mahmoud Darwish.",
        "category": "hope_poetry",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["hope_poetry", "calming", "helping", "spiritual"],
    },
    {
        "title": "Rage & Anger in Verse",
        "description": "Poetry that channels fury into art — raw, honest, transformative.",
        "category": "anger_poetry",
        "noise": "moderate",
        "social": "low",
        "mood": "intense",
        "tags": ["anger_poetry", "protest"],
    },
    {
        "title": "Wisdom Poetry & Aphorisms",
        "description": "Omar Khayyam, Khalil Gibran, Mary Oliver — timeless wisdom in verse.",
        "category": "wisdom_poetry",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wisdom_poetry", "traditional", "spiritual", "theory"],
    },
    {
        "title": "Humorous & Light Verse",
        "description": "Ogden Nash, Shel Silverstein, Edward Lear — poetry that makes you smile.",
        "category": "funny_poetry",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["funny_poetry", "social"],
    },
    {
        "title": "Philosophical Poetry",
        "description": "Existential musings — T.S. Eliot, Borges, Szymborska, and beyond.",
        "category": "philosophical",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["philosophical", "theory", "quiet"],
    },
    {
        "title": "War Poetry & Witness Verse",
        "description": "Wilfred Owen, Yusef Komunyakaa — bearing witness through poetry.",
        "category": "war_poetry",
        "noise": "quiet",
        "social": "low",
        "mood": "intense",
        "tags": ["war_poetry", "protest"],
    },
    {
        "title": "Spiritual & Sacred Poetry",
        "description": "Psalms, Bhakti verse, Sufi qawwali — the divine expressed in words.",
        "category": "spiritual",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["spiritual", "traditional", "heritage", "calming"],
    },
    {
        "title": "Feminist Poetry & Women's Voices",
        "description": "Audre Lorde, Adrienne Rich, Forough Farrokhzad — fierce and fearless.",
        "category": "feminist",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["feminist", "protest", "social"],
    },
    {
        "title": "Indigenous Poetry & Oral Traditions",
        "description": "First Nations, Aboriginal, Native voices — poetry rooted in land and ancestry.",
        "category": "indigenous",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["indigenous", "traditional", "heritage", "nature"],
    },
    {
        "title": "Protest Poetry & Spoken Word",
        "description": "From the Harlem Renaissance to modern slam — poetry as resistance.",
        "category": "protest",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["protest", "social"],
    },
    {
        "title": "Children's Poetry & Nursery Rhymes",
        "description": "Playful verse for young readers — rhythm, rhyme, and imagination.",
        "category": "children",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["children", "practical"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_POETRY_KEYWORDS: dict[str, list[str]] = {
    "诗": ["poetry"],
    "poetry": ["poetry"],
    "poem": ["poetry"],
    "文学": ["poetry", "traditional"],
    "literature": ["poetry", "traditional"],
    "شعر": ["poetry", "arabic_classical"],
    "rumi": ["sufi_poetry", "spiritual"],
    "haiku": ["japanese_haiku"],
    "唐诗": ["chinese_tang"],
    "sonnets": ["english_romantic"],
    "sonnet": ["english_romantic"],
    "grief": ["grief_poetry"],
    "hope": ["hope_poetry"],
    "love poem": ["love_poetry"],
    "nature poem": ["nature_poetry"],
    "protest": ["protest"],
    "wisdom": ["wisdom_poetry"],
    "funny poem": ["funny_poetry"],
    "spiritual": ["spiritual"],
    "feminist": ["feminist"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _POETRY_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _emotion_to_poetry_tags(emotions: dict) -> list[str]:
    """Map user's detected emotions to poetry categories."""
    tags: list[str] = []
    for emotion, score in emotions.items():
        if score > 0.3:
            for tag in EMOTION_POETRY_MAP.get(emotion, []):
                if tag not in tags:
                    tags.append(tag)
    return tags


def _culture_to_poetry_tags(culture: str) -> list[str]:
    """Map user's culture to poetry categories."""
    return CULTURE_POETRY_MAP.get(culture, [])


def _build_relevance_reason(item: dict, emotions: dict, culture: str) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")
    tags = set(item.get("tags", []))

    # Emotion-based reasons
    if emotions.get("sadness", 0) > 0.3 and category in ("grief_poetry", "hope_poetry"):
        return "Poetry to hold space for what you're feeling"
    if emotions.get("anger", 0) > 0.3 and category in ("protest", "war_poetry"):
        return "Channel your fire into powerful verse"
    if emotions.get("joy", 0) > 0.3 and "love" in tags:
        return "Beautiful verse to match your radiant mood"

    # Culture-based reasons
    culture_reasons = {
        "arabic_classical": "Reconnect with the rich tradition of Arabic poetry",
        "chinese_tang": "Timeless verses from the golden age of Chinese literature",
        "japanese_haiku": "Find beauty in simplicity with haiku masters",
        "sufi_poetry": "Mystical verse to nourish your soul",
        "english_romantic": "Classic poetry celebrating nature and emotion",
    }
    if category in culture_reasons:
        return culture_reasons[category]

    return "Poetry chosen to resonate with your soul"


class PoetryFulfiller(L2Fulfiller):
    """L2 fulfiller for poetry/literature wishes — emotion & culture-aware.

    Uses keyword matching + emotion→poetry + culture→poetry mapping to select
    from 20-category catalog, then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Add emotion-based categories
        emotions = detector_results.emotion.get("emotions", {})
        emotion_tags = _emotion_to_poetry_tags(emotions)

        # 3. Add culture-based categories
        culture = detector_results.values.get("culture", "")
        culture_tags = _culture_to_poetry_tags(culture)

        all_tags = list(matched_categories)
        for t in emotion_tags + culture_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 4. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in POETRY_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in POETRY_CATALOG]

        # 5. Fallback
        if not candidates:
            candidates = [dict(item) for item in POETRY_CATALOG]

        # 6. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, emotions, culture)

        # 7. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New poetry picks await — come back for fresh inspiration!",
                delay_hours=24,
            ),
        )
