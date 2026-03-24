"""SoulGraph Adapter — converts SoulItem data into Wish Engine format.

Bridges the gap between SoulGraph's SoulItem and Wish Engine's detector.
Provides the structured detection path (Path A) that reads metadata
instead of doing regex on text.
"""

from __future__ import annotations

from typing import Any

from wish_engine.models import DetectedWish, WishType


# ── Intention recognition from SoulItem metadata ────────────────────────────

_INTENTION_TAGS = {"intention", "desire", "need", "aspiration", "goal"}
_INTENTION_DOMAINS = {"intention", "ambition"}  # "ambition" also signals desire
_NON_INTENTION_TAGS = {"fact", "symptom", "preference", "behavior", "story", "trait", "belief", "value"}

# Text-based desire markers (for items without tags)
_TEXT_DESIRE_MARKERS = [
    r"想(?:要|做|创|找|学|去|试|培|证|买|成|改|了解|理解|知道|弄|搞)",
    r"希望", r"渴望", r"内心.*想",
    r"\bwant\s+to\b", r"\bwish\b", r"\bhope\s+to\b", r"\bneed\s+to\b",
    r"أريد", r"أتمنى",
]

import re as _re


def _is_intention_item(item: dict[str, Any]) -> bool:
    """Check if a SoulItem represents an intention (vs fact/emotion/value).

    An item is an intention if:
    1. tags contain "intention"/"desire"/"need"/"goal", OR
    2. domains contain "intention"/"ambition", OR
    3. item_type is "action" or "cognitive" with supporting context, OR
    4. Text contains explicit desire markers (for items without tags)

    NOT an intention if:
    - tags explicitly mark it as fact/symptom/preference/behavior/story/trait
    """
    tags = set(item.get("tags", []))
    domains = set(item.get("domains", []))
    text = item.get("text", "")

    # Explicit non-intention tags → skip (even if text has "想")
    if tags and tags <= _NON_INTENTION_TAGS:
        return False

    # Direct tag match — but fear-only intentions are not wishes
    if tags & _INTENTION_TAGS:
        # "intention" + "fear" without desire marker → fear, not wish
        if "fear" in tags:
            lower = text.lower()
            if not any(_re.search(p, lower) for p in _TEXT_DESIRE_MARKERS):
                return False  # Pure fear like "害怕创业失败" — not a wish
        return True

    # Domain match
    if domains & _INTENTION_DOMAINS:
        return True

    # Action items with intention domain or desire markers in text
    item_type = item.get("item_type", "")
    confidence = item.get("confidence", 0.0)
    if item_type == "action" and confidence >= 0.5:
        # Only if text also has a desire marker (prevents "运动的时候很轻松" FP)
        lower = text.lower()
        if any(_re.search(p, lower) for p in _TEXT_DESIRE_MARKERS):
            return True

    # Text-based desire marker (for items WITHOUT tags — common in some fixtures)
    if not tags:
        lower = text.lower()
        # Filter: purchase/physical actions are not psychological wishes
        if _re.search(r"想买|想吃|想喝|想去(?!理解|了解)|want\s+to\s+buy|purchase", lower):
            return False
        if any(_re.search(p, lower) for p in _TEXT_DESIRE_MARKERS):
            return True

    return False


# ── Domain → WishType mapping ───────────────────────────────────────────────

# Priority-ordered: first match wins
_DOMAIN_TO_TYPE: list[tuple[set[str], WishType]] = [
    # L2 types FIRST (more specific, concrete actions — before L1 catch-alls)
    ({"ambition", "career"}, WishType.CAREER_DIRECTION),
    ({"ambition", "technology"}, WishType.CAREER_DIRECTION),
    ({"ambition"}, WishType.CAREER_DIRECTION),
    ({"career", "identity"}, WishType.CAREER_DIRECTION),
    ({"career"}, WishType.CAREER_DIRECTION),
    ({"wellness"}, WishType.HEALTH_WELLNESS),
    ({"health"}, WishType.HEALTH_WELLNESS),
    ({"education", "learning"}, WishType.LEARN_SKILL),
    # L1 types (catch broader signals)
    ({"relationship", "emotion"}, WishType.RELATIONSHIP_INSIGHT),
    ({"relationship"}, WishType.RELATIONSHIP_INSIGHT),
    ({"family", "values"}, WishType.LIFE_REFLECTION),  # "希望给女儿更好的教育" = life reflection
    ({"family"}, WishType.RELATIONSHIP_INSIGHT),
    ({"identity", "emotion"}, WishType.SELF_UNDERSTANDING),
    ({"identity"}, WishType.SELF_UNDERSTANDING),
    ({"emotion", "anxiety"}, WishType.EMOTIONAL_PROCESSING),
    ({"emotion"}, WishType.EMOTIONAL_PROCESSING),
    # L3 types
    ({"social", "connection"}, WishType.FIND_COMPANION),
    ({"social"}, WishType.FIND_COMPANION),
]

