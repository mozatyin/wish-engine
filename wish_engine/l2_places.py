"""PlaceFulfiller — local-compute place recommendation with personality filtering.

28-place curated catalog across 15 categories. Zero LLM. Keyword matching
(English/Chinese/Arabic) routes wish text to relevant place categories, then
PersonalityFilter scores and ranks candidates.
"""

from __future__ import annotations

from wish_engine.apis import places_api
from wish_engine.apis import places_personality
from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    MapData,
    ReminderOption,
)

# ── Place Catalog (28 entries) ───────────────────────────────────────────────

PLACE_CATALOG: list[dict] = [
    # meditation_center (2)
    {
        "title": "Mindfulness Meditation Center",
        "description": "Guided meditation sessions for beginners and experienced practitioners.",
        "category": "meditation_center",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "calming", "meditation", "mindfulness", "self-paced"],
    },
    {
        "title": "Zen Garden Retreat",
        "description": "Traditional zen meditation in a serene garden setting.",
        "category": "meditation_center",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "calming", "meditation", "traditional", "peaceful"],
    },
    # park (3)
    {
        "title": "Lakeside Park",
        "description": "Spacious park with walking trails, lake views, and quiet benches.",
        "category": "park",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "nature", "walking", "peaceful", "calming"],
    },
    {
        "title": "Community Sports Park",
        "description": "Open fields, basketball courts, and running tracks for active recreation.",
        "category": "park",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["exercise", "social", "practical", "outdoor"],
    },
    {
        "title": "Botanical Garden",
        "description": "Curated plant collections with peaceful walking paths.",
        "category": "park",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "nature", "peaceful", "calming", "educational"],
    },
    # cafe (2)
    {
        "title": "Quiet Reading Cafe",
        "description": "Cozy cafe with a no-laptop-free zone and curated book shelves.",
        "category": "cafe",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "reading", "calming", "coffee"],
    },
    {
        "title": "Social Coffee House",
        "description": "Vibrant cafe with community events, open mic nights, and board games.",
        "category": "cafe",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["social", "community", "creative", "coffee"],
    },
    # library (2)
    {
        "title": "Central Public Library",
        "description": "Extensive collection with study rooms and free workshops.",
        "category": "library",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "reading", "educational", "self-paced", "peaceful"],
    },
    {
        "title": "University Research Library",
        "description": "Academic resources, quiet study carrels, and research databases.",
        "category": "library",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["quiet", "theory", "academic", "self-paced", "peaceful"],
    },
    # gym (2)
    {
        "title": "24-Hour Fitness Center",
        "description": "Full equipment gym with cardio, weights, and personal training.",
        "category": "gym",
        "noise": "loud",
        "social": "medium",
        "mood": "intense",
        "tags": ["exercise", "fitness", "practical", "intense"],
    },
    {
        "title": "Boutique Strength Studio",
        "description": "Small-group strength training with personal coaching.",
        "category": "gym",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["exercise", "fitness", "practical", "structured"],
    },
    # fitness_studio (2)
    {
        "title": "Dance Fitness Studio",
        "description": "High-energy dance classes: Zumba, hip-hop, and contemporary.",
        "category": "fitness_studio",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["exercise", "dance", "social", "intense", "noisy"],
    },
    {
        "title": "Pilates & Barre Studio",
        "description": "Low-impact strengthening with pilates reformers and barre work.",
        "category": "fitness_studio",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["exercise", "fitness", "calming", "structured", "quiet"],
    },
    # yoga_studio (2)
    {
        "title": "Hot Yoga Studio",
        "description": "Heated yoga sessions for deep stretching and detoxification.",
        "category": "yoga_studio",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["yoga", "exercise", "calming", "quiet", "mindfulness"],
    },
    {
        "title": "Community Yoga Center",
        "description": "Donation-based classes for all levels, emphasis on breathing and relaxation.",
        "category": "yoga_studio",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["yoga", "exercise", "calming", "quiet", "community", "helping"],
    },
    # swimming_pool (1)
    {
        "title": "Olympic Swimming Complex",
        "description": "Lap swimming, water aerobics, and recreational pool areas.",
        "category": "swimming_pool",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["exercise", "swimming", "practical", "calming"],
    },
    # art_studio (2)
    {
        "title": "Open Art Studio",
        "description": "Drop-in painting, pottery, and sculpture sessions.",
        "category": "art_studio",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["creative", "art", "quiet", "self-paced", "calming"],
    },
    {
        "title": "Community Art Workshop",
        "description": "Group art classes with local artists. Collaborative murals and exhibits.",
        "category": "art_studio",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["creative", "art", "social", "community", "helping"],
    },
    # music_studio (2)
    {
        "title": "Practice Room Rental",
        "description": "Soundproofed rooms with piano, drums, and recording gear.",
        "category": "music_studio",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["music", "creative", "quiet", "self-paced", "autonomous"],
    },
    {
        "title": "Open Jam Studio",
        "description": "Weekly jam sessions for all instruments and skill levels.",
        "category": "music_studio",
        "noise": "loud",
        "social": "high",
        "mood": "calming",
        "tags": ["music", "creative", "social", "noisy"],
    },
    # therapy_center (2)
    {
        "title": "Counseling & Therapy Center",
        "description": "Licensed therapists offering CBT, talk therapy, and couples counseling.",
        "category": "therapy_center",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["therapy", "quiet", "calming", "structured", "helping"],
    },
    {
        "title": "Group Support Center",
        "description": "Peer support groups for anxiety, grief, addiction, and life transitions.",
        "category": "therapy_center",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["therapy", "quiet", "calming", "social", "community", "helping"],
    },
    # spa (1)
    {
        "title": "Day Spa & Wellness",
        "description": "Massage, facials, and hydrotherapy in a tranquil environment.",
        "category": "spa",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["relaxation", "quiet", "calming", "peaceful", "self-paced"],
    },
    # community_center (2)
    {
        "title": "Neighborhood Community Center",
        "description": "Classes, events, and meeting rooms for local residents.",
        "category": "community_center",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["community", "social", "practical", "helping"],
    },
    {
        "title": "Youth Activity Center",
        "description": "Programs for teens and young adults: sports, tutoring, and mentorship.",
        "category": "community_center",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["community", "social", "educational", "helping"],
    },
    # restaurant (1)
    {
        "title": "Farm-to-Table Restaurant",
        "description": "Locally sourced seasonal menu in a relaxed dining atmosphere.",
        "category": "restaurant",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["food", "social", "calming", "traditional"],
    },
    # coworking (2)
    {
        "title": "Quiet Coworking Space",
        "description": "Individual desks, phone booths, and a strict quiet policy.",
        "category": "coworking",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["work", "quiet", "self-paced", "autonomous", "peaceful"],
    },
    {
        "title": "Creative Coworking Hub",
        "description": "Open-plan space with networking events and brainstorming rooms.",
        "category": "coworking",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["work", "social", "creative", "community"],
    },
]


