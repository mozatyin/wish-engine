"""ScamDetectionFulfiller — scam and fraud detection resources.

10-entry catalog of scam identification and prevention guides. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Catalog (10 entries) ─────────────────────────────────────────────────────

SCAM_CATALOG: list[dict] = [
    {
        "title": "Phishing Email Detection",
        "description": "Learn to spot phishing emails — red flags, sender verification, and safe practices.",
        "category": "phishing_email",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["phishing", "email", "detection", "calming", "self-paced"],
    },
    {
        "title": "Romance Scam Warning Signs",
        "description": "Recognize romance scams — common patterns, reverse image search, and red flags.",
        "category": "romance_scam",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["romance", "scam", "detection", "calming"],
    },
    {
        "title": "Investment Scam Guide",
        "description": "Identify fake investment schemes — crypto scams, Ponzi schemes, and too-good-to-be-true returns.",
        "category": "investment_scam",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["investment", "scam", "financial", "detection", "calming"],
    },
    {
        "title": "Deepfake Detection Tools",
        "description": "Identify AI-generated fake videos and images — tools and techniques for verification.",
        "category": "deepfake_detection",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["deepfake", "ai", "detection", "calming", "self-paced"],
    },
    {
        "title": "Phone Scam Protection",
        "description": "Block robocalls, identify spoofed numbers, and handle phone-based scams safely.",
        "category": "phone_scam",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["phone", "scam", "protection", "calming", "practical"],
    },
    {
        "title": "QR Code Scam Awareness",
        "description": "Verify QR codes before scanning — avoid malicious redirects and payment fraud.",
        "category": "qr_code_scam",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["qr_code", "scam", "detection", "calming"],
    },
    {
        "title": "Job Scam Detection",
        "description": "Spot fake job postings — upfront payment requests, vague descriptions, and verification tips.",
        "category": "job_scam",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["job", "scam", "detection", "calming", "practical"],
    },
    {
        "title": "Rental Scam Prevention",
        "description": "Avoid rental fraud — verify listings, meet landlords safely, and protect deposits.",
        "category": "rental_scam",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["rental", "scam", "detection", "calming", "practical"],
    },
    {
        "title": "Lottery and Prize Scam Guide",
        "description": "If you did not enter, you did not win — recognizing lottery and prize fraud.",
        "category": "lottery_scam",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["lottery", "scam", "detection", "calming"],
    },
    {
        "title": "Identity Theft Protection",
        "description": "Prevent identity theft — credit monitoring, document security, and recovery steps.",
        "category": "identity_theft",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["identity", "theft", "protection", "calming", "self-paced"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_SCAM_KEYWORDS: dict[str, list[str]] = {
    "诈骗": [],
    "scam": [],
    "fraud": [],
    "骗": [],
    "احتيال": [],
    "fake": [],
    "deepfake": ["deepfake", "ai"],
    "phishing": ["phishing", "email"],
    "钓鱼": ["phishing", "email"],
    "romance scam": ["romance", "scam"],
    "杀猪盘": ["romance", "scam"],
    "investment": ["investment", "financial"],
    "投资": ["investment", "financial"],
    "identity theft": ["identity", "theft"],
    "身份盗用": ["identity", "theft"],
    "phone": ["phone"],
    "电话": ["phone"],
    "job scam": ["job", "scam"],
    "rental": ["rental"],
}


def _match_scam_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _SCAM_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class ScamDetectionFulfiller(L2Fulfiller):
    """L2 fulfiller for scam detection — fraud identification and prevention.

    10 curated entries covering common scam types. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_scam_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in SCAM_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in SCAM_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in SCAM_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Stay vigilant — scammers constantly evolve their tactics.",
                delay_hours=168,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "detection" in tags:
        return "Learn to identify this type of scam before it happens"
    if "protection" in tags:
        return "Proactive protection against fraud"
    if "practical" in tags:
        return "Actionable steps to stay safe"
    return "Knowledge to protect yourself from scams"
