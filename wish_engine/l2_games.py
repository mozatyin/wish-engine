"""GameFulfiller — MBTI-aware game and play experience recommendations.

15-type curated catalog of gaming activities with MBTI introversion/extraversion
personality mapping for solo vs. social games. Zero LLM.
"""

from __future__ import annotations

from wish_engine.l2_fulfiller import L2Fulfiller
from wish_engine.models import (
    ClassifiedWish,
    DetectorResults,
    L2FulfillmentResult,
    ReminderOption,
)

# ── MBTI → Game Style Mapping ────────────────────────────────────────────────

MBTI_GAME_MAP: dict[str, list[str]] = {
    "I": ["puzzle_game", "strategy_game", "chess_club", "retro_gaming", "mobile_game_rec"],
    "E": ["party_game", "trivia_night", "board_game_cafe", "tabletop_rpg", "vr_arcade"],
}

# ── Game Catalog (15 entries) ────────────────────────────────────────────────

GAME_CATALOG: list[dict] = [
    {
        "title": "Board Game Cafe Night",
        "description": "Explore 200+ board games over coffee and snacks — perfect for groups.",
        "category": "board_game_cafe",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["board_game_cafe", "social", "practical"],
    },
    {
        "title": "Escape Room Challenge",
        "description": "Solve puzzles and escape the room — teamwork and adrenaline.",
        "category": "escape_room",
        "noise": "moderate",
        "social": "high",
        "mood": "intense",
        "tags": ["escape_room", "social", "adventure"],
    },
    {
        "title": "Puzzle Game Collection",
        "description": "Curated brain teasers, jigsaws, and logic puzzles for solo play.",
        "category": "puzzle_game",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["puzzle_game", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Strategy Board Games",
        "description": "Settlers of Catan, Terraforming Mars, and more — deep thinking games.",
        "category": "strategy_game",
        "noise": "quiet",
        "social": "medium",
        "mood": "calming",
        "tags": ["strategy_game", "quiet", "theory", "self-paced"],
    },
    {
        "title": "Party Game Night",
        "description": "Codenames, Werewolf, Cards Against Humanity — laughs guaranteed.",
        "category": "party_game",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["party_game", "social", "adventure"],
    },
    {
        "title": "Video Game Cafe",
        "description": "PC and console gaming lounge — play the latest titles with friends.",
        "category": "video_game_cafe",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["video_game_cafe", "social", "practical"],
    },
    {
        "title": "Tabletop RPG Session",
        "description": "D&D, Call of Cthulhu, Pathfinder — collaborative storytelling adventures.",
        "category": "tabletop_rpg",
        "noise": "moderate",
        "social": "high",
        "mood": "calming",
        "tags": ["tabletop_rpg", "social", "theory", "traditional"],
    },
    {
        "title": "Chess Club Meetup",
        "description": "Join local chess enthusiasts — all skill levels welcome.",
        "category": "chess_club",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["chess_club", "quiet", "calming", "theory", "traditional"],
    },
    {
        "title": "Mahjong Table",
        "description": "Classic mahjong sessions — a timeless social strategy game.",
        "category": "mahjong",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["mahjong", "traditional", "social", "practical"],
    },
    {
        "title": "Card Game Night",
        "description": "Poker, bridge, UNO, and more — classic card games for any group size.",
        "category": "card_game",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["card_game", "social", "traditional", "practical"],
    },
    {
        "title": "Trivia Night at Local Pub",
        "description": "Test your knowledge — fun team trivia with prizes and drinks.",
        "category": "trivia_night",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["trivia_night", "social", "adventure"],
    },
    {
        "title": "VR Arcade Experience",
        "description": "Step into virtual reality — racing, shooting, and exploration games.",
        "category": "vr_arcade",
        "noise": "loud",
        "social": "high",
        "mood": "intense",
        "tags": ["vr_arcade", "social", "adventure"],
    },
    {
        "title": "Retro Gaming Lounge",
        "description": "NES, SNES, arcade cabinets — nostalgic gaming in a cozy setting.",
        "category": "retro_gaming",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["retro_gaming", "quiet", "calming", "self-paced"],
    },
    {
        "title": "Sports Simulation Center",
        "description": "Golf, racing, cricket simulators — realistic sports in a fun environment.",
        "category": "sports_simulation",
        "noise": "moderate",
        "social": "medium",
        "mood": "calming",
        "tags": ["sports_simulation", "social", "practical"],
    },
    {
        "title": "Mobile Game Recommendations",
        "description": "Curated picks for solo mobile gaming — puzzles, RPGs, and strategy.",
        "category": "mobile_game_rec",
        "noise": "quiet",
        "social": "low",
        "mood": "calming",
        "tags": ["mobile_game_rec", "quiet", "self-paced", "calming"],
    },
]

# ── Keyword → Tag Mapping ────────────────────────────────────────────────────

_GAME_KEYWORDS: dict[str, list[str]] = {
    "游戏": ["game"],
    "game": ["game"],
    "play": ["game"],
    "桌游": ["board_game_cafe"],
    "board game": ["board_game_cafe"],
    "لعبة": ["game"],
    "escape room": ["escape_room"],
    "密室": ["escape_room"],
    "puzzle": ["puzzle_game"],
    "拼图": ["puzzle_game"],
    "strategy": ["strategy_game"],
    "party game": ["party_game"],
    "聚会游戏": ["party_game"],
    "chess": ["chess_club"],
    "象棋": ["chess_club"],
    "国际象棋": ["chess_club"],
    "شطرنج": ["chess_club"],
    "mahjong": ["mahjong"],
    "麻将": ["mahjong"],
    "trivia": ["trivia_night"],
    "vr": ["vr_arcade"],
    "retro": ["retro_gaming"],
    "复古": ["retro_gaming"],
}


def _match_categories(wish_text: str) -> list[str]:
    """Extract matching tag categories from wish text."""
    text_lower = wish_text.lower()
    matched: list[str] = []
    for keyword, categories in _GAME_KEYWORDS.items():
        if keyword in text_lower:
            for cat in categories:
                if cat not in matched:
                    matched.append(cat)
    return matched


def _mbti_to_game_tags(mbti_type: str) -> list[str]:
    """Map MBTI E/I to preferred game styles."""
    if len(mbti_type) >= 1:
        return MBTI_GAME_MAP.get(mbti_type[0], [])
    return []


def _build_relevance_reason(item: dict, mbti_type: str) -> str:
    """Build a personalized relevance reason."""
    category = item.get("category", "")

    if mbti_type and len(mbti_type) >= 1:
        if mbti_type[0] == "I" and item.get("social") == "low":
            return "A focused solo game — perfect for your reflective style"
        if mbti_type[0] == "E" and item.get("social") in ("high", "medium"):
            return "A fun social game to play with friends"

    reason_map = {
        "board_game_cafe": "Explore hundreds of board games in one visit",
        "escape_room": "Test your teamwork and problem-solving",
        "puzzle_game": "Satisfying brain teasers at your own pace",
        "strategy_game": "Deep strategy for the analytical mind",
        "party_game": "Guaranteed laughs with friends",
        "chess_club": "The timeless game of strategy",
        "trivia_night": "Show off your knowledge and have fun",
    }
    return reason_map.get(category, "Discover your next favorite game")


class GameFulfiller(L2Fulfiller):
    """L2 fulfiller for game/play wishes — MBTI-aware recommendations.

    Uses keyword matching + MBTI E/I→solo/social mapping to select from 15-type
    catalog, then applies PersonalityFilter. Zero LLM.
    """

    def fulfill(
        self,
        wish: ClassifiedWish,
        detector_results: DetectorResults,
    ) -> L2FulfillmentResult:
        # 1. Match from keywords
        matched_categories = _match_categories(wish.wish_text)

        # 2. Add MBTI-based preferences
        mbti_type = detector_results.mbti.get("type", "")
        mbti_tags = _mbti_to_game_tags(mbti_type)

        all_tags = list(matched_categories)
        for t in mbti_tags:
            if t not in all_tags:
                all_tags.append(t)

        # 3. Filter catalog
        if all_tags:
            tag_set = set(all_tags)
            candidates = [
                dict(item) for item in GAME_CATALOG
                if tag_set & set(item["tags"]) or item["category"] in tag_set
            ]
        else:
            candidates = [dict(item) for item in GAME_CATALOG]

        # 4. Fallback
        if not candidates:
            candidates = [dict(item) for item in GAME_CATALOG]

        # 5. Add relevance reasons
        for c in candidates:
            c["relevance_reason"] = _build_relevance_reason(c, mbti_type)

        # 6. Build recommendations via personality filter
        recommendations = self._build_recommendations(
            candidates, detector_results, max_results=3,
        )

        return L2FulfillmentResult(
            recommendations=recommendations,
            reminder_option=ReminderOption(
                text="New game nights happening this week — check back!",
                delay_hours=48,
            ),
        )
