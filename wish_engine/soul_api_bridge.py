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
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["bank", "atm"]}, "template": "最近的: {title} — 可以取款或咨询", "star": "meteor", "cat": "finance"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice", "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
    ],
    "need_medicine": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["pharmacy", "hospital"]}, "template": "最近的: {title} — {description}", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "478"}, "template": "🌬️ 先深呼吸放松: 吸4-屏7-呼8，有助缓解不适", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice",
         "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
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
        {"api": "wish_engine.apis.joke_api", "fn": "get_joke",
         "params": {}, "template": "😄 笑一个: {joke}", "star": "meteor", "cat": "healing"},
    ],
    "angry": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["gym", "fitness_centre"]}, "template": "{title} — 把怒气转化为力量", "star": "meteor", "cat": "exercise"},
        {"api": "wish_engine.apis.exercise_api", "fn": "search_exercises", "params": {"term": "boxing"}, "template": "试试: {name} — 释放压力", "star": "meteor", "cat": "exercise"},
    ],
    "lonely": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe", "community_centre"]}, "template": "{title} — 有人的地方，不需要说话，但不是一个人", "star": "meteor", "cat": "social"},
        {"api": "wish_engine.apis.social_apis", "fn": "conversation_starter", "params": {"context": "general"}, "template": "💬 如果想开口: {result}", "star": "meteor", "cat": "social"},
        {"api": "wish_engine.apis.cat_api", "fn": "random_cat_image", "params": {}, "template": "🐱 猫咪陪你", "star": "meteor", "cat": "healing"},
        {"api": "wish_engine.apis.joke_api", "fn": "get_joke",
         "params": {}, "template": "😄 {joke}", "star": "meteor", "cat": "healing"},
        {"api": "wish_engine.apis.nature_apis", "fn": "random_shiba_image",
         "params": {}, "template": "🐕 柴犬来陪你了", "star": "meteor", "cat": "healing"},
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
        {"api": "wish_engine.apis.nature_apis", "fn": "random_bird_image",
         "params": {}, "template": "🐦 一只鸟，静静的", "star": "meteor", "cat": "healing"},
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
        {"api": "wish_engine.apis.open_library_api", "fn": "search_books",
         "params": {"query": "classic literature", "max_results": 3}, "template": "📚 {title} by {authors[0]} ({year}) — {description:.60}", "star": "star", "cat": "books"},
    ],
    "want_learn": [
        {"api": "wish_engine.apis.knowledge_apis", "fn": "random_wikipedia", "params": {}, "template": "🌐 今日知识: {title} — {extract:.100}", "star": "star", "cat": "learning"},
        {"api": "wish_engine.apis.knowledge_apis", "fn": "today_in_history", "params": {}, "template": "📅 历史上的今天 ({year}): {text:.80}", "star": "star", "cat": "learning"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["library", "community_centre"]}, "template": "{title} — 可能有课程或资源", "star": "star", "cat": "learning"},
        {"api": "wish_engine.apis.github_trending_api", "fn": "trending_repos",
         "params": {"language": "", "since": "daily"}, "template": "⭐ GitHub趋势: {author}/{name} — {description:.60} ({stars}★)", "star": "star", "cat": "tech"},
        {"api": "wish_engine.apis.dictionary_api", "fn": "define",
         "params": {}, "template": "📖 {word} [{phonetic}]: {definitions[0][definition]:.80}", "star": "star", "cat": "learning"},
        {"api": "wish_engine.apis.numbers_api", "fn": "random_fact",
         "params": {}, "template": "🔢 有趣数字: {result}", "star": "star", "cat": "learning"},
        {"api": "wish_engine.apis.podcast_api", "fn": "search_podcasts",
         "params": {"query": "knowledge learning", "max_results": 2}, "template": "🎙️ 播客: {title} — {description:.60}", "star": "star", "cat": "learning"},
    ],
    "want_art": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["arts_centre", "gallery", "museum"]}, "template": "🎨 {title} — 去看看", "star": "star", "cat": "art"},
        {"api": "wish_engine.apis.wikipedia_api", "fn": "get_summary", "params": {}, "template": "🖼️ 关于{topic}: {extract:.100}", "star": "star", "cat": "art"},
    ],
    "want_music": [
        {"api": "wish_engine.apis.radio_api", "fn": "search_stations", "params": {}, "template": "📻 {name} ({country}) — 正在播放", "star": "star", "cat": "music"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["theatre", "cinema"]}, "template": "🎵 {title} — 可能有演出", "star": "star", "cat": "music"},
        {"api": "wish_engine.apis.events_free", "fn": "discover_events_free", "params": {}, "template": "🎶 {name} — 可能有演出", "star": "meteor", "cat": "music"},
        {"api": "wish_engine.apis.music_api", "fn": "search_playlists",
         "params": {"query": "chill", "limit": 3}, "template": "🎵 Spotify: {name} — {tracks} 首", "star": "star", "cat": "music"},
    ],
    "want_work": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe", "library"]}, "template": "💻 {title} — 安静、有WiFi", "star": "star", "cat": "work"},
        {"api": "wish_engine.apis.productivity_apis", "fn": "pomodoro_schedule", "params": {"total_hours": 2}, "template": "🍅 番茄钟已准备: {len(result)}个时段", "star": "star", "cat": "work"},
        {"api": "wish_engine.apis.github_trending_api", "fn": "trending_repos",
         "params": {"language": "", "since": "daily"}, "template": "⭐ 今日最热项目: {author}/{name} — {stars}★", "star": "star", "cat": "tech"},
    ],
    "need_exercise": [
        {"api": "wish_engine.apis.exercise_api", "fn": "search_exercises", "params": {"term": "yoga"}, "template": "🧘 试试: {name}", "star": "star", "cat": "exercise"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["gym", "fitness_centre", "swimming_pool", "park"]}, "template": "🏃 {title} — 动起来", "star": "star", "cat": "exercise"},
        {"api": "wish_engine.apis.health_apis", "fn": "estimate_calories", "params": {"activity": "running", "weight_kg": 70, "minutes": 30}, "template": "跑步30分钟 ≈ 消耗{result}卡路里", "star": "star", "cat": "exercise"},
        {"api": "wish_engine.apis.air_quality_api", "fn": "get_air_quality",
         "params": {}, "template": "🌬️ 户外锻炼前: AQI {aqi}，{dominant_pollutant}", "star": "meteor", "cat": "health"},
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
        {"api": "wish_engine.apis.philosophy_quotes", "fn": "get_quote", "params": {}, "template": "🏛️ {tradition}: {text} — {author}", "star": "earth", "cat": "meaning"},
        {"api": "wish_engine.apis.tarot_api", "fn": "draw_cards",
         "params": {"count": 1}, "template": "🔮 {result[0][name]}: {result[0][meaning_up]}", "star": "earth", "cat": "meaning"},
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
        {"api": "wish_engine.apis.knowledge_apis", "fn": "random_wikipedia",
         "params": {}, "template": "📖 离线也能读: {title} — {extract:.80}", "star": "meteor", "cat": "learning"},
        {"api": "wish_engine.apis.productivity_apis", "fn": "pomodoro_schedule",
         "params": {"total_hours": 1}, "template": "🍅 先做离线任务: 专注{len(result)}个番茄钟", "star": "meteor", "cat": "work"},
    ],
    "need_quiet": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["library", "park", "garden"]}, "template": "🤫 {title} — 附近最安静的地方", "star": "meteor", "cat": "quiet"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "478"}, "template": "🌬️ 先用呼吸找到内心的安静: 吸4-屏7-呼8", "star": "meteor", "cat": "calm"},
        {"api": "wish_engine.apis.spiritual_apis", "fn": "mindfulness_reminder",
         "params": {}, "template": "🔔 {result}", "star": "meteor", "cat": "mindfulness"},
    ],

    # ═══ FUN / BOREDOM ═══
    "bored": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["museum", "gallery", "park", "arts_centre", "cinema"]}, "template": "✨ {title} — 现在就可以去", "star": "meteor", "cat": "explore"},
        {"api": "wish_engine.apis.bored_api", "fn": "get_activity", "params": {}, "template": "💡 或者试试: {activity} ({type})", "star": "meteor", "cat": "fun"},
        {"api": "wish_engine.apis.events_free", "fn": "discover_events_free", "params": {}, "template": "🎪 {name} — 今晚可能有活动", "star": "meteor", "cat": "events"},
        {"api": "wish_engine.apis.joke_api", "fn": "get_joke",
         "params": {}, "template": "😄 无聊？来个笑话: {joke}", "star": "meteor", "cat": "fun"},
        {"api": "wish_engine.apis.numbers_api", "fn": "random_fact",
         "params": {}, "template": "🔢 无聊之余: {result}", "star": "meteor", "cat": "fun"},
        {"api": "wish_engine.apis.events_api", "fn": "search_all",
         "params": {"radius_km": 5, "keyword": "fun", "max_results": 3}, "template": "🎪 附近活动: {name} — {date}", "star": "meteor", "cat": "events"},
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
        {"api": "wish_engine.apis.tarot_api", "fn": "draw_cards",
         "params": {"count": 1}, "template": "🔮 {result[0][name]}: {result[0][meaning_up]}", "star": "star", "cat": "reflection"},
    ],

    # ═══ TIME/WEATHER AWARE ═══
    "morning": [
        {"api": "wish_engine.apis.open_meteo_api", "fn": "get_weather", "params": {}, "template": "🌤️ 早安。现在{temperature_c}°C，{condition}", "star": "meteor", "cat": "weather"},
        {"api": "wish_engine.apis.sunrise_sunset_api", "fn": "get_sun_times", "params": {}, "template": "🌅 日出: {sunrise}", "star": "meteor", "cat": "time"},
        {"api": "wish_engine.apis.affirmations_api", "fn": "get_affirmation", "params": {}, "template": "☀️ 今日肯定: {result}", "star": "meteor", "cat": "morning"},
        {"api": "wish_engine.apis.music_api", "fn": "search_playlists",
         "params": {"query": "morning energy", "limit": 1}, "template": "☀️ 早安歌单: {name}", "star": "meteor", "cat": "music"},
        {"api": "wish_engine.apis.iss_api", "fn": "people_in_space",
         "params": {}, "template": "🚀 此刻太空中有 {count} 人: {names}", "star": "meteor", "cat": "wonder"},
    ],
    "evening": [
        {"api": "wish_engine.apis.open_meteo_api", "fn": "get_weather", "params": {}, "template": "🌙 现在{temperature_c}°C。适合出去走走", "star": "meteor", "cat": "weather"},
        {"api": "wish_engine.apis.spiritual_apis", "fn": "mindfulness_reminder", "params": {}, "template": "🔔 {result}", "star": "meteor", "cat": "evening"},
    ],
    "weekend": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["museum", "gallery", "park", "arts_centre"]}, "template": "🎉 周末探索: {title}", "star": "meteor", "cat": "explore"},
        {"api": "wish_engine.apis.bored_api", "fn": "get_activity", "params": {}, "template": "💡 周末活动: {activity}", "star": "meteor", "cat": "explore"},
        {"api": "wish_engine.apis.events_free", "fn": "discover_events_free", "params": {}, "template": "🎭 {name} — 周末活动", "star": "meteor", "cat": "events"},
        {"api": "wish_engine.apis.events_api", "fn": "search_all",
         "params": {"radius_km": 10, "keyword": "weekend", "max_results": 3}, "template": "🎟️ 周末活动: {name} — {date}", "star": "meteor", "cat": "events"},
    ],

    # ═══ LOCATION AWARE ═══
    "new_place": [
        {"api": "wish_engine.apis.teleport_api", "fn": "get_urban_area",
         "params": {"city_name": "Dubai"}, "template": "🌆 {name}: {highlights}", "star": "meteor", "cat": "explore"},
        {"api": "wish_engine.apis.wikipedia_api", "fn": "get_summary", "params": {}, "template": "📍 关于这个地方: {extract:.100}", "star": "meteor", "cat": "explore"},
        {"api": "wish_engine.apis.holidays_api", "fn": "get_next_holiday", "params": {}, "template": "🎊 下一个假期: {name} ({date})", "star": "star", "cat": "culture"},
        {"api": "wish_engine.apis.countries_api", "fn": "get_country", "params": {}, "template": "🌍 {name} — 语言: {languages}, 货币: {currencies}", "star": "star", "cat": "culture"},
    ],

    # ═══ HEALTH AWARE ═══
    "insomnia": [
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise", "params": {"technique": "478"}, "template": "4-7-8 助眠呼吸，现在就试: 吸4秒—屏7秒—呼8秒，重复3次", "star": "meteor", "cat": "sleep"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["pharmacy"]}, "template": "{title} — 可能有助眠产品", "star": "meteor", "cat": "health"},
    ],

    # ═══ TEMPERATURE / ENVIRONMENT ═══
    "cold": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe", "library"]}, "template": "{title} — 暖和，可以进去待一会", "star": "meteor", "cat": "place"},
        {"api": "wish_engine.apis.open_meteo_api", "fn": "get_weather", "params": {}, "template": "🌡️ 现在{temperature_c}°C，{condition}", "star": "meteor", "cat": "weather"},
    ],
    "hot": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe", "library", "swimming_pool"]}, "template": "{title} — 有空调 / 游泳池", "star": "meteor", "cat": "place"},
        {"api": "wish_engine.apis.open_meteo_api", "fn": "get_weather", "params": {}, "template": "🌡️ 现在{temperature_c}°C，{condition}", "star": "meteor", "cat": "weather"},
    ],
    "tired": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe", "park"]}, "template": "{title} — 坐下来歇一歇", "star": "meteor", "cat": "place"},
        {"api": "wish_engine.apis.health_apis", "fn": "sleep_times", "params": {"wake_time_hour": 7}, "template": "😴 今晚最佳入睡: {result[0]}", "star": "meteor", "cat": "sleep"},
    ],

    # ═══ MISSING LIFE NEEDS ═══
    "celebrating": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["restaurant", "cafe", "arts_centre"]}, "template": "🎉 庆祝一下: {title}", "star": "meteor", "cat": "celebration"},
        {"api": "wish_engine.apis.meal_api", "fn": "random_meal", "params": {}, "template": "🍽️ 特别的一餐: {name} ({area})", "star": "meteor", "cat": "food"},
        {"api": "wish_engine.apis.creative_apis", "fn": "daily_motivation", "params": {}, "template": "🌟 {result}", "star": "meteor", "cat": "celebration"},
    ],
    "homesick": [
        {"api": "wish_engine.apis.meal_api", "fn": "random_meal", "params": {}, "template": "🍜 一道让你想家的菜: {name}", "star": "meteor", "cat": "food"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["community_centre", "place_of_worship"]}, "template": "{title} — 可能遇到同乡", "star": "meteor", "cat": "social"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice", "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
    ],
    "headache": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["pharmacy"]}, "template": "💊 最近的药店: {title}", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise", "params": {"technique": "478"}, "template": "🌬️ 深呼吸缓解头疼: 吸4-屏7-呼8", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.air_quality_api", "fn": "get_air_quality",
         "params": {}, "template": "🌫️ 空气质量 AQI {aqi}，可能是诱因之一", "star": "meteor", "cat": "health"},
    ],
    "overwhelmed": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["park", "garden"]}, "template": "{title} — 离开屏幕，去外面走走", "star": "meteor", "cat": "calm"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise", "params": {"technique": "box"}, "template": "📦 盒式呼吸: 一次一步", "star": "meteor", "cat": "calm"},
        {"api": "wish_engine.apis.productivity_apis", "fn": "pomodoro_schedule", "params": {"total_hours": 1}, "template": "🍅 把任务切小，一次只做一件事", "star": "star", "cat": "work"},
    ],
    "want_outdoor": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["park", "garden"]}, "template": "🌿 {title} — 去户外走走", "star": "meteor", "cat": "nature"},
        {"api": "wish_engine.apis.open_meteo_api", "fn": "get_weather", "params": {}, "template": "🌤️ 现在{temperature_c}°C，{condition}", "star": "meteor", "cat": "weather"},
        {"api": "wish_engine.apis.exercise_api", "fn": "search_exercises", "params": {"term": "walking"}, "template": "🏃 {name} — 户外运动", "star": "star", "cat": "exercise"},
        {"api": "wish_engine.apis.air_quality_api", "fn": "get_air_quality",
         "params": {}, "template": "🌿 当前空气质量 AQI: {aqi} — {dominant_pollutant}", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.nature_apis", "fn": "random_bird_image",
         "params": {}, "template": "🐦 在户外也许能看到这只鸟", "star": "meteor", "cat": "nature"},
        {"api": "wish_engine.apis.iss_api", "fn": "iss_location",
         "params": {}, "template": "🛰️ 国际空间站此刻在 {lat:.1f}°, {lng:.1f}°", "star": "meteor", "cat": "wonder"},
    ],
    "want_create": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["arts_centre", "library"]}, "template": "🎨 {title} — 有创作空间", "star": "star", "cat": "art"},
        {"api": "wish_engine.apis.creative_apis", "fn": "random_palette", "params": {}, "template": "🎨 今日配色: {colors[0]} {colors[1]} {colors[2]}", "star": "star", "cat": "creative"},
        {"api": "wish_engine.apis.creative_apis", "fn": "daily_motivation", "params": {}, "template": "✨ {result}", "star": "star", "cat": "creative"},
    ],

    # ═══ RELATIONSHIP / EMOTIONAL PAIN (from real data) ═══
    "heartbreak": [
        {"api": "wish_engine.apis.poetry_api", "fn": "random_poem", "params": {}, "template": "📜 {title} by {author}\n{lines[0]}\n{lines[1]}", "star": "meteor", "cat": "healing"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice", "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["park", "garden"]}, "template": "{title} — 给自己一点空间和时间", "star": "meteor", "cat": "place"},
    ],
    "missing_someone": [
        {"api": "wish_engine.apis.poetry_api", "fn": "random_poem", "params": {}, "template": "📜 {title} by {author}\n{lines[0]}", "star": "meteor", "cat": "healing"},
        {"api": "wish_engine.apis.social_apis", "fn": "conversation_starter", "params": {"context": "reconnect"}, "template": "💬 想联系他们? 试试: {result}", "star": "meteor", "cat": "social"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["cafe", "park"]}, "template": "{title} — 一个可以安静想念的地方", "star": "meteor", "cat": "place"},
    ],
    "relationship_pain": [
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise", "params": {"technique": "box"}, "template": "📦 先深呼吸: 吸4-屏4-呼4-屏4", "star": "meteor", "cat": "calm"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice", "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich", "params": {"place_types": ["community_centre", "library"]}, "template": "{title} — 可以找到支持的地方", "star": "meteor", "cat": "safety"},
    ],

    # ═══ CRITICAL: LIFE SAFETY — crisis API always first ═══

    "suicidal_ideation": [
        {"api": "wish_engine.apis.crisis_apis", "fn": "get_crisis_resources",
         "params": {"crisis_type": "suicide"}, "template": "{primary_name}: {primary_number} — {description}", "star": "meteor", "cat": "crisis"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "478"}, "template": "先深呼吸: 吸4秒 — 屏7秒 — 呼8秒", "star": "meteor", "cat": "crisis"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility", "clinic"]}, "template": "{title} — 可以去找人说话", "star": "meteor", "cat": "crisis"},
    ],

    "domestic_violence": [
        {"api": "wish_engine.apis.crisis_apis", "fn": "get_crisis_resources",
         "params": {"crisis_type": "domestic_violence"}, "template": "{primary_name}: {primary_number} — 保密，24小时", "star": "meteor", "cat": "crisis"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "{title} — 安全的庇护所", "star": "meteor", "cat": "safety"},
    ],

    "addiction_crisis": [
        {"api": "wish_engine.apis.crisis_apis", "fn": "get_crisis_resources",
         "params": {"crisis_type": "addiction"}, "template": "{primary_name}: {primary_number}", "star": "meteor", "cat": "crisis"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility", "clinic"]}, "template": "{title} — 戒断支持中心", "star": "meteor", "cat": "health"},
    ],

    "homelessness": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "{title} — 庇护所 / 收容所", "star": "meteor", "cat": "shelter"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice",
         "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
    ],

    # ═══ MENTAL HEALTH CLINICAL ═══

    "need_therapy": [
        {"api": "wish_engine.apis.crisis_apis", "fn": "get_crisis_resources",
         "params": {"crisis_type": "mental_health"}, "template": "{primary_name}: {primary_number}", "star": "meteor", "cat": "mental_health"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["clinic", "social_facility"]}, "template": "{title} — 心理健康诊所", "star": "meteor", "cat": "mental_health"},
    ],

    "trauma_ptsd": [
        {"api": "wish_engine.apis.crisis_apis", "fn": "get_crisis_resources",
         "params": {"crisis_type": "mental_health"}, "template": "{primary_name}: {primary_number}", "star": "meteor", "cat": "mental_health"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "box"}, "template": "盒式呼吸: 让身体慢下来 — 吸4-屏4-呼4-屏4", "star": "meteor", "cat": "calm"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["clinic", "social_facility"]}, "template": "{title} — 创伤治疗师", "star": "meteor", "cat": "mental_health"},
    ],

    "eating_disorder": [
        {"api": "wish_engine.apis.crisis_apis", "fn": "get_crisis_resources",
         "params": {"crisis_type": "mental_health"}, "template": "{primary_name}: {primary_number}", "star": "meteor", "cat": "mental_health"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["clinic", "social_facility"]}, "template": "{title} — 饮食失调支持诊所", "star": "meteor", "cat": "health"},
    ],

    "postpartum": [
        {"api": "wish_engine.apis.crisis_apis", "fn": "get_crisis_resources",
         "params": {"crisis_type": "mental_health"}, "template": "{primary_name}: {primary_number}", "star": "meteor", "cat": "mental_health"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["clinic", "community_centre"]}, "template": "{title} — 产后支持服务", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.social_apis", "fn": "random_compliment",
         "params": {}, "template": "💛 {result}", "star": "meteor", "cat": "confidence"},
    ],

    # ═══ FINANCIAL ═══

    "debt_crisis": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "{title} — 债务援助和住房支持", "star": "meteor", "cat": "finance"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["bank"]}, "template": "{title} — 银行顾问", "star": "meteor", "cat": "finance"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice",
         "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
    ],

    "want_save_money": [
        {"api": "wish_engine.apis.budget_calculator", "fn": "fifty_thirty_twenty",
         "params": {"income": 3000}, "template": "💰 50/30/20: 必要{needs:.0f} / 想要{wants:.0f} / 储蓄{savings:.0f}", "star": "star", "cat": "finance"},
        {"api": "wish_engine.apis.budget_calculator", "fn": "emergency_fund_target",
         "params": {"monthly_expenses": 2000}, "template": "🏦 紧急备用金目标: {result:.0f}", "star": "star", "cat": "finance"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["bank"]}, "template": "{title} — 咨询储蓄账户", "star": "star", "cat": "finance"},
    ],

    "budget_help": [
        {"api": "wish_engine.apis.budget_calculator", "fn": "fifty_thirty_twenty",
         "params": {"income": 3000}, "template": "📊 预算建议: 必要{needs:.0f} / 想要{wants:.0f} / 储蓄{savings:.0f}", "star": "star", "cat": "finance"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice",
         "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
    ],

    "exchange_money": [
        {"api": "wish_engine.apis.currency_api", "fn": "get_rates",
         "params": {"base": "USD"}, "template": "💱 1 USD = {EUR:.4f} EUR / {GBP:.4f} GBP / {CNY:.4f} CNY", "star": "meteor", "cat": "finance"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["bank", "atm"]}, "template": "{title} — 换汇服务", "star": "meteor", "cat": "finance"},
    ],

    "job_loss": [
        {"api": "wish_engine.apis.jobs_api", "fn": "search_jobs",
         "params": {}, "template": "💼 现有职位: {title} @ {company}", "star": "meteor", "cat": "career"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["employment_agency", "social_facility"]}, "template": "{title} — 就业援助服务", "star": "meteor", "cat": "career"},
        {"api": "wish_engine.apis.affirmations_api", "fn": "get_affirmation",
         "params": {}, "template": "💪 {result}", "star": "meteor", "cat": "confidence"},
        {"api": "wish_engine.apis.adzuna_api", "fn": "search_jobs",
         "params": {"query": "remote"}, "template": "💼 {title} @ {company} — {location}", "star": "meteor", "cat": "jobs"},
    ],

    # ═══ CAREER ═══

    "job_seeking": [
        {"api": "wish_engine.apis.jobs_api", "fn": "search_jobs",
         "params": {}, "template": "💼 实时职位: {title} @ {company} — {location}", "star": "star", "cat": "career"},
        {"api": "wish_engine.apis.jobs_api", "fn": "remoteok_jobs",
         "params": {"max_results": 3}, "template": "🌐 远程机会: {title} @ {company}", "star": "star", "cat": "career"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["employment_agency", "library"]}, "template": "{title} — 就业中心 / 简历帮助", "star": "star", "cat": "career"},
        {"api": "wish_engine.apis.adzuna_api", "fn": "search_jobs",
         "params": {"query": "software"}, "template": "🔍 {title} @ {company} — {location}", "star": "star", "cat": "jobs"},
    ],

    "career_change": [
        {"api": "wish_engine.apis.jobs_api", "fn": "search_jobs",
         "params": {}, "template": "💼 新方向: {title} @ {company} — {location}", "star": "star", "cat": "career"},
        {"api": "wish_engine.apis.teleport_api", "fn": "get_urban_area",
         "params": {"city_name": "London"}, "template": "🌆 城市对比: {name} — {highlights}", "star": "star", "cat": "career"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["employment_agency", "community_centre"]}, "template": "{title} — 职业咨询", "star": "star", "cat": "career"},
        {"api": "wish_engine.apis.affirmations_api", "fn": "get_affirmation",
         "params": {}, "template": "💡 {result}", "star": "star", "cat": "confidence"},
        {"api": "wish_engine.apis.adzuna_api", "fn": "search_jobs",
         "params": {"query": "career change"}, "template": "🔄 {title} @ {company} — {location}", "star": "star", "cat": "jobs"},
    ],

    # ═══ HOUSING ═══

    "need_housing": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "{title} — 住房援助服务", "star": "meteor", "cat": "housing"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["community_centre"]}, "template": "{title} — 社区中心可能有租房资源", "star": "meteor", "cat": "housing"},
    ],

    # ═══ FAMILY ═══

    "parenting_stress": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility", "community_centre"]}, "template": "{title} — 家长支持服务", "star": "meteor", "cat": "family"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "box"}, "template": "📦 60秒盒式呼吸 — 先让自己平静", "star": "meteor", "cat": "calm"},
        {"api": "wish_engine.apis.social_apis", "fn": "random_compliment",
         "params": {}, "template": "💛 {result}", "star": "meteor", "cat": "confidence"},
    ],

    "need_childcare": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["childcare", "social_facility"]}, "template": "{title} — 托儿所 / 儿童照看服务", "star": "meteor", "cat": "family"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["community_centre"]}, "template": "{title} — 社区儿童活动", "star": "meteor", "cat": "family"},
    ],

    "family_conflict": [
        {"api": "wish_engine.apis.social_apis", "fn": "conflict_prompt",
         "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "reflection"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility", "community_centre"]}, "template": "{title} — 家庭调解服务", "star": "meteor", "cat": "family"},
        {"api": "wish_engine.apis.spiritual_apis", "fn": "daily_wisdom",
         "params": {}, "template": "🌿 {text} — {source}", "star": "meteor", "cat": "wisdom"},
    ],

    "friend_conflict": [
        {"api": "wish_engine.apis.social_apis", "fn": "conflict_prompt",
         "params": {}, "template": "💭 朋友之间: {result}", "star": "meteor", "cat": "reflection"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["cafe", "park"]}, "template": "{title} — 找个安静的地方，先冷静下来", "star": "meteor", "cat": "place"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice",
         "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
    ],

    "elder_care": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "{title} — 老年护理服务", "star": "meteor", "cat": "family"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["community_centre"]}, "template": "{title} — 社区老年服务", "star": "meteor", "cat": "family"},
    ],

    "divorce": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "{title} — 法律援助 / 家庭法律服务", "star": "meteor", "cat": "legal"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "box"}, "template": "深呼吸: 离婚是漫长的路，一步一步走", "star": "meteor", "cat": "calm"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice",
         "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
    ],

    # ═══ LEGAL ═══

    "legal_trouble": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "{title} — 法律援助服务", "star": "meteor", "cat": "legal"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["community_centre"]}, "template": "{title} — 社区法律诊所", "star": "meteor", "cat": "legal"},
    ],

    "immigration_stress": [
        {"api": "wish_engine.apis.translation_api", "fn": "get_translation_resources",
         "params": {"target_lang": "en"}, "template": "🌐 {app}: {description}", "star": "meteor", "cat": "language"},
        {"api": "wish_engine.apis.jobs_api", "fn": "arbeitnow_jobs",
         "params": {"visa_sponsorship": True, "max_results": 3}, "template": "💼 签证担保职位: {title} @ {company} ({location})", "star": "star", "cat": "career"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility", "community_centre"]}, "template": "{title} — 移民援助服务", "star": "meteor", "cat": "legal"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "478"}, "template": "深呼吸: 慢慢来，一件事一件事处理", "star": "meteor", "cat": "calm"},
        {"api": "wish_engine.apis.adzuna_api", "fn": "search_visa_jobs",
         "params": {}, "template": "🌍 {title} @ {company} — 签证担保 ({location})", "star": "star", "cat": "jobs"},
    ],

    # ═══ HEALTH ═══

    "chronic_pain": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["clinic", "social_facility"]}, "template": "{title} — 疼痛管理诊所", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "box"}, "template": "盒式呼吸: 有助于疼痛感知 — 吸4-屏4-呼4-屏4", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.exercise_api", "fn": "search_exercises",
         "params": {"term": "stretching"}, "template": "🧘 轻柔拉伸: {name}", "star": "star", "cat": "health"},
    ],

    "need_dental": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["dentist"]}, "template": "🦷 最近的牙科诊所: {title} — {description}", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "{title} — 可能提供免费牙科援助", "star": "meteor", "cat": "health"},
    ],

    "disability_access": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility", "community_centre"]}, "template": "{title} — 残疾人支持服务", "star": "meteor", "cat": "access"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice",
         "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
    ],

    "pregnancy": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["clinic", "hospital"]}, "template": "{title} — 产前护理诊所", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "{title} — 孕妇支持服务", "star": "meteor", "cat": "health"},
    ],

    # ═══ NUTRITION / WEIGHT ═══

    "want_lose_weight": [
        {"api": "wish_engine.apis.food_nutrition_api", "fn": "get_nutrition_summary",
         "params": {"query": "salad"}, "template": "🥗 {name}: {calories:.0f}卡/100g，蛋白质{protein:.1f}g", "star": "star", "cat": "health"},
        {"api": "wish_engine.apis.health_apis", "fn": "calorie_budget",
         "params": {"weight_kg": 75, "height_cm": 170, "age": 30, "sex": "male", "activity": "sedentary"},
         "template": "📊 你的每日热量预算约 {tdee:.0f} 卡，减脂目标 {deficit_500:.0f} 卡", "star": "star", "cat": "health"},
        {"api": "wish_engine.apis.exercise_api", "fn": "search_exercises",
         "params": {"term": "cardio"}, "template": "🏃 有氧运动: {name}", "star": "star", "cat": "exercise"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["gym", "fitness_centre", "swimming_pool"]}, "template": "{title} — 开始行动", "star": "star", "cat": "exercise"},
    ],

    "ate_too_much": [
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "478"}, "template": "🌬️ 饭后深呼吸: 吸4-屏7-呼8，帮助消化", "star": "meteor", "cat": "health"},
        {"api": "wish_engine.apis.exercise_api", "fn": "search_exercises",
         "params": {"term": "walking"}, "template": "🚶 饭后散步: {name} — 促进消化", "star": "meteor", "cat": "exercise"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["park", "garden"]}, "template": "{title} — 出去散个步", "star": "meteor", "cat": "place"},
    ],

    "want_eat_healthy": [
        {"api": "wish_engine.apis.food_nutrition_api", "fn": "search_food",
         "params": {"query": "vegetables", "max_results": 3}, "template": "🥦 {name}: 每100g {calories:.0f}卡路里", "star": "star", "cat": "health"},
        {"api": "wish_engine.apis.meal_api", "fn": "random_meal",
         "params": {}, "template": "🍽️ 今天试试: {name} ({area})", "star": "star", "cat": "food"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["supermarket"]}, "template": "{title} — 买新鲜食材", "star": "star", "cat": "food"},
    ],

    # ═══ PRACTICAL ═══

    "need_vet": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["veterinary"]}, "template": "🐾 最近的兽医: {title} — {description}", "star": "meteor", "cat": "pet"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "box"}, "template": "🐾 先深呼吸保持冷静: 你的宠物感受到你的状态", "star": "meteor", "cat": "calm"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice",
         "params": {}, "template": "💭 {result}", "star": "meteor", "cat": "wisdom"},
    ],

    "want_pet": [
        {"api": "wish_engine.apis.dog_api", "fn": "random_dog_image",
         "params": {}, "template": "🐕 先看看这只狗狗", "star": "meteor", "cat": "healing"},
        {"api": "wish_engine.apis.cat_api", "fn": "random_cat_image",
         "params": {}, "template": "🐱 或者这只猫咪？", "star": "meteor", "cat": "healing"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["veterinary", "community_centre"]}, "template": "{title} — 可以了解宠物领养", "star": "star", "cat": "pet"},
    ],

    "home_emergency": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility", "community_centre"]}, "template": "{title} — 紧急援助", "star": "meteor", "cat": "safety"},
        {"api": "wish_engine.apis.advice_api", "fn": "get_advice",
         "params": {}, "template": "⚠️ 如是煤气泄漏: 立刻离开，拨打紧急服务 (119/999/911)", "star": "meteor", "cat": "safety"},
    ],

    "need_translation": [
        {"api": "wish_engine.apis.translation_api", "fn": "get_translation_resources",
         "params": {"target_lang": "en"}, "template": "🌐 {app}: {description}", "star": "meteor", "cat": "language"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["community_centre", "social_facility"]}, "template": "{title} — 语言援助服务", "star": "meteor", "cat": "language"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["library"]}, "template": "{title} — 图书馆通常提供翻译服务", "star": "meteor", "cat": "language"},
    ],

    "food_insecurity": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "🍱 {title} — 食物银行 / 免费餐", "star": "meteor", "cat": "food"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["community_centre"]}, "template": "{title} — 社区餐食项目", "star": "meteor", "cat": "food"},
    ],

    "need_clothes": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility"]}, "template": "👗 {title} — 衣物援助", "star": "meteor", "cat": "clothing"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["community_centre"]}, "template": "{title} — 社区衣物交换", "star": "meteor", "cat": "clothing"},
    ],

    "tech_help": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["library"]}, "template": "{title} — 图书馆提供免费电脑和技术帮助", "star": "star", "cat": "utility"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["community_centre"]}, "template": "{title} — 社区科技帮助班", "star": "star", "cat": "utility"},
    ],

    # ═══ TRANSIT ═══

    "need_transit": [
        {"api": "wish_engine.apis.free_transit_api", "fn": "find_nearest_stops",
         "params": {}, "template": "🚌 附近站点: {name} ({type}) — 距{distance_m:.0f}米", "star": "meteor", "cat": "transit"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["bus_stop", "subway_entrance", "train_station"]}, "template": "🚉 {title} — 最近的公共交通", "star": "meteor", "cat": "transit"},
    ],

    "missed_bus": [
        {"api": "wish_engine.apis.free_transit_api", "fn": "find_nearest_stops",
         "params": {}, "template": "🚌 下一个最近站点: {name} — 距{distance_m:.0f}米", "star": "meteor", "cat": "transit"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["cafe", "library"]}, "template": "{title} — 等下班车的好地方", "star": "meteor", "cat": "place"},
    ],

    "want_navigate": [
        {"api": "wish_engine.apis.free_transit_api", "fn": "route_summary",
         "params": {"mode": "foot-walking"}, "template": "🗺️ 步行路线: 约{duration_min:.0f}分钟 / {distance_km:.1f}公里", "star": "meteor", "cat": "transit"},
        {"api": "wish_engine.apis.free_transit_api", "fn": "find_nearest_stops",
         "params": {}, "template": "🚌 最近站点: {name} ({type})", "star": "meteor", "cat": "transit"},
    ],

    # ═══ MOTIVATION ═══

    "procrastinating": [
        {"api": "wish_engine.apis.productivity_apis", "fn": "pomodoro_schedule",
         "params": {"total_hours": 1}, "template": "🍅 不用全部做完。先做25分钟: {result[0]}", "star": "meteor", "cat": "work"},
        {"api": "wish_engine.apis.joke_api", "fn": "get_joke",
         "params": {}, "template": "😄 先笑一个再说: {joke}", "star": "meteor", "cat": "fun"},
        {"api": "wish_engine.apis.affirmations_api", "fn": "get_affirmation",
         "params": {}, "template": "💪 {result}", "star": "meteor", "cat": "confidence"},
        {"api": "wish_engine.apis.bored_api", "fn": "get_activity",
         "params": {}, "template": "💡 或者先做件小事热身: {activity}", "star": "meteor", "cat": "fun"},
    ],

    # ═══ ROMANCE ═══

    "want_romance": [
        {"api": "wish_engine.apis.social_apis", "fn": "ice_breaker",
         "params": {}, "template": "💬 破冰开场: {result}", "star": "meteor", "cat": "social"},
        {"api": "wish_engine.apis.philosophy_quotes", "fn": "get_quote",
         "params": {"tradition": "Sufi"}, "template": "💝 {author}: {text}", "star": "star", "cat": "meaning"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["restaurant", "cafe", "arts_centre"]}, "template": "🌹 {title} — 约会好去处", "star": "star", "cat": "social"},
        {"api": "wish_engine.apis.meal_api", "fn": "random_meal",
         "params": {}, "template": "🍽️ 亲手做一道: {name} ({area}) — 比任何餐厅都动人", "star": "star", "cat": "food"},
    ],

    # ═══ SLEEP ═══

    "poor_sleep": [
        {"api": "wish_engine.apis.health_apis", "fn": "sleep_times",
         "params": {"wake_time_hour": 7}, "template": "😴 睡眠周期: 最佳入睡时间 {result[0]} 或 {result[1]}", "star": "meteor", "cat": "sleep"},
        {"api": "wish_engine.apis.wellness_apis", "fn": "breathing_exercise",
         "params": {"technique": "478"}, "template": "🌙 助眠呼吸: 吸4-屏7-呼8，重复4次", "star": "meteor", "cat": "sleep"},
        {"api": "wish_engine.apis.spiritual_apis", "fn": "mindfulness_reminder",
         "params": {}, "template": "🔔 睡前正念: {result}", "star": "meteor", "cat": "sleep"},
        {"api": "wish_engine.apis.open_meteo_api", "fn": "get_weather",
         "params": {}, "template": "🌡️ 室温参考: 现在{temperature_c}°C — 理想睡眠温度16-19°C", "star": "meteor", "cat": "health"},
    ],

    # ═══ ENTERTAINMENT ═══

    "entertainment": [
        {"api": "wish_engine.apis.joke_api", "fn": "get_joke",
         "params": {}, "template": "😄 {joke}", "star": "meteor", "cat": "fun"},
        {"api": "wish_engine.apis.bored_api", "fn": "get_activity",
         "params": {}, "template": "💡 试试: {activity} ({type})", "star": "meteor", "cat": "fun"},
        {"api": "wish_engine.apis.knowledge_apis", "fn": "today_in_history",
         "params": {}, "template": "📅 历史上的今天 ({year}): {text:.80}", "star": "meteor", "cat": "learning"},
        {"api": "wish_engine.apis.cocktail_api", "fn": "random_cocktail",
         "params": {}, "template": "🍹 今晚来一杯: {name} — {instructions:.60}", "star": "meteor", "cat": "drink"},
        {"api": "wish_engine.apis.podcast_api", "fn": "search_podcasts",
         "params": {"query": "entertainment comedy", "max_results": 2}, "template": "🎙️ 播客: {title} — {description:.60}", "star": "meteor", "cat": "audio"},
    ],

    # ═══ TRAVEL ═══

    "want_travel": [
        {"api": "wish_engine.apis.teleport_api", "fn": "get_urban_area",
         "params": {"city_name": "Barcelona"}, "template": "🌆 {name}: {highlights}", "star": "star", "cat": "travel"},
        {"api": "wish_engine.apis.countries_api", "fn": "get_country",
         "params": {}, "template": "🌍 {name} — 语言: {languages} | 货币: {currencies}", "star": "star", "cat": "travel"},
        {"api": "wish_engine.apis.holidays_api", "fn": "get_next_holiday",
         "params": {}, "template": "🎊 下一个假期: {name} ({date}) — 出行好时机", "star": "star", "cat": "travel"},
        {"api": "wish_engine.apis.open_meteo_api", "fn": "get_weather",
         "params": {}, "template": "🌤️ 当地天气: {temperature_c}°C，{condition}", "star": "meteor", "cat": "weather"},
    ],

    # ═══ INVESTING ═══

    "want_invest": [
        {"api": "wish_engine.apis.currency_api", "fn": "get_rates",
         "params": {"base": "USD"}, "template": "📈 实时汇率: 1 USD = {EUR:.4f} EUR / {GBP:.4f} GBP / {CNY:.4f} CNY", "star": "star", "cat": "finance"},
        {"api": "wish_engine.apis.knowledge_apis", "fn": "random_wikipedia",
         "params": {}, "template": "📖 了解一个概念: {title} — {extract:.100}", "star": "star", "cat": "learning"},
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["bank"]}, "template": "{title} — 咨询理财顾问", "star": "star", "cat": "finance"},
        {"api": "wish_engine.apis.philosophy_quotes", "fn": "get_quote",
         "params": {"tradition": "Philosophy"}, "template": "💭 {author}: {text}", "star": "star", "cat": "wisdom"},
    ],

    # ═══ VOLUNTEERING ═══

    "want_volunteer": [
        {"api": "wish_engine.apis.osm_api", "fn": "search_and_enrich",
         "params": {"place_types": ["social_facility", "community_centre"]}, "template": "🤝 {title} — 可能需要志愿者", "star": "star", "cat": "community"},
        {"api": "wish_engine.apis.spiritual_apis", "fn": "daily_wisdom",
         "params": {}, "template": "🌿 {tradition}: {text} — {source}", "star": "star", "cat": "wisdom"},
        {"api": "wish_engine.apis.philosophy_quotes", "fn": "get_quote",
         "params": {}, "template": "💭 {author}: {text}", "star": "star", "cat": "meaning"},
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
