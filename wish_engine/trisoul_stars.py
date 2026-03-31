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
    _find_trigger_phrase,
)
from wish_engine.compass.compass import WishCompass
from wish_engine.compass.models import ShellStage
from wish_engine.apis.osm_api import search_and_enrich
from wish_engine.soul_api_bridge import SOUL_API_MAP, get_api_actions
from wish_engine.soul_layer_classifier import classify_layer, filter_actions_by_layer, SoulLayer, VowSuppressor
from wish_engine.narrative_tracker import NarrativeTracker, LifePhase
from wish_engine.star_feedback import StarFeedbackStore


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


# ── Attention → "Why This" Prefix ────────────────────────────────────────────
# When a meteor fires, prepend "你说X → " so the user always sees WHY this recommendation
# connects to what they just expressed. Without this, a poem just appears with no context.
_ATTENTION_WHY_PREFIX: dict[str, str] = {
    "hungry":           "你说饿了",
    "thirsty":          "你需要喝点什么",
    "tired":            "你说很累了",
    "cold":             "你说很冷",
    "hot":              "你说很热",
    "sad":              "你心情很低落",
    "angry":            "你感到愤怒",
    "anxious":          "你感到焦虑",
    "lonely":           "你感到孤独",
    "scared":           "你感到害怕",
    "panicking":        "你在恐慌",
    "grieving":         "你在悲痛中",
    "guilty":           "你感到内疚",
    "headache":         "你头很疼",
    "insomnia":         "你无法入睡",
    "overwhelmed":      "你感到不堪重负",
    "heartbreak":       "你的心碎了",
    "missing_someone":  "你很想念某人",
    "relationship_pain":"你的感情让你很痛苦",
    "need_medicine":    "你需要药物",
    "need_money":       "你在财务上遇到了困难",
    "need_wifi":        "你需要网络",
    "need_quiet":       "你需要安静",
    "need_talk":        "你需要倾诉",
    "need_pray":        "你想要祈祷",
    "need_exercise":    "你想运动",
    "want_read":        "你想读点什么",
    "want_learn":       "你想学习新东西",
    "want_art":         "你想感受艺术",
    "want_music":       "你想听音乐",
    "want_work":        "你需要一个工作的地方",
    "want_friends":     "你想认识新朋友",
    "want_outdoor":     "你想出去走走",
    "want_create":      "你想创作",
    "bored":            "你感到无聊",
    "celebrating":      "你在庆祝",
    "homesick":         "你想家了",
    "confidence":       "你需要一些鼓励",
    "reflection":       "你想反思",
    "new_place":        "你到了一个新地方",
    "morning":          "早安",
    "evening":          "晚上好",
    "weekend":          "周末到了",
    "need_meaning":     "你在寻找生命的意义",
}


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


# ── Compound Need Synthesis ───────────────────────────────────────────────────
# When two needs fire simultaneously, find ONE place that addresses both.
# Added BEFORE individual attention meteors — compound meteor always ranks first.
# Each entry: (frozenset of attentions, synthesis config)
_COMPOUND_NEEDS: list[tuple[frozenset, dict]] = [
    (frozenset({"hungry", "lonely"}), {
        "place_types": ["community_centre", "cafe"],
        "why_prefix": "你既饿了又孤独",
        "why_suffix": "这里有吃的，也有人陪",
    }),
    (frozenset({"hungry", "need_money"}), {
        "place_types": ["community_centre"],
        "why_prefix": "你饿了，又缺钱",
        "why_suffix": "可能有免费餐食或帮助",
    }),
    (frozenset({"sad", "lonely"}), {
        "place_types": ["cafe", "community_centre"],
        "why_prefix": "你心情低落，又很孤独",
        "why_suffix": "有人在旁边，可能会好受一点",
    }),
    (frozenset({"anxious", "lonely"}), {
        "place_types": ["cafe", "library"],
        "why_prefix": "你焦虑又孤独",
        "why_suffix": "有人在旁边，但不用说话",
    }),
    (frozenset({"tired", "cold"}), {
        "place_types": ["cafe", "library"],
        "why_prefix": "你又冷又累",
        "why_suffix": "暖和，可以坐下来歇一歇",
    }),
    (frozenset({"scared", "lonely"}), {
        "place_types": ["library", "cafe", "place_of_worship"],
        "why_prefix": "你害怕，又一个人",
        "why_suffix": "安全的地方，有人在",
    }),
    (frozenset({"overwhelmed", "need_quiet"}), {
        "place_types": ["park", "garden", "library"],
        "why_prefix": "你不堪重负，需要安静",
        "why_suffix": "离开一切，找个安静的地方",
    }),
    (frozenset({"headache", "need_medicine"}), {
        "place_types": ["pharmacy"],
        "why_prefix": "你头疼，需要药",
        "why_suffix": "最近的药店",
    }),
]


