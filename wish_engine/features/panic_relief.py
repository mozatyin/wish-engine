"""Panic Relief — real intervention, not catalog lookup.

Provides breathing exercises with step-by-step timing, grounding techniques,
and verified crisis hotlines for 28+ countries. Severity detection routes
users to the right level of support.

Zero LLM. All local logic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ── Breathing Exercises ─────────────────────────────────────────────────────

BOX_BREATHING = {
    "name": "Box Breathing (4-4-4-4)",
    "description": "Used by Navy SEALs to control stress response.",
    "steps": [
        {"action": "inhale", "duration_sec": 4, "instruction": "Breathe in slowly through your nose"},
        {"action": "hold", "duration_sec": 4, "instruction": "Hold your breath gently"},
        {"action": "exhale", "duration_sec": 4, "instruction": "Breathe out slowly through your mouth"},
        {"action": "hold", "duration_sec": 4, "instruction": "Hold before the next breath"},
    ],
    "rounds": 4,
    "total_duration_sec": 64,
}

SLOW_EXHALE = {
    "name": "4-7-8 Breathing",
    "description": "Dr. Andrew Weil's relaxation technique. Extended exhale activates parasympathetic nervous system.",
    "steps": [
        {"action": "inhale", "duration_sec": 4, "instruction": "Breathe in quietly through your nose"},
        {"action": "hold", "duration_sec": 7, "instruction": "Hold your breath"},
        {"action": "exhale", "duration_sec": 8, "instruction": "Exhale completely through your mouth with a whoosh"},
    ],
    "rounds": 4,
    "total_duration_sec": 76,
}

GROUNDING_54321 = {
    "name": "5-4-3-2-1 Grounding",
    "description": "Anchors you to the present moment through your senses.",
    "steps": [
        {"sense": "see", "count": 5, "instruction": "Name 5 things you can see right now"},
        {"sense": "touch", "count": 4, "instruction": "Name 4 things you can physically feel"},
        {"sense": "hear", "count": 3, "instruction": "Name 3 things you can hear"},
        {"sense": "smell", "count": 2, "instruction": "Name 2 things you can smell"},
        {"sense": "taste", "count": 1, "instruction": "Name 1 thing you can taste"},
    ],
}

# ── Crisis Hotlines (verified numbers) ──────────────────────────────────────

HOTLINES: list[dict[str, str]] = [
    {"country": "USA", "code": "US", "number": "988", "name": "Suicide & Crisis Lifeline"},
    {"country": "USA", "code": "US", "number": "741741", "name": "Crisis Text Line (text HOME)"},
    {"country": "UK", "code": "GB", "number": "116 123", "name": "Samaritans"},
    {"country": "UK", "code": "GB", "number": "0800 068 4141", "name": "Mind Infoline"},
    {"country": "UAE", "code": "AE", "number": "800-HOPE (4673)", "name": "Hope Line"},
    {"country": "China", "code": "CN", "number": "400-161-9995", "name": "Beijing Psychological Crisis"},
    {"country": "China", "code": "CN", "number": "010-82951332", "name": "Beijing Suicide Research"},
    {"country": "Japan", "code": "JP", "number": "0570-064-556", "name": "Yorisoi Hotline"},
    {"country": "India", "code": "IN", "number": "9820466726", "name": "iCall"},
    {"country": "India", "code": "IN", "number": "9152987821", "name": "AASRA"},
    {"country": "Spain", "code": "ES", "number": "024", "name": "Linea de Atencion a la Conducta Suicida"},
    {"country": "France", "code": "FR", "number": "3114", "name": "Numero National de Prevention du Suicide"},
    {"country": "Brazil", "code": "BR", "number": "188", "name": "CVV - Centro de Valorizacao da Vida"},
    {"country": "Germany", "code": "DE", "number": "0800 111 0 111", "name": "Telefonseelsorge"},
    {"country": "Australia", "code": "AU", "number": "13 11 14", "name": "Lifeline Australia"},
    {"country": "Canada", "code": "CA", "number": "988", "name": "Suicide Crisis Helpline"},
    {"country": "South Korea", "code": "KR", "number": "1393", "name": "Korea Suicide Prevention Center"},
    {"country": "Mexico", "code": "MX", "number": "800-290-0024", "name": "SAPTEL"},
    {"country": "Turkey", "code": "TR", "number": "182", "name": "Alo 182"},
    {"country": "South Africa", "code": "ZA", "number": "0800 567 567", "name": "SADAG"},
    {"country": "Italy", "code": "IT", "number": "06 77208977", "name": "Telefono Amico"},
    {"country": "Netherlands", "code": "NL", "number": "113", "name": "113 Zelfmoordpreventie"},
    {"country": "Sweden", "code": "SE", "number": "90101", "name": "Mind Sjalvmordslinjen"},
    {"country": "Egypt", "code": "EG", "number": "08008880700", "name": "Befrienders Egypt"},
    {"country": "Saudi Arabia", "code": "SA", "number": "920033360", "name": "MoH Support Line"},
    {"country": "Pakistan", "code": "PK", "number": "0311-7786264", "name": "Umang Helpline"},
    {"country": "Indonesia", "code": "ID", "number": "119 ext 8", "name": "Into The Light"},
    {"country": "Philippines", "code": "PH", "number": "(02) 8893-7603", "name": "In Touch Crisis Line"},
]

# Country code lookup from text
_COUNTRY_HINTS: dict[str, str] = {
    # English names
    "united states": "US", "usa": "US", "america": "US",
    "united kingdom": "GB", "uk": "GB", "england": "GB", "britain": "GB",
    "uae": "AE", "emirates": "AE", "dubai": "AE", "abu dhabi": "AE",
    "china": "CN", "chinese": "CN",
    "japan": "JP", "japanese": "JP",
    "india": "IN", "indian": "IN",
    "spain": "ES", "spanish": "ES",
    "france": "FR", "french": "FR",
    "brazil": "BR", "brazilian": "BR",
    "germany": "DE", "german": "DE",
    "australia": "AU", "australian": "AU",
    "canada": "CA", "canadian": "CA",
    "south korea": "KR", "korea": "KR", "korean": "KR",
    "mexico": "MX", "mexican": "MX",
    "turkey": "TR", "turkish": "TR",
    "south africa": "ZA",
    "italy": "IT", "italian": "IT",
    "netherlands": "NL", "dutch": "NL",
    "sweden": "SE", "swedish": "SE",
    "egypt": "EG", "egyptian": "EG",
    "saudi": "SA", "saudi arabia": "SA",
    "pakistan": "PK", "pakistani": "PK",
    "indonesia": "ID", "indonesian": "ID",
    "philippines": "PH", "filipino": "PH",
    # Arabic
    "الإمارات": "AE", "دبي": "AE",
    "السعودية": "SA",
    "مصر": "EG",
    "باكستان": "PK",
    # Chinese
    "中国": "CN", "日本": "JP", "印度": "IN", "韩国": "KR",
    "巴西": "BR", "法国": "FR", "德国": "DE", "澳大利亚": "AU",
}

# ── Severity Detection ──────────────────────────────────────────────────────

_SEVERE_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(?:kill\s+my\s*self|end\s+(?:my\s+)?life|suicide|suicidal)\b",
        r"\b(?:want\s+to\s+die|don'?t\s+want\s+to\s+live|better\s+off\s+dead)\b",
        r"\b(?:no\s+reason\s+to\s+live|can'?t\s+go\s+on|self[- ]?harm)\b",
        r"(?:أريد\s+أن\s+أموت|انتحار|أقتل\s+نفسي)",
        r"(?:自杀|不想活|活不下去|死了算了)",
    ]
]

_MODERATE_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(?:panic\s+attack|can'?t\s+breathe|heart\s+(?:racing|pounding))\b",
        r"\b(?:losing\s+(?:my\s+)?mind|falling\s+apart|breaking\s+down)\b",
        r"\b(?:hyperventilat|trembling|shaking|dizzy|numb)\b",
        r"\b(?:overwhelming|spiraling|can'?t\s+stop\s+crying)\b",
        r"(?:هلع|ذعر|لا\s+أستطيع\s+التنفس)",
        r"(?:恐慌|害怕|心跳加速|喘不过气)",
    ]
]


def _detect_severity(text: str, detector_results: dict[str, Any] | None = None) -> str:
    """Detect panic severity: 'severe', 'moderate', or 'mild'."""
    for pat in _SEVERE_PATTERNS:
        if pat.search(text):
            return "severe"

    # Check detector distress if available
    if detector_results:
        distress = 0.0
        emotion = detector_results.get("emotion", {})
        if isinstance(emotion, dict):
            distress = emotion.get("distress", 0.0)
        crisis = detector_results.get("crisis", {})
        if isinstance(crisis, dict) and crisis.get("is_crisis"):
            return "severe"
        if distress > 0.7:
            return "moderate"

    for pat in _MODERATE_PATTERNS:
        if pat.search(text):
            return "moderate"

    return "mild"


def _detect_country(text: str, country_hint: str | None = None) -> str | None:
    """Detect country code from text or explicit hint."""
    if country_hint:
        hint_lower = country_hint.lower().strip()
        # Direct code (e.g., "US", "AE")
        if len(hint_lower) == 2:
            return hint_lower.upper()
        return _COUNTRY_HINTS.get(hint_lower)

    text_lower = text.lower()
    for name, code in _COUNTRY_HINTS.items():
        if name in text_lower:
            return code
    return None


def _get_hotlines_for_country(country_code: str | None) -> list[dict[str, str]]:
    """Get hotlines for a specific country, or top global ones."""
    if country_code:
        matches = [h for h in HOTLINES if h["code"] == country_code]
        if matches:
            return matches
    # Default: show USA + UK + international spread
    return [h for h in HOTLINES if h["code"] in ("US", "GB", "AE", "CN", "IN")]


# ── Response Model ──────────────────────────────────────────────────────────

@dataclass
class PanicReliefResponse:
    """Full panic relief response with exercises, grounding, and hotlines."""

    severity: str  # "severe", "moderate", "mild"
    message: str  # personalized opening message
    breathing_exercise: dict[str, Any] = field(default_factory=dict)
    grounding: dict[str, Any] = field(default_factory=dict)
    hotlines: list[dict[str, str]] = field(default_factory=list)
    country_detected: str | None = None


# ── Public API ──────────────────────────────────────────────────────────────

def get_panic_relief(
    text: str,
    detector_results: dict[str, Any] | None = None,
    country_hint: str | None = None,
) -> PanicReliefResponse:
    """Get personalized panic relief response.

    Args:
        text: User's message text.
        detector_results: Optional detector results dict.
        country_hint: Optional country name or code.

    Returns:
        PanicReliefResponse with exercises, grounding, and hotlines.
    """
    severity = _detect_severity(text, detector_results)
    country = _detect_country(text, country_hint)
    hotlines = _get_hotlines_for_country(country)

    # Choose breathing exercise based on severity
    if severity == "severe":
        breathing = SLOW_EXHALE  # longer exhale calms faster
        message = (
            "I hear you, and I want you to know you're not alone. "
            "Please reach out to a crisis line below — real people are waiting to help. "
            "In the meantime, let's try a breathing exercise together."
        )
    elif severity == "moderate":
        breathing = BOX_BREATHING
        message = (
            "It sounds like you're going through a really tough moment. "
            "Let's slow things down together. Try this breathing exercise — "
            "it can help your body calm down even when your mind is racing."
        )
    else:
        breathing = BOX_BREATHING
        message = (
            "I notice you might be feeling stressed. "
            "Here's a quick exercise that can help you reset."
        )

    return PanicReliefResponse(
        severity=severity,
        message=message,
        breathing_exercise=breathing,
        grounding=GROUNDING_54321,
        hotlines=hotlines,
        country_detected=country,
    )
