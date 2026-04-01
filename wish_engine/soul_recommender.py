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

    # New additions
    "friend_conflict":   {"osm": ["cafe", "park"], "why": "朋友闹矛盾 — {place}冷静一下"},
    "want_pet":          {"osm": ["veterinary", "community_centre"], "why": "想养宠物 — {place}可以了解领养"},
    "want_save_money":   {"osm": ["bank"], "why": "想省钱 — {place}可以咨询储蓄账户"},
    "budget_help":       {"osm": ["bank", "library"], "why": "需要预算帮助 — {place}有理财资源"},
    "exchange_money":    {"osm": ["bank", "atm"], "why": "需要换汇 — {place}提供外汇服务"},
    "want_lose_weight":  {"osm": ["gym", "fitness_centre", "swimming_pool"], "why": "想减肥 — {place}是好的开始"},
    "ate_too_much":      {"osm": ["park", "garden"], "why": "吃太多了 — {place}去散个步"},
    "want_eat_healthy":  {"osm": ["supermarket"], "why": "想吃健康 — {place}买新鲜食材"},
    "need_transit":      {"osm": ["bus_stop", "subway_entrance", "train_station"], "why": "需要交通 — {place}离你最近"},
    "missed_bus":        {"osm": ["cafe", "library"], "why": "错过公交了 — {place}等下一班"},
    "want_navigate":     {"osm": ["bus_stop", "train_station"], "why": "想导航 — {place}是最近的交通站"},
}


import re as _re

# Words that negate the meaning of whatever follows (within ~3 words)
_NEGATION_WORDS = frozenset({
    "not", "no", "never", "don't", "dont", "doesn't", "doesnt",
    "didn't", "didnt", "won't", "wont", "isn't", "isnt",
    "aren't", "arent", "wasn't", "wasnt", "haven't", "havent",
    "neither", "nor", "without",
})


def _is_negated_at(text: str, match_start: int) -> bool:
    """Return True if the word at match_start is preceded by a negation (within 3 words).

    Phrases (multi-word keywords) are NOT passed here — they already encode their
    own meaning precisely ("haven't eaten" is not negated by context).
    """
    before = text[max(0, match_start - 40):match_start].strip()
    preceding = before.split()[-3:]
    return any(w in _NEGATION_WORDS for w in preceding)


