"""Soul API Bridge — maps every Soul signal to real API calls.

TriSoul signal → which API to call → real data → Star on the map.

This is the 知行合一 layer: from the heart to the real world.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class APIAction:
    """A concrete action: which API to call, with what params, returning what."""
    api_module: str        # e.g. "wish_engine.apis.open_meteo_api"
    api_function: str      # e.g. "get_weather"
    params: dict           # e.g. {"lat": 25.2, "lng": 55.3}
    display_template: str  # e.g. "现在{city} {temperature}°C，{condition}"
    star_type: str         # "meteor" / "star" / "earth"
    category: str          # what soul need this serves


# ── Soul Signal → API Mapping ────────────────────────────────────────────────

# Key: (layer, attention) → list of APIActions to try
# Layer: "surface" (当下), "middle" (历史), "deep" (Compass)

SOUL_API_MAP: dict[str, list[dict]] = {

    # ═══ SURVIVAL NEEDS ═══
    "hungry": [
        {"api": "wish_engine.apis.meal_api", "fn": "random_meal", "params": {}, "template": "试试这道菜: {name} ({area}) — {instructions:.80}", "star": "meteor", "cat": "food"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["restaurant", "cafe"]}, "template": "附近: {title} — {description}", "star": "meteor", "cat": "place"},
    ],
    "thirsty": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe"]}, "template": "{title} — 坐下来喝点什么", "star": "meteor", "cat": "place"},
        {"api": "wish_engine.apis.cocktail_api", "fn": "random_cocktail", "params": {}, "template": "试试: {name} — {instructions:.60}", "star": "meteor", "cat": "drink"},
    ],
    "need_money": [
        {"api": "wish_engine.apis.currency_api", "fn": "get_rates", "params": {"base": "USD"}, "template": "当前汇率: 1 USD = {EUR} EUR / {CNY} CNY", "star": "meteor", "cat": "finance"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["bank", "atm"]}, "template": "最近的: {title}", "star": "meteor", "cat": "finance"},
    ],
    "need_medicine": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["pharmacy", "hospital"]}, "template": "最近的: {title} — {description}", "star": "meteor", "cat": "health"},
    ],

    # ═══ EMOTIONAL NEEDS ═══
    "anxious": [
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise", "params": {"technique": "478"}, "template": "4-7-8 呼吸: {name} — 吸气{steps[0][1]}秒，屏息{steps[1][1]}秒，呼气{steps[2][1]}秒", "star": "meteor", "cat": "calm"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["park", "garden", "library"]}, "template": "{title} — 安静的地方，适合深呼吸", "star": "meteor", "cat": "place"},
        {"api": "wish_engine.apis.spiritual_apis", "fn": "mindfulness_reminder", "params": {}, "template": "🔔 {result}", "star": "meteor", "cat": "mindfulness"},
    ],
    "sad": [
        {"api": "wish_engine.apis.dog_api", "fn": "random_dog_image", "params": {}, "template": "🐕 看看这只狗狗", "star": "meteor", "cat": "healing"},
        {"api": "wish_engine.apis.poetry_api", "fn": "random_poem", "params": {}, "template": "📜 {title} by {author}\n{lines[0]}\n{lines[1]}", "star": "meteor", "cat": "poetry"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice", "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
    ],
    "angry": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["gym", "fitness_centre"]}, "template": "{title} — 把怒气转化为力量", "star": "meteor", "cat": "exercise"},
        {"api": "wish_engine.apis.exercise_api", "fn": "search_exercises", "params": {"term": "boxing"}, "template": "试试: {name} — 释放压力", "star": "meteor", "cat": "exercise"},
    ],
    "lonely": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe", "community_centre"]}, "template": "{title} — 有人的地方，不需要说话，但不是一个人", "star": "meteor", "cat": "social"},
        {"api": "wish_engine.apis.social_apis", "fn": "conversation_starter", "params": {"context": "general"}, "template": "💬 如果想开口: {result}", "star": "meteor", "cat": "social"},
        {"api": "wish_engine.apis.cat_api", "fn": "random_cat_image", "params": {}, "template": "🐱 猫咪陪你", "star": "meteor", "cat": "healing"},
    ],
    "scared": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["library", "cafe", "place_of_worship"]}, "template": "{title} — 安全的、有人的地方", "star": "meteor", "cat": "safety"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise", "params": {"technique": "box"}, "template": "盒式呼吸: 吸4秒-屏4秒-呼4秒-屏4秒，重复4次", "star": "meteor", "cat": "calm"},
    ],
    "panicking": [
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise", "params": {"technique": "478"}, "template": "⚠️ 4-7-8 呼吸，现在开始。吸气4秒...", "star": "meteor", "cat": "crisis"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["park", "garden"]}, "template": "最近的安静空间: {title}", "star": "meteor", "cat": "crisis"},
    ],
    "grieving": [
        {"api": "wish_engine.apis.poetry_api", "fn": "search_by_author", "params": {"author": "Emily Dickinson"}, "template": "📜 {title} — {author}", "star": "meteor", "cat": "grief"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["park", "garden", "place_of_worship"]}, "template": "{title} — 一个可以安静待着的地方", "star": "meteor", "cat": "grief"},
    ],
    "guilty": [
        {"api": "wish_engine.apis.spiritual_apis", "fn": "daily_wisdom", "params": {}, "template": "🌿 {tradition}: {text} — {source}", "star": "meteor", "cat": "wisdom"},
        {"api": "wish_engine.apis.social_apis", "fn": "conflict_prompt", "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "reflection"},
    ],

    # ═══ GROWTH NEEDS ═══
    "want_read": [
        {"api": "wish_engine.apis.google_books_api", "fn": "search_books", "params": {}, "template": "📚 {title} by {authors[0]} — ⭐{rating}", "star": "star", "cat": "books"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["library", "bookshop"]}, "template": "📖 {title} — 去翻翻看", "star": "star", "cat": "place"},
        {"api": "wish_engine.apis.knowledge_apis", "fn": "search_books_gutenberg", "params": {}, "template": "📕 免费电子书: {title} — {authors[0]}", "star": "star", "cat": "books"},
    ],
    "want_learn": [
        {"api": "wish_engine.apis.knowledge_apis", "fn": "random_wikipedia", "params": {}, "template": "🌐 今日知识: {title} — {extract:.100}", "star": "star", "cat": "learning"},
        {"api": "wish_engine.apis.knowledge_apis", "fn": "today_in_history", "params": {}, "template": "📅 历史上的今天 ({year}): {text:.80}", "star": "star", "cat": "learning"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["library", "community_centre"]}, "template": "{title} — 可能有课程或资源", "star": "star", "cat": "learning"},
    ],
    "want_art": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["arts_centre", "gallery", "museum"]}, "template": "🎨 {title} — 去看看", "star": "star", "cat": "art"},
        {"api": "wish_engine.apis.wikipedia_api", "fn": "get_summary", "params": {}, "template": "🖼️ 关于{topic}: {extract:.100}", "star": "star", "cat": "art"},
    ],
    "want_music": [
        {"api": "wish_engine.apis.radio_api", "fn": "search_stations", "params": {}, "template": "📻 {name} ({country}) — 正在播放", "star": "star", "cat": "music"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["theatre", "cinema"]}, "template": "🎵 {title} — 可能有演出", "star": "star", "cat": "music"},
    ],
    "want_work": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe", "library"]}, "template": "💻 {title} — 安静、有WiFi", "star": "star", "cat": "work"},
        {"api": "wish_engine.apis.productivity_apis", "fn": "pomodoro_schedule", "params": {"total_hours": 2}, "template": "🍅 番茄钟已准备: {len(result)}个时段", "star": "star", "cat": "work"},
    ],
    "need_exercise": [
        {"api": "wish_engine.apis.exercise_api", "fn": "search_exercises", "params": {"term": "yoga"}, "template": "🧘 试试: {name}", "star": "star", "cat": "exercise"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["gym", "fitness_centre", "swimming_pool", "park"]}, "template": "🏃 {title} — 动起来", "star": "star", "cat": "exercise"},
        {"api": "wish_engine.apis.health_apis", "fn": "estimate_calories", "params": {"activity": "running", "weight_kg": 70, "minutes": 30}, "template": "跑步30分钟 ≈ 消耗{result}卡路里", "star": "star", "cat": "exercise"},
    ],

    # ═══ SPIRITUAL NEEDS ═══
    "need_pray": [
        {"api": "wish_engine.apis.aladhan_api", "fn": "get_prayer_times", "params": {}, "template": "🕌 祈祷时间: Fajr {fajr} | Dhuhr {dhuhr} | Asr {asr} | Maghrib {maghrib} | Isha {isha}", "star": "meteor", "cat": "prayer"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["place_of_worship"]}, "template": "🕌 最近: {title}", "star": "meteor", "cat": "prayer"},
        {"api": "wish_engine.apis.quran_api", "fn": "get_ayah", "params": {"reference": "random"}, "template": "📖 {surah}: {text:.100}", "star": "meteor", "cat": "prayer"},
    ],
    "need_meaning": [
        {"api": "wish_engine.apis.spiritual_apis", "fn": "daily_wisdom", "params": {}, "template": "🌿 {tradition}: {text} — {source}", "star": "earth", "cat": "meaning"},
        {"api": "wish_engine.apis.bible_api", "fn": "random_verse", "params": {}, "template": "✝️ {reference}: {text:.100}", "star": "earth", "cat": "meaning"},
        {"api": "wish_engine.apis.philosophy_quotes", "fn": "get_quote", "params": {}, "template": "🏛️ {result}", "star": "earth", "cat": "meaning"},
    ],

    # ═══ SOCIAL NEEDS ═══
    "need_talk": [
        {"api": "wish_engine.apis.social_apis", "fn": "conversation_starter", "params": {"context": "deep"}, "template": "💬 打开话题: {result}", "star": "meteor", "cat": "social"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe", "community_centre"]}, "template": "{title} — 适合聊天的地方", "star": "meteor", "cat": "social"},
    ],
    "want_friends": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["community_centre", "cafe", "gym"]}, "template": "{title} — 可以认识人的地方", "star": "star", "cat": "social"},
        {"api": "wish_engine.apis.social_apis", "fn": "ice_breaker", "params": {}, "template": "🧊 破冰: {result}", "star": "star", "cat": "social"},
    ],

    # ═══ PRACTICAL NEEDS ═══
    "need_wifi": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe", "library"]}, "template": "📶 {title} — 通常有免费WiFi", "star": "meteor", "cat": "utility"},
    ],
    "need_quiet": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["library", "park", "garden"]}, "template": "🤫 {title} — 附近最安静的地方", "star": "meteor", "cat": "quiet"},
    ],

    # ═══ FUN / BOREDOM ═══
    "bored": [
        {"api": "wish_engine.apis.bored_api", "fn": "get_activity", "params": {}, "template": "💡 试试: {activity} ({type})", "star": "meteor", "cat": "fun"},
        {"api": "wish_engine.apis.joke_api", "fn": "get_joke", "params": {}, "template": "😂 {joke}", "star": "meteor", "cat": "fun"},
        {"api": "wish_engine.apis.micro_apis", "fn": "random_trivia", "params": {}, "template": "🧠 {category}: {question}", "star": "meteor", "cat": "fun"},
        {"api": "wish_engine.apis.iss_api", "fn": "iss_location", "params": {}, "template": "🛸 国际空间站现在在 {lat:.1f}, {lng:.1f} 上空", "star": "meteor", "cat": "wonder"},
    ],

    # ═══ SELF-IMPROVEMENT ═══
    "confidence": [
        {"api": "wish_engine.apis.affirmations_api", "fn": "get_affirmation", "params": {}, "template": "💪 {result}", "star": "star", "cat": "confidence"},
        {"api": "wish_engine.apis.social_apis", "fn": "random_compliment", "params": {}, "template": "🌟 {result}", "star": "star", "cat": "confidence"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "daily_challenge", "params": {}, "template": "🎯 今日挑战: {result}", "star": "star", "cat": "confidence"},
    ],
    "reflection": [
        {"api": "wish_engine.apis.wellness_apis", "fn": "gratitude_prompt", "params": {}, "template": "🙏 {result}", "star": "star", "cat": "reflection"},
        {"api": "wish_engine.apis.productivity_apis", "fn": "weekly_reflection", "params": {}, "template": "📝 本周反思: {result[0]}", "star": "star", "cat": "reflection"},
    ],

    # ═══ TIME/WEATHER AWARE ═══
    "morning": [
        {"api": "wish_engine.apis.open_meteo_api", "fn": "get_weather", "params": {}, "template": "🌤️ 早安。现在{temperature_c}°C，{condition}", "star": "meteor", "cat": "weather"},
        {"api": "wish_engine.apis.sunrise_sunset_api", "fn": "get_sun_times", "params": {}, "template": "🌅 日出: {sunrise}", "star": "meteor", "cat": "time"},
        {"api": "wish_engine.apis.affirmations_api", "fn": "get_affirmation", "params": {}, "template": "☀️ 今日肯定: {result}", "star": "meteor", "cat": "morning"},
    ],
    "evening": [
        {"api": "wish_engine.apis.open_meteo_api", "fn": "get_weather", "params": {}, "template": "🌙 现在{temperature_c}°C。适合出去走走", "star": "meteor", "cat": "weather"},
        {"api": "wish_engine.apis.spiritual_apis", "fn": "mindfulness_reminder", "params": {}, "template": "🔔 {result}", "star": "meteor", "cat": "evening"},
    ],
    "weekend": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["museum", "gallery", "park", "arts_centre"]}, "template": "🎉 周末探索: {title}", "star": "meteor", "cat": "explore"},
        {"api": "wish_engine.apis.bored_api", "fn": "get_activity", "params": {}, "template": "💡 周末活动: {activity}", "star": "meteor", "cat": "explore"},
    ],

    # ═══ LOCATION AWARE ═══
    "new_place": [
        {"api": "wish_engine.apis.wikipedia_api", "fn": "get_summary", "params": {}, "template": "📍 关于这个地方: {extract:.100}", "star": "meteor", "cat": "explore"},
        {"api": "wish_engine.apis.holidays_api", "fn": "get_next_holiday", "params": {}, "template": "🎊 下一个假期: {name} ({date})", "star": "star", "cat": "culture"},
        {"api": "wish_engine.apis.countries_api", "fn": "get_country", "params": {}, "template": "🌍 {name} — 语言: {languages}, 货币: {currencies}", "star": "star", "cat": "culture"},
    ],

    # ═══ HEALTH AWARE ═══
    "insomnia": [
        {"api": "wish_engine.apis.health_apis", "fn": "sleep_times", "params": {"wake_time_hour": 7}, "template": "😴 最佳入睡时间: {result[0]}", "star": "meteor", "cat": "sleep"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise", "params": {"technique": "478"}, "template": "4-7-8 助眠呼吸: 吸4-屏7-呼8", "star": "meteor", "cat": "sleep"},
    ],
}


def get_api_actions(attention: str) -> list[dict]:
    """Get all API actions for a given Soul attention signal."""
    return SOUL_API_MAP.get(attention, [])


def get_all_attentions() -> list[str]:
    """Get all supported Soul attention signals."""
    return list(SOUL_API_MAP.keys())


def count_api_connections() -> dict:
    """Count how many API connections exist per category."""
    total = 0
    by_cat = {}
    for attention, actions in SOUL_API_MAP.items():
        for a in actions:
            total += 1
            cat = a.get("cat", "other")
            by_cat[cat] = by_cat.get(cat, 0) + 1
    return {"total_connections": total, "attentions": len(SOUL_API_MAP), "by_category": by_cat}
