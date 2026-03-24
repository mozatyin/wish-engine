"""Wish Detector — identifies fulfillable wishes from Deep Soul intentions.

Input: intentions + emotion state + cross-detector patterns
Output: list of DetectedWish

Strategy: rule-based fast path (regex keyword match) → 1x Haiku fallback for ambiguous.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from wish_engine.models import (
    CrossDetectorPattern,
    DetectedWish,
    EmotionState,
    Intention,
    WishType,
)

# ── Wish keyword patterns per language ───────────────────────────────────────

# Desire markers: words that signal "I want/wish/need/hope to..."
_DESIRE_MARKERS: dict[str, list[str]] = {
    "en": [
        r"\bi\s+(?:want|wish|hope|need|long|yearn|desire|wanna)\s+(?:to\s+)?\b",
        r"\bi\s+just\s+wanna\b",
        r"\bi\s+(?:also\s+)?(?:wish|want|need)\s+i?\s*(?:could|would|can|knew|know)\b",
        r"\bi(?:'d| would)\s+(?:love|like)\s+to\b",
        r"\bif\s+(?:only|i could)\b",
        r"\bi\s+(?:want|need)\s+(?:a|an|some|the|to)\b",
        r"\bi\s+(?:want|need)\s+to\s+(?:figure|work|sort)\s+out\b",
        r"\bi\s+dream\s+of\b",
    ],
    "zh": [
        r"我?想(?:要|了解|知道|理解|学|找|做|写|看|去|有|成为|变得|给|弄|搞|把)",
        r"希望(?:能|可以|自己|我)",
        r"渴望",
        r"如果(?:能|可以)",
        r"要是(?:能|可以)",
        r"我?需要",
    ],
    "ar": [
        r"أتمنى",
        r"أريد\s+أن",
        r"أحتاج",
        r"أرغب",
        r"لو\s+أستطيع",
        r"أود\s+أن",
    ],
}

# Type classification keywords (checked AFTER desire is confirmed)
_TYPE_KEYWORDS: dict[WishType, list[str]] = {
    WishType.SELF_UNDERSTANDING: [
        r"understand\s+(?:myself|why\s+i|who\s+i)",
        r"(?:figure|work|sort)\s+out\s+(?:why|who|what|how)\s+i\b",
        r"why\s+(?:am\s+i|do\s+i|i\s+always|i\s+keep)",
        r"(?:knew|know)\s+why\s+i\b",
        r"理解自己", r"为什么(?:我|自己)(?:总是|会|老是|一直)?",
        r"了解自己", r"认识自己",
        r"弄清楚.*(?:自己|为什么)", r"搞懂.*(?:自己|为什么)",
        r"أفهم\s+نفسي", r"لماذا\s+أنا",
    ],
    WishType.SELF_EXPRESSION: [
        r"(?:write|express|say|tell|share)\s+(?:my|what|how|a|about|down)",
        r"write\s+(?:a\s+)?letter",
        r"写(?:信|下|出|一封)", r"把.*(?:写|说)出",
        r"表达(?:自己|我的)",
        r"给自己写", r"说出", r"倾诉",
        r"أعبر\s+عن", r"أكتب",
    ],
    WishType.RELATIONSHIP_INSIGHT: [
        r"(?:relationship|between\s+us|why\s+we)",
        r"(?:我和他|我和她|我们俩|我们为什么)",
        r"(?:总是?吵|为什么.*吵|亲密关系|关系)",
        r"(?:每段感情|感情.*失败)",
        r"علاقت", r"بيننا",
    ],
    WishType.EMOTIONAL_PROCESSING: [
        r"(?:my|this|the)\s+(?:anger|sadness|anxiety|fear|grief|pain|frustration)",
        r"(?:where|why).*(?:anger|sadness|anxiety|fear)\s+(?:comes?\s+from|from)",
        r"(?:process|deal\s+with|handle|cope|figure\s+out)\s+(?:my|this|the|what)",
        r"(?:eating|weighing|gnawing)\s+(?:at|on)\s+me",
        r"(?:愤怒|悲伤|焦虑|恐惧|痛苦).*(?:从哪|为什么|怎么)",
        r"理解我的(?:愤怒|悲伤|焦虑|情绪)",
        r"处理.*(?:情绪|感受)", r"放下.*(?:执念|过去|前任)",
        r"غضب", r"حزن", r"قلق",
    ],
    WishType.LIFE_REFLECTION: [
        r"(?:summary|reflection|look\s+back|overview|portrait)\s+(?:of|about|on|my)",
        r"(?:portrait|snapshot|overview)\s+(?:of\s+)?(?:my|me|myself|who)",
        r"总结(?:一下|关于)?(?:自己|我的|人生|生活)?",
        r"回顾", r"复盘",
        r"أراجع", r"ملخص",
    ],
    # L2 types
    WishType.LEARN_SKILL: [
        r"(?:learn|study|master|practice)\s+",
        r"学(?:会|习|(?=\w))", r"أتعلم",
    ],
    WishType.FIND_PLACE: [
        r"(?:find|go\s+to|visit)\s+(?:a\s+)?(?:place|park|café|library|quiet)",
        r"找.*(?:地方|去处|安静)", r"أجد\s+مكان",
    ],
    WishType.FIND_RESOURCE: [
        r"(?:read|find|recommend)\s+(?:a\s+)?(?:book|course|article|resource)",
        r"(?:读|找|推荐).*(?:书|课程|文章|资源)",
        r"أقرأ\s+كتاب", r"أجد\s+مصدر",
    ],
    WishType.CAREER_DIRECTION: [
        r"(?:career|job|work|profession)",
        r"(?:职业|工作|转行|换工作)",
        r"مهنة", r"عمل",
    ],
    WishType.HEALTH_WELLNESS: [
        r"(?:meditat|yoga|therap|wellness|heal|exercise|counsell)",
        r"(?:冥想|瑜伽|疗愈|健康|运动)",
        r"تأمل", r"صحة",
    ],
    # L3 types
    WishType.FIND_COMPANION: [
        r"(?:find|meet)\s+(?:someone|a\s+friend|people|a\s+companion)",
        r"找.*(?:人|朋友|伙伴|同伴)",
        r"أجد\s+(?:شخص|صديق)",
    ],
    WishType.FIND_MENTOR: [
        r"(?:mentor|guide|advisor|teacher)",
        r"(?:导师|前辈|指导)",
        r"مرشد",
    ],
    WishType.SKILL_EXCHANGE: [
        r"(?:exchange|swap|trade)\s+(?:skill|language)",
        r"(?:互换|交换).*(?:技能|语言)",
        r"تبادل",
    ],
    WishType.SHARED_EXPERIENCE: [
        r"(?:together|with\s+someone|一起|一块)",
        r"مع\s+شخص",
    ],
    WishType.EMOTIONAL_SUPPORT: [
        r"(?:talk\s+to\s+someone|someone\s+who\s+understands)",
        r"(?:找人聊|有人理解|有人懂)",
        r"أتحدث\s+مع",
    ],
}


def _detect_language(text: str) -> str:
    """Simple language detection based on character ranges."""
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[\u0600-\u06ff]", text):
        return "ar"
    return "en"


# Negation patterns — if these appear BEFORE the desire marker, reject
_NEGATION_PATTERNS: dict[str, list[str]] = {
    "en": [
        r"\b(?:don't|doesn't|didn't|do\s+not|never|no\s+i\s+don't)\b.*\b(?:want|wish|need|wanna)\b",
        r"\b(?:i\s+(?:don't|never|didn't))\b.*\b(?:want|wish|need|wanna)\b",
    ],
    "zh": [
        r"(?:不想|不需要|不要|别想|不用)",
        r"真的不想",
    ],
    "ar": [
        r"لا\s+(?:أريد|أتمنى|أحتاج)",
        r"ما\s+(?:أريد|أبغى)",
    ],
}


def _is_negated(text: str, lang: str) -> bool:
    """Check if the desire is negated (I don't want, 不想, etc.)."""
    patterns = _NEGATION_PATTERNS.get(lang, _NEGATION_PATTERNS["en"])
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


def _has_desire_marker(text: str, lang: str) -> bool:
    """Check if text contains a desire/wish keyword (and is NOT negated)."""
    # Check negation first
    if _is_negated(text, lang):
        return False
    patterns = _DESIRE_MARKERS.get(lang, _DESIRE_MARKERS["en"])
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


def _classify_wish_type(text: str) -> WishType | None:
    """Try to classify wish type from text keywords. Returns None if no match.

    When multiple types match, returns the one with the most keyword hits (specificity wins).
    """
    lower = text.lower()
    best_type: WishType | None = None
    best_hits = 0

    for wish_type, patterns in _TYPE_KEYWORDS.items():
        hits = sum(1 for p in patterns if re.search(p, lower))
        if hits > best_hits:
            best_hits = hits
            best_type = wish_type

    return best_type


# ── Local fallback scorer (replaces Haiku for ambiguous cases) ───────────────

# Broad category keywords — less specific, used when desire marker is present
# but _classify_wish_type found no match. Scored by relevance.
_FALLBACK_KEYWORDS: list[tuple[WishType, list[str], float]] = [
    # (type, keyword patterns, base confidence)
    (WishType.SELF_UNDERSTANDING, [r"myself|自己|نفسي", r"why|为什么|لماذا", r"understand|明白|أفهم"], 0.65),
    (WishType.EMOTIONAL_PROCESSING, [r"feel|emotion|mood|感受|情绪|心情|شعور", r"angry|sad|anxious|scared|害怕|难过|生气"], 0.65),
    (WishType.RELATIONSHIP_INSIGHT, [r"relation|partner|friend|他|她|朋友|伴侣|前任|ex\b|صديق", r"fight|argue|吵|争|感情|失败"], 0.60),
    (WishType.SELF_EXPRESSION, [r"write|letter|journal|diary|写|日记|信|أكتب", r"express|tell|说|表达"], 0.60),
    (WishType.LIFE_REFLECTION, [r"life|past|future|growth|人生|过去|未来|成长|حياة"], 0.55),
    (WishType.HEALTH_WELLNESS, [r"health|wellness|relax|calm|peace|放松|平静|健康|هدوء"], 0.55),
    (WishType.FIND_COMPANION, [r"someone|people|somebody|人|谁|شخص"], 0.50),
]


def _local_fallback_classify(text: str) -> tuple[WishType | None, float]:
    """Attempt local classification for ambiguous intentions.

    Uses broad keyword scoring instead of LLM.
    Returns (wish_type, confidence) or (None, 0.0) if no match.
    """
    lower = text.lower()
    best_type: WishType | None = None
    best_score: float = 0.0

    for wish_type, keyword_patterns, base_conf in _FALLBACK_KEYWORDS:
        matches = sum(1 for p in keyword_patterns if re.search(p, lower))
        if matches >= 1:
            score = base_conf + (matches - 1) * 0.10
            if score > best_score:
                best_score = score
                best_type = wish_type

    return best_type, min(best_score, 0.80)


def _build_haiku_prompt(intention_text: str) -> str:
    """Build a minimal prompt for Haiku fallback."""
    return (
        "Is this intention a fulfillable wish? If yes, classify its type.\n"
        f'Intention: "{intention_text}"\n'
        "Types: self_understanding, self_expression, relationship_insight, "
        "emotional_processing, life_reflection, learn_skill, find_place, "
        "find_resource, career_direction, health_wellness, find_companion, "
        "find_mentor, skill_exchange, shared_experience, emotional_support\n"
        'JSON: {"is_wish": bool, "wish_type": str|null, "confidence": float}'
    )


def _call_haiku(prompt: str, api_key: str) -> dict[str, Any]:
    """Call Haiku via Anthropic SDK. Returns parsed JSON dict."""
    import anthropic

    client = anthropic.Anthropic(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    response = client.messages.create(
        model="anthropic/claude-haiku",
        max_tokens=128,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    # Extract JSON from response
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(raw[start:end])
    return {"is_wish": False, "wish_type": None, "confidence": 0.0}


def detect_wishes(
    intentions: list[Intention],
    emotion_state: EmotionState | None = None,
    cross_detector_patterns: list[CrossDetectorPattern] | None = None,
    api_key: str | None = None,
) -> list[DetectedWish]:
    """Detect fulfillable wishes from a list of intentions.

    Strategy:
    1. Rule-based fast path: regex keyword matching (zero LLM)
    2. Haiku fallback: for intentions that look wish-like but couldn't be classified

    Args:
        intentions: List of intentions from Deep Soul / SoulGraph.
        emotion_state: Current emotion snapshot (used for confidence boosting).
        cross_detector_patterns: Cross-detector patterns (used for context).
        api_key: API key for Haiku fallback. If None, reads from ANTHROPIC_API_KEY env.

    Returns:
        List of detected wishes, sorted by confidence descending.
    """
    if not intentions:
        return []

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    results: list[DetectedWish] = []
    ambiguous: list[Intention] = []

    # Pass 1: rule-based fast path
    for intent in intentions:
        lang = _detect_language(intent.text)
        has_desire = _has_desire_marker(intent.text, lang)

        if has_desire:
            wish_type = _classify_wish_type(intent.text)
            if wish_type is not None:
                # Confidence boost if emotion state aligns
                conf = 0.85
                if emotion_state and emotion_state.distress > 0.3:
                    conf = min(conf + 0.05, 0.95)
                # Confidence boost if cross-detector pattern matches
                if cross_detector_patterns:
                    pattern_names = {p.pattern_name for p in cross_detector_patterns}
                    if pattern_names & {
                        "safe_silence", "frozen_distance", "honest_anchor"
                    }:
                        conf = min(conf + 0.05, 0.95)

                results.append(
                    DetectedWish(
                        wish_text=intent.text,
                        wish_type=wish_type,
                        confidence=conf,
                        source_intention_id=intent.id,
                    )
                )
            else:
                # Has desire marker but type unclear → ambiguous
                ambiguous.append(intent)
        # No desire marker → not a wish, skip

    # Pass 2: Local fallback for ambiguous intentions (zero LLM)
    still_ambiguous: list[Intention] = []
    for intent in ambiguous:
        fallback_type, fallback_conf = _local_fallback_classify(intent.text)
        if fallback_type is not None and fallback_conf >= 0.50:
            results.append(
                DetectedWish(
                    wish_text=intent.text,
                    wish_type=fallback_type,
                    confidence=fallback_conf,
                    source_intention_id=intent.id,
                )
            )
        else:
            still_ambiguous.append(intent)

    # Pass 3: Haiku fallback for still-ambiguous intentions (rare)
    if still_ambiguous and key:
        for intent in still_ambiguous:
            try:
                prompt = _build_haiku_prompt(intent.text)
                resp = _call_haiku(prompt, key)
                if resp.get("is_wish") and resp.get("wish_type"):
                    try:
                        wtype = WishType(resp["wish_type"])
                    except ValueError:
                        continue
                    conf = min(float(resp.get("confidence", 0.7)), 0.95)
                    results.append(
                        DetectedWish(
                            wish_text=intent.text,
                            wish_type=wtype,
                            confidence=conf,
                            source_intention_id=intent.id,
                        )
                    )
            except Exception:
                # LLM failure → skip this intention
                continue

    # Sort by confidence descending
    results.sort(key=lambda w: w.confidence, reverse=True)
    return results
