"""Creative & fun APIs. All free, no key."""
from __future__ import annotations
import json
import random
from urllib.request import urlopen, Request
from urllib.error import URLError


# 71. Random color palette (colormind.io)
def random_palette() -> list[list[int]]:
    try:
        req = Request(
            "http://colormind.io/api/",
            data=json.dumps({"model": "default"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode()).get("result", [])
    except Exception:
        return [[random.randint(0, 255) for _ in range(3)] for _ in range(5)]


# 72. ASCII art text
def ascii_art(text: str) -> str:
    """Simple ASCII art using figlet-like approach (local)."""
    return text.upper()  # Placeholder -- real impl would use pyfiglet


# 73. Random name generator
def random_name(gender: str = "") -> dict | None:
    url = "https://randomuser.me/api/"
    if gender:
        url += f"?gender={gender}"
    try:
        with urlopen(Request(url), timeout=5) as r:
            data = json.loads(r.read().decode())
            user = data.get("results", [{}])[0]
            name = user.get("name", {})
            return {
                "first": name.get("first", ""),
                "last": name.get("last", ""),
                "title": name.get("title", ""),
                "country": user.get("nat", ""),
            }
    except Exception:
        return None


# 74. Emoji search (local mapping)
def emoji_for_mood(mood: str) -> str:
    moods = {
        "happy": "\U0001f60a",
        "sad": "\U0001f622",
        "angry": "\U0001f624",
        "anxious": "\U0001f630",
        "calm": "\U0001f60c",
        "love": "\u2764\ufe0f",
        "tired": "\U0001f634",
        "excited": "\U0001f389",
        "confused": "\U0001f615",
        "grateful": "\U0001f64f",
        "lonely": "\U0001f494",
        "proud": "\U0001f4aa",
        "scared": "\U0001f628",
        "peaceful": "\U0001f54a\ufe0f",
        "hopeful": "\U0001f31f",
        "bored": "\U0001f610",
    }
    return moods.get(mood.lower(), "\U0001f31f")


# 75. Daily motivation quote (from multiple sources, with fallback)
def daily_motivation() -> str:
    try:
        with urlopen(Request("https://zenquotes.io/api/today"), timeout=5) as r:
            data = json.loads(r.read().decode())
            if data:
                return f"{data[0].get('q', '')} — {data[0].get('a', '')}"
    except Exception:
        pass
    quotes = [
        "The only way out is through.",
        "This too shall pass.",
        "You are stronger than you think.",
        "One day at a time.",
        "Begin anywhere.",
    ]
    return random.choice(quotes)


def is_available() -> bool:
    return True