# Text keyword fallback for when domains don't map clearly
_TEXT_TO_TYPE: list[tuple[list[str], WishType]] = [
    # L1
    (["理解自己", "了解自己", "弄清楚", "搞懂", "understand myself", "figure out why i", "who i am"],
     WishType.SELF_UNDERSTANDING),
    (["写信", "表达", "倾诉", "write", "express", "letter"],
     WishType.SELF_EXPRESSION),
    (["关系", "吵架", "他为什么", "她为什么", "relationship", "between us", "why we"],
     WishType.RELATIONSHIP_INSIGHT),
    (["愤怒", "悲伤", "焦虑", "放下", "anger", "grief", "anxiety", "sadness", "process"],
     WishType.EMOTIONAL_PROCESSING),
    (["总结", "回顾", "复盘", "summary", "reflection", "portrait"],
     WishType.LIFE_REFLECTION),
    # L2
    (["学", "learn", "study", "practice"],
     WishType.LEARN_SKILL),
    (["找.*地方", "安静", "find.*place", "quiet"],
     WishType.FIND_PLACE),
    (["书", "课程", "资源", "book", "course", "resource"],
     WishType.FIND_RESOURCE),
    (["创业", "工作", "职业", "career", "job", "business"],
     WishType.CAREER_DIRECTION),
    (["冥想", "瑜伽", "健康", "运动", "meditation", "yoga", "therapy", "exercise", "咨询师"],
     WishType.HEALTH_WELLNESS),
    # L3
    (["找人", "朋友", "伙伴", "find someone", "friend", "companion"],
     WishType.FIND_COMPANION),
    (["导师", "mentor"],
     WishType.FIND_MENTOR),
]


def _classify_from_domains(domains: list[str]) -> WishType | None:
    """Classify wish type from SoulItem domains."""
    domain_set = set(domains)
    for required_domains, wish_type in _DOMAIN_TO_TYPE:
        if required_domains <= domain_set:
            return wish_type
    return None


def _classify_from_text(text: str) -> WishType | None:
    """Fallback: classify from text keywords when domains aren't specific enough."""
    lower = text.lower()
    for keywords, wish_type in _TEXT_TO_TYPE:
        if any(kw in lower for kw in keywords):
            return wish_type
    return None


def _compute_confidence(item: dict[str, Any]) -> float:
    """Compute wish confidence from SoulItem metadata.

    Factors:
    - item confidence (how sure Deep Soul is)
    - mention_count (more mentions = stronger signal)
    - emotional_valence (aroused/extreme = more urgent)
    - specificity (more specific = clearer wish)
    """
    base = item.get("confidence", 0.5)

    # Mention count boost: 3+ mentions → +0.05, 5+ → +0.10
    mentions = item.get("mention_count", 0)
    if mentions >= 5:
        base = min(base + 0.10, 0.95)
    elif mentions >= 3:
        base = min(base + 0.05, 0.95)

    # Emotional valence boost
    valence = item.get("emotional_valence", "neutral")
    if valence == "extreme":
        base = min(base + 0.10, 0.95)
    elif valence == "aroused":
        base = min(base + 0.05, 0.95)

    # Specificity boost
    specificity = item.get("specificity", 0.5)
    if specificity >= 0.7:
        base = min(base + 0.05, 0.95)

    # Fear tag boost (fear-tagged intentions are strong signals)
    tags = set(item.get("tags", []))
    if "fear" in tags:
        base = min(base + 0.05, 0.95)

    return round(base, 3)


def detect_from_soul_items(items: list[dict[str, Any]]) -> list[DetectedWish]:
    """Detect wishes from SoulGraph SoulItem dicts.

    This is the primary detection path (Path A).
    Uses structured metadata: tags, domains, confidence, item_type.
    Zero regex on text (except fallback classification).

    Args:
        items: List of SoulItem dicts (as from SoulGraph fixtures/API).

    Returns:
        List of DetectedWish, sorted by confidence descending.
    """
    results: list[DetectedWish] = []

    for item in items:
        # Step 1: Is this an intention?
        if not _is_intention_item(item):
            continue

        # Step 2: Classify wish type
        domains = item.get("domains", [])
        wish_type = _classify_from_domains(domains)

        # Fallback to text classification if domains not specific enough
        if wish_type is None:
            wish_type = _classify_from_text(item.get("text", ""))

        if wish_type is None:
            continue  # Can't classify → skip

        # Step 3: Compute confidence
        confidence = _compute_confidence(item)

        results.append(DetectedWish(
            wish_text=item.get("text", ""),
            wish_type=wish_type,
            confidence=confidence,
            source_intention_id=item.get("id", ""),
        ))

    # Sort by confidence descending
    results.sort(key=lambda w: w.confidence, reverse=True)
    return results
