"""Wish Deduplicator — merges duplicate wishes from the same session.

Users often express the same wish multiple times across turns:
- Turn 3: "想理解自己为什么害怕承诺"
- Turn 7: "我就是搞不懂自己为什么一到关键时刻就退缩"

These are the same wish. Without dedup, star map shows duplicate stars.

Strategy: same wish_type + keyword overlap > threshold → merge.
Zero LLM.
"""

from __future__ import annotations

import re
from wish_engine.models import DetectedWish, WishType


def _extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text for overlap calculation."""
    # Remove common stop words
    stop_en = {"i", "a", "an", "the", "to", "of", "and", "is", "it", "my", "me",
               "want", "wish", "need", "hope", "would", "could", "like", "just",
               "really", "also", "about", "that", "this", "what", "why", "how",
               "do", "don't", "be", "am", "was", "have", "has", "been", "so",
               "but", "or", "if", "in", "on", "at", "for", "with", "from"}
    stop_zh = {"我", "的", "了", "是", "在", "不", "有", "和", "就", "也",
               "想", "要", "会", "能", "可以", "为什么", "总是", "自己",
               "一个", "这", "那", "都", "很", "还", "吗", "呢", "把"}

    lower = text.lower()

    # Chinese: extract characters/bigrams
    zh_chars = re.findall(r"[\u4e00-\u9fff]+", lower)
    zh_words = set()
    for seg in zh_chars:
        for i in range(len(seg)):
            if seg[i] not in stop_zh:
                zh_words.add(seg[i])
            if i + 1 < len(seg):
                bigram = seg[i:i+2]
                zh_words.add(bigram)

    # English: split by whitespace
    en_words = set()
    for word in re.findall(r"[a-z]+", lower):
        if word not in stop_en and len(word) > 2:
            en_words.add(word)

    # Arabic
    ar_words = set(re.findall(r"[\u0600-\u06ff]+", lower))

    return zh_words | en_words | ar_words


def _keyword_overlap(a: set[str], b: set[str]) -> float:
    """Jaccard-like overlap between keyword sets."""
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


def deduplicate(
    wishes: list[DetectedWish],
    type_weight: float = 0.5,
    keyword_threshold: float = 0.25,
) -> list[DetectedWish]:
    """Deduplicate wishes by merging similar ones.

    Two wishes are considered duplicates if:
    1. Same wish_type (weighted by type_weight), AND
    2. Keyword overlap > keyword_threshold

    When merging, keeps the one with higher confidence.

    Args:
        wishes: List of detected wishes (may contain duplicates).
        type_weight: Weight bonus for same type (0-1).
        keyword_threshold: Minimum keyword overlap to consider as duplicate.

    Returns:
        Deduplicated list of wishes.
    """
    if len(wishes) <= 1:
        return wishes

    # Extract keywords for each wish
    keywords = [_extract_keywords(w.wish_text) for w in wishes]

    # Track which wishes are merged into others
    merged: set[int] = set()
    result: list[DetectedWish] = []

    for i, wish_i in enumerate(wishes):
        if i in merged:
            continue

        best = wish_i
        for j in range(i + 1, len(wishes)):
            if j in merged:
                continue

            wish_j = wishes[j]

            # Same type check
            if wish_i.wish_type != wish_j.wish_type:
                continue

            # Keyword overlap check
            overlap = _keyword_overlap(keywords[i], keywords[j])
            if overlap >= keyword_threshold:
                # Merge: keep higher confidence
                merged.add(j)
                if wish_j.confidence > best.confidence:
                    best = wish_j

        result.append(best)

    return result
