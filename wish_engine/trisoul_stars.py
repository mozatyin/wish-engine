"""TriSoul Stars — three types of stars on the star map, each from a different Soul layer.

☄️ 流星 Meteor (Surface Soul): fleeting, urgent, based on what user just said
⭐ 星星 Star (Middle Soul): persistent, based on recurring patterns over weeks
🌍 地球 Earth (Deep Soul): permanent, based on Compass hidden desires

王阳明心学: 知行合一。All recommendations originate from the user's heart (TriSoul).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from wish_engine.soul_recommender import (
    detect_surface_attention,
    detect_middle_history,
    recommend_from_soul,
    SoulRecommendation,
    ATTENTION_TO_PLACES,
)
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import ShellStage
from wish_engine.apis.osm_api import search_and_enrich


# ── Star Types ───────────────────────────────────────────────────────────────

@dataclass
class MeteorStar:
    """☄️ 流星 — a fleeting need from this moment. Fades after fulfilled or time passes."""
    text_trigger: str        # what they said that triggered this
    attention: str           # detected attention type
    place_name: str          # real place from OSM
    place_category: str
    why: str                 # "你说饿了 — 华润万家就在500米外"
    lat: float | None = None
    lng: float | None = None
    distance_m: float = 0
    opening_hours: str = ""
    # Visual
    color: str = "#FFD700"          # gold/yellow — fleeting
    animation: str = "streak_fast"  # fast streak across sky
    lifespan_hours: int = 4         # disappears after 4 hours


@dataclass
class StarStar:
    """⭐ 星星 — a persistent interest. Glows steadily, based on weeks of conversation."""
    recurring_topic: str     # what they keep talking about
    mention_count: int       # how many times across sessions
    place_name: str
    place_category: str
    why: str                 # "你连续3周都在聊瑜伽 — 这家瑜伽馆离你200米"
    lat: float | None = None
    lng: float | None = None
    distance_m: float = 0
    opening_hours: str = ""
    # Visual
    color: str = "#4A90D9"          # blue — steady
    animation: str = "glow_steady"  # constant soft glow
    lifespan_hours: int = 168       # lasts a week


@dataclass
class EarthStar:
    """🌍 地球 — a core hidden desire. Always there, discovered by Compass."""
    compass_topic: str       # what Compass detected
    confidence: float        # how certain Compass is
    stage: str               # seed/sprout/bud/bloom
    place_name: str          # a place to sit with this realization
    place_category: str
    why: str                 # "有一颗很远的星一直在靠近你...关于Rhett的感觉比你承认的更深"
    lat: float | None = None
    lng: float | None = None
    # Visual
    color: str = "#E8A0BF"          # rose gold — deep/eternal
    animation: str = "pulse_deep"   # slow, deep pulse like heartbeat
    lifespan_hours: int = 0         # permanent until resolved


@dataclass
class TriSoulStarMap:
    """The complete star map — all three layers."""
    meteors: list[MeteorStar] = field(default_factory=list)
    stars: list[StarStar] = field(default_factory=list)
    earths: list[EarthStar] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.meteors) + len(self.stars) + len(self.earths)

    def summary(self) -> str:
        parts = []
        if self.meteors:
            parts.append(f"☄️ {len(self.meteors)} meteor{'s' if len(self.meteors) > 1 else ''}")
        if self.stars:
            parts.append(f"⭐ {len(self.stars)} star{'s' if len(self.stars) > 1 else ''}")
        if self.earths:
            parts.append(f"🌍 {len(self.earths)} earth{'s' if len(self.earths) > 1 else ''}")
        if not parts:
            return "The sky is quiet. Check back later."
        return " | ".join(parts) + f" — {self.total} lights in your sky"


# ── Main Generator ───────────────────────────────────────────────────────────

def generate_trisoul_stars(
    recent_texts: list[str],
    lat: float,
    lng: float,
    topic_history: dict[str, int] | None = None,
    compass: WishCompass | None = None,
    history: set[str] | None = None,
) -> TriSoulStarMap:
    """Generate the complete TriSoul star map.

    Args:
        recent_texts: User's recent messages (last few turns)
        lat, lng: Current GPS
        topic_history: Historical topic counts {topic: mention_count}
        compass: WishCompass instance with accumulated shells
        history: Set of already-shown place names (dedup)

    Returns:
        TriSoulStarMap with meteors, stars, and earths.
    """
    import math
    star_map = TriSoulStarMap()
    used_places = set(history or {})

    # ── ☄️ METEORS: Surface Soul — what they just said ────────────────
    surface_attentions = detect_surface_attention(recent_texts)

    for attention in surface_attentions[:2]:  # Max 2 meteors
        spec = ATTENTION_TO_PLACES.get(attention)
        if not spec:
            continue

        places = search_and_enrich(lat, lng, radius_m=2000, place_types=spec["osm"])
        if not places:
            places = search_and_enrich(lat, lng, radius_m=5000, place_types=spec["osm"])

        for place in places:
            name = place.get("title", "")
            if not name or name in used_places:
                continue
            used_places.add(name)

            why = spec["why"].format(place=name)
            p_lat = place.get("_lat") or 0
            p_lng = place.get("_lng") or 0
            dist_m = 0
            if p_lat and p_lng:
                dlat = (p_lat - lat) * 111000
                dlng = (p_lng - lng) * 111000 * math.cos(math.radians(lat))
                dist_m = math.sqrt(dlat**2 + dlng**2)
                if dist_m < 500:
                    why += f"，就在{int(dist_m)}米外"
                elif dist_m < 2000:
                    why += f"，{dist_m/1000:.1f}公里"

            # Find what they actually said that triggered this
            trigger_text = ""
            for t in recent_texts:
                if any(kw in t.lower() for kw in ATTENTION_TO_PLACES.get(attention, {}).get("osm", [])):
                    trigger_text = t[:60]
                    break
            if not trigger_text:
                trigger_text = recent_texts[-1][:60] if recent_texts else ""

            star_map.meteors.append(MeteorStar(
                text_trigger=trigger_text,
                attention=attention,
                place_name=name,
                place_category=place.get("category", ""),
                why=why,
                lat=p_lat or None,
                lng=p_lng or None,
                distance_m=dist_m,
                opening_hours=place.get("_opening_hours", ""),
            ))
            break

    # ── ⭐ STARS: Middle Soul — recurring interests ───────────────────
    if topic_history:
        middle_attentions = detect_middle_history(topic_history)
        # Don't duplicate surface attentions
        middle_attentions = [a for a in middle_attentions if a not in surface_attentions]

        for attention in middle_attentions[:2]:  # Max 2 stars
            spec = ATTENTION_TO_PLACES.get(attention)
            if not spec:
                continue

            places = search_and_enrich(lat, lng, radius_m=3000, place_types=spec["osm"])
            for place in places:
                name = place.get("title", "")
                if not name or name in used_places:
                    continue
                used_places.add(name)

                # Find the original topic that maps to this attention
                topic_name = ""
                for topic, count in sorted(topic_history.items(), key=lambda x: -x[1]):
                    if count >= 3:
                        topic_name = topic
                        break

                p_lat = place.get("_lat") or 0
                p_lng = place.get("_lng") or 0
                dist_m = 0
                if p_lat and p_lng:
                    dlat = (p_lat - lat) * 111000
                    dlng = (p_lng - lng) * 111000 * math.cos(math.radians(lat))
                    dist_m = math.sqrt(dlat**2 + dlng**2)

                why = f"你已经连续聊了{topic_history.get(topic_name, 0)}次关于{topic_name}的话题 — {name}可能是你一直在找的地方"

                star_map.stars.append(StarStar(
                    recurring_topic=topic_name,
                    mention_count=topic_history.get(topic_name, 0),
                    place_name=name,
                    place_category=place.get("category", ""),
                    why=why,
                    lat=p_lat or None,
                    lng=p_lng or None,
                    distance_m=dist_m,
                    opening_hours=place.get("_opening_hours", ""),
                ))
                break

    # ── 🌍 EARTHS: Deep Soul — Compass hidden desires ────────────────
    if compass:
        for shell in compass.vault.all_shells:
            if shell.confidence < 0.3:
                continue

            # Find a quiet place nearby for contemplation
            quiet_places = search_and_enrich(lat, lng, radius_m=2000, place_types=["park", "garden", "library", "cafe"])
            place_name = ""
            place_cat = ""
            p_lat = None
            p_lng = None

            for place in quiet_places:
                name = place.get("title", "")
                if name and name not in used_places:
                    used_places.add(name)
                    place_name = name
                    place_cat = place.get("category", "")
                    p_lat = place.get("_lat")
                    p_lng = place.get("_lng")
                    break

            if not place_name:
                place_name = "a quiet corner"
                place_cat = "contemplation"

            # Why text depends on maturity
            if shell.stage == ShellStage.SEED:
                why = f"有一颗很远的星在闪烁...你最近提到{shell.topic}时，情绪会变得不一样"
            elif shell.stage == ShellStage.SPROUT:
                why = f"你有没有注意到，每次聊到{shell.topic}，你的感受和聊其他话题时不一样？"
            elif shell.stage == ShellStage.BUD:
                why = f"你对{shell.topic}的在意，可能比你意识到的更深。{place_name}是个安静的地方，也许可以想一想"
            else:  # BLOOM
                why = f"你的星星替你发现了一件事：关于{shell.topic}，你内心的感受远超你表达的。是时候面对了"

            star_map.earths.append(EarthStar(
                compass_topic=shell.topic,
                confidence=shell.confidence,
                stage=shell.stage.value,
                place_name=place_name,
                place_category=place_cat,
                why=why,
                lat=p_lat,
                lng=p_lng,
            ))

    return star_map
