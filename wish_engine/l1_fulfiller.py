"""L1 Fulfiller — generates personalized insights for L1 wishes.

Uses 1x Sonnet call per fulfillment. Selects card_type locally (zero LLM).

5 fulfillment types:
  a) Personalized psychological insight ("why do you always avoid conflict")
  b) Relationship dynamic analysis (Bond Comparator)
  c) Emotion trace (emotion timeline tracing)
  d) Soul Portrait (16-dimension self-portrait)
  e) Assisted self-dialogue / letter writing
"""

from __future__ import annotations

import json
import os
from typing import Any

from wish_engine.models import (
    CardType,
    ClassifiedWish,
    CrossDetectorPattern,
    DetectorResults,
    L1FulfillmentResult,
    WishLevel,
    WishType,
)

# ── Card type routing (zero LLM) ────────────────────────────────────────────

_WISH_TO_CARD: dict[WishType, CardType] = {
    WishType.SELF_UNDERSTANDING: CardType.INSIGHT,
    WishType.SELF_EXPRESSION: CardType.SELF_DIALOGUE,
    WishType.RELATIONSHIP_INSIGHT: CardType.RELATIONSHIP_ANALYSIS,
    WishType.EMOTIONAL_PROCESSING: CardType.EMOTION_TRACE,
    WishType.LIFE_REFLECTION: CardType.SOUL_PORTRAIT,
}


def _select_card_type(wish_type: WishType) -> CardType:
    """Select card type from wish type. Zero LLM."""
    return _WISH_TO_CARD.get(wish_type, CardType.INSIGHT)


def _extract_profile_summary(
    detector_results: DetectorResults,
    soul_type: dict[str, Any],
    life_chapter: dict[str, Any],
) -> str:
    """Build a compact profile summary from detector results for the prompt."""
    parts: list[str] = []

    # Emotion
    if detector_results.emotion:
        top_emotions = detector_results.emotion.get("emotions", {})
        if top_emotions:
            sorted_emo = sorted(top_emotions.items(), key=lambda x: x[1], reverse=True)[:3]
            parts.append(f"Emotions: {', '.join(f'{k}({v:.1f})' for k, v in sorted_emo)}")
        distress = detector_results.emotion.get("distress")
        if distress is not None:
            parts.append(f"Distress: {distress:.2f}")

    # Conflict style
    if detector_results.conflict:
        style = detector_results.conflict.get("style")
        if style:
            parts.append(f"Conflict style: {style}")

    # MBTI
    if detector_results.mbti:
        mbti_type = detector_results.mbti.get("type")
        if mbti_type:
            parts.append(f"MBTI: {mbti_type}")

    # Attachment
    if detector_results.attachment:
        att_style = detector_results.attachment.get("style")
        if att_style:
            parts.append(f"Attachment: {att_style}")

    # Values
    if detector_results.values:
        top_values = detector_results.values.get("top_values", [])
        if top_values:
            parts.append(f"Values: {', '.join(top_values[:3])}")

    # Fragility
    if detector_results.fragility:
        pattern = detector_results.fragility.get("pattern")
        if pattern:
            parts.append(f"Fragility: {pattern}")

    # EQ
    if detector_results.eq:
        overall = detector_results.eq.get("overall")
        if overall is not None:
            parts.append(f"EQ: {overall:.2f}")

    # Communication DNA
    if detector_results.communication_dna:
        style = detector_results.communication_dna.get("dominant_style")
        if style:
            parts.append(f"Communication: {style}")

    # Soul type
    if soul_type:
        name = soul_type.get("name")
        if name:
            parts.append(f"Soul type: {name}")

    # Life chapter
    if life_chapter:
        theme = life_chapter.get("theme")
        if theme:
            parts.append(f"Life chapter: {theme}")

    return "\n".join(parts) if parts else "No profile data available"


# Banned therapy-speak phrases — these make insights feel generic
_BANNED_PHRASES = [
    "It's important to remember",
    "This is perfectly normal",
    "You might want to consider",
    "journey of self-discovery",
    "safe space",
    "validate your feelings",
    "processing your emotions",
    "emotional regulation",
    "coping mechanism",
    "mental health professional",
    "therapeutic",
    "self-care routine",
]