# ── Fallback Text ─────────────────────────────────────────────────────────────
# When ALL APIs fail for an attention (no network, OSM empty, etc.), show this
# instead of silence. A text-only meteor is always better than nothing.
_ATTENTION_FALLBACK_TEXT: dict[str, str] = {
    "hungry":       "附近暂时没找到餐厅，可以搜索外卖",
    "thirsty":      "找不到咖啡馆，便利店可以买水",
    "tired":        "找个地方坐下来，哪怕只是路边的椅子",
    "cold":         "找找室内的地方：商场、便利店、任何有顶的地方",
    "hot":          "商场或室内任何有空调的地方",
    "anxious":      "深呼吸：吸气4秒 — 屏气7秒 — 呼气8秒，重复3次",
    "panicking":    "现在开始：吸气4秒 — 屏气7秒 — 呼气8秒",
    "sad":          "你不需要做任何事，就这样待着也可以",
    "angry":        "走出去走一走，哪怕只是绕着街区走一圈",
    "lonely":       "给一个老朋友发一条消息，哪怕只是「最近怎么样」",
    "scared":       "找一个人多的地方待着，不需要说话",
    "grieving":     "这时候不需要做任何事，允许自己难过",
    "headache":     "喝一杯水，闭眼休息一会儿",
    "insomnia":     "4-7-8 呼吸：吸4秒 — 屏7秒 — 呼8秒，重复3次",
    "overwhelmed":  "把所有事情写下来，先只做第一件",
    "heartbreak":   "哭出来也没关系，这是你应得的空间",
    "need_medicine":"搜索附近的「药店」或「医院」",
    "need_money":   "联系银行客服，或者找家人帮忙",
    "need_talk":    "心理援助热线：随时都可以拨打",
}


# ── Main Generator ───────────────────────────────────────────────────────────

