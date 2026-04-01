"""Crisis APIs — hardcoded, zero-network crisis resources.

NO network calls. Returns phone numbers + org names immediately.
For: suicide, domestic violence, addiction, mental health.

Organized by:
  - crisis_type: "suicide" | "domestic_violence" | "addiction" | "mental_health"
  - language: "en" | "zh" | "ar" (fallback always "en")
  - country_code: ISO2 (e.g. "US", "GB", "AE") — falls back to global list

All numbers verified as of 2025. Update this list periodically.
"""
from __future__ import annotations

_CRISIS_DATA: dict[str, list[dict]] = {

    # ── SUICIDE / SELF-HARM ────────────────────────────────────────────────
    "suicide": [
        {"country": "US",  "name": "988 Suicide & Crisis Lifeline",         "number": "988",              "text": "Text HOME to 741741", "lang": "en"},
        {"country": "US",  "name": "Crisis Text Line",                       "number": "741741",           "text": "Text HOME",          "lang": "en"},
        {"country": "GB",  "name": "Samaritans",                             "number": "116 123",          "text": None,                 "lang": "en"},
        {"country": "GB",  "name": "PAPYRUS (under-35)",                     "number": "0800 068 4141",    "text": "Text PAP to 88247",  "lang": "en"},
        {"country": "AE",  "name": "Hope Line",                              "number": "800-4673",         "text": None,                 "lang": "en"},
        {"country": "CN",  "name": "北京心理危机研究与干预中心",              "number": "010-82951332",     "text": None,                 "lang": "zh"},
        {"country": "CN",  "name": "全国心理援助热线",                       "number": "400-161-9995",     "text": None,                 "lang": "zh"},
        {"country": "IN",  "name": "iCall",                                  "number": "9820466627",       "text": None,                 "lang": "en"},
        {"country": "IN",  "name": "AASRA",                                  "number": "9152987821",       "text": None,                 "lang": "en"},
        {"country": "AU",  "name": "Lifeline Australia",                     "number": "13 11 14",         "text": "Text 0477 13 11 14", "lang": "en"},
        {"country": "CA",  "name": "988 Suicide Crisis Helpline",            "number": "988",              "text": None,                 "lang": "en"},
        {"country": "DE",  "name": "Telefonseelsorge",                       "number": "0800 111 0 111",   "text": None,                 "lang": "en"},
        {"country": "FR",  "name": "3114 Prevention du Suicide",             "number": "3114",             "text": None,                 "lang": "en"},
        {"country": "BR",  "name": "CVV",                                    "number": "188",              "text": None,                 "lang": "en"},
        {"country": "JP",  "name": "Yorisoi Hotline",                        "number": "0120-279-338",     "text": None,                 "lang": "en"},
        {"country": "KR",  "name": "Suicide Prevention Counseling Line",     "number": "1393",             "text": None,                 "lang": "en"},
        {"country": "MX",  "name": "SAPTEL",                                 "number": "800-290-0024",     "text": None,                 "lang": "en"},
        {"country": "ES",  "name": "Linea Atencion Conducta Suicida",        "number": "024",              "text": None,                 "lang": "en"},
        {"country": "ZA",  "name": "SADAG",                                  "number": "0800 567 567",     "text": None,                 "lang": "en"},
        {"country": "SA",  "name": "Mental Health Support Line",             "number": "920033360",        "text": None,                 "lang": "ar"},
        {"country": "EG",  "name": "Befrienders Egypt",                      "number": "08008880700",      "text": None,                 "lang": "ar"},
        {"country": "PK",  "name": "Umang Helpline",                         "number": "0311-7786264",     "text": None,                 "lang": "en"},
        {"country": "ID",  "name": "Into The Light",                         "number": "119 ext 8",        "text": None,                 "lang": "en"},
        {"country": "PH",  "name": "In Touch Crisis Line",                   "number": "(02) 8893-7603",   "text": None,                 "lang": "en"},
        # Global fallback
        {"country": "GLOBAL", "name": "International Association for Suicide Prevention", "number": None, "text": "https://www.iasp.info/resources/Crisis_Centres/", "lang": "en"},
    ],

    # ── DOMESTIC VIOLENCE ────────────────────────────────────────────────
    "domestic_violence": [
        {"country": "US",     "name": "National DV Hotline",            "number": "1-800-799-7233",   "text": "Text START to 88788",  "lang": "en"},
        {"country": "US",     "name": "loveisrespect (teen DV)",        "number": "1-866-331-9474",   "text": "Text LOVEIS to 22522", "lang": "en"},
        {"country": "GB",     "name": "National Domestic Abuse Helpline","number": "0808 2000 247",   "text": None,                   "lang": "en"},
        {"country": "AU",     "name": "1800RESPECT",                    "number": "1800 737 732",     "text": None,                   "lang": "en"},
        {"country": "CA",     "name": "ShelterSafe",                    "number": None,               "text": "sheltersafe.ca",       "lang": "en"},
        {"country": "AE",     "name": "Dubai Foundation for Women & Children", "number": "800-988",  "text": None,                   "lang": "en"},
        {"country": "IN",     "name": "Women Helpline",                 "number": "1091",             "text": None,                   "lang": "en"},
        {"country": "CN",     "name": "National Women Aid Hotline",     "number": "12338",            "text": None,                   "lang": "zh"},
        {"country": "SA",     "name": "Family Safety Program",          "number": "1919",             "text": None,                   "lang": "ar"},
        {"country": "EG",     "name": "National Council for Women",     "number": "15115",            "text": None,                   "lang": "ar"},
        {"country": "DE",     "name": "Hilfetelefon Gewalt gegen Frauen","number": "08000 116 016",   "text": None,                   "lang": "en"},
        {"country": "GLOBAL", "name": "UN Women SafeCities",            "number": None,               "text": "https://www.unwomen.org", "lang": "en"},
    ],

    # ── ADDICTION ────────────────────────────────────────────────────────
    "addiction": [
        {"country": "US",     "name": "SAMHSA National Helpline",       "number": "1-800-662-4357",   "text": None,                   "lang": "en"},
        {"country": "US",     "name": "Alcoholics Anonymous",           "number": None,               "text": "aa.org/find-aa",       "lang": "en"},
        {"country": "US",     "name": "Narcotics Anonymous",            "number": None,               "text": "na.org",               "lang": "en"},
        {"country": "GB",     "name": "Drinkline",                      "number": "0300 123 1110",    "text": None,                   "lang": "en"},
        {"country": "GB",     "name": "Frank (drugs)",                  "number": "0300 123 6600",    "text": "Text 82111",           "lang": "en"},
        {"country": "AU",     "name": "Alcohol Drug Foundation",        "number": "1300 85 85 84",    "text": None,                   "lang": "en"},
        {"country": "CA",     "name": "CAMH",                           "number": "1-800-463-6273",   "text": None,                   "lang": "en"},
        {"country": "CN",     "name": "National Drug Rehab Hotline",    "number": "12320",            "text": None,                   "lang": "zh"},
        {"country": "IN",     "name": "NDDTC Helpline",                 "number": "1800-11-0031",     "text": None,                   "lang": "en"},
        {"country": "AE",     "name": "National Rehabilitation Centre", "number": "800-NRC (672)",    "text": None,                   "lang": "en"},
        {"country": "GLOBAL", "name": "AA World Services",              "number": None,               "text": "aa.org",               "lang": "en"},
    ],

    # ── MENTAL HEALTH (clinical / therapy) ──────────────────────────────
    "mental_health": [
        {"country": "US",     "name": "NAMI Helpline",                  "number": "1-800-950-6264",   "text": "Text NAMI to 741741",  "lang": "en"},
        {"country": "US",     "name": "Psychology Today Find a Therapist","number": None,             "text": "psychologytoday.com/us/therapists", "lang": "en"},
        {"country": "GB",     "name": "Mind Infoline",                  "number": "0300 123 3393",    "text": None,                   "lang": "en"},
        {"country": "AU",     "name": "Beyond Blue",                    "number": "1300 22 4636",     "text": None,                   "lang": "en"},
        {"country": "CA",     "name": "Crisis Services Canada",         "number": "1-833-456-4566",   "text": None,                   "lang": "en"},
        {"country": "IN",     "name": "Vandrevala Foundation",          "number": "1860-2662-345",    "text": None,                   "lang": "en"},
        {"country": "CN",     "name": "Beijing Mental Health Crisis Line","number": "010-82951332",   "text": None,                   "lang": "zh"},
        {"country": "AE",     "name": "Priory Wellbeing Centre Dubai",  "number": "+971-4-2578989",   "text": None,                   "lang": "en"},
        {"country": "SA",     "name": "Mental Health Hotline",          "number": "920033360",        "text": None,                   "lang": "ar"},
        {"country": "GLOBAL", "name": "WHO Mental Health Atlas",        "number": None,               "text": "https://www.who.int/teams/mental-health-and-substance-use", "lang": "en"},
    ],
}


