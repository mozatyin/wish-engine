"""WeddingFulfiller — cultural-aware wedding service recommendations.

15-type curated catalog with Islamic/Chinese/Western ceremony support. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── Wedding Catalog (15 entries) ──────────────────────────────────────────────

WEDDING_CATALOG: list[dict] = [
    {
        "title": "Wedding Venue",
        "description": "Beautiful venues for your big day — gardens, ballrooms, and beachfront.",
        "category": "wedding_venue",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["wedding_venue", "celebration", "social", "islamic_ceremony", "chinese_tea_ceremony", "western_church"],
    },
    {
        "title": "Wedding Photographer",
        "description": "Capture every moment — pre-wedding shoots, ceremony, and reception.",
        "category": "photographer",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["photographer", "practical", "calming"],
    },
    {
        "title": "Wedding Florist",
        "description": "Bouquets, centerpieces, and floral arches crafted for your theme.",
        "category": "florist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["florist", "practical", "calming"],
    },
    {
        "title": "Wedding Catering",
        "description": "Full-service catering — halal, Chinese banquet, or Western plated dinner.",
        "category": "catering",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["catering", "practical", "social", "islamic_ceremony", "chinese_tea_ceremony"],
    },
    {
        "title": "Wedding Planner",
        "description": "End-to-end planning — timeline, vendors, and day-of coordination.",
        "category": "wedding_planner",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wedding_planner", "practical", "calming"],
    },
    {
        "title": "Bridal Shop",
        "description": "Wedding dresses, hijab bridal wear, and qipao — find your dream look.",
        "category": "bridal_shop",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["bridal_shop", "practical", "calming", "islamic_ceremony", "chinese_tea_ceremony"],
    },
    {
        "title": "Groom's Suit & Attire",
        "description": "Tailored suits, thobes, and traditional groom attire for the big day.",
        "category": "groom_suit",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["groom_suit", "practical", "calming", "traditional"],
    },
    {
        "title": "Makeup Artist",
        "description": "Bridal makeup and hair styling — look your absolute best.",
        "category": "makeup_artist",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["makeup_artist", "practical", "calming"],
    },
    {
        "title": "Wedding DJ & Live Band",
        "description": "Music that sets the mood — DJ sets, live bands, and cultural ensembles.",
        "category": "dj_band",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["dj_band", "social", "celebration"],
    },
    {
        "title": "Wedding Cake Baker",
        "description": "Custom wedding cakes — multi-tier, fondant, or traditional sweets.",
        "category": "cake_baker",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["cake_baker", "practical", "calming", "celebration"],
    },
    {
        "title": "Invitation Designer",
        "description": "Custom invitations — bilingual, calligraphy, and digital options.",
        "category": "invitation_designer",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["invitation_designer", "practical", "calming"],
    },
    {
        "title": "Honeymoon Destination",
        "description": "Romantic getaways — beach, mountain, or city escapes for newlyweds.",
        "category": "honeymoon_destination",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["honeymoon_destination", "calming", "quiet"],
    },
    {
        "title": "Wedding Gift Registry",
        "description": "Create your dream registry — kitchen, home, or experience gifts.",
        "category": "wedding_registry",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["wedding_registry", "practical", "calming"],
    },
    {
        "title": "Rehearsal Dinner Venue",
        "description": "Intimate dinner the night before — close family and friends only.",
        "category": "rehearsal_dinner",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["rehearsal_dinner", "calming", "social", "quiet"],
    },
    {
        "title": "Wedding Transport Service",
        "description": "Vintage cars, limos, and horse carriages for a grand arrival.",
        "category": "transport_service",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["transport_service", "practical", "celebration"],
    },
]

# ── Cultural Mapping ─────────────────────────────────────────────────────────

CULTURAL_MAP: dict[str, list[str]] = {
    "islamic": ["islamic_ceremony"],
    "chinese": ["chinese_tea_ceremony"],
    "western": ["western_church"],
}

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_WEDDING_KEYWORDS: dict[str, list[str]] = {
    "婚礼": [],
    "wedding": [],
    "结婚": [],
    "marriage": [],
    "زفاف": [],
    "bridal": ["bridal_shop"],
    "venue": ["wedding_venue"],
    "photographer": ["photographer"],
    "摄影": ["photographer"],
    "florist": ["florist"],
    "花": ["florist"],
    "catering": ["catering"],
    "planner": ["wedding_planner"],
    "策划": ["wedding_planner"],
    "dress": ["bridal_shop"],
    "suit": ["groom_suit"],
    "makeup": ["makeup_artist"],
    "dj": ["dj_band"],
    "band": ["dj_band"],
    "cake": ["cake_baker"],
    "蛋糕": ["cake_baker"],
    "invitation": ["invitation_designer"],
    "请帖": ["invitation_designer"],
    "honeymoon": ["honeymoon_destination"],
    "蜜月": ["honeymoon_destination"],
    "registry": ["wedding_registry"],
    "transport": ["transport_service"],
    "islamic": ["islamic_ceremony"],
    "hijab": ["islamic_ceremony"],
    "tea ceremony": ["chinese_tea_ceremony"],
    "敬茶": ["chinese_tea_ceremony"],
    "church": ["western_church"],
    "教堂": ["western_church"],
}


def _match_categories(wish_text: str) -> list[str]:
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _WEDDING_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _build_relevance_reason(item: dict) -> str:
    category = item.get("category", "")
    reason_map = {
        "wedding_venue": "The perfect setting for your special day",
        "photographer": "Memories captured beautifully, forever",
        "florist": "Flowers that bring your vision to life",
        "catering": "A feast your guests will remember",
        "wedding_planner": "Stress-free planning from start to finish",
        "bridal_shop": "Find the look that makes you shine",
        "groom_suit": "Dress sharp for the biggest day of your life",
        "makeup_artist": "Look your absolute best on your wedding day",
        "dj_band": "Music that gets everyone celebrating",
        "cake_baker": "A cake as sweet as your love story",
        "invitation_designer": "Set the tone with beautiful invitations",
        "honeymoon_destination": "Start your new chapter with a dream getaway",
        "wedding_registry": "Help guests give you exactly what you need",
        "rehearsal_dinner": "A warm gathering before the big day",
        "transport_service": "Arrive in style on your wedding day",
    }
    return reason_map.get(category, "Making your wedding dreams come true")


class WeddingFulfiller(L2Fulfiller):
    """L2 fulfiller for wedding wishes — cultural-aware service recommendations.

    Uses keyword matching + cultural ceremony tags to select from 15-type catalog,
    then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        matched_categories = _match_categories(wish.wish_text)

        if matched_categories:
            tag_set = set(matched_categories)
            candidates = [
                dict(item) for item in WEDDING_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in WEDDING_CATALOG]

        if not candidates:
            candidates = [dict(item) for item in WEDDING_CATALOG]

        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c)

        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="More wedding services available — check back soon!",
                delay_hours=48,
            ),
        )
