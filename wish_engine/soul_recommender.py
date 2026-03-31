"""Soul Recommender — recommendations driven by TriSoul layers, not personality types.

NOT: "You're INFJ so here's a quiet place"
YES: "You just said you're starving → nearest cheap restaurant open now"
YES: "You've been talking about yoga for 3 weeks → there's a yoga studio 200m away"
YES: "Compass detected you care about Rhett more than you admit → a quiet bench to think"

Three layers:
  Surface: current attention / what's on their mind RIGHT NOW
  Middle: historical interests / what they keep coming back to
  Deep: hidden desires / Compass shells
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from wish_engine.apis.osm_api import search_and_enrich


# ── Surface Soul: what's on their mind RIGHT NOW ────────────────────────────

# Map user's current attention to what OSM places would help
ATTENTION_TO_PLACES: dict[str, dict] = {
    # Survival / basic needs
    "hungry": {"osm": ["restaurant", "cafe", "supermarket"], "why": "你说饿了 — {place}现在还开着"},
    "thirsty": {"osm": ["cafe"], "why": "附近的{place}可以坐下来喝点东西"},
    "tired": {"osm": ["cafe", "park"], "why": "你说累了 — {place}可以让你歇一歇"},
    "cold": {"osm": ["cafe", "library"], "why": "外面冷 — {place}暖和，可以待一会"},
    "hot": {"osm": ["cafe", "library", "swimming_pool"], "why": "太热了 — {place}有空调"},

    # Emotional needs
    "anxious": {"osm": ["park", "garden", "library"], "why": "你的焦虑在升高 — {place}很安静，适合深呼吸"},
    "sad": {"osm": ["park", "garden", "cafe"], "why": "你最近心情低落 — {place}的环境可能让你好受一点"},
    "angry": {"osm": ["gym", "fitness_centre", "park"], "why": "这股怒气需要出口 — {place}可以让你动起来"},
    "lonely": {"osm": ["cafe", "community_centre", "library"], "why": "你说觉得孤独 — {place}有人的地方，不需要说话，但不是一个人"},
    "scared": {"osm": ["library", "cafe", "place_of_worship"], "why": "你说害怕 — {place}是安全的、有人的地方"},
    "panicking": {"osm": ["park", "garden", "place_of_worship"], "why": "深呼吸。{place}离你很近，去那里坐下来"},
    "grieving": {"osm": ["park", "garden", "place_of_worship"], "why": "失去亲人的痛不会马上好 — {place}可以让你安静地待着"},
    "guilty": {"osm": ["place_of_worship", "park"], "why": "内疚需要空间来面对 — {place}很安静"},

    # Practical needs
    "need_money": {"osm": ["bank", "atm"], "why": "你说需要钱 — 最近的{place}"},
    "need_medicine": {"osm": ["pharmacy", "hospital"], "why": "你说需要药 — {place}离你最近"},
    "need_wifi": {"osm": ["cafe", "library"], "why": "需要上网 — {place}有免费WiFi"},
    "need_quiet": {"osm": ["library", "park", "garden"], "why": "你说想安静 — {place}是附近最安静的地方"},
    "need_exercise": {"osm": ["gym", "fitness_centre", "swimming_pool", "park"], "why": "想运动 — {place}离你不远"},

    # Spiritual needs
    "need_pray": {"osm": ["place_of_worship"], "why": "祈祷时间到了 — {place}离你最近"},
    "need_meaning": {"osm": ["place_of_worship", "museum", "park"], "why": "你在寻找意义 — {place}可能给你一些启发"},

    # Social needs
    "need_talk": {"osm": ["cafe", "community_centre"], "why": "你说想跟人说话 — {place}是个适合坐下来聊天的地方"},
    "want_friends": {"osm": ["community_centre", "cafe", "gym"], "why": "想认识人 — {place}有社区活动"},

    # Creative needs
    "want_art": {"osm": ["arts_centre", "gallery", "museum"], "why": "你对艺术有兴趣 — {place}现在有展览"},
    "want_read": {"osm": ["library", "bookshop"], "why": "想看书 — {place}离你很近"},
    "want_music": {"osm": ["theatre", "cinema"], "why": "想听音乐 — {place}可能有演出"},

    # Career needs
    "want_work": {"osm": ["cafe", "library"], "why": "想找地方工作 — {place}安静、有WiFi"},
    "want_learn": {"osm": ["library", "community_centre"], "why": "想学东西 — {place}可能有课程或资源"},

    # Context-aware (time, location)
    "bored":       {"osm": ["museum", "gallery", "park", "arts_centre"], "why": "有点无聊 — {place}可能有意思"},
    "morning":     {"osm": ["cafe"], "why": "早安 — {place}可以开始新的一天"},
    "evening":     {"osm": ["park", "cafe"], "why": "傍晚了 — {place}很适合放松"},
    "weekend":     {"osm": ["museum", "park", "arts_centre"], "why": "周末探索 — {place}值得去看看"},
    "new_place":   {"osm": ["museum", "community_centre"], "why": "探索新地方 — {place}"},
    "insomnia":    {"osm": ["pharmacy", "park"], "why": "睡不着 — {place}可能有帮助"},

    # Self-improvement
    "confidence":  {"osm": ["gym", "community_centre"], "why": "需要振作 — {place}可以帮你找回状态"},
    "reflection":  {"osm": ["park", "garden", "library"], "why": "你在思考 — {place}是个安静的地方"},

    # Missing life needs
    "celebrating": {"osm": ["restaurant", "cafe", "arts_centre"], "why": "值得庆祝 — {place}是个好地方"},
    "homesick":    {"osm": ["community_centre", "place_of_worship"], "why": "想家了 — {place}可能有同乡"},
    "headache":    {"osm": ["pharmacy"], "why": "头疼 — {place}离你最近"},
    "overwhelmed": {"osm": ["park", "garden"], "why": "需要喘息 — {place}很安静"},
    "want_outdoor":{"osm": ["park", "garden", "nature_reserve"], "why": "想去户外 — {place}离你不远"},
    "want_create": {"osm": ["arts_centre", "library", "community_centre"], "why": "想创作 — {place}有空间和工具"},

    # Relationship / emotional pain
    "heartbreak":        {"osm": ["park", "garden", "cafe"], "why": "心里不好受 — {place}可以坐下来，慢慢想清楚"},
    "missing_someone":   {"osm": ["park", "garden", "cafe"], "why": "想念一个人 — {place}安静，适合思念"},
    "relationship_pain": {"osm": ["community_centre", "library", "place_of_worship"], "why": "关系里不容易 — {place}可以是你的安全空间"},
}


def detect_surface_attention(recent_texts: list[str]) -> list[str]:
    """Detect what's on the user's mind from their recent messages.

    Returns list of attention keys (e.g., ["hungry", "anxious", "lonely"]).
    Zero LLM — keyword detection from actual words they said.
    """
    combined = " ".join(recent_texts).lower()
    attentions = []

    # Direct statements (what they literally said)
    keyword_map = {
        "hungry": ["hungry", "starving", "饿", "没吃", "food", "eat", "جائع"],
        "thirsty": ["thirsty", "渴", "drink", "water"],
        "tired": ["tired", "exhausted", "drained", "burnt out", "burnout", "no energy", "depleted", "累", "疲", "متعب", "can't move"],
        "cold": ["cold", "freezing", "冷"],
        "hot": ["hot", "burning", "热", "حر"],
        "anxious": ["anxious", "worried", "nervous", "can't breathe", "panic", "restless", "uneasy", "on edge", "焦虑", "紧张", "قلق"],
        "sad": ["sad", "crying", "tears", "depressed", "numb", "hopeless", "feel low", "feeling low", "lost all hope", "breaking down", "down lately", "伤心", "哭", "难过", "حزين"],
        "angry": ["angry", "furious", "rage", "hate", "damn", "生气", "愤怒", "غاضب"],
        "lonely": ["lonely", "alone", "nobody", "no one", "isolated", "disconnected", "no friends", "feel invisible", "孤独", "一个人", "وحيد"],
        "scared": ["scared", "afraid", "terrified", "害怕", "恐惧", "خائف"],
        "panicking": ["panic attack", "can't breathe", "help me", "恐慌发作"],
        "grieving": ["died", "dead", "funeral", "loss", "去世", "死", "失去", "وفاة"],
        "guilty": ["guilty", "fault", "wrong", "sorry", "shouldn't", "内疚", "对不起"],
        "need_money": ["money", "i'm broke", "im broke", "flat broke", "can't afford", "debt", "钱", "穷", "مال"],
        "need_medicine": ["medicine", "sick", "ill", "pain", "药", "生病", "مريض"],
        "need_wifi": ["wifi", "internet", "上网", "إنترنت"],
        "need_quiet": ["quiet", "silence", "peace", "安静", "هدوء"],
        "need_exercise": ["exercise", "gym", "run", "workout", "运动", "锻炼", "رياضة"],
        "need_pray": ["pray", "prayer", "mosque", "church", "temple", "祈祷", "صلاة", "مسجد"],
        "need_meaning": ["meaning", "purpose", "why am i", "意义", "目的"],
        "need_talk": ["talk to someone", "need someone", "想说话", "need to talk", "confused about my", "don't know what to do", "need advice", "don't know who to talk"],
        "want_friends": ["friends", "meet people", "交朋友", "认识人"],
        "want_art": ["art", "gallery", "exhibition", "画", "展览"],
        "want_read": ["book", "read", "library", "书", "读", "图书馆"],
        "want_music": ["music", "concert", "sing", "音乐", "唱"],
        "want_work": ["work", "productive", "focus", "deadline", "工作", "写代码"],
        "want_learn": ["learn", "study", "course", "学", "课"],
        # Context-aware
        "bored":       ["bored", "boring", "nothing to do", "kill time", "无聊", "ممل"],
        "morning":     ["good morning", "this morning", "just woke up", "早上好", "刚起床", "صباح الخير"],
        "evening":     ["tonight", "this evening", "after work", "winding down", "晚上了", "مساء"],
        "weekend":     ["weekend", "saturday", "sunday", "周末", "星期六", "星期天", "نهاية الأسبوع"],
        "new_place":   ["new here", "just moved", "just arrived", "visiting", "tourist", "刚来", "陌生的地方", "وصلت"],
        "insomnia":    ["can't sleep", "insomnia", "wide awake", "lying awake", "失眠", "睡不着", "أرق"],
        # Self-improvement
        "confidence":  ["not confident", "insecure", "worthless", "can't do it", "nobody likes", "feel useless", "i'm a failure", "not good enough", "hate myself", "没信心", "不自信", "لا أستطيع"],
        "reflection":  ["reflecting on", "looking back", "in hindsight", "i wonder why", "i've been reflecting", "回想起来", "反思"],
        # Missing life needs
        "celebrating": ["celebrating", "birthday", "anniversary", "promotion", "good news", "庆祝", "生日", "升职", "احتفال"],
        "homesick":    ["homesick", "miss home", "miss my family", "far from home", "想家", "思乡", "أشتاق للبيت"],
        "headache":    ["headache", "migraine", "head hurts", "头疼", "头痛", "صداع"],
        "overwhelmed": ["overwhelmed", "too much", "can't handle", "falling apart", "can't cope", "can't take it", "stuck and", "不知所措", "崩溃了", "مرهق"],
        "want_outdoor":["outdoors", "nature", "fresh air", "hike", "hiking", "户外", "大自然", "الطبيعة"],
        "want_create": ["want to create", "creative", "make something", "draw", "paint", "craft", "创作", "画画", "أبدع"],
        # Relationship / emotional pain (from real data)
        "heartbreak":        ["broke up", "break up", "my ex", "she left", "he left", "want her back", "want him back", "want them back", "want my person back", "my heart is broken", "heartbreak", "heartbroken", "失恋", "分手", "قلبي"],
        "missing_someone":   ["miss him", "miss her", "miss them", "missing him", "missing her", "missing someone", "think about him", "think about her", "think about them", "can't stop thinking about", "thinking of you", "想他", "想她", "想你", "想某人"],
        "relationship_pain": ["controlling", "won't let me", "won't allow me", "trapped", "toxic relationship", "confused in my relationship", "relationship problems", "relationship issues", "he controls", "she controls", "abusive", "can't leave", "stuck with", "affection", "caring about", "doesn't care", "مشكلة في العلاقة"],
    }

    import re
    for attention, keywords in keyword_map.items():
        for kw in keywords:
            # For CJK/Arabic: substring match (word boundaries don't work)
            if any(ord(c) > 127 for c in kw):
                if kw in combined:
                    attentions.append(attention)
                    break
            else:
                # For Latin: word boundary match to avoid "weather" matching "eat"
                if re.search(r'\b' + re.escape(kw) + r'\b', combined):
                    attentions.append(attention)
                    break

    return attentions


# ── Middle Soul: topic accumulator ──────────────────────────────────────────

# Topic → detection keywords (used by update_topic_history)
_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "yoga":         ["yoga"],
    "meditation":   ["meditat", "mindful"],
    "running":      ["running", "jogging"],
    "swimming":     ["swimming", "swim"],
    "gym":          ["gym", "weightlift", "lifting"],
    "fitness":      ["fitness", "workout", "exercise"],
    "hiking":       ["hiking", "hike", "trail"],
    "nature":       ["nature", "forest", "outdoors"],
    "garden":       ["garden", "gardening"],
    "coffee":       ["coffee", "espresso", "cappuccino"],
    "cooking":      ["cooking", "cook", "recipe", "baking", "bake"],
    "food":         ["food", "eating", "restaurant", "meal"],
    "art":          ["art", "museum", "gallery", "exhibition"],
    "drawing":      ["drawing", "draw", "sketch", "illustration"],
    "painting":     ["painting", "paint", "watercolor"],
    "photography":  ["photo", "photography", "camera", "shoot"],
    "writing":      ["writing", "write", "story", "blog", "journal"],
    "crafts":       ["craft", "knit", "sew", "pottery"],
    "design":       ["design", "ui", "ux", "figma"],
    "books":        ["book", "reading", "novel", "fiction", "nonfiction"],
    "language":     ["language learning", "english class", "arabic lesson", "chinese lesson", "duolingo"],
    "coding":       ["coding", "programming", "developer", "software", "python", "javascript"],
    "podcast":      ["podcast", "episode", "listen to"],
    "study":        ["studying", "exam", "homework", "assignment"],
    "music":        ["music", "song", "playlist", "concert", "band"],
    "film":         ["movie", "film", "cinema", "documentary", "series"],
    "gaming":       ["gaming", "game", "playing games", "video game"],
    "travel":       ["travel", "trip", "visited", "flight", "passport"],
    "family":       ["family", "mom", "dad", "sister", "brother", "parents"],
    "friends":      ["friends", "friendship", "social life", "hang out"],
    "loneliness":   ["lonely", "alone", "isolated", "no friends"],
    "anxiety":      ["anxiety", "anxious", "panic", "worry"],
    "work":         ["work", "job", "career", "office", "meeting"],
    "career":       ["career", "promotion", "interview", "resume"],
    "startup":      ["startup", "founder", "launch", "product"],
    "prayer":       ["prayer", "pray", "mosque", "church", "temple"],
    "faith":        ["faith", "god", "spiritual", "religion"],
    "home":         ["home", "house", "apartment", "hometown"],
}


def update_topic_history(
    text: str,
    history: dict[str, int] | None = None,
    decay: float = 0.99,
) -> dict[str, int]:
    """Extract topics from a user message and update running topic history.

    Call once per user turn. Feed the returned dict back into the next call,
    then pass it to generate_trisoul_stars() as topic_history.

    Args:
        text:    One user message (any language).
        history: Existing topic counts from previous turns (or None to start).
        decay:   Multiply all existing counts by this each call (slow forgetting).
                 Default 0.99 means a topic drops below threshold (~3) after
                 ~500 turns of silence — effectively permanent within a session.

    Returns:
        Updated {topic: count} dict. Store and pass back next call.

    Example (App integration):
        topic_history: dict = {}
        for user_message in conversation:
            topic_history = update_topic_history(user_message, topic_history)
        stars = generate_trisoul_stars(..., topic_history=topic_history)
    """
    result = {t: round(c * decay) for t, c in (history or {}).items() if round(c * decay) >= 1}
    text_lower = text.lower()
    for topic, keywords in _TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                result[topic] = result.get(topic, 0) + 1
                break  # one match per topic per message
    return result


def detect_middle_history(topic_counts: dict[str, int]) -> list[str]:
    """Detect what they've been CONSISTENTLY interested in from conversation history.

    topic_counts: {"yoga": 12, "career": 8, "coffee": 15, "anxiety": 20}
    Returns top recurring interests that map to real-world services.
    """
    interest_to_attention = {
        # Physical / health
        "yoga":         "need_exercise",
        "meditation":   "need_quiet",
        "running":      "need_exercise",
        "swimming":     "need_exercise",
        "fitness":      "need_exercise",
        "gym":          "need_exercise",
        "hiking":       "want_outdoor",
        "nature":       "want_outdoor",
        "outdoors":     "want_outdoor",
        "garden":       "want_outdoor",
        # Food
        "coffee":       "hungry",
        "food":         "hungry",
        "cooking":      "hungry",
        "baking":       "hungry",
        "recipes":      "hungry",
        # Creative
        "art":          "want_art",
        "drawing":      "want_create",
        "painting":     "want_create",
        "photography":  "want_art",
        "writing":      "want_create",
        "crafts":       "want_create",
        "design":       "want_create",
        # Learning
        "books":        "want_read",
        "reading":      "want_read",
        "language":     "want_learn",
        "coding":       "want_work",
        "podcast":      "want_learn",
        "study":        "want_learn",
        # Social / emotional
        "friends":      "want_friends",
        "loneliness":   "lonely",
        "anxiety":      "anxious",
        "family":       "homesick",
        "home":         "homesick",
        # Career / productivity
        "work":         "want_work",
        "career":       "want_work",
        "startup":      "want_work",
        "project":      "want_work",
        # Spiritual
        "prayer":       "need_pray",
        "faith":        "need_pray",
        "spirituality": "need_meaning",
        # Entertainment
        "music":        "want_music",
        "film":         "want_art",
        "gaming":       "bored",
        "games":        "bored",
        "travel":       "new_place",
    }

    # Only topics mentioned 3+ times count as recurring
    recurring = [(topic, count) for topic, count in topic_counts.items() if count >= 3]
    recurring.sort(key=lambda x: -x[1])

    attentions = []
    for topic, _ in recurring[:3]:
        mapped = interest_to_attention.get(topic)
        if mapped:
            attentions.append(mapped)

    return attentions


@dataclass
class SoulRecommendation:
    """A recommendation grounded in what the user actually said/felt/needs."""
    layer: str              # "surface" / "middle" / "deep"
    attention: str          # what triggered this (e.g., "hungry", "anxious")
    place_name: str         # real place name from OSM
    place_category: str     # cafe, park, library...
    why: str                # specific reason in their language
    lat: float | None = None
    lng: float | None = None
    distance_m: float = 0
    opening_hours: str = ""


def recommend_from_soul(
    recent_texts: list[str],
    lat: float,
    lng: float,
    topic_history: dict[str, int] | None = None,
    compass_topics: list[str] | None = None,
    max_results: int = 3,
) -> list[SoulRecommendation]:
    """The main function. Takes Soul state + location → real place recommendations.

    Args:
        recent_texts: User's recent messages (last few turns)
        lat, lng: Current GPS
        topic_history: Historical topic counts from middle soul
        compass_topics: Topics from Compass deep layer (hidden desires)
        max_results: Max recommendations

    Returns:
        List of SoulRecommendation with real place names and specific reasons.
    """
    import math

    # ── Layer 1: Surface — what are they thinking RIGHT NOW ──────────
    surface_attentions = detect_surface_attention(recent_texts)

    # ── Layer 2: Middle — what do they keep coming back to ───────────
    middle_attentions = detect_middle_history(topic_history or {})

    # ── Layer 3: Deep — Compass hidden desires ───────────────────────
    deep_attentions = []
    for topic in (compass_topics or []):
        deep_attentions.append("need_quiet")  # default: place to think about the hidden thing

    # Combine, surface first (most urgent)
    all_attentions = []
    for a in surface_attentions:
        all_attentions.append(("surface", a))
    for a in middle_attentions:
        if a not in surface_attentions:
            all_attentions.append(("middle", a))
    for a in deep_attentions:
        all_attentions.append(("deep", a))

    # ── Search OSM for each attention ────────────────────────────────
    results = []
    used_places = set()

    for layer, attention in all_attentions:
        if len(results) >= max_results:
            break

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

            # Calculate distance
            p_lat = place.get("_lat") or 0
            p_lng = place.get("_lng") or 0
            dist_m = 0
            if p_lat and p_lng:
                dlat = (p_lat - lat) * 111000
                dlng = (p_lng - lng) * 111000 * math.cos(math.radians(lat))
                dist_m = math.sqrt(dlat**2 + dlng**2)

            # Build the "why" — specific to this place + this attention
            why = spec["why"].format(place=name)

            # Add distance context
            if dist_m > 0:
                if dist_m < 500:
                    why += f"，就在{int(dist_m)}米外"
                elif dist_m < 2000:
                    why += f"，{dist_m/1000:.1f}公里"

            results.append(SoulRecommendation(
                layer=layer,
                attention=attention,
                place_name=name,
                place_category=place.get("category", ""),
                why=why,
                lat=p_lat if p_lat else None,
                lng=p_lng if p_lng else None,
                distance_m=dist_m,
                opening_hours=place.get("_opening_hours", ""),
            ))
            break  # One place per attention

    return results
