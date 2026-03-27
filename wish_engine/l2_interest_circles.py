"""InterestCircleFulfiller — local-compute interest circle matching.

20-entry curated catalog of niche hobbies with personality tags.
MBTI filtering: I->small groups (3-5), E->larger meetups (10+).
Multilingual keyword routing (EN/ZH/AR). Zero LLM.
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

# ── Interest Circle Catalog (20 entries) ─────────────────────────────────────

INTEREST_CATALOG: list[dict] = [
    {
        "title": "考古探索小组",
        "description": "Explore local archaeological sites and historical ruins with fellow history enthusiasts.",
        "category": "interest_circle",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["intellectual", "traditional", "quiet", "outdoor"],
    },
    {
        "title": "茶艺品鉴会",
        "description": "Learn and share tea brewing techniques in a serene atmosphere.",
        "category": "interest_circle",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["traditional", "quiet", "creative"],
    },
    {
        "title": "独立游戏之夜",
        "description": "Gather to play and discuss indie games — discover hidden gems together.",
        "category": "interest_circle",
        "group_size": "medium",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["modern", "creative", "social", "intellectual"],
    },
    {
        "title": "手工皮具工坊",
        "description": "Handcraft leather goods — wallets, belts, bags — in a focused workshop.",
        "category": "interest_circle",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "traditional", "quiet"],
    },
    {
        "title": "天文观星团",
        "description": "Set up telescopes and explore the night sky together in low-light locations.",
        "category": "interest_circle",
        "group_size": "medium",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["intellectual", "outdoor", "quiet"],
    },
    {
        "title": "城市速写团",
        "description": "Urban sketching meetup — capture cityscapes and street scenes on the spot.",
        "category": "interest_circle",
        "group_size": "medium",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "outdoor", "quiet", "modern"],
    },
    {
        "title": "桌游俱乐部",
        "description": "Strategy board games, cooperative adventures, and card game nights.",
        "category": "interest_circle",
        "group_size": "large",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "intellectual", "modern"],
    },
    {
        "title": "读书会",
        "description": "Monthly book club — read, discuss, and share perspectives on great books.",
        "category": "interest_circle",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["intellectual", "quiet", "traditional"],
    },
    {
        "title": "业余无线电社",
        "description": "Ham radio enthusiasts — build antennas, make contacts, explore the airwaves.",
        "category": "interest_circle",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["intellectual", "modern", "quiet"],
    },
    {
        "title": "精酿啤酒品鉴",
        "description": "Taste and discuss craft beers from local breweries and homebrew experiments.",
        "category": "interest_circle",
        "group_size": "large",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "modern", "creative"],
    },
    {
        "title": "古典音乐欣赏会",
        "description": "Listen to and discuss classical compositions in an intimate setting.",
        "category": "interest_circle",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["traditional", "quiet", "intellectual"],
    },
    {
        "title": "独立电影放映会",
        "description": "Screen and discuss independent films — art-house cinema for cinephiles.",
        "category": "interest_circle",
        "group_size": "medium",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["creative", "modern", "quiet", "intellectual"],
    },
    {
        "title": "园艺种植社",
        "description": "Grow plants, share seeds, and learn sustainable gardening techniques.",
        "category": "interest_circle",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["outdoor", "quiet", "traditional", "creative"],
    },
    {
        "title": "手冲咖啡研习社",
        "description": "Master pour-over techniques, explore single-origin beans, and share brews.",
        "category": "interest_circle",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "quiet", "modern"],
    },
    {
        "title": "街舞Battle场",
        "description": "Street dance jams — freestyle, battle, and learn from each other.",
        "category": "interest_circle",
        "group_size": "large",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["physical", "social", "modern", "creative"],
    },
    {
        "title": "书法修习班",
        "description": "Practice calligraphy in a meditative atmosphere — Chinese, Arabic, or Western styles.",
        "category": "interest_circle",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["traditional", "quiet", "creative"],
    },
    {
        "title": "刺绣手作圈",
        "description": "Embroidery circle — share patterns, techniques, and finished works.",
        "category": "interest_circle",
        "group_size": "small",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "traditional", "quiet"],
    },
    {
        "title": "骑行探索队",
        "description": "Cycling group — weekend rides exploring city trails and scenic routes.",
        "category": "interest_circle",
        "group_size": "large",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["physical", "outdoor", "social", "modern"],
    },
    {
        "title": "攀岩训练营",
        "description": "Indoor and outdoor climbing sessions — build strength, conquer walls together.",
        "category": "interest_circle",
        "group_size": "medium",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["physical", "outdoor", "social"],
    },
    {
        "title": "辩论俱乐部",
        "description": "Structured debates on hot topics — sharpen your thinking and persuasion skills.",
        "category": "interest_circle",
        "group_size": "large",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["intellectual", "social", "modern"],
    },
]

# ── Keywords ──────────────────────────────────────────────────────────────────

_INTEREST_KEYWORDS: set[str] = {
    "兴趣", "hobby", "爱好", "circle", "圈子", "同好", "هواية",
    "interest", "club", "meetup", "group",
}


def _mbti_group_filter(
    candidates: list[dict],
    detector_results: DetectorResults,
) -> list[dict]:
    """Filter by MBTI: introverts get small groups, extraverts get larger ones."""
    mbti = detector_results.mbti
    if not mbti.get("type"):
        return candidates

    ei = mbti.get("dimensions", {}).get("E_I", 0.5)
    is_introvert = ei < 0.4

    if is_introvert:
        # Prefer small groups (3-5 people)
        return [c for c in candidates if c.get("group_size") in ("small", "medium")]
    else:
        # Prefer larger meetups (10+)
        return [c for c in candidates if c.get("group_size") in ("medium", "large")]


class InterestCircleFulfiller(L2Fulfiller):
    """L2 fulfiller for interest circle wishes — niche hobby matching.

    20-entry curated catalog with MBTI group size filtering. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Start with full catalog
        candidates = [dict(item) for item in INTEREST_CATALOG]

        # 2. Apply MBTI group size filter
        filtered = _mbti_group_filter(candidates, detector_results)
        if not filtered:
            filtered = candidates  # fallback to all

        # 3. Add relevance reasons
        for c in filtered:
            tags = c.get("tags", [])
            if "quiet" in tags:
                c["relevance_reason"] = "A calm, focused group for deep connection"
            elif "social" in tags:
                c["relevance_reason"] = "An energetic community to meet new people"
            elif "creative" in tags:
                c["relevance_reason"] = "Express your creativity with like-minded people"
            else:
                c["relevance_reason"] = "Connect with people who share your interests"

        # 4. Personality filter and rank
        recommendations = self._build_recommendations(
            filtered, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type="community_center", radius_km=10.0),
            reminder_option=ReminderOption(
                text="Join an interest circle this weekend?",
                delay_hours=24,
            ),
        )