def detect_surface_attention(recent_texts: list[str]) -> list[str]:
    """Detect what's on the user's mind from their recent messages.

    Returns list of attention keys (e.g., ["hungry", "anxious", "lonely"]).
    Zero LLM — keyword + phrase detection.

    Single keywords are checked for negation ("I'm not hungry" → no match).
    Multi-word phrases are never negation-filtered (they encode their own context).
    """
    combined = " ".join(recent_texts).lower()
    attentions: list[str] = []

    # Map attention → signal patterns.
    # Single words: subject to negation filtering ("hungry", "sad").
    # Phrases (contains space): exact phrase match, no negation filter.
    keyword_map: dict[str, list[str]] = {
        # ── Survival ─────────────────────────────────────────────────────────
        "hungry": [
            # Direct
            "hungry", "starving", "famished", "جائع", "饿",
            # Indirect phrases — the real-data gap
            "haven't eaten", "havent eaten", "didn't eat", "didnt eat",
            "nothing to eat", "no food", "skipped breakfast", "skipped lunch",
            "skipped dinner", "skipped meals", "skip meals",
            "stomach is growling", "stomach is empty", "running out of food",
            "haven't had anything", "nothing left to eat",
            "没吃东西", "没饭吃",
        ],
        "thirsty": [
            "thirsty", "dehydrated", "渴",
            "nothing to drink", "no water", "dying for a drink",
        ],
        "tired": [
            "tired", "exhausted", "drained", "burnt out", "burnout",
            "no energy", "depleted", "累", "疲", "متعب",
            "can't keep my eyes open", "running on empty", "barely function",
            "haven't slept", "havent slept", "running on fumes",
        ],
        "cold": ["cold", "freezing", "冷", "chilly", "shivering"],
        "hot":  ["hot", "boiling", "sweltering", "热", "حر", "burning up"],

        # ── Emotional states ─────────────────────────────────────────────────
        "anxious": [
            "anxious", "worried", "nervous", "panic", "restless",
            "uneasy", "on edge", "焦虑", "紧张", "قلق",
            # Indirect phrases
            "can't breathe", "heart is racing", "can't calm down",
            "stomach in knots", "palms sweating", "can't stop worrying",
            "dreading", "filled with dread", "terrified of",
        ],
        "sad": [
            "sad", "crying", "tears", "depressed", "numb", "hopeless",
            "feel low", "feeling low", "lost all hope", "breaking down",
            "down lately", "伤心", "哭", "难过", "حزين",
            # Indirect phrases
            "can't get out of bed", "lost interest in", "nothing matters",
            "what's the point", "don't see the point", "feel empty inside",
            "don't want to get up",
        ],
        "angry": [
            "angry", "furious", "rage", "infuriated", "argument", "生气", "愤怒", "غاضب",
            # Indirect phrases — real data gap
            "just argued", "just had an argument", "got into a fight",
            "had a fight", "got into it with", "got into an argument",
            "so frustrated", "exasperated", "can't believe they",
            "this is ridiculous", "blew up at", "lost my temper",
            "heated argument", "big fight",
        ],
        "lonely": [
            "lonely", "alone", "nobody", "no one", "isolated",
            "disconnected", "no friends", "feel invisible", "孤独", "一个人", "وحيد",
            # Indirect phrases
            "eating alone", "nobody to talk to", "all by myself",
            "spending the evening alone", "nobody cares", "no one around",
        ],
        "scared": [
            "scared", "afraid", "terrified", "fearful", "害怕", "恐惧", "خائف",
            "freaking out", "something is wrong",
        ],
        "panicking": [
            "panic attack", "can't breathe", "help me", "恐慌发作",
            "heart is pounding", "shaking uncontrollably",
        ],
        "grieving": [
            "died", "dead", "funeral", "passed away", "they're gone",
            "lost them", "loss", "去世", "死", "失去", "وفاة",
            "can't believe they're gone",
        ],
        "guilty": [
            "guilty", "fault", "shouldn't", "内疚", "对不起",
            # Indirect phrases
            "feel like a burden", "burden to everyone", "let everyone down",
            "all my fault", "i ruined", "i messed up", "i hurt them",
        ],

        # ── Practical needs ───────────────────────────────────────────────────
        "need_money": [
            "i'm broke", "im broke", "flat broke", "can't afford", "debt",
            "out of cash", "no money", "can't pay", "钱", "穷", "مال",
        ],
        "need_medicine": [
            "medicine", "sick", "ill", "药", "生病", "مريض",
            "need a doctor", "need to see a doctor", "feel awful physically",
        ],
        "need_wifi":  ["wifi", "internet", "上网", "إنترنت", "no signal", "no connection"],
        "need_quiet": ["quiet", "silence", "peace", "安静", "هدوء", "need some quiet", "need silence"],
        "need_exercise": [
            "exercise", "gym", "workout", "运动", "锻炼", "رياضة",
            "need to move", "need to get moving", "body feels stiff",
        ],
        "need_pray": [
            "pray", "prayer", "mosque", "church", "temple",
            "祈祷", "صلاة", "مسجد", "time for prayer", "it's prayer time",
        ],
        "need_meaning": [
            "meaning", "purpose", "why am i", "意义", "目的",
            "what's the point of living", "feel like nothing matters",
        ],
        "need_talk": [
            "talk to someone", "need someone", "想说话", "need to talk",
            "confused about my", "don't know what to do",
            "need advice", "don't know who to talk",
            "someone to talk to", "no one to talk to",
        ],

        # ── Social ───────────────────────────────────────────────────────────
        "want_friends": ["friends", "meet people", "交朋友", "认识人", "make new friends", "make friends", "meet friends"],

        # ── Creative & learning ───────────────────────────────────────────────
        "want_art":    ["gallery", "exhibition", "画", "展览", "art museum"],
        "want_read":   ["library", "书", "图书馆", "want to read", "good book"],
        "want_music":  ["music", "concert", "音乐", "live music", "gig tonight"],
        "want_work":   ["productive", "focus", "deadline", "工作", "写代码", "need to work", "need to get work done"],
        "want_learn":  ["study", "course", "学", "想学", "want to learn", "learn something new"],

        # ── Context-aware ─────────────────────────────────────────────────────
        "bored":     ["bored", "boring", "nothing to do", "kill time", "无聊", "ممل"],
        "morning":   ["good morning", "this morning", "just woke up", "早上好", "刚起床", "صباح الخير"],
        "evening":   ["tonight", "this evening", "after work", "winding down", "晚上了", "مساء"],
        "weekend":   ["weekend", "saturday", "sunday", "周末", "星期六", "星期天", "نهاية الأسبوع"],
        "new_place": ["new here", "just moved", "just arrived", "visiting", "tourist", "刚来", "陌生的地方", "وصلت"],
        "insomnia":  [
            "can't sleep", "insomnia", "wide awake", "lying awake", "失眠", "睡不着", "أرق",
            "been up all night", "up all night", "staring at the ceiling",
            "stared at the ceiling", "counting sheep",
            "3am", "4am", "wide awake at", "awake since", "couldn't sleep",
        ],

        # ── Self-improvement ──────────────────────────────────────────────────
        "confidence": [
            "not confident", "insecure", "worthless", "can't do it",
            "nobody likes", "feel useless", "i'm a failure", "not good enough",
            "hate myself", "没信心", "不自信", "لا أستطيع",
        ],
        "reflection": [
            "reflecting on", "looking back", "in hindsight",
            "i wonder why", "i've been reflecting", "回想起来", "反思",
        ],

        # ── Life events ───────────────────────────────────────────────────────
        "celebrating": [
            "celebrating", "birthday", "anniversary", "promotion", "good news",
            "庆祝", "生日", "升职", "احتفال", "just got promoted", "just got the job",
        ],
        "homesick": [
            "homesick", "miss home", "miss my family", "far from home",
            "想家", "思乡", "أشتاق للبيت", "wish i was home",
        ],
        "headache": [
            "headache", "migraine", "头疼", "头痛", "صداع",
            # Real data gap: indirect phrases
            "head is killing me", "head hurts", "head is pounding",
            "splitting headache", "throbbing in my head",
            "my head won't stop",
        ],
        "overwhelmed": [
            "overwhelmed", "can't handle", "falling apart", "can't cope",
            "can't take it", "不知所措", "崩溃了", "مرهق",
            # Indirect phrases
            "drowning in", "too much on my plate", "plate is full",
            "losing track of everything", "can't keep up",
        ],
        "want_outdoor": [
            "outdoors", "nature", "fresh air", "hike", "hiking", "户外", "大自然", "الطبيعة",
        ],
        "want_create": [
            "want to create", "creative", "make something", "draw", "paint", "craft",
            "创作", "画画", "أبدع",
        ],

        # ── Relationship / emotional pain ─────────────────────────────────────
        "heartbreak": [
            "broke up", "break up", "my ex", "she left", "he left",
            "want her back", "want him back", "want them back", "want my person back",
            "my heart is broken", "heartbreak", "heartbroken", "失恋", "分手",
        ],
        "missing_someone": [
            "miss him", "miss her", "miss them", "missing him", "missing her",
            "missing someone", "think about him", "think about her",
            "can't stop thinking about", "thinking of you", "想他", "想她", "想你",
        ],
        "relationship_pain": [
            "controlling", "won't let me", "won't allow me", "toxic relationship",
            "relationship problems", "relationship issues", "he controls", "she controls",
            "abusive", "can't leave", "mixed signals", "blowing hot and cold",
            "on and off again", "push and pull", "emotional manipulation",
            "مشكلة في العلاقة",
        ],

        # ── CRITICAL: Life-safety ─────────────────────────────────────────────
        "suicidal_ideation": [
            # Direct
            "suicidal", "suicide", "kill myself", "end my life", "end it all",
            "want to die", "don't want to live", "better off dead",
            "no reason to live", "can't go on", "self harm", "self-harm",
            "hurt myself", "自杀", "不想活", "活不下去", "死了算了",
            # Indirect phrases
            "thinking about ending things", "thinking about ending it",
            "nobody would miss me", "world would be better without me",
            "can't see a way out", "just want it to stop",
            "tired of living", "tired of being alive",
            "what's the point of living", "make it stop",
            # Arabic
            "أريد أن أموت", "انتحار", "أقتل نفسي",
        ],
        "domestic_violence": [
            # Direct
            "he hit me", "she hit me", "they hit me",
            "he beats me", "she beats me", "being abused",
            "domestic violence", "domestic abuse",
            "he threatened me", "she threatened me",
            "afraid of my partner", "afraid of my husband", "afraid of my wife",
            "家暴", "打我", "暴力",
            # Indirect phrases
            "scared to go home", "can't leave him", "can't leave her",
            "he controls all my money", "she controls all my money",
            "not allowed to see my friends", "not allowed to leave",
            "he checks my phone", "she checks my phone",
            "walking on eggshells", "next time he'll hurt me",
            "hiding bruises", "called me worthless",
            # Arabic
            "يضربني", "العنف الأسري",
        ],
        "addiction_crisis": [
            # Direct
            "withdrawal", "detox", "addicted", "addiction",
            "can't stop drinking", "can't stop using",
            "relapsed", "relapse", "overdose",
            "drug problem", "alcohol problem",
            "依赖", "成瘾", "戒断", "复发",
            # Indirect phrases
            "been drinking every day", "using every day",
            "need a drink to function", "need it just to get through",
            "been hiding how much i drink", "been hiding how much i use",
            "my family doesn't know how bad it is",
            "drinking is out of control", "using is out of control",
            "can't stop even though i want to",
            "morning drink", "drinking since morning",
        ],
        "homelessness": [
            # Direct
            "homeless", "no place to sleep", "no place to stay",
            "sleeping rough", "sleeping on the street",
            "evicted", "got evicted", "being evicted",
            "no shelter", "lost my home", "无家可归", "流浪",
            # Indirect phrases
            "don't have anywhere to sleep tonight",
            "don't have anywhere to go tonight",
            "got kicked out", "thrown out of my apartment",
            "car is my home now", "sleeping in my car",
            "couch surfing", "staying on a friend's couch",
            "can't afford rent anymore", "can't make rent",
            "landlord changed the locks",
        ],

        # ── Mental health clinical ────────────────────────────────────────────
        "need_therapy": [
            # Direct
            "therapist", "therapy", "counseling", "counsellor",
            "psychiatrist", "psychologist", "mental health help",
            "心理咨询", "治疗师", "心理医生",
            # Indirect phrases
            "need to talk to a professional", "need professional help",
            "where do i find a therapist", "how do i find a therapist",
            "can't afford therapy", "looking for a counselor",
            "thinking about starting therapy", "should i see a therapist",
        ],
        "trauma_ptsd": [
            # Direct
            "trauma", "traumatized", "ptsd", "flashbacks", "flashback",
            "triggered", "nightmare", "nightmares", "创伤", "闪回",
            # Indirect phrases
            "can't stop reliving it", "keeps coming back to me",
            "can't get it out of my head", "intrusive thoughts",
            "something happened to me that i can't talk about",
            "can't stop thinking about what happened",
            "body won't calm down when i think about it",
            "startle at everything", "always on high alert",
            "don't feel safe even at home",
        ],
        "eating_disorder": [
            # Direct
            "eating disorder", "anorexia", "bulimia", "binge eating",
            "purging", "restricting food", "进食障碍",
            # Indirect phrases
            "scared to eat", "afraid of food", "hate my body",
            "can't stop eating and then making myself sick",
            "counting every calorie obsessively",
            "haven't eaten in days because of fear",
            "throwing up after eating", "laxatives after eating",
            "my relationship with food is destroying me",
        ],
        "postpartum": [
            # Direct
            "postpartum", "postnatal", "after having my baby", "after giving birth",
            "new mom", "new mother", "产后", "产后抑郁",
            # Indirect phrases
            "can't bond with my baby", "feel nothing for my baby",
            "since having the baby i can't stop crying",
            "everyone says i should be happy but i'm not",
            "scared i'm going to hurt my baby",
            "postpartum depression", "baby blues that won't go away",
            "feel like my baby deserves a better mom",
        ],

        # ── Financial ────────────────────────────────────────────────────────
        "debt_crisis": [
            # Direct
            "eviction notice",
            "can't pay rent", "behind on rent", "missed rent",
            "can't pay my bills", "debt collector", "debt collectors",
            "bankruptcy", "bankrupt", "can't make ends meet",
            "债务", "欠债", "欠款", "无法还款",
            # Indirect phrases
            "about to lose my home", "about to be evicted",
            "can't pay my mortgage", "behind on my mortgage",
            "bailiffs coming", "court summons for debt",
            "three months behind on rent", "rent is due and i have nothing",
            "disconnected my electricity", "utilities cut off",
            "can't afford food and rent both",
        ],
        "job_loss": [
            # Direct
            "fired", "got fired", "laid off", "got laid off",
            "made redundant", "lost my job", "unemployment",
            "被解雇", "失业", "裁员",
            # Indirect phrases
            "just lost my job", "lost my job today",
            "company is closing", "company went under",
            "position was eliminated", "contract wasn't renewed",
            "let go from my job", "terminated",
            "first time unemployed", "don't know how i'll pay bills now",
        ],

        # ── Career ────────────────────────────────────────────────────────────
        "job_seeking": [
            # Direct
            "job hunting", "job search", "looking for work", "looking for a job",
            "applying for jobs", "job applications", "求职", "找工作",
            # Indirect phrases
            "can't find a job", "sending out resumes", "sending out cvs",
            "haven't heard back from any applications",
            "been unemployed for months",
            "need a job desperately", "where to find job listings",
        ],
        "career_change": [
            # Direct
            "career change", "change careers", "switching careers",
            "new career", "different field", "转行",
            # Indirect phrases
            "hate my job but don't know what else to do",
            "stuck in the wrong career",
            "thinking about changing what i do",
            "want to do something completely different",
            "don't know what i'm meant to do with my life",
            "should i quit my job", "thinking of leaving my career",
        ],

        # ── Housing ────────────────────────────────────────────────────────────
        "need_housing": [
            # Direct
            "looking for an apartment", "looking for a flat", "apartment hunting",
            "flat hunting", "need to find housing", "house hunting",
            "找房", "租房", "找公寓",
            # Indirect phrases
            "where do i find cheap housing", "affordable housing",
            "need to move", "need a new place to live",
            "landlord won't renew my lease",
            "where can i find a room to rent",
        ],

        # ── Family ────────────────────────────────────────────────────────────
        "parenting_stress": [
            # Direct
            "parenting stress", "overwhelmed as a parent",
            "育儿压力",
            # Indirect phrases
            "my kids are driving me insane",
            "don't know how to handle my child",
            "screaming all the time at my kids", "losing patience with my kids",
            "feel like a terrible parent", "terrible mother", "terrible father",
            "my toddler won't stop", "can't cope with the kids",
            "haven't slept since the baby came",
        ],
        "need_childcare": [
            # Direct
            "childcare", "daycare", "nursery", "babysitter",
            "after school care", "托儿所", "托育",
            # Indirect phrases
            "can't find childcare", "can't afford daycare",
            "need someone to watch my kids",
            "where do i find a babysitter",
            "kids have nowhere to go while i work",
        ],
        "family_conflict": [
            # Direct
            "family conflict", "family fight", "family argument",
            "fighting with my parents", "fighting with my siblings",
            "家庭矛盾", "家庭冲突",
            # Indirect phrases
            "my parents don't talk to me",
            "cut off from my family",
            "estranged from my family",
            "huge argument with my dad", "huge argument with my mom",
            "family is falling apart", "my family is toxic",
        ],
        "elder_care": [
            # Direct
            "elderly parent", "aging parent", "my parent has dementia",
            "caring for my elderly", "caregiver burnout",
            "养老", "照顾老人",
            # Indirect phrases
            "mom can't live alone anymore",
            "dad can't take care of himself",
            "don't know how to get help for my aging parent",
            "can't afford a nursing home",
            "how do i find care for my elderly parent",
        ],
        "divorce": [
            # Direct
            "divorce", "divorcing", "going through a divorce",
            "separated", "separation", "离婚",
            # Indirect phrases
            "husband and i are splitting up", "wife and i are splitting up",
            "marriage is over", "filing for divorce",
            "can't afford a divorce lawyer",
            "custody battle", "custody dispute",
            "co-parenting is a nightmare",
        ],

        # ── Legal ─────────────────────────────────────────────────────────────
        "legal_trouble": [
            # Direct
            "arrested", "arrest", "in trouble with the law",
            "facing charges", "criminal charges", "court date",
            "need a lawyer", "can't afford a lawyer",
            "法律问题", "被捕", "法庭",
            # Indirect phrases
            "police showed up at my door",
            "subpoena", "got a subpoena",
            "being sued", "lawsuit against me",
            "don't know my legal rights",
            "need free legal help", "where to find legal aid",
        ],
        "immigration_stress": [
            # Direct
            "visa expired", "undocumented", "deportation",
            "asylum", "asylum seeker", "refugee", "immigration",
            "签证", "移民", "难民", "庇护",
            # Indirect phrases
            "scared of being deported",
            "don't have papers", "no papers",
            "immigration appointment",
            "my visa is running out",
            "don't know if i can stay",
            "immigration lawyer",
        ],

        # ── Health ────────────────────────────────────────────────────────────
        "chronic_pain": [
            # Direct
            "chronic pain", "fibromyalgia", "chronic illness",
            "pain every day", "constant pain", "慢性疼痛",
            # Indirect phrases
            "been in pain for months", "pain that won't go away",
            "doctors can't figure out what's wrong",
            "pain is affecting my life",
            "can't do normal things because of pain",
            "pain management", "pain clinic",
        ],
        "need_dental": [
            # Direct
            "toothache", "tooth pain", "dental", "dentist",
            "tooth is killing me", "broken tooth", "牙疼", "牙医",
            # Indirect phrases
            "can't afford a dentist", "tooth hurts so bad",
            "my tooth is infected", "dental emergency",
            "where to find a free dentist",
        ],
        "disability_access": [
            # Direct
            "disability", "disabled", "wheelchair", "mobility aid",
            "accessibility", "accessibility needs", "残疾", "无障碍",
            # Indirect phrases
            "can't access because of my disability",
            "need accessible venue",
            "disability benefits",
            "where to find disability support",
        ],
        "pregnancy": [
            # Direct
            "pregnant", "pregnancy", "expecting a baby",
            "prenatal", "antenatal", "怀孕", "孕妇",
            # Indirect phrases
            "just found out i'm pregnant",
            "need prenatal care", "where to go for pregnancy care",
            "first trimester", "morning sickness",
            "midwife", "obstetrician",
        ],

        # ── Practical ─────────────────────────────────────────────────────────
        "need_vet": [
            # Direct
            "vet", "veterinarian", "veterinary",
            "my dog is sick", "my cat is sick", "my pet is sick",
            "pet emergency", "兽医", "宠物生病",
            # Indirect phrases
            "where is the nearest vet",
            "my pet needs a doctor", "my animal is injured",
            "can't afford a vet",
        ],
        "home_emergency": [
            # Direct
            "gas leak", "smell gas", "flooded", "flooding",
            "locked out", "locked out of my house",
            "electrical problem", "power outage", "smoke alarm",
            "煤气泄漏", "漏水", "停电",
            # Indirect phrases
            "something is wrong with the pipes",
            "no heating in winter", "boiler is broken",
            "can't get into my apartment",
            "emergency plumber", "emergency electrician",
        ],
        "need_translation": [
            # Direct
            "translator", "translation", "interpret",
            "interpreter", "翻译", "مترجم",
            # Indirect phrases
            "don't speak the language",
            "can't understand what they're saying",
            "need help communicating",
            "language barrier",
            "need someone who speaks",
        ],
        "food_insecurity": [
            # Direct
            "food bank", "food pantry", "food stamps", "snap", "food assistance",
            "food voucher", "free food", "食物援助", "食物银行",
            # Indirect phrases
            "can't afford groceries", "run out of food",
            "children haven't eaten", "kids haven't eaten",
            "don't have money for food",
            "where to get free food",
            "no food in the house",
        ],
        "need_clothes": [
            # Direct
            "clothes bank", "clothing donation", "charity clothes",
            "free clothing", "can't afford clothes",
            "旧衣服", "捐赠衣物",
            # Indirect phrases
            "need warm clothes", "don't have a winter coat",
            "children need clothes", "kids need school clothes",
            "where to find free clothing",
        ],
        "tech_help": [
            # Direct
            "computer help", "tech support", "it help",
            "laptop broken", "laptop is broken", "phone broken", "internet issue",
            "电脑坏了", "手机坏了",
            # Indirect phrases
            "can't figure out how to", "don't know how to use",
            "keep getting error", "where to get tech help for free",
            "library computer help",
        ],

        # ── Relationships ─────────────────────────────────────────────────────
        "friend_conflict": [
            "friend and i had a fight", "fight with a friend",
            "argument with my friend", "argued with my friend",
            "friend and i aren't talking", "falling out with a friend",
            "friend betrayed me", "best friend hurt me",
            "friend problem", "friend drama",
            "falling out with my best friend",
            "朋友吵架", "朋友矛盾", "跟朋友闹翻",
        ],
        "want_pet": [
            "want a pet", "want a dog", "want a cat",
            "thinking of getting a pet", "thinking of getting a dog",
            "thinking of getting a cat", "adopting a dog", "adopting a cat",
            "pet adoption", "adopt a dog", "adopt a cat",
            "miss having a pet", "lonely without a pet",
            "想养宠物", "想养狗", "想养猫",
        ],

        # ── Finance (non-crisis) ──────────────────────────────────────────────
        "want_save_money": [
            "want to save money", "trying to save", "need to save up",
            "save more money", "start saving", "how to save",
            "build an emergency fund", "how to budget", "financial goals",
            "节省", "存钱", "攒钱",
        ],
        "budget_help": [
            "help with budget", "need a budget", "budgeting tips",
            "can't manage my money", "where does my money go",
            "overspending", "spending too much", "money management",
            "预算", "理财",
        ],
        "exchange_money": [
            "exchange rate", "exchange money", "convert currency",
            "transfer money abroad", "send money home",
            "wire transfer", "how much is the dollar",
            "换汇", "汇率", "汇款", "外汇",
        ],

        # ── Nutrition / weight ────────────────────────────────────────────────
        "want_lose_weight": [
            "want to lose weight", "trying to lose weight",
            "lose some weight", "slim down", "lose fat", "weight loss",
            "overweight", "too heavy", "diet plan",
            "减肥", "减重", "想瘦",
        ],
        "ate_too_much": [
            "ate too much", "overate", "ate way too much",
            "so full", "stuffed", "feel bloated", "food coma",
            "can't stop eating", "吃太多了", "吃撑了",
        ],
        "want_eat_healthy": [
            "eat healthy", "eat healthier", "eating healthy",
            "want to eat better", "clean eating", "healthy diet",
            "eat more vegetables", "nutritious food", "balanced diet",
            "健康饮食", "吃健康", "营养",
        ],

        # ── Transit ───────────────────────────────────────────────────────────
        "need_transit": [
            "nearest bus stop", "nearest subway", "nearest train station",
            "public transport", "how do i get to", "how to get there",
            "take the bus", "take the subway", "take the train",
            "bus timetable", "train schedule",
            "怎么去", "公交", "地铁", "公共交通", "坐什么车",
        ],
        "missed_bus": [
            "missed the bus", "missed my bus", "bus just left",
            "missed the train", "missed my train",
            "just missed the bus", "just missed my train",
            "错过了公交", "错过了地铁", "没赶上",
        ],
        "want_navigate": [
            "how do i get to", "directions to", "navigate to",
            "how far is", "walking distance to", "i'm lost",
            "i am lost", "lost my way", "help me get to",
            "route to", "path to",
            "怎么走", "路线", "导航", "我迷路了",
        ],
    }

    for attention, keywords in keyword_map.items():
        for kw in keywords:
            # CJK/Arabic: substring match (no word boundaries)
            if any(ord(c) > 127 for c in kw):
                if kw in combined:
                    attentions.append(attention)
                    break
            else:
                m = _re.search(r'\b' + _re.escape(kw) + r'\b', combined)
                if m:
                    # Negation filter: only for single-word keywords.
                    # Phrases encode their own meaning ("can't breathe" is already specific).
                    if ' ' not in kw and _is_negated_at(combined, m.start()):
                        continue
                    attentions.append(attention)
                    break

    return attentions


