"""CravingAlternativeFulfiller — immediate substitute activities for cravings.

12-entry curated catalog of accessible alternatives. All immediate/actionable. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Craving Alternative Catalog (12 entries) ─────────────────────────────────

CRAVING_CATALOG: list[dict] = [
    {
        "title": "Intense Exercise — Burn It Off",
        "description": "Drop and do 20 pushups, run a mile, or hit a punching bag — redirect the energy.",
        "category": "intense_exercise",
        "noise": "moderate",
        "social": "low",
        "mood": "intense",
        "tags": ["craving", "physical", "immediate", "intense", "body"],
    },
    {
        "title": "Cold Shower Reset",
        "description": "30 seconds of cold water — shocks your nervous system out of craving mode.",
        "category": "cold_shower",
        "noise": "quiet",
        "social": "low",
        "mood": "intense",
        "tags": ["craving", "physical", "immediate", "reset", "solo"],
    },
    {
        "title": "Call Your Sponsor",
        "description": "Pick up the phone right now — your sponsor exists for this exact moment.",
        "category": "call_sponsor",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["craving", "support", "immediate", "connection", "guided"],
    },
    {
        "title": "Urge Surfing Meditation",
        "description": "Observe the craving like a wave — it will rise, peak, and pass. Just watch.",
        "category": "meditation_urge",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["craving", "meditation", "immediate", "mindfulness", "gentle"],
    },
    {
        "title": "Craving Journal Entry",
        "description": "Write down what triggered you right now — naming it weakens it.",
        "category": "journaling_craving",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["craving", "journaling", "immediate", "awareness", "solo"],
    },
    {
        "title": "Healthy Snack Redirect",
        "description": "Eat something flavorful — dark chocolate, spicy nuts, sour candy. Satisfy the mouth.",
        "category": "healthy_snack",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["craving", "food", "immediate", "sensory", "solo"],
    },
    {
        "title": "Nature Walk — 15 Minutes",
        "description": "Step outside and walk for 15 minutes — change your environment, change your state.",
        "category": "walk_nature",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["craving", "nature", "immediate", "movement", "gentle"],
    },
    {
        "title": "Play Music Loud",
        "description": "Put on headphones and blast your favorite song — let sound drown the craving.",
        "category": "play_music",
        "noise": "loud",
        "social": "low",
        "mood": "intense",
        "tags": ["craving", "music", "immediate", "sensory", "solo"],
    },
    {
        "title": "Puzzle or Brain Game",
        "description": "Sudoku, crossword, or any brain teaser — occupy your mind completely.",
        "category": "puzzle_game",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["craving", "cognitive", "immediate", "distraction", "solo"],
    },
    {
        "title": "Quick Volunteer Act",
        "description": "Help someone right now — carry groceries, reply to a friend, do a kind deed.",
        "category": "volunteer_quick",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["craving", "service", "immediate", "connection", "gentle"],
    },
    {
        "title": "Deep Breathing — 4-7-8",
        "description": "Breathe in 4 seconds, hold 7, out 8. Repeat 4 times. Craving weakens each cycle.",
        "category": "deep_breathing",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["craving", "breathing", "immediate", "calming", "solo"],
    },
    {
        "title": "Creative Outlet — Draw or Write",
        "description": "Grab a pen and express what you are feeling — no rules, just release.",
        "category": "creative_outlet",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["craving", "creative", "immediate", "expression", "solo"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_CRAVING_KEYWORDS: dict[str, list[str]] = {
    "渴望": ["craving", "immediate"],
    "craving": ["craving", "immediate"],
    "urge": ["craving", "immediate"],
    "想喝": ["craving", "immediate"],
    "想抽": ["craving", "immediate"],
    "رغبة": ["craving", "immediate"],
    "alternative": ["craving", "distraction"],
    "替代": ["craving", "distraction"],
    "instead": ["craving", "distraction"],
    "relapse": ["craving", "support"],
    "复发": ["craving", "support"],
    "sponsor": ["craving", "connection"],
    "exercise": ["craving", "physical"],
    "breathe": ["craving", "breathing"],
}


def _match_craving_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _CRAVING_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class CravingAlternativeFulfiller(L2Fulfiller):
    """L2 fulfiller for craving alternatives — immediate, accessible substitutes.

    12 curated entries, all actionable right now. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_craving_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in CRAVING_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in CRAVING_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in CRAVING_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Cravings pass. Every one you survive makes you stronger.",
                delay_hours=4,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "physical" in tags:
        return "Burn it off — physical action beats mental wrestling"
    if "connection" in tags:
        return "You do not have to fight this alone"
    if "mindfulness" in tags:
        return "Watch the wave — it will pass"
    if "sensory" in tags:
        return "Redirect your senses to something healthy"
    if "cognitive" in tags:
        return "Occupy your mind — starve the craving"
    return "An immediate alternative to ride out the craving"