def get_crisis_resources(
    crisis_type: str = "suicide",
    country_code: str | None = None,
    language: str = "en",
    max_results: int = 3,
) -> dict:
    """Return crisis hotlines as a display-ready dict.

    Args:
        crisis_type: "suicide" | "domestic_violence" | "addiction" | "mental_health"
        country_code: ISO2 country code (e.g. "US"). None -> global fallback list.
        language: "en" | "zh" | "ar". Filters results by language when non-"en".
        max_results: Max hotlines to return (default 3 to avoid overwhelming).

    Returns:
        dict with keys: "title", "description", "hotlines" (list), "result" (formatted string).
        The "result" key ensures compatibility with the soul bridge's _format_why() fallback.

    Never raises. Worst case returns the GLOBAL entry.
    """
    all_resources = _CRISIS_DATA.get(crisis_type, _CRISIS_DATA["suicide"])

    candidates: list[dict] = []

    # First priority: exact country match
    if country_code:
        candidates = [r for r in all_resources if r["country"] == country_code]

    # Second priority: language match (for non-English speakers)
    if not candidates and language != "en":
        candidates = [r for r in all_resources if r["lang"] == language]

    # Third priority: global fallbacks (US + GB as most recognized)
    if not candidates:
        candidates = [r for r in all_resources if r["country"] in ("US", "GB", "GLOBAL")]

    # Always cap at max_results
    selected = candidates[:max_results]

    # Format the primary result string for soul bridge template rendering
    if selected:
        primary = selected[0]
        number_str = primary["number"] or primary.get("text", "")
        result_str = f"{primary['name']}: {number_str}"
    else:
        result_str = "Search your local crisis center or call emergency services (911/999/112)"

    # Build formatted description lines
    lines = []
    for r in selected:
        if r["number"]:
            lines.append(f"{r['name']}: {r['number']}")
        elif r.get("text"):
            lines.append(f"{r['name']}: {r['text']}")

    description = " | ".join(lines) if lines else result_str

    return {
        "title": _CRISIS_TITLES.get(crisis_type, "Crisis Support"),
        "description": description,
        "hotlines": selected,
        "result": result_str,          # for {result} in soul bridge templates
        "primary_number": selected[0]["number"] if selected and selected[0]["number"] else None,
        "primary_name": selected[0]["name"] if selected else "Crisis Line",
    }


_CRISIS_TITLES: dict[str, str] = {
    "suicide":          "Crisis Lifeline — Call Now",
    "domestic_violence":"DV Hotline — Confidential 24/7",
    "addiction":        "Addiction Support Line",
    "mental_health":    "Mental Health Support",
}


def is_available() -> bool:
    """Always available — no network required."""
    return True
