"""Wellness & self-care APIs. All free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError


# 61. Daily horoscope
def daily_horoscope(sign: str = "aries") -> dict | None:
    url = f"https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily?sign={sign}&day=TODAY"
    try:
        with urlopen(
            Request(url, headers={"Accept": "application/json"}), timeout=5
        ) as r:
            data = json.loads(r.read().decode()).get("data", {})
            return {
                "sign": sign,
                "date": data.get("date", ""),
                "horoscope": data.get("horoscope_data", ""),
            }
    except Exception:
        return None


# 62. Random color palette
def random_color() -> dict:
    import random

    r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    return {"hex": hex_color, "rgb": f"rgb({r},{g},{b})", "name": _closest_color_name(r, g, b)}


def _closest_color_name(r: int, g: int, b: int) -> str:
    colors = {
        "red": (255, 0, 0),
        "green": (0, 128, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "purple": (128, 0, 128),
        "orange": (255, 165, 0),
        "pink": (255, 192, 203),
        "brown": (139, 69, 19),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "gray": (128, 128, 128),
        "teal": (0, 128, 128),
        "coral": (255, 127, 80),
    }
    min_dist = float("inf")
    closest = "unknown"
    for name, (cr, cg, cb) in colors.items():
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < min_dist:
            min_dist = d
            closest = name
    return closest


# 63. Breathing exercise generator (local compute)
def breathing_exercise(technique: str = "box") -> dict:
    techniques = {
        "box": {
            "name": "Box Breathing",
            "steps": [("inhale", 4), ("hold", 4), ("exhale", 4), ("hold", 4)],
            "cycles": 4,
        },
        "478": {
            "name": "4-7-8 Breathing",
            "steps": [("inhale", 4), ("hold", 7), ("exhale", 8)],
            "cycles": 3,
        },
        "resonant": {
            "name": "Resonant Breathing",
            "steps": [("inhale", 5), ("exhale", 5)],
            "cycles": 10,
        },
        "lion": {
            "name": "Lion's Breath",
            "steps": [("inhale deeply", 4), ("exhale with tongue out", 4)],
            "cycles": 5,
        },
        "alternate_nostril": {
            "name": "Alternate Nostril",
            "steps": [
                ("close right, inhale left", 4),
                ("close both, hold", 2),
                ("close left, exhale right", 4),
                ("inhale right", 4),
                ("hold", 2),
                ("exhale left", 4),
            ],
            "cycles": 5,
        },
    }
    return techniques.get(technique, techniques["box"])


# 64. Gratitude prompt generator (local compute)
def gratitude_prompt() -> str:
    import random

    prompts = [
        "Name three things you can see right now that you're grateful for",
        "Who is someone who helped you recently? What did they do?",
        "What is a simple pleasure you enjoyed today?",
        "What part of your body are you grateful for?",
        "What is a challenge you overcame that made you stronger?",
        "Name a food you love. Why does it make you happy?",
        "What's a memory that always makes you smile?",
        "Who taught you something valuable? What was it?",
        "What's something in nature that amazes you?",
        "What's a skill you have that you're proud of?",
        "Name a book, song, or movie that changed your perspective",
        "What's one thing about today that was better than yesterday?",
        "Who makes you feel safe? Send them a message right now.",
        "What's a mistake that turned into something good?",
        "If you could keep only one memory, which would it be?",
    ]
    return random.choice(prompts)


# 65. Daily challenge generator (local compute, personality-aware)
def daily_challenge(personality_type: str = "") -> str:
    import random

    introvert = [
        "Write a letter to someone you appreciate (don't send it yet)",
        "Spend 10 minutes drawing something",
        "Listen to a full album with no distractions",
        "Write down 3 things you learned this week",
        "Cook a new recipe from scratch",
    ]
    extrovert = [
        "Start a conversation with a stranger today",
        "Organize a small gathering this weekend",
        "Call someone you haven't talked to in months",
        "Give a genuine compliment to 3 people today",
        "Try a group fitness class",
    ]
    universal = [
        "Take a different route today",
        "Go 2 hours without your phone",
        "Try a food you've never had",
        "Write down your biggest worry, then tear it up",
        "Watch the sunset today",
    ]
    if personality_type and personality_type[0] == "I":
        return random.choice(introvert + universal)
    elif personality_type and personality_type[0] == "E":
        return random.choice(extrovert + universal)
    return random.choice(introvert + extrovert + universal)


def is_available() -> bool:
    return True