def generate_trisoul_stars(
    recent_texts: list[str],
    lat: float,
    lng: float,
    topic_history: dict[str, int] | None = None,
    compass: WishCompass | None = None,
    history: set[str] | None = None,
    vow_suppressor: VowSuppressor | None = None,
    narrative: NarrativeTracker | None = None,
    feedback: StarFeedbackStore | None = None,
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
        vow_suppressor: Cross-layer suppressor (blocks food after "never hungry again")
        narrative: Life narrative tracker (shapes weights by life phase)
        feedback: Star engagement feedback store (boosts high-CTR attentions)

    Returns:
        TriSoulStarMap with meteors, stars, and earths — each backed by real API data.
    """
    star_map = TriSoulStarMap()
    used_items = set(history or {})

    # ── Update narrative phase ────────────────────────────────────────
    if narrative and recent_texts:
        narrative.update(recent_texts)

    # ── ☄️ METEORS: Surface Soul ─────────────────────────────────────
    # Only generate meteors for statements classified as SURFACE layer
    surface_attentions = detect_surface_attention(recent_texts)
    trigger_text = recent_texts[-1][:60] if recent_texts else ""

    # Classify each recent text — only surface-layer texts generate meteors
    # Deep statements → record vow suppression, generate wisdom meteors instead
    surface_texts = []
    deep_texts = []
    for text in recent_texts:
        layer, reason = classify_layer(text)
        if layer == SoulLayer.SURFACE:
            surface_texts.append(text)
        elif layer == SoulLayer.DEEP:
            deep_texts.append(text)
            # Register vow: duration depends on narrative phase
            # Survival → 12h (user is in crisis, may still need food soon)
            # Meaning   → 168h (deep commitment, suppress for a week)
            # Default   → 72h
            if vow_suppressor:
                vow_duration = 72
                if narrative:
                    phase_val = narrative.current_phase.value
                    if phase_val == "survival":
                        vow_duration = 12
                    elif phase_val == "meaning":
                        vow_duration = 168
                vow_suppressor.record(text, layer, hours=vow_duration)

    # Re-detect attentions from SURFACE-only texts
    if surface_texts:
        surface_attentions = detect_surface_attention(surface_texts)
    else:
        surface_attentions = []  # No surface needs → no meteors for physical world

    # Apply narrative weights to generation caps
    # surface_weight → meteors, middle_weight → stars, deep_weight → earths
    max_meteors = 5
    max_stars = 2
    max_earths = 6  # Compass shells are unbounded by default

    if narrative:
        w = narrative.weights
        sw = w.get("surface_weight", 1.0)
        mw = w.get("middle_weight", 1.0)
        dw = w.get("deep_weight", 1.0)
        max_meteors = max(1, min(5, round(sw * 3)))   # 0.5→2, 1.0→3, 2.0→5
        max_stars   = max(1, min(4, round(mw * 2)))   # 0.3→1, 1.0→2, 1.5→3
        max_earths  = max(0, min(6, round(dw * 3)))   # 0.2→1, 1.0→3, 2.0→6

    # Apply feedback signals to boost narrative phase scoring
    # If user consistently clicks growth/learning content → nudge narrative toward growth
    if feedback and narrative:
        top = feedback.top_attentions(n=3)
        growth_cats = {"learning", "books", "courses", "skill", "exercise", "social"}
        wisdom_cats = {"wisdom", "poetry", "reflection", "meaning", "mindfulness"}
        growth_clicks = sum(1 for att, _ in top if att in growth_cats)
        wisdom_clicks = sum(1 for att, _ in top if att in wisdom_cats)
        if growth_clicks >= 2:
            narrative.update(["learn", "course", "improve", "skill", "goal"])
        elif wisdom_clicks >= 2:
            narrative.update(["meaning", "believe", "who am i", "reflect"])

    # ── Compound need synthesis: one place for two simultaneous needs ────────
    attention_set = set(surface_attentions)
    for need_pair, synthesis in _COMPOUND_NEEDS:
        if not need_pair.issubset(attention_set):
            continue
        if len(star_map.meteors) >= max_meteors:
            break
        compound_action = {
            "api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
            "params": {"place_types": synthesis["place_types"]}, "cat": "place",
        }
        data = _call_api(compound_action, lat, lng)
        if not data:
            continue
        place_name = data.get("title", "")
        dedup_key = f"compound_{place_name[:20]}"
        if dedup_key in used_items:
            continue
        used_items.add(dedup_key)
        why = f"{synthesis['why_prefix']} → {place_name} — {synthesis['why_suffix']}"
        p_lat = data.get("_lat")
        p_lng = data.get("_lng")
        dist_m = 0
        if p_lat and p_lng and isinstance(p_lat, (int, float)):
            import math as _math
            dlat = (p_lat - lat) * 111000
            dlng = (p_lng - lng) * 111000 * _math.cos(_math.radians(lat))
            dist_m = _math.sqrt(dlat**2 + dlng**2)
        star_map.meteors.append(MeteorStar(
            text_trigger=trigger_text,
            attention="+".join(sorted(need_pair)),
            place_name=place_name,
            place_category="place",
            why=why,
            lat=p_lat if isinstance(p_lat, (int, float)) else None,
            lng=p_lng if isinstance(p_lng, (int, float)) else None,
            distance_m=dist_m,
            opening_hours=data.get("_opening_hours", ""),
        ))
        break  # One compound meteor maximum

    for attention in surface_attentions[:3]:
        meteors_before = len(star_map.meteors)
        actions = get_api_actions(attention)
        # Filter: only physical-world APIs for surface layer
        actions = filter_actions_by_layer(actions, SoulLayer.SURFACE)
        # Re-rank by feedback engagement weight
        if feedback:
            actions = feedback.sort_actions_by_weight(
                [{**a, "attention": attention} for a in actions]
            )

        # Record impression for feedback tracking
        if feedback:
            feedback.impression(attention)

        for action in actions:
            if len(star_map.meteors) >= max_meteors:
                break

            # Cross-layer suppression: skip if a Deep vow suppresses this category.
            # Pass current surface attentions so urgent physical needs override the vow.
            if vow_suppressor and vow_suppressor.is_suppressed(
                action.get("cat", ""), current_attentions=surface_attentions
            ):
                continue

            data = _call_api(action, lat, lng)
            if not data:
                continue

            # Build display text — use the user's ACTUAL WORDS when possible.
            # "你说「haven't eaten」→ Corner Cafe" beats "你说饿了 → Corner Cafe"
            why = _format_why(action.get("template", ""), data)
            if not why:
                continue
            trigger = _find_trigger_phrase(recent_texts, attention)
            if trigger:
                why = f"你说「{trigger}」→ {why}"
            else:
                prefix = _ATTENTION_WHY_PREFIX.get(attention, "")
                if prefix:
                    why = f"{prefix} → {why}"

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

        # ── Fallback: if ALL APIs failed for this attention, never leave user with nothing
        if len(star_map.meteors) == meteors_before and len(star_map.meteors) < max_meteors:
            fallback_text = _ATTENTION_FALLBACK_TEXT.get(attention)
            if fallback_text:
                trigger = _find_trigger_phrase(recent_texts, attention)
                if trigger:
                    fallback_why = f"你说「{trigger}」→ {fallback_text}"
                else:
                    prefix = _ATTENTION_WHY_PREFIX.get(attention, "")
                    fallback_why = f"{prefix} → {fallback_text}" if prefix else fallback_text
                star_map.meteors.append(MeteorStar(
                    text_trigger=trigger_text,
                    attention=attention,
                    place_name="",
                    place_category="text",
                    why=fallback_why,
                ))

    # ── ☄️ DEEP METEORS: Deep statements → wisdom, not physical ────
    # "I'll never be hungry again" → Stoic wisdom, NOT restaurant
    for text in deep_texts[:2]:
        # Deep statements get wisdom APIs
        wisdom_actions = [
            {"api": "wish_engine.apis.spiritual_apis", "fn": "daily_wisdom", "params": {},
             "template": "🌿 {tradition}: {text} — {source}", "star": "meteor", "cat": "wisdom"},
            {"api": "wish_engine.apis.poetry_api", "fn": "random_poem", "params": {},
             "template": "📜 {title} by {author}", "star": "meteor", "cat": "poetry"},
            {"api": "wish_engine.apis.advice_api", "fn": "get_advice", "params": {},
             "template": "💭 {result}", "star": "meteor", "cat": "reflection"},
        ]

        for action in wisdom_actions:
            if len(star_map.meteors) >= max_meteors:
                break
            data = _call_api(action, lat, lng)
            if not data:
                continue
            why = _format_why(action.get("template", ""), data)
            if not why or why[:40] in used_items:
                continue
            used_items.add(why[:40])

            star_map.meteors.append(MeteorStar(
                text_trigger=text[:60],
                attention="deep_reflection",
                place_name="",
                place_category=action.get("cat", "wisdom"),
                why=why,
                color="#E8A0BF",  # Rose gold for deep
                animation="pulse_deep",
            ))
            break  # One wisdom per deep text

    # ── ⭐ STARS: Middle Soul ────────────────────────────────────────
    if topic_history:
        middle_attentions = detect_middle_history(topic_history)
        middle_attentions = [a for a in middle_attentions if a not in surface_attentions]

        for attention in middle_attentions[:max_stars]:
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
            if len(star_map.earths) >= max_earths:
                break

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
