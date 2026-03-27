"""SocialJusticeFulfiller — social justice and civic engagement resources.

12-entry catalog of activism, advocacy, and civic participation tools.
Values(universalism) driven. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Catalog (12 entries) ─────────────────────────────────────────────────────

SOCIAL_JUSTICE_CATALOG: list[dict] = [
    {
        "title": "Petition Platform Guide",
        "description": "Create and sign petitions that drive real change — effective petition writing tips.",
        "category": "petition_platform",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["petition", "advocacy", "practical", "calming", "self-paced"],
    },
    {
        "title": "Community Organizing Toolkit",
        "description": "Build coalitions, organize campaigns, and mobilize your community for change.",
        "category": "community_organizing",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["organizing", "community", "activism", "calming"],
    },
    {
        "title": "Policy Advocacy Guide",
        "description": "How to influence policy — contacting representatives, testimony writing, and lobbying basics.",
        "category": "policy_advocacy",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["policy", "advocacy", "government", "calming"],
    },
    {
        "title": "Protest Safety Guide",
        "description": "Stay safe at protests — know your rights, what to bring, and emergency contacts.",
        "category": "protest_safety",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["protest", "safety", "rights", "practical"],
    },
    {
        "title": "Civic Education Resources",
        "description": "Understand how government works — voting, legislation, and your civic rights.",
        "category": "civic_education",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["civic", "education", "rights", "calming", "self-paced"],
    },
    {
        "title": "Voter Registration Help",
        "description": "Register to vote, check your registration status, and find your polling location.",
        "category": "voter_registration",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["voting", "registration", "civic", "calming", "practical"],
    },
    {
        "title": "Human Rights Watch",
        "description": "Stay informed about human rights issues worldwide — reports, actions, and solidarity.",
        "category": "human_rights_watch",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["human_rights", "awareness", "global", "calming"],
    },
    {
        "title": "Investigative Journalism Support",
        "description": "Support independent journalism — platforms, donations, and media literacy.",
        "category": "investigative_journalism",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["journalism", "media", "transparency", "calming"],
    },
    {
        "title": "Whistleblower Support",
        "description": "Resources for whistleblowers — legal protections, secure communication, and support.",
        "category": "whistleblower_support",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["whistleblower", "protection", "legal", "calming"],
    },
    {
        "title": "Transparency Organizations",
        "description": "Connect with organizations working for government and corporate transparency.",
        "category": "transparency_org",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["transparency", "accountability", "advocacy", "calming"],
    },
    {
        "title": "Anti-Corruption Resources",
        "description": "Tools and organizations fighting corruption — reporting channels and awareness.",
        "category": "anti_corruption",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["corruption", "accountability", "advocacy", "calming"],
    },
    {
        "title": "Grassroots Movement Builder",
        "description": "Start a grassroots movement from scratch — templates, strategies, and success stories.",
        "category": "grassroots_movement",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["grassroots", "organizing", "community", "activism", "calming"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_JUSTICE_KEYWORDS: dict[str, list[str]] = {
    "社会正义": [],
    "social justice": [],
    "公正": [],
    "عدالة": [],
    "activism": ["activism"],
    "advocacy": ["advocacy"],
    "protest": ["protest", "safety"],
    "抗议": ["protest", "safety"],
    "vote": ["voting", "registration"],
    "投票": ["voting", "registration"],
    "petition": ["petition", "advocacy"],
    "请愿": ["petition", "advocacy"],
    "human rights": ["human_rights", "awareness"],
    "人权": ["human_rights", "awareness"],
    "corruption": ["corruption", "accountability"],
    "腐败": ["corruption", "accountability"],
    "whistleblower": ["whistleblower", "protection"],
    "grassroots": ["grassroots", "organizing"],
}


def _match_justice_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _JUSTICE_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class SocialJusticeFulfiller(L2Fulfiller):
    """L2 fulfiller for social justice — activism, advocacy, civic engagement.

    12 curated entries. Values(universalism) driven. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_justice_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in SOCIAL_JUSTICE_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in SOCIAL_JUSTICE_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in SOCIAL_JUSTICE_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Change happens one action at a time. Keep going.",
                delay_hours=72,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "activism" in tags:
        return "Take direct action for the change you want to see"
    if "advocacy" in tags:
        return "Advocate for policies that reflect your values"
    if "civic" in tags:
        return "Your civic engagement shapes the world"
    if "accountability" in tags:
        return "Hold power accountable through transparency"
    return "Contribute to a more just society"
