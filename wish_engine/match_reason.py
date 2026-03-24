"""Match Reason Generator — creates human-readable reason for L3 matches.

Called ONLY after mutual verification. 1× Haiku per match.
Uses Zero-AI language (V10 §7.2).
"""

from __future__ import annotations

import json
import os
from typing import Any

from wish_engine.marketplace import Match


# Zero-LLM templates for common match patterns (avoids Haiku for simple cases)
_TEMPLATES: dict[str, list[str]] = {
    "en": [
        "You both know what it feels like to {shared}",
        "Your stars share something rare — {shared}",
        "A resonance was discovered: {shared}",
    ],
    "zh": [
        "你们都经历过{shared}",
        "你们的星星有着相同的频率 — {shared}",
        "一种共鸣被发现了：{shared}",
    ],
    "ar": [
        "كلاكما يعرف شعور {shared}",
        "نجومكما تتشارك شيئاً نادراً — {shared}",
    ],
}

# Capability → human-readable description
_CAPABILITY_TEXT: dict[str, dict[str, str]] = {
    "entrepreneurial_experience": {"en": "building something from nothing", "zh": "从零开始创造", "ar": "بناء شيء من لا شيء"},
    "willing_to_listen": {"en": "truly listening", "zh": "真正的倾听", "ar": "الاستماع الحقيقي"},
    "empathy": {"en": "understanding without judgment", "zh": "不带评判的理解", "ar": "التفهم بلا أحكام"},
    "shared_experience": {"en": "walking a similar path", "zh": "走过相似的路", "ar": "المشي في طريق مشابه"},
    "understands_loneliness": {"en": "the weight of being alone in a crowd", "zh": "人群中的孤独", "ar": "ثقل الوحدة وسط الناس"},
    "non_judgmental": {"en": "accepting others as they are", "zh": "接纳真实的彼此", "ar": "قبول الآخرين كما هم"},
    "good_listener": {"en": "hearing what's left unsaid", "zh": "听见未说出口的话", "ar": "سماع ما لم يُقال"},
    "active_listening": {"en": "being fully present", "zh": "全心全意的陪伴", "ar": "الحضور الكامل"},
    "domain_expertise": {"en": "deep knowledge in the field", "zh": "领域的深度经验", "ar": "خبرة عميقة في المجال"},
    "high_benevolence": {"en": "caring for others", "zh": "关心他人的善意", "ar": "الاهتمام بالآخرين"},
}


def generate_match_reason(
    match: Match,
    need_seeking: list[str],
    offer_capabilities: list[str],
    language: str = "en",
    api_key: str | None = None,
) -> str:
    """Generate a human-readable match reason.

    Strategy:
    1. If shared capabilities have known templates → use template (zero LLM)
    2. If not → 1× Haiku to generate reason

    Uses Zero-AI language: never say "algorithm matched you".
    """
    # Find shared capabilities
    shared = set(need_seeking) & set(offer_capabilities)

    if shared:
        # Try template path (zero LLM)
        lang_templates = _TEMPLATES.get(language, _TEMPLATES["en"])
        lang_caps = _CAPABILITY_TEXT

        # Pick the most descriptive shared capability
        for cap in shared:
            if cap in lang_caps:
                cap_text = lang_caps[cap].get(language, lang_caps[cap]["en"])
                template = lang_templates[0]
                return template.format(shared=cap_text)

    # Fallback: 1× Haiku
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return _generate_via_haiku(need_seeking, offer_capabilities, language, key)

    # No API key, no template match → generic
    generic = {
        "en": "Your stars found each other",
        "zh": "你们的星星找到了彼此",
        "ar": "نجومكما وجدت بعضها",
    }
    return generic.get(language, generic["en"])


def _generate_via_haiku(
    seeking: list[str],
    offering: list[str],
    language: str,
    api_key: str,
) -> str:
    """Generate match reason via Haiku. 1 call, ~30 tokens output."""
    import anthropic

    lang_instruction = {
        "en": "in English",
        "zh": "in Chinese (中文)",
        "ar": "in Arabic (العربية)",
    }

    prompt = (
        f"Two people's wishes resonate. One seeks: {', '.join(seeking)}. "
        f"The other offers: {', '.join(offering)}.\n"
        f"Write ONE sentence {lang_instruction.get(language, 'in English')} "
        f"explaining their connection. Warm, poetic. "
        f"NEVER say 'AI', 'algorithm', 'match', 'system'. "
        f"Say it like: 'You both know what it feels like to...'"
    )

    try:
        client = anthropic.Anthropic(api_key=api_key, base_url="https://openrouter.ai/api")
        response = client.messages.create(
            model="anthropic/claude-haiku-4-5-20251001",
            max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip().strip('"')
    except Exception:
        generic = {"en": "Your stars found each other", "zh": "你们的星星找到了彼此", "ar": "نجومكما وجدت بعضها"}
        return generic.get(language, generic["en"])