# ── Keyword → Category Mapping ──────────────────────────────────────────────

_WISH_KEYWORDS: dict[str, list[str]] = {
    # meditation / mindfulness
    "meditation": ["meditation_center"],
    "meditate": ["meditation_center"],
    "mindfulness": ["meditation_center"],
    "冥想": ["meditation_center"],
    "正念": ["meditation_center"],
    "تأمل": ["meditation_center"],
    # park / nature
    "park": ["park"],
    "nature": ["park"],
    "garden": ["park"],
    "公园": ["park"],
    "自然": ["park"],
    "花园": ["park"],
    "حديقة": ["park"],
    "طبيعة": ["park"],
    # cafe / coffee
    "cafe": ["cafe"],
    "coffee": ["cafe"],
    "咖啡": ["cafe"],
    "مقهى": ["cafe"],
    "قهوة": ["cafe"],
    # library / reading
    "library": ["library"],
    "reading": ["library"],
    "read": ["library"],
    "图书馆": ["library"],
    "阅读": ["library"],
    "看书": ["library"],
    "مكتبة": ["library"],
    "قراءة": ["library"],
    # gym / fitness / exercise
    "gym": ["gym"],
    "fitness": ["gym", "fitness_studio"],
    "exercise": ["gym", "fitness_studio", "park", "swimming_pool", "yoga_studio"],
    "workout": ["gym", "fitness_studio"],
    "运动": ["gym", "fitness_studio", "park", "swimming_pool", "yoga_studio"],
    "健身": ["gym", "fitness_studio"],
    "锻炼": ["gym", "fitness_studio", "park"],
    "رياضة": ["gym", "fitness_studio"],
    "تمرين": ["gym", "fitness_studio"],
    # yoga
    "yoga": ["yoga_studio"],
    "瑜伽": ["yoga_studio"],
    "يوغا": ["yoga_studio"],
    # swimming
    "swim": ["swimming_pool"],
    "swimming": ["swimming_pool"],
    "游泳": ["swimming_pool"],
    "سباحة": ["swimming_pool"],
    # art / creative
    "art": ["art_studio"],
    "paint": ["art_studio"],
    "painting": ["art_studio"],
    "draw": ["art_studio"],
    "pottery": ["art_studio"],
    "艺术": ["art_studio"],
    "画画": ["art_studio"],
    "绘画": ["art_studio"],
    "فن": ["art_studio"],
    "رسم": ["art_studio"],
    # music
    "music": ["music_studio"],
    "instrument": ["music_studio"],
    "piano": ["music_studio"],
    "guitar": ["music_studio"],
    "音乐": ["music_studio"],
    "乐器": ["music_studio"],
    "موسيقى": ["music_studio"],
    # therapy / counseling
    "therapy": ["therapy_center"],
    "counseling": ["therapy_center"],
    "therapist": ["therapy_center"],
    "心理": ["therapy_center"],
    "咨询": ["therapy_center"],
    "治疗": ["therapy_center"],
    "علاج": ["therapy_center"],
    "استشارة": ["therapy_center"],
    # spa / relaxation
    "spa": ["spa"],
    "massage": ["spa"],
    "relax": ["spa", "park"],
    "放松": ["spa", "park"],
    "按摩": ["spa"],
    "سبا": ["spa"],
    "تدليك": ["spa"],
    # coworking / work
    "coworking": ["coworking"],
    "cowork": ["coworking"],
    "办公": ["coworking"],
    "工作空间": ["coworking"],
    # quiet / peaceful
    "quiet": ["library", "cafe", "park", "spa", "meditation_center"],
    "安静": ["library", "cafe", "park", "spa", "meditation_center"],
    "peaceful": ["library", "park", "spa", "meditation_center"],
    "هدوء": ["library", "cafe", "park", "spa", "meditation_center"],
    # community
    "community": ["community_center"],
    "social": ["community_center", "cafe"],
    "社区": ["community_center"],
    "مجتمع": ["community_center"],
    # food / restaurant
    "restaurant": ["restaurant"],
    "food": ["restaurant"],
    "餐厅": ["restaurant"],
    "吃饭": ["restaurant"],
    "مطعم": ["restaurant"],
    # dance
    "dance": ["fitness_studio"],
    "跳舞": ["fitness_studio"],
    "رقص": ["fitness_studio"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching place categories from wish text via keyword lookup.

    Returns deduplicated list of category strings. If no keywords match,
    returns empty list (caller should fall back to full catalog).
    """
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _WISH_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


class PlaceFulfiller(L2Fulfiller):
    """L2 fulfiller for FIND_PLACE wishes.

    Uses keyword matching to narrow down the 28-place catalog, then applies
    PersonalityFilter for scoring and ranking. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
        location: tuple[float, float] | None = None,
    ) -> L2FulfillmentResult:
        # Try Google Places API first (requires API key + location)
        if location and places_api.is_available():
            search_params = places_personality.wish_to_search_params(wish.wish_text)
            raw_places = places_api.nearby_search(
                lat=location[0],
                lng=location[1],
                place_type=search_params.get("place_type"),
                keyword=search_params.get("keyword"),
            )
            if raw_places:
                candidates = places_personality.enrich_places(raw_places)
                recs = self._build_recommendations(
                    candidates, detector_results, max_results=3,
                )
                if recs:
                    primary = recs[0].category
                    return L2FulfillmentResult(
                        recommendations=recs,
                        map_data=MapData(place_type=primary, radius_km=5.0),
                        reminder_option=ReminderOption(
                            text="Want a reminder to visit?",
                            delay_hours=48,
                        ),
                    )

        # Fallback: static catalog
        # 1. Match categories from wish text
        matched_categories = _match_categories(wish.wish_text)

        # 2. Filter catalog to matched categories (or use full catalog)
        if matched_categories:
            candidates = [
                dict(p) for p in PLACE_CATALOG
                if p["category"] in matched_categories
            ]
        else:
            candidates = [dict(p) for p in PLACE_CATALOG]

        # 3. If filtering left nothing, fall back to full catalog
        if not candidates:
            candidates = [dict(p) for p in PLACE_CATALOG]

        # 4. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        # 5. Determine map place_type from top recommendation
        top_category = recommendations[0].category if recommendations else "park"

        return L2FulfillmentResult(
            recommendations=recommendations,
            map_data=MapData(place_type=top_category, radius_km=5.0),
            reminder_option=ReminderOption(
                text="Visit this place this weekend?",
                delay_hours=48,
            ),
        )