_TONE_CALIBRATION = """TONE: Write like a perceptive friend, NOT a therapist.
BAD: "Your avoidant conflict style suggests you may benefit from exploring healthier communication patterns."
GOOD: "You'd rather walk away from a fight than win one. That's not weakness — it's a bet that silence costs less than drama."
BAD: "Your high emotional intelligence score indicates strong empathetic capabilities."
GOOD: "You read rooms like other people read text messages — fast and without trying."
"""

_ANTI_HOROSCOPE = "ANTI-HOROSCOPE: Before writing, check — would this be true if the profile scores were reversed? If yes, delete it. Only keep insights that are TRUE for THIS specific profile and FALSE for the opposite profile."


def _find_profile_tensions(profile: str) -> str:
    """Find contradictions/tensions in the profile that make the best insights."""
    tensions = []
    lower = profile.lower()

    # High EQ + avoidant
    if "avoiding" in lower and ("eq:" in lower or "eq :" in lower):
        tensions.append("high EQ + conflict-avoiding (sees fights coming but walks away)")
    # Anxious attachment + accommodating
    if "anxious" in lower and "accommodating" in lower:
        tensions.append("anxious attachment + accommodating (craves closeness but gives too much)")
    # High fragility + competing
    if ("defensive" in lower or "approval" in lower) and "competing" in lower:
        tensions.append("fragile yet combative (armored vulnerability)")
    # Values belonging + avoidant
    if "belonging" in lower and ("avoiding" in lower or "avoidant" in lower):
        tensions.append("values belonging but avoids the conflicts that deepen bonds")
    # Secure attachment + high distress
    if "secure" in lower and "distress" in lower:
        tensions.append("secure foundation under acute stress (resilient but hurting)")

    return "Tensions: " + "; ".join(tensions) if tensions else ""


def _build_fulfillment_prompt(
    wish: ClassifiedWish,
    card_type: CardType,
    profile: str,
    patterns: list[CrossDetectorPattern],
) -> str:
    """Build a Sonnet prompt using research-backed personalization techniques."""
    pattern_str = ""
    if patterns:
        pattern_str = "\nPatterns: " + ", ".join(p.pattern_name for p in patterns[:3])

    tensions = _find_profile_tensions(profile)
    tension_str = f"\n{tensions}" if tensions else ""

    card_instruction = {
        CardType.INSIGHT: "Write a personalized insight (150-250 words). Ground EVERY sentence in a specific profile data point. Find the tension/contradiction in their profile — that's where the real insight lives. End with a reflection question.",
        CardType.RELATIONSHIP_ANALYSIS: "Analyze the relationship dynamic (150-250 words). Name their specific conflict style and attachment pattern. Show how these create the friction they're experiencing. End with one concrete suggestion.",
        CardType.EMOTION_TRACE: "Trace where this emotion comes from (150-250 words). Connect their current distress to their fragility pattern and attachment style. Show the chain: trigger → pattern → feeling. End with a grounding thought.",
        CardType.SOUL_PORTRAIT: "Write a soul self-portrait (200-300 words). Weave their MBTI, conflict style, values, EQ, and soul type into a vivid narrative. Name each trait as you weave it in. Warm, poetic, deeply personal.",
        CardType.SELF_DIALOGUE: "Write the opening of a letter from them to themselves (100-200 words). Reference their fragility pattern or attachment style by name. Warm, honest, slightly vulnerable. Leave the letter unfinished for them to continue.",
    }

    return (
        f"Wish: \"{wish.wish_text}\"\n"
        f"Profile:\n{profile}{pattern_str}{tension_str}\n\n"
        f"{card_instruction[card_type]}\n"
        f"{_TONE_CALIBRATION}"
        f"{_ANTI_HOROSCOPE}\n"
        f"BANNED phrases: {', '.join(_BANNED_PHRASES[:6])}\n"
        'JSON: {"text": str, "related_dimensions": [str]}'
    )


