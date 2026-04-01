"""Translation API — MyMemory free translation service.

Zero auth (up to 1000 words/day free). No API key required for basic usage.
Great for: need_translation, homesick, new_place, immigration_stress.
"""

from __future__ import annotations

import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote


MYMEMORY_URL = "https://api.mymemory.translated.net/get"

# Common language codes for detection
_LANG_MAP = {
    "zh": "Chinese", "ar": "Arabic", "es": "Spanish", "fr": "French",
    "de": "German", "ja": "Japanese", "ko": "Korean", "pt": "Portuguese",
    "ru": "Russian", "hi": "Hindi", "tr": "Turkish", "it": "Italian",
    "nl": "Dutch", "pl": "Polish", "sv": "Swedish", "en": "English",
    "fa": "Persian", "ur": "Urdu", "bn": "Bengali", "vi": "Vietnamese",
    "id": "Indonesian", "ms": "Malay", "th": "Thai",
}


def translate_text(
    text: str,
    source_lang: str = "auto",
    target_lang: str = "en",
) -> dict[str, Any]:
    """Translate text using MyMemory API (no auth required).

    Args:
        text: Text to translate (max ~500 chars for free tier)
        source_lang: Source language code (e.g. "zh", "ar") or "auto"
        target_lang: Target language code

    Returns dict with: translated, source_lang, target_lang, result.
    """
    if not text or not text.strip():
        return {}

    # Truncate to safe length
    text_clean = text.strip()[:500]

    lang_pair = f"{source_lang}|{target_lang}"
    url = f"{MYMEMORY_URL}?q={quote(text_clean)}&langpair={lang_pair}"

    try:
        req = Request(url, headers={"User-Agent": "wish-engine/1.0"})
        with urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        if data.get("responseStatus") != 200:
            return {}

        translated = data.get("responseData", {}).get("translatedText", "")
        if not translated:
            return {}

        detected = data.get("responseData", {}).get("detectedLanguage") or source_lang
        target_name = _LANG_MAP.get(target_lang, target_lang.upper())

        return {
            "original": text_clean,
            "translated": translated,
            "source_lang": detected,
            "target_lang": target_lang,
            "target_lang_name": target_name,
            "result": translated,
        }

    except (URLError, json.JSONDecodeError, OSError, TimeoutError, KeyError):
        return {}


def get_translation_resources(target_lang: str = "en") -> dict[str, Any]:
    """Return free translation/language-learning resources for a language.

    Used when user needs language help but no specific text to translate.
    """
    lang_name = _LANG_MAP.get(target_lang, target_lang.upper())

    resources = {
        "en": {
            "app": "Duolingo (free)",
            "url": "https://www.duolingo.com",
            "description": "Learn English for free — 15 min/day",
        },
        "zh": {
            "app": "HelloChinese (free)",
            "url": "https://www.hellochinese.cc",
            "description": "Learn Mandarin — free app",
        },
        "ar": {
            "app": "Duolingo Arabic",
            "url": "https://www.duolingo.com",
            "description": "Learn Arabic for free",
        },
        "es": {
            "app": "Duolingo Spanish",
            "url": "https://www.duolingo.com",
            "description": "Learn Spanish for free",
        },
        "fr": {
            "app": "Duolingo French",
            "url": "https://www.duolingo.com",
            "description": "Learn French for free",
        },
    }

    res = resources.get(target_lang, {
        "app": "Google Translate (free)",
        "url": "https://translate.google.com",
        "description": f"Translate to/from {lang_name} — free",
    })

    return {
        "language": lang_name,
        "app": res["app"],
        "url": res["url"],
        "description": res["description"],
        "result": f"{res['app']}: {res['description']}",
    }
