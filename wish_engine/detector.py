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
    "hi": [
        r"(?:मैं|मुझे)\s+(?:चाहता|चाहती)\s+(?:हूँ|हूं|हैं)",
        r"मुझे\s+(?:ज़रूरत|जरूरत)\s+है",
        r"काश",
        r"(?:मैं|मुझे)\s+(?:चाहिए|चाहिये)",
        r"अगर\s+(?:मैं|मुझे)\s+(?:मिल|कर)\s+(?:सकता|सकती|पाता|पाती)",
        r"मेरी\s+(?:इच्छा|तमन्ना|ख़्वाहिश|ख्वाहिश)\s+है",
    ],
    "tr": [
        r"\b(?:i|İ)stiyorum\b",
        r"\bkeşke\b",
        r"\bihtiyacım\s+var\b",
        r"\bumuyorum\b",
        r"\b(?:i|İ)sterim\b",
        r"\barzu\s+ediyorum\b",
    ],
    "ru": [
        r"\bя\s+хочу\b",
        r"\bмне\s+нужно\b",
        r"\bнадеюсь\b",
        r"\bя\s+мечтаю\b",
        r"\bесли\s+бы\s+(?:я\s+)?(?:мог|могла|мог(?:ла)?)\b",
        r"\bхотел(?:а|ось)?\s+бы\b",
    ],
    "fr": [
        r"\bje\s+veux\b",
        r"\bj'aimerais\b",
        r"\bj'espère\b",
        r"\bje\s+souhaite\b",
        r"\bsi\s+(?:seulement|je\s+pouvais)\b",
        r"\bj'ai\s+besoin\s+de\b",
    ],
    "es": [
        r"\bquiero\b",
        r"\bdeseo\b",
        r"\bnecesito\b",
        r"\bojalá\b",
        r"\bme\s+gustaría\b",
        r"\bespero\b",
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
    """Simple language detection based on character ranges.

    Unicode ranges used:
      zh: \\u4e00-\\u9fff  (CJK Unified Ideographs)
      ar: \\u0600-\\u06ff  (Arabic)
      hi: \\u0900-\\u097f  (Devanagari)
      ru: \\u0400-\\u04ff  (Cyrillic)
      tr: Turkish-specific characters (\\u011e-\\u011f, \\u0130-\\u0131, etc.)
      fr/es: Latin with diacritics — detected via keyword heuristics after others
    """
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[\u0900-\u097f]", text):
        return "hi"
    if re.search(r"[\u0600-\u06ff]", text):
        return "ar"
    if re.search(r"[\u0400-\u04ff]", text):
        return "ru"
    # Turkish: check for Turkish-specific characters or common Turkish words
    if re.search(r"[\u011e\u011f\u0130\u0131\u015e\u015f\u00d6\u00f6\u00dc\u00fc\u00c7\u00e7]", text):
        return "tr"
    if re.search(r"\b(?:istiyorum|keşke|ihtiyacım|umuyorum|isterim)\b", text, re.IGNORECASE):
        return "tr"
    # French: check for characteristic patterns
    if re.search(r"\b(?:je|j'|qu'|c'est|d'|l'|n'|s'|avoir|être)\b", text, re.IGNORECASE):
        return "fr"
    # Spanish: check for characteristic patterns
    if re.search(r"\b(?:quiero|necesito|deseo|ojalá|estoy|tengo|puedo|también|está|más)\b", text, re.IGNORECASE):
        return "es"
    return "en"


# Negation patterns — if these appear BEFORE the desire marker, reject
_NEGATION_PATTERNS: dict[str, list[str]] = {
    "en": [
        # Only negate when "I" is the subject who doesn't want
        r"\bi\s+(?:don't|never|didn't)\s+(?:want|wish|need|wanna)\b",
        r"\bno\s+i\s+don't\s+(?:want|need)\b",
        r"\bi\s+do\s+not\s+(?:want|wish|need)\b",
    ],
    "zh": [
        r"(?:不想|不需要|不要|别想|不用)",
        r"真的不想",
    ],
    "ar": [
        r"لا\s+(?:أريد|أتمنى|أحتاج)",
        r"ما\s+(?:أريد|أبغى)",
    ],
    "hi": [
        r"(?:मैं|मुझे)\s+(?:नहीं)\s+(?:चाहता|चाहती|चाहिए)",
        r"(?:ज़रूरत|जरूरत)\s+नहीं",
    ],
    "tr": [
        r"\b(?:i|İ)stemiyorum\b",
        r"\bihtiyacım\s+yok\b",
    ],
    "ru": [
        r"\bя\s+не\s+хочу\b",
        r"\bмне\s+не\s+нужно\b",
    ],
    "fr": [
        r"\bje\s+ne\s+veux\s+(?:pas|plus)\b",
        r"\bje\s+n'ai\s+pas\s+besoin\b",
    ],
    "es": [
        r"\bno\s+(?:quiero|necesito|deseo)\b",
        r"\bno\s+me\s+gustaría\b",
    ],
}


def _is_negated(text: str, lang: str) -> bool:
    """Check if the desire is negated (I don't want, 不想, etc.)."""
    patterns = _NEGATION_PATTERNS.get(lang, _NEGATION_PATTERNS["en"])
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


# Casual/physical "want" that are NOT psychological wishes
_CASUAL_WANT_PATTERNS: dict[str, list[str]] = {
    "en": [
        # Only filter basic physical needs — NOT aspirational activities
        r"\bwant\s+to\s+(?:eat|sleep|drink|leave|come|stay|sit|stand|run|walk|stop|start|say|tell\s+you|mention|add|get|buy|pay|watch|listen|try\s+(?:this|that|it))\b",
        r"\bwant\s+(?:pizza|food|coffee|water|some|this|that|it)\b",
        r"\bneed\s+to\s+(?:eat|sleep|go|leave|pee|rest|shower)\b",
        r"\bwanna\s+(?:eat|sleep|leave|hang|chill|watch)\b",
    ],
    "zh": [
        r"想(?:吃|喝|睡|买|看看|听|坐|走|回)",
        r"想(?:上厕所|洗澡|休息一下)",
    ],
    "ar": [
        r"أريد\s+أن\s+(?:آكل|أنام|أذهب|أشرب|أرتاح)",
    ],
    "hi": [
        r"(?:खाना|सोना|पीना|जाना|नहाना|आराम)\s+(?:चाहता|चाहती|चाहिए)",
        r"(?:मैं|मुझे)\s+(?:खाना|सोना|पीना|जाना|नहाना)\s+(?:है|हैं)",
    ],
    "tr": [
        r"\b(?:i|İ)stiyorum\s+(?:yemek|uyumak|gitmek|içmek|dinlenmek|yürümek|oturmak)\b",
        r"\bihtiyacım\s+var\s+(?:yemek|uyumak|gitmek|dinlenmek)\b",
    ],
    "ru": [
        r"\bхочу\s+(?:есть|спать|пить|идти|гулять|отдохнуть|сесть|встать|уйти)\b",
        r"\bнужно\s+(?:поесть|поспать|попить|уйти|отдохнуть|помыться)\b",
    ],
    "fr": [
        r"\bveux\s+(?:manger|dormir|boire|partir|aller|rester|marcher|m'asseoir)\b",
        r"\bbesoin\s+de\s+(?:manger|dormir|boire|partir|me\s+reposer|me\s+doucher)\b",
    ],
    "es": [
        r"\bquiero\s+(?:comer|dormir|beber|ir|irme|salir|caminar|sentarme|descansar)\b",
        r"\bnecesito\s+(?:comer|dormir|beber|irme|descansar|ducharme)\b",
    ],
}


def _is_casual_want(text: str, lang: str) -> bool:
    """Check if 'want' is casual/physical, not a psychological wish."""
    patterns = _CASUAL_WANT_PATTERNS.get(lang, _CASUAL_WANT_PATTERNS["en"])
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


# ── Implicit wish patterns (no explicit desire marker needed) ────────────────

# Problem-as-wish: describing a problem implies a wish to solve it
_PROBLEM_AS_WISH_PATTERNS: dict[str, list[str]] = {
    "en": [
        r"\bi\s+keep\s+(?:failing|struggling|fighting|losing|forgetting|messing|screwing|getting|making)",
        r"\bi\s+can'?t\s+(?:stop|handle|deal|cope|manage|figure|control|help|get\s+over|move\s+on)",
        r"\bi\s+don'?t\s+know\s+(?:how\s+to|what\s+to|why|where|when|if)",
        r"\bit'?s\s+(?:so\s+)?hard\s+to\b",
        r"\bi'?m\s+stuck\b",
        r"\bi'?m\s+(?:so\s+)?tired\s+of\b",
        r"\bi\s+always\s+(?:end\s+up|fail|mess|screw|ruin)",
        r"\bi\s+struggle\s+(?:with|to)\b",
    ],
    "zh": [
        r"我不知道怎么",
        r"我一直(?:在|都)",
        r"很难(?:做到|接受|面对|理解|相信|放下|忘记)",
        r"受不了",
        r"我总是",
        r"怎么都(?:不|无法)",
    ],
    "ar": [
        r"لا\s+أعرف\s+كيف",
        r"مشكلتي",
        r"أحتاج\s+مساعدة",
        r"تعبت\s+من",
        r"لا\s+أستطيع",
        r"ما\s+أقدر",
    ],
}

# Help-seeking patterns
_HELP_SEEKING_PATTERNS: dict[str, list[str]] = {
    "en": [
        r"\bhow\s+(?:do|can|should)\s+i\b",
        r"\bwhat\s+should\s+i\b",
        r"\bcan\s+you\s+help\b",
        r"\bany\s+(?:advice|suggestions?|tips?|ideas?)\b",
        r"\bwhat\s+do\s+you\s+think\s+i\s+should\b",
        r"\bhow\s+(?:do\s+i|to)\s+(?:deal|cope|handle|manage|fix|solve|stop|get\s+over)\b",
    ],
    "zh": [
        r"怎么办",
        r"该怎么",
        r"有什么建议",
        r"帮帮我",
        r"怎么(?:才能|样才)",
    ],
    "ar": [
        r"كيف\s+(?:أ|ا)",
        r"ماذا\s+أفعل",
        r"ساعدني",
        r"ما\s+الحل",
    ],
}

# Aspiration patterns
_ASPIRATION_PATTERNS: dict[str, list[str]] = {
    "en": [
        r"\bi'?ve\s+been\s+(?:thinking|wondering)\s+about\b",
        r"\bit\s+would\s+be\s+nice\s+(?:if|to)\b",
        r"\bsometimes\s+i\s+(?:think|wonder|dream)\s+about\b",
        r"\bi'?ve\s+been\s+considering\b",
        r"\bi\s+(?:really\s+)?wish\s+(?:i|things|life|it)\b",
    ],
    "zh": [
        r"我在想",
        r"如果能(?:够|\.{0})",
        r"我考虑",
        r"希望有一天",
        r"要是.*就好了",
    ],
    "ar": [
        r"أفكر\s+في",
        r"لو\s+أستطيع",
        r"أتمنى\s+لو",
        r"يا\s+ريت",
    ],
}

# Short-message emotional keywords that imply a wish for emotional support
_SHORT_EMOTIONAL_KEYWORDS: dict[str, list[str]] = {
    "en": [
        r"\b(?:lonely|scared|lost|confused|stuck|help|hopeless|alone|overwhelmed|terrified|desperate|broken)\b",
    ],
    "zh": [
        r"(?:孤独|害怕|迷茫|无助|崩溃|救|绝望|痛苦|难受|焦虑)",
    ],
    "ar": [
        r"(?:وحيد|خايف|ضايع|محتاج|تعبان|مكسور)",
    ],
}


def _check_implicit_wish(text: str, lang: str) -> tuple[bool, str]:
    """Check for implicit wish patterns (problem-as-wish, help-seeking, aspiration).

    Returns (is_implicit_wish, pattern_category).
    """
    lower = text.lower()

    for category, pattern_dict in [
        ("problem", _PROBLEM_AS_WISH_PATTERNS),
        ("help_seeking", _HELP_SEEKING_PATTERNS),
        ("aspiration", _ASPIRATION_PATTERNS),
    ]:
        patterns = pattern_dict.get(lang, pattern_dict.get("en", []))
        if any(re.search(p, lower) for p in patterns):
            return True, category

    return False, ""


def _check_short_emotional(text: str, lang: str) -> bool:
    """Check if short message contains strong emotional keywords."""
    patterns = _SHORT_EMOTIONAL_KEYWORDS.get(lang, _SHORT_EMOTIONAL_KEYWORDS.get("en", []))
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


def _has_desire_marker(text: str, lang: str) -> bool:
    """Check if text contains a desire/wish keyword (and is NOT negated or casual)."""
    if _is_negated(text, lang):
        return False
    if _is_casual_want(text, lang):
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
    """Call Haiku via shared LLM client. Returns parsed JSON dict."""
    from wish_engine.llm_client import call_llm

    result = call_llm(
        model="claude-haiku-4-5-20251001",
        prompt=prompt,
        api_key=api_key,
        max_tokens=128,
        parse_json=True,
    )
    if isinstance(result, dict):
        return result
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

    # Pass 1: rule-based fast path (explicit desire markers)
    implicit_candidates: list[Intention] = []

    for intent in intentions:
        lang = _detect_language(intent.text)
        text_stripped = intent.text.strip()
        text_len = len(text_stripped)

        # Skip very short texts (language-aware minimum)
        min_len = 4 if lang in ("zh", "ar", "hi") else 10

        # For short messages: check desire markers first (they're more specific),
        # then fall back to emotional/implicit detection
        has_desire_short = _has_desire_marker(intent.text, lang) if text_len >= min_len else False

        if text_len < min_len and not has_desire_short:
            # Check short-message emotional keywords
            if _check_short_emotional(text_stripped, lang):
                results.append(
                    DetectedWish(
                        wish_text=intent.text,
                        wish_type=WishType.EMOTIONAL_PROCESSING,
                        confidence=0.40,
                        source_intention_id=intent.id,
                    )
                )
                continue
            # Check if it's an implicit wish even though short (e.g., "怎么办")
            is_imp_short, cat_short = _check_implicit_wish(text_stripped, lang)
            if is_imp_short:
                results.append(
                    DetectedWish(
                        wish_text=intent.text,
                        wish_type=WishType.EMOTIONAL_PROCESSING,
                        confidence=0.45,
                        source_intention_id=intent.id,
                    )
                )
            continue

        # Short-message emotional boost (for messages >= min_len but < 20 chars,
        # only if no explicit desire marker — desire markers are more specific)
        if text_len < 20 and not _has_desire_marker(intent.text, lang) and _check_short_emotional(text_stripped, lang):
            results.append(
                DetectedWish(
                    wish_text=intent.text,
                    wish_type=WishType.EMOTIONAL_PROCESSING,
                    confidence=0.40,
                    source_intention_id=intent.id,
                )
            )
            continue

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
        else:
            # No explicit desire marker → check implicit patterns
            implicit_candidates.append(intent)

    # Pass 1b: Implicit wish detection (problem-as-wish, help-seeking, aspiration)
    for intent in implicit_candidates:
        lang = _detect_language(intent.text)
        is_implicit, category = _check_implicit_wish(intent.text, lang)

        if is_implicit:
            # Try to classify the type
            wish_type = _classify_wish_type(intent.text)
            if wish_type is None:
                # Use local fallback for type classification
                wish_type, fallback_conf = _local_fallback_classify(intent.text)

            if wish_type is None:
                # Implicit pattern matched but no specific type → default based on category
                if category == "problem":
                    wish_type = WishType.SELF_UNDERSTANDING
                elif category == "help_seeking":
                    wish_type = WishType.EMOTIONAL_PROCESSING
                elif category == "aspiration":
                    wish_type = WishType.SELF_UNDERSTANDING
                else:
                    wish_type = WishType.EMOTIONAL_PROCESSING

            # Implicit wishes get lower base confidence
            conf = 0.60
            if category == "help_seeking":
                conf = 0.65  # help-seeking is more intentional
            # Emotion distress boost for implicit wishes
            if emotion_state and emotion_state.distress > 0.3:
                conf = min(conf + 0.10, 0.80)
            results.append(
                DetectedWish(
                    wish_text=intent.text,
                    wish_type=wish_type,
                    confidence=conf,
                    source_intention_id=intent.id,
                )
            )
        elif emotion_state and emotion_state.distress > 0.5 and len(intent.text.strip()) > 15:
            # High distress + non-trivial message → implicit emotional support wish
            results.append(
                DetectedWish(
                    wish_text=intent.text,
                    wish_type=WishType.EMOTIONAL_PROCESSING,
                    confidence=0.50,
                    source_intention_id=intent.id,
                )
            )

    # Pass 2: Local fallback for ambiguous intentions (zero LLM)
    still_ambiguous: list[Intention] = []
    for intent in ambiguous:
        fallback_type, fallback_conf = _local_fallback_classify(intent.text)
        if fallback_type is not None and fallback_conf >= 0.30:
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
