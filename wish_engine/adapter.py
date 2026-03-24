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
_INTENTION_DOMAINS = {"intention"}  # Some fixtures put "intention" in domains


def _is_intention_item(item: dict[str, Any]) -> bool:
    """Check if a SoulItem represents an intention (vs fact/emotion/value).

    An item is an intention if:
    1. tags contain "intention"/"desire"/"need", OR
    2. domains contain "intention", OR
    3. item_type is "action" or "cognitive" with supporting tags
    """
    tags = set(item.get("tags", []))
    domains = set(item.get("domains", []))

    # Direct tag match
    if tags & _INTENTION_TAGS:
        return True

    # Domain match (some fixtures use domains to flag intentions)
    if domains & _INTENTION_DOMAINS:
        return True

    # Action items with reasonable confidence are often intentions
    item_type = item.get("item_type", "")
    confidence = item.get("confidence", 0.0)
    if item_type == "action" and confidence >= 0.5:
        return True

    return False


# ── Domain → WishType mapping ───────────────────────────────────────────────

# Priority-ordered: first match wins
_DOMAIN_TO_TYPE: list[tuple[set[str], WishType]] = [
    # L2 types FIRST (more specific, concrete actions — before L1 catch-alls)
    ({"career", "ambition"}, WishType.CAREER_DIRECTION),
    ({"career", "identity"}, WishType.CAREER_DIRECTION),  # "想创业" = career, not self-understanding
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
