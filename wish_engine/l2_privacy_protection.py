"""PrivacyProtectionFulfiller — digital privacy and security resources.

10-entry catalog of privacy protection tools and guides. Zero LLM.
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

PRIVACY_CATALOG: list[dict] = [
    {
        "title": "Privacy Audit Checklist",
        "description": "Comprehensive privacy audit — check your accounts, permissions, and data exposure.",
        "category": "privacy_audit",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["audit", "checklist", "practical", "calming", "self-paced"],
    },
    {
        "title": "Password Manager Setup",
        "description": "Set up a password manager — never reuse passwords again. Step-by-step guide.",
        "category": "password_manager",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["password", "security", "practical", "calming", "self-paced"],
    },
    {
        "title": "Two-Factor Authentication Guide",
        "description": "Enable 2FA on all your important accounts — the single best security upgrade.",
        "category": "two_factor_auth",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["2fa", "security", "practical", "calming", "self-paced"],
    },
    {
        "title": "Social Media Privacy Settings",
        "description": "Platform-by-platform guide to tightening privacy settings — Facebook, Instagram, TikTok, etc.",
        "category": "social_media_privacy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["social_media", "privacy", "practical", "calming", "self-paced"],
    },
    {
        "title": "Data Deletion Request Guide",
        "description": "How to request deletion of your data from companies — GDPR, CCPA, and templates.",
        "category": "data_deletion_request",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["data", "deletion", "rights", "practical", "calming"],
    },
    {
        "title": "VPN Guide",
        "description": "Understand VPNs — when you need one, how to choose, and how to set it up.",
        "category": "vpn_guide",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["vpn", "security", "privacy", "practical", "calming"],
    },
    {
        "title": "Phishing Detection Training",
        "description": "Learn to spot phishing emails, texts, and websites — protect yourself from scams.",
        "category": "phishing_detection",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["phishing", "detection", "education", "calming", "self-paced"],
    },
    {
        "title": "Stalkerware Detection",
        "description": "Check your phone for stalkerware/spyware — detection tools and removal guide.",
        "category": "stalkerware_check",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["stalkerware", "detection", "safety", "calming"],
    },
    {
        "title": "Location Privacy Guide",
        "description": "Manage who can see your location — turn off tracking, review app permissions.",
        "category": "location_privacy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["location", "privacy", "practical", "calming", "self-paced"],
    },
    {
        "title": "Digital Will and Legacy",
        "description": "Plan what happens to your digital accounts — social media, email, cloud storage.",
        "category": "digital_will",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["digital_will", "legacy", "planning", "calming"],
    },
]

# ── Keyword Matching ─────────────────────────────────────────────────────────

_PRIVACY_KEYWORDS: dict[str, list[str]] = {
    "隐私": [],
    "privacy": [],
    "密码": ["password", "security"],
    "password": ["password", "security"],
    "خصوصية": [],
    "security": ["security"],
    "data": ["data"],
    "数据": ["data"],
    "vpn": ["vpn", "privacy"],
    "phishing": ["phishing", "detection"],
    "钓鱼": ["phishing", "detection"],
    "stalker": ["stalkerware", "safety"],
    "跟踪": ["stalkerware", "safety"],
    "location": ["location", "privacy"],
    "定位": ["location", "privacy"],
    "2fa": ["2fa", "security"],
    "audit": ["audit", "checklist"],
}


def _match_privacy_tags(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, tags in _PRIVACY_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in matched:
                    matched.append(t)
    return matched


class PrivacyProtectionFulfiller(L2Fulfiller):
    """L2 fulfiller for digital privacy — security tools and guides.

    10 curated entries for privacy protection. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        keyword_tags = _match_privacy_tags(wish.wish_text)

        if keyword_tags:
            tag_set = set(keyword_tags)
            candidates = [
                dict(item) for item in PRIVACY_CATALOG
                if tag_set & set(item["tags"])
            ]
        else:
            candidates = [dict(item) for item in PRIVACY_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in PRIVACY_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="Privacy is an ongoing practice. Review your settings periodically.",
                delay_hours=168,
            ),
        )


def _build_relevance_reason(item: dict) -> str:
    tags = set(item.get("tags", []))
    if "security" in tags:
        return "Essential security step to protect your accounts"
    if "privacy" in tags:
        return "Take control of your personal data"
    if "detection" in tags:
        return "Learn to identify and avoid threats"
    if "safety" in tags:
        return "Protect yourself from digital surveillance"
    return "Practical privacy protection step"
