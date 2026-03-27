"""LocalServiceFulfiller — local-compute urgent service finder.

15-entry curated catalog of local services (print, courier, repair, etc.).
Zero LLM. Keyword matching (English/Chinese/Arabic) routes wish text to
relevant categories, then PersonalityFilter scores and ranks candidates.

Tags: urgent/24h/quick/affordable.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller, PersonalityFilter
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    ReminderOption,
)

# ── Local Services Catalog (15 entries) ──────────────────────────────────────

SERVICES_CATALOG: list[dict] = [
    {
        "title": "Print Shop",
        "description": "Fast printing, copying, and binding — documents ready in minutes.",
        "category": "print_shop",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["urgent", "quick", "practical", "affordable"],
    },
    {
        "title": "Courier Service",
        "description": "Reliable same-day pickup and delivery for your packages.",
        "category": "courier_service",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["urgent", "quick", "practical", "delivery"],
    },
    {
        "title": "Luggage Storage",
        "description": "Secure luggage storage so you can explore hands-free.",
        "category": "luggage_storage",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quick", "practical", "affordable", "travel"],
    },
    {
        "title": "Key Copy Service",
        "description": "Duplicate keys made quickly — spare keys in minutes.",
        "category": "key_copy",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quick", "practical", "affordable"],
    },
    {
        "title": "Laundry Service",
        "description": "Drop off your clothes and pick them up fresh and clean.",
        "category": "laundry",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quick", "practical", "affordable", "calming"],
    },
    {
        "title": "Dry Cleaning",
        "description": "Professional dry cleaning for your delicate and formal garments.",
        "category": "dry_cleaning",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quick", "practical", "professional"],
    },
    {
        "title": "Tailor & Alterations",
        "description": "Expert tailoring to make your clothes fit perfectly.",
        "category": "tailor",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "affordable", "professional"],
    },
    {
        "title": "Phone Repair Shop",
        "description": "Quick screen fixes, battery swaps, and phone repairs.",
        "category": "phone_repair",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["urgent", "quick", "practical", "tech"],
    },
    {
        "title": "Computer Repair",
        "description": "Laptop and desktop repairs by certified technicians.",
        "category": "computer_repair",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["urgent", "practical", "tech", "professional"],
    },
    {
        "title": "Notary Service",
        "description": "Certified notary for documents, contracts, and legal papers.",
        "category": "notary",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "professional", "legal"],
    },
    {
        "title": "Translation Service",
        "description": "Professional translation and interpretation for any language pair.",
        "category": "translation_service",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "professional", "language"],
    },
    {
        "title": "Passport Photo Studio",
        "description": "Quick passport and ID photos that meet official requirements.",
        "category": "passport_photo",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quick", "practical", "affordable", "photo"],
    },
    {
        "title": "ATM / Cash Point",
        "description": "Nearby ATM for quick cash withdrawals.",
        "category": "atm",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["24h", "quick", "practical", "financial"],
    },
    {
        "title": "Currency Exchange",
        "description": "Competitive exchange rates for international currencies.",
        "category": "currency_exchange",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "financial", "travel", "affordable"],
    },
    {
        "title": "Post Office",
        "description": "Mail letters, ship packages, and access postal services.",
        "category": "post_office",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["practical", "affordable", "delivery"],
    },
]

# ── Keywords ─────────────────────────────────────────────────────────────────

SERVICES_KEYWORDS: set[str] = {
    "打印", "print", "快递", "courier", "寄存", "storage", "修", "repair",
    "洗衣", "laundry", "dry cleaning", "tailor", "裁缝", "phone repair",
    "computer repair", "notary", "公证", "translation", "翻译",
    "passport photo", "证件照", "atm", "currency exchange", "换汇",
    "post office", "邮局", "key copy", "配钥匙", "luggage", "行李",
    "طباعة", "توصيل", "غسيل", "إصلاح", "صراف",
}


def _match_candidates(
    wish_text: str,
    detector_results: DetectorResults,
) -> list[dict]:
    """Select catalog candidates based on keyword matching."""
    text_lower = wish_text.lower()
    candidates: list[dict] = []

    want_urgent = any(kw in text_lower for kw in ["urgent", "紧急", "عاجل", "asap", "now", "快"])

    for item in SERVICES_CATALOG:
        item_copy = dict(item)
        score_boost = 0.0
        tags = set(item.get("tags", []))

        # Keyword matching for specific categories
        category = item["category"]
        if any(kw in text_lower for kw in _CATEGORY_KEYWORDS.get(category, [])):
            score_boost += 0.25

        # Urgency boost
        if want_urgent and "urgent" in tags:
            score_boost += 0.15

        item_copy["_emotion_boost"] = score_boost
        item_copy["relevance_reason"] = _build_relevance(item)
        candidates.append(item_copy)

    return candidates


_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "print_shop": ["print", "打印", "复印", "copy", "طباعة", "binding"],
    "courier_service": ["courier", "快递", "delivery", "ship", "寄", "توصيل"],
    "luggage_storage": ["luggage", "storage", "寄存", "行李", "أمتعة"],
    "key_copy": ["key", "钥匙", "配钥匙", "مفتاح"],
    "laundry": ["laundry", "洗衣", "wash", "غسيل"],
    "dry_cleaning": ["dry clean", "干洗"],
    "tailor": ["tailor", "裁缝", "alter", "خياط"],
    "phone_repair": ["phone repair", "手机修", "screen fix", "إصلاح هاتف"],
    "computer_repair": ["computer repair", "电脑修", "laptop", "إصلاح كمبيوتر"],
    "notary": ["notary", "公证", "توثيق"],
    "translation_service": ["translat", "翻译", "ترجمة"],
    "passport_photo": ["passport photo", "证件照", "id photo", "صورة جواز"],
    "atm": ["atm", "cash", "取钱", "صراف"],
    "currency_exchange": ["exchange", "换汇", "currency", "صرف"],
    "post_office": ["post office", "邮局", "mail", "بريد"],
}


def _build_relevance(item: dict) -> str:
    """Build a relevance reason."""
    reasons = {
        "print_shop": "Quick printing and copying nearby",
        "courier_service": "Fast delivery for your package",
        "luggage_storage": "Store your bags safely while you explore",
        "key_copy": "Spare keys made in minutes",
        "laundry": "Fresh, clean clothes without the hassle",
        "dry_cleaning": "Professional care for your garments",
        "tailor": "Perfect fit from a skilled tailor",
        "phone_repair": "Get your phone fixed quickly",
        "computer_repair": "Expert tech repair nearby",
        "notary": "Certified notary services available",
        "translation_service": "Professional translation when you need it",
        "passport_photo": "Quick ID photos that meet requirements",
        "atm": "Cash available nearby",
        "currency_exchange": "Competitive exchange rates nearby",
        "post_office": "Postal services for your mail and packages",
    }
    return reasons.get(item["category"], "A useful local service nearby")


class LocalServiceFulfiller(L2Fulfiller):
    """L2 fulfiller for local service wishes (print, courier, repair, etc.).

    15-entry curated catalog. Tags: urgent/24h/quick/affordable.
    Zero LLM.
    """

    def _build_recommendations_with_boost(
        self,
        candidates: list[dict],
        detector_results: DetectorResults,
        max_results: int = 3,
    ) -> list:
        from wish_engine.models import Recommendation

        pf = PersonalityFilter(detector_results)
        filtered = pf.apply(candidates)
        scored = pf.score(filtered)

        for c in scored:
            boost = c.pop("_emotion_boost", 0.0)
            c["_personality_score"] = min(c.get("_personality_score", 0.5) + boost, 1.0)

        scored.sort(key=lambda c: c.get("_personality_score", 0), reverse=True)
        ranked = scored[:max_results]

        return [
            Recommendation(
                title=c["title"],
                description=c["description"],
                category=c["category"],
                relevance_reason=c.get("relevance_reason", "A useful local service nearby"),
                score=c.get("_personality_score", 0.5),
                tags=c.get("tags", []),
            )
            for c in ranked
        ]

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        candidates = _match_candidates(wish.wish_text, detector_results)
        recommendations = self._build_recommendations_with_boost(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="local_service", radius_km=3.0),
            reminder_option=ReminderOption(
                text="Visit this service today?",
                delay_hours=2,
            ),
        )