def _call_sonnet(prompt: str, api_key: str, prefill: str = "") -> dict[str, Any]:
    """Call Sonnet via Anthropic SDK. Returns parsed JSON dict.

    Uses prefill technique: start the assistant response with grounded text
    to force personalization from the first sentence.
    """
    import anthropic

    client = anthropic.Anthropic(
        api_key=api_key,
        base_url="https://openrouter.ai/api",
    )

    messages = [{"role": "user", "content": prompt}]
    # Prefill forces Claude to continue from a grounded starting point
    if prefill:
        messages.append({"role": "assistant", "content": prefill})

    response = client.messages.create(
        model="anthropic/claude-sonnet-4",
        max_tokens=512,
        messages=messages,
    )
    raw = response.content[0].text.strip()
    # If prefilled, prepend the prefill to the response
    if prefill:
        raw = prefill + raw

    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(raw[start:end])
    return {"text": raw, "related_dimensions": []}


def _extract_related_stars(
    card_type: CardType,
    detector_results: DetectorResults,
) -> list[str]:
    """Extract star labels related to the fulfillment. Zero LLM."""
    stars: list[str] = []

    if card_type == CardType.INSIGHT:
        if detector_results.conflict.get("style"):
            stars.append(f"conflict:{detector_results.conflict['style']}")
        if detector_results.attachment.get("style"):
            stars.append(f"attachment:{detector_results.attachment['style']}")

    elif card_type == CardType.RELATIONSHIP_ANALYSIS:
        if detector_results.conflict.get("style"):
            stars.append(f"conflict:{detector_results.conflict['style']}")
        if detector_results.love_language.get("primary"):
            stars.append(f"love_language:{detector_results.love_language['primary']}")

    elif card_type == CardType.EMOTION_TRACE:
        top_emo = detector_results.emotion.get("emotions", {})
        for emo, score in sorted(top_emo.items(), key=lambda x: x[1], reverse=True)[:2]:
            stars.append(f"emotion:{emo}")

    elif card_type == CardType.SOUL_PORTRAIT:
        if detector_results.mbti.get("type"):
            stars.append(f"mbti:{detector_results.mbti['type']}")
        if detector_results.values.get("top_values"):
            stars.append(f"values:{detector_results.values['top_values'][0]}")

    elif card_type == CardType.SELF_DIALOGUE:
        if detector_results.fragility.get("pattern"):
            stars.append(f"fragility:{detector_results.fragility['pattern']}")

    return stars


def fulfill(
    wish: ClassifiedWish,
    detector_results: DetectorResults,
    cross_detector_patterns: list[CrossDetectorPattern] | None = None,
    soul_type: dict[str, Any] | None = None,
    life_chapter: dict[str, Any] | None = None,
    api_key: str | None = None,
) -> L1FulfillmentResult:
    """Generate a personalized L1 fulfillment for a classified wish.

    Args:
        wish: Classified wish (must be L1).
        detector_results: All 16 detector results.
        cross_detector_patterns: Cross-detector synthesized patterns.
        soul_type: Soul type dict (name, tagline, description).
        life_chapter: Current life chapter dict (theme, narrative).
        api_key: API key for Sonnet. If None, reads from ANTHROPIC_API_KEY env.

    Returns:
        L1FulfillmentResult with personalized text, related stars, and card type.

    Raises:
        ValueError: If wish is not L1 level.
    """
    if wish.level != WishLevel.L1:
        raise ValueError(f"L1Fulfiller only handles L1 wishes, got {wish.level}")

    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    card_type = _select_card_type(wish.wish_type)
    patterns = cross_detector_patterns or []
    soul = soul_type or {}
    chapter = life_chapter or {}

    # Build profile and prompt
    profile = _extract_profile_summary(detector_results, soul, chapter)
    prompt = _build_fulfillment_prompt(wish, card_type, profile, patterns)

    # Build prefill to force grounding (Claude-specific technique)
    prefill = '{"text": "'

    # Call Sonnet
    resp = _call_sonnet(prompt, key, prefill=prefill)
    text = resp.get("text", "")
    related_dims = resp.get("related_dimensions", [])

    # Extract related star references (zero LLM)
    related_stars = _extract_related_stars(card_type, detector_results)
    # Add dimensions from LLM response
    for dim in related_dims:
        tag = f"dimension:{dim}"
        if tag not in related_stars:
            related_stars.append(tag)

    return L1FulfillmentResult(
        fulfillment_text=text,
        related_stars=related_stars,
        card_type=card_type,
    )