# ── Trigger phrase lookup ────────────────────────────────────────────────────
# Subset of keywords per attention — the most RECOGNISABLE phrases to echo back.
# Priority order: multi-word phrases first (more specific), then single words.
# Used by _find_trigger_phrase() to find what the user ACTUALLY SAID.
_TRIGGER_PHRASES: dict[str, list[str]] = {
    "hungry":           ["haven't eaten", "havent eaten", "nothing to eat", "skipped breakfast",
                         "stomach is growling", "starving", "famished", "hungry", "没吃东西"],
    "thirsty":          ["nothing to drink", "dying for a drink", "thirsty", "dehydrated"],
    "tired":            ["running on empty", "burnt out", "can barely function", "running on fumes",
                         "exhausted", "drained", "tired"],
    "cold":             ["shivering", "freezing", "cold"],
    "hot":              ["sweltering", "burning up", "boiling", "hot"],
    "sad":              ["can't get out of bed", "nothing matters", "feel empty inside", "hopeless",
                         "numb", "crying", "sad"],
    "angry":            ["lost my temper", "got into a fight", "just argued", "blew up at",
                         "heated argument", "furious", "angry"],
    "anxious":          ["heart is racing", "can't calm down", "can't stop worrying", "stomach in knots",
                         "filled with dread", "anxious", "nervous"],
    "lonely":           ["nobody to talk to", "eating alone", "all by myself", "no one around",
                         "disconnected", "isolated", "lonely"],
    "scared":           ["freaking out", "something is wrong", "terrified", "scared"],
    "panicking":        ["panic attack", "heart is pounding", "shaking uncontrollably", "can't breathe"],
    "grieving":         ["can't believe they're gone", "passed away", "they're gone", "lost them"],
    "guilty":           ["feel like a burden", "let everyone down", "all my fault", "i ruined"],
    "headache":         ["head is killing me", "splitting headache", "head is pounding",
                         "throbbing in my head", "headache", "migraine"],
    "insomnia":         ["staring at the ceiling", "been up all night", "wide awake at",
                         "awake since", "couldn't sleep", "can't sleep"],
    "overwhelmed":      ["drowning in", "too much on my plate", "can't cope", "can't keep up",
                         "overwhelmed", "falling apart"],
    "heartbreak":       ["my heart is broken", "she left", "he left", "broke up", "heartbroken"],
    "missing_someone":  ["can't stop thinking about", "missing him", "missing her", "miss him", "miss her"],
    "relationship_pain":["emotional manipulation", "toxic relationship", "won't let me", "controlling"],
    "need_money":       ["i'm broke", "flat broke", "out of cash", "no money", "can't afford"],
    "need_medicine":    ["need a doctor", "feel awful physically"],
    "need_talk":        ["no one to talk to", "nobody to talk to", "need someone to talk to"],
    "need_pray":        ["time for prayer", "it's prayer time"],
    "bored":            ["nothing to do", "killing time", "bored"],
    "celebrating":      ["just got promoted", "just got the job", "celebrating", "birthday"],
    "homesick":         ["miss home", "miss my family", "wish i was home", "homesick"],
    "confidence":       ["hate myself", "feel useless", "worthless", "not good enough"],
    "want_outdoor":     ["fresh air", "need to get outside", "go for a walk"],
    "panicking":        ["panic attack", "heart is pounding"],
    "suicidal_ideation":  ["thinking about ending things", "nobody would miss me",
                           "world would be better without me", "want to die",
                           "tired of being alive", "can't see a way out",
                           "自杀", "不想活"],
    "domestic_violence":  ["scared to go home", "walking on eggshells",
                           "he hit me", "she hit me", "hiding bruises",
                           "can't leave him", "can't leave her", "家暴"],
    "addiction_crisis":   ["drinking is out of control", "can't stop even though i want to",
                           "relapsed", "been drinking every day", "overdose"],
    "homelessness":       ["sleeping in my car", "don't have anywhere to sleep tonight",
                           "got kicked out", "sleeping rough", "evicted", "homeless"],
    "need_therapy":       ["need to talk to a professional", "where do i find a therapist",
                           "thinking about starting therapy"],
    "trauma_ptsd":        ["can't stop reliving it", "intrusive thoughts",
                           "keeps coming back to me", "flashbacks", "always on high alert"],
    "eating_disorder":    ["throwing up after eating", "scared to eat",
                           "my relationship with food is destroying me", "purging"],
    "postpartum":         ["can't bond with my baby", "since having the baby i can't stop crying",
                           "postpartum depression", "everyone says i should be happy but"],
    "debt_crisis":        ["about to be evicted", "rent is due and i have nothing",
                           "can't pay rent", "utilities cut off", "bankruptcy"],
    "job_loss":           ["just lost my job", "got fired", "got laid off",
                           "made redundant", "position was eliminated"],
    "job_seeking":        ["can't find a job", "sending out resumes",
                           "haven't heard back from any applications", "job hunting"],
    "career_change":      ["stuck in the wrong career", "hate my job but don't know what else",
                           "thinking of leaving my career", "career change"],
    "need_housing":       ["apartment hunting", "need to find housing",
                           "looking for an apartment", "affordable housing"],
    "parenting_stress":   ["feel like a terrible parent", "losing patience with my kids",
                           "screaming all the time at my kids", "can't cope with the kids"],
    "need_childcare":     ["can't find childcare", "kids have nowhere to go while i work"],
    "family_conflict":    ["estranged from my family", "huge argument with my dad",
                           "family is falling apart", "cut off from my family"],
    "elder_care":         ["mom can't live alone anymore", "dad can't take care of himself",
                           "can't afford a nursing home"],
    "divorce":            ["going through a divorce", "marriage is over",
                           "custody battle", "filing for divorce"],
    "legal_trouble":      ["being sued", "need free legal help", "facing charges",
                           "can't afford a lawyer", "arrested"],
    "immigration_stress": ["scared of being deported", "visa expired",
                           "don't have papers", "my visa is running out"],
    "chronic_pain":       ["pain that won't go away", "been in pain for months",
                           "chronic pain", "doctors can't figure out what's wrong"],
    "need_dental":        ["tooth is killing me", "my tooth is infected",
                           "can't afford a dentist", "dental emergency"],
    "disability_access":  ["can't access because of my disability",
                           "disability benefits", "need accessible venue"],
    "pregnancy":          ["just found out i'm pregnant", "need prenatal care",
                           "first trimester", "morning sickness"],
    "need_vet":           ["my dog is sick", "my cat is sick", "pet emergency",
                           "where is the nearest vet"],
    "home_emergency":     ["gas leak", "smell gas", "locked out of my house",
                           "boiler is broken", "no heating in winter"],
    "need_translation":   ["language barrier", "don't speak the language",
                           "need help communicating"],
    "food_insecurity":    ["no food in the house", "can't afford groceries",
                           "children haven't eaten", "where to get free food", "food bank"],
    "need_clothes":       ["don't have a winter coat", "need warm clothes",
                           "where to find free clothing"],
    "tech_help":          ["laptop broken", "keep getting error",
                           "where to get tech help for free"],
    "friend_conflict":    ["argument with my friend", "friend betrayed me",
                           "friend and i had a fight", "falling out with a friend"],
    "want_pet":           ["want a dog", "want a cat", "thinking of getting a pet",
                           "adopt a dog", "adopt a cat"],
    "want_save_money":    ["want to save money", "start saving",
                           "build an emergency fund", "need to save up"],
    "budget_help":        ["where does my money go", "can't manage my money",
                           "help with budget", "overspending"],
    "exchange_money":     ["exchange rate", "send money home",
                           "换汇", "transfer money abroad"],
    "want_lose_weight":   ["want to lose weight", "trying to lose weight",
                           "减肥", "weight loss"],
    "ate_too_much":       ["ate too much", "overate", "so full", "feel bloated", "吃太多了"],
    "want_eat_healthy":   ["eat healthy", "eat healthier", "clean eating", "healthy diet"],
    "need_transit":       ["nearest bus stop", "public transport",
                           "how do i get to", "怎么去"],
    "missed_bus":         ["missed the bus", "missed the train", "bus just left"],
    "want_navigate":      ["how do i get to", "directions to", "i'm lost", "find my way"],
}


def _find_trigger_phrase(texts: list[str], attention: str) -> str | None:
    """Find the exact phrase the user said that triggered this attention signal.

    Returns the original-case snippet from the user's text, or None.
    Used to build "你说「haven't eaten」→ Corner Cafe" instead of generic "你说饿了 →".
    """
    original = " ".join(texts)
    combined = original.lower()
    for phrase in _TRIGGER_PHRASES.get(attention, []):
        if any(ord(c) > 127 for c in phrase):
            idx = combined.find(phrase)
            if idx >= 0:
                return original[idx:idx + len(phrase)]
        else:
            m = _re.search(r'\b' + _re.escape(phrase) + r'\b', combined)
            if m:
                return original[m.start():m.end()]
    return None


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
