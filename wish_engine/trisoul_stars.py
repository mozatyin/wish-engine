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
)
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import ShellStage
from wish_engine.apis.osm_api import search_and_enrich
from wish_engine.soul_api_bridge import SOUL_API_MAP, get_api_actions


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


# ── API Caller ───────────────────────────────────────────────────────────────

def _call_api(action: dict, lat: float, lng: float) -> dict | None:
    """Call a single API from the Bridge and return the result."""
    import importlib
    try:
        mod = importlib.import_module(action["api"])
        fn = getattr(mod, action["fn"])

        # Build params — inject lat/lng for location-based APIs
        params = dict(action.get("params", {}))
        if "lat" in fn.__code__.co_varnames and "lat" not in params:
            params["lat"] = lat
        if "lng" in fn.__code__.co_varnames and "lng" not in params:
            params["lng"] = lng

        result = fn(**params)

        if result is None:
            return None

        # Normalize result
        if isinstance(result, str):
            return {"result": result}
        if isinstance(result, list):
            return result[0] if result else None
        if isinstance(result, dict):
            return result
        return {"result": str(result)}
    except Exception:
        return None


def _format_why(template: str, data: dict) -> str:
    """Format the display template with API result data."""
    try:
        return template.format(**data)
    except (KeyError, IndexError, TypeError):
        # Fallback: just show what we have
        useful = {k: v for k, v in data.items() if isinstance(v, (str, int, float)) and v and not k.startswith("_")}
        if useful:
            first_key = next(iter(useful))
            return str(useful[first_key])
        return ""


# ── Main Generator ───────────────────────────────────────────────────────────

def generate_trisoul_stars(
    recent_texts: list[str],
    lat: float,
    lng: float,
    topic_history: dict[str, int] | None = None,
    compass: WishCompass | None = None,
    history: set[str] | None = None,
) -> TriSoulStarMap:
    """Generate the complete TriSoul star map via Soul API Bridge.

    For each Soul signal, calls ALL mapped APIs (not just OSM).
    A meteor might be a real recipe, a breathing exercise, AND a nearby park.

    Args:
        recent_texts: User's recent messages
        lat, lng: Current GPS
        topic_history: Historical topic counts
        compass: WishCompass with accumulated shells
        history: Set of already-shown items (dedup)

    Returns:
        TriSoulStarMap with meteors, stars, and earths — each backed by real API data.
    """
    star_map = TriSoulStarMap()
    used_items = set(history or {})

    # ── ☄️ METEORS: Surface Soul ─────────────────────────────────────
    surface_attentions = detect_surface_attention(recent_texts)
    trigger_text = recent_texts[-1][:60] if recent_texts else ""

    for attention in surface_attentions[:3]:  # Max 3 meteor triggers
        actions = get_api_actions(attention)

        for action in actions:
            if len(star_map.meteors) >= 5:  # Cap total meteors
                break

            data = _call_api(action, lat, lng)
            if not data:
                continue

            # Build display text
            why = _format_why(action.get("template", ""), data)
            if not why:
                continue

            # Dedup by content
            dedup_key = why[:40]
            if dedup_key in used_items:
                continue
            used_items.add(dedup_key)

            # Extract place info if available
            place_name = data.get("title") or data.get("name") or action.get("cat", "")
            p_lat = data.get("_lat") or data.get("lat")
            p_lng = data.get("_lng") or data.get("lng")

            import math
            dist_m = 0
            if p_lat and p_lng and isinstance(p_lat, (int, float)):
                dlat = (p_lat - lat) * 111000
                dlng = (p_lng - lng) * 111000 * math.cos(math.radians(lat))
                dist_m = math.sqrt(dlat**2 + dlng**2)

            star_map.meteors.append(MeteorStar(
                text_trigger=trigger_text,
                attention=attention,
                place_name=place_name,
                place_category=action.get("cat", ""),
                why=why,
                lat=p_lat if isinstance(p_lat, (int, float)) else None,
                lng=p_lng if isinstance(p_lng, (int, float)) else None,
                distance_m=dist_m,
                opening_hours=data.get("_opening_hours", data.get("opening_hours", "")),
            ))

    # ── ⭐ STARS: Middle Soul ────────────────────────────────────────
    if topic_history:
        middle_attentions = detect_middle_history(topic_history)
        middle_attentions = [a for a in middle_attentions if a not in surface_attentions]

        for attention in middle_attentions[:2]:
            actions = get_api_actions(attention)

            # Find the recurring topic name
            topic_name = ""
            for topic, count in sorted(topic_history.items(), key=lambda x: -x[1]):
                if count >= 3:
                    topic_name = topic
                    break

            for action in actions[:2]:  # Max 2 API calls per star
                data = _call_api(action, lat, lng)
                if not data:
                    continue

                why = _format_why(action.get("template", ""), data)
                if not why:
                    continue

                dedup_key = why[:40]
                if dedup_key in used_items:
                    continue
                used_items.add(dedup_key)

                place_name = data.get("title") or data.get("name") or topic_name

                star_map.stars.append(StarStar(
                    recurring_topic=topic_name,
                    mention_count=topic_history.get(topic_name, 0),
                    place_name=place_name,
                    place_category=action.get("cat", ""),
                    why=f"你一直在关注{topic_name} — {why}",
                    lat=data.get("_lat") or data.get("lat"),
                    lng=data.get("_lng") or data.get("lng"),
                    distance_m=0,
                    opening_hours=data.get("_opening_hours", ""),
                ))
                break  # One result per attention for stars

    # ── 🌍 EARTHS: Deep Soul (Compass) ───────────────────────────────
    if compass:
        for shell in compass.vault.all_shells:
            if shell.confidence < 0.3:
                continue

            # Try to find a quiet place via Bridge
            quiet_data = _call_api(
                {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
                 "params": {"place_types": ["park", "garden", "library", "cafe"]}},
                lat, lng,
            )

            place_name = ""
            place_cat = "contemplation"
            p_lat = None
            p_lng = None

            if quiet_data and isinstance(quiet_data, dict):
                name = quiet_data.get("title", "")
                if name and name not in used_items:
                    used_items.add(name)
                    place_name = name
                    place_cat = quiet_data.get("category", "contemplation")
                    p_lat = quiet_data.get("_lat")
                    p_lng = quiet_data.get("_lng")

            if not place_name:
                place_name = "a quiet corner"

            # Also get wisdom for the Earth star
            wisdom_data = _call_api(
                {"api": "wish_engine.apis.spiritual_apis", "fn": "daily_wisdom", "params": {}},
                lat, lng,
            )
            wisdom_text = ""
            if wisdom_data:
                wisdom_text = f"\n🌿 {wisdom_data.get('tradition', '')}: {wisdom_data.get('text', '')}"

            # Why text depends on maturity
            if shell.stage == ShellStage.SEED:
                why = f"有一颗很远的星在闪烁...你最近提到{shell.topic}时，情绪会变得不一样"
            elif shell.stage == ShellStage.SPROUT:
                why = f"你有没有注意到，每次聊到{shell.topic}，你的感受和聊其他话题时不一样？"
            elif shell.stage == ShellStage.BUD:
                why = f"你对{shell.topic}的在意，可能比你意识到的更深。{place_name}是个安静的地方，也许可以想一想{wisdom_text}"
            else:  # BLOOM
                why = f"你的星星替你发现了一件事：关于{shell.topic}，你内心的感受远超你表达的。是时候面对了{wisdom_text}"

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
