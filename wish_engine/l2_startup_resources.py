"""StartupResourceFulfiller — values-driven startup resource recommendations.

15-entry curated startup resource catalog. Values: self-direction + achievement
map to entrepreneurial resources. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Values → Startup Resource Mapping ────────────────────────────────────────

VALUES_STARTUP_MAP: dict[str, list[str]] = {
    "self-direction": ["solo_founder", "learning", "mentorship", "community"],
    "achievement": ["accelerator", "competition", "funding", "networking"],
    "stimulation": ["events", "competition", "networking"],
    "security": ["legal", "accounting", "grants", "structured"],
    "benevolence": ["social_impact", "community", "mentorship"],
    "universalism": ["social_impact", "grants", "community"],
    "power": ["funding", "accelerator", "networking"],
}

# ── Startup Resource Catalog (15 entries) ────────────────────────────────────

STARTUP_CATALOG: list[dict] = [
    {
        "title": "Startup Incubator Program",
        "description": "6-12 month program with mentors, office space, and demo day. Structured path from idea to MVP.",
        "category": "incubator",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["structured", "mentorship", "community", "learning", "early_stage"],
    },
    {
        "title": "Accelerator (YC/Techstars style)",
        "description": "3-month intensive: seed funding, mentor access, and investor demo day.",
        "category": "accelerator",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["accelerator", "funding", "networking", "competition", "intensive"],
    },
    {
        "title": "Startup-Focused Coworking",
        "description": "Work alongside other founders. Serendipity happens at the coffee machine.",
        "category": "coworking_startup",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["community", "networking", "solo_founder", "practical"],
    },
    {
        "title": "Angel Investor Meetup",
        "description": "Pitch informally to angel investors. Build relationships before you need money.",
        "category": "angel_investor_meetup",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["funding", "networking", "events", "practical"],
    },
    {
        "title": "Pitch Competition",
        "description": "Practice your pitch, get feedback, and potentially win seed capital.",
        "category": "pitch_event",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["competition", "events", "funding", "networking"],
    },
    {
        "title": "Startup Weekend",
        "description": "54 hours to go from idea to prototype. Find cofounders and test ideas fast.",
        "category": "startup_weekend",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["competition", "events", "community", "intensive", "learning"],
    },
    {
        "title": "Founder Community (Online/Local)",
        "description": "Slack groups, WhatsApp circles, or local meetups of people who get it.",
        "category": "founder_community",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["community", "solo_founder", "networking", "mentorship", "self-paced"],
    },
    {
        "title": "Startup Legal Clinic",
        "description": "Free or low-cost legal advice on incorporation, IP, and contracts.",
        "category": "legal_clinic_startup",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["legal", "structured", "practical", "early_stage"],
    },
    {
        "title": "Startup Accounting / Tax Help",
        "description": "Bookkeeping, tax optimization, and financial modeling for early-stage startups.",
        "category": "accounting_startup",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["accounting", "structured", "practical", "early_stage"],
    },
    {
        "title": "Mentor Network",
        "description": "Experienced founders offering 1-on-1 guidance. Find someone who has been where you are.",
        "category": "mentor_network",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["mentorship", "solo_founder", "learning", "self-paced", "calming"],
    },
    {
        "title": "University Innovation Lab",
        "description": "Access to research, talent, and prototype labs. Often free for student founders.",
        "category": "university_innovation",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["learning", "community", "practical", "early_stage"],
    },
    {
        "title": "Government Grants & Programs",
        "description": "Non-dilutive funding — grants, subsidies, and tax incentives for startups.",
        "category": "government_grants",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["grants", "funding", "structured", "practical", "social_impact"],
    },
    {
        "title": "Venture Capital Introduction",
        "description": "Warm introductions to Series A/B investors. For post-traction startups.",
        "category": "venture_capital",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["funding", "networking", "accelerator"],
    },
    {
        "title": "Startup Conference",
        "description": "Web Summit, TechCrunch Disrupt, or local equivalents. Learn, network, and get inspired.",
        "category": "startup_conference",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["events", "networking", "learning", "competition"],
    },
    {
        "title": "Founder Retreat",
        "description": "Step back from the grind. Strategy, reflection, and peer support in nature.",
        "category": "founder_retreat",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["community", "solo_founder", "mentorship", "calming", "self-paced"],
    },
]


def _match_startup_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    kw_map = {
        "funding": ["funding"],
        "融资": ["funding"],
        "investor": ["funding", "networking"],
        "投资": ["funding", "networking"],
        "mentor": ["mentorship"],
        "导师": ["mentorship"],
        "legal": ["legal", "structured"],
        "法律": ["legal", "structured"],
        "cowork": ["community", "solo_founder"],
        "community": ["community"],
        "社区": ["community"],
        "pitch": ["competition", "events"],
        "路演": ["competition", "events"],
        "grant": ["grants", "funding"],
        "补贴": ["grants", "funding"],
        "accelerator": ["accelerator", "intensive"],
        "加速器": ["accelerator", "intensive"],
        "incubator": ["structured", "mentorship"],
        "孵化器": ["structured", "mentorship"],
    }
    for keyword, tags in kw_map.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


def _values_to_startup_tags(det: DetectorResults) -> list[str]:
    tags: list[str] = []
    top_values = det.values.get("top_values", [])
    for value in top_values:
        for t in VALUES_STARTUP_MAP.get(value, []):
            if t not in tags:
                tags.append(t)
    return tags


class StartupResourceFulfiller(L2Fulfiller):
    """L2 fulfiller for startup wishes — values-driven resource recommendations.

    15 startup resources, values-matched. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_startup_tags(wish.wish_text)
        values_tags = _values_to_startup_tags(detector_results)

        all_tags = list(keyword_tags)
        for t in values_tags:
            if t not in all_tags:
                all_tags.append(t)

        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in STARTUP_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in STARTUP_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in STARTUP_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, detector_results)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Every big company started with one small step. Take yours.",
                delay_hours=48,
            ),
        )


def _build_relevance_reason(item: dict, det: DetectorResults) -> str:
    tags = set(item.get("tags", []))
    top_values = det.values.get("top_values", [])

    if "self-direction" in top_values and "solo_founder" in tags:
        return "Resources for independent founders like you"
    if "achievement" in top_values and "accelerator" in tags:
        return "High-achievement path matching your drive"
    if "security" in top_values and "structured" in tags:
        return "Structured support to reduce startup risk"
    if "benevolence" in top_values and "social_impact" in tags:
        return "Build something that helps others — matching your values"

    return f"Startup resource: {item.get('category', '').replace('_', ' ')}"
