"""Spiritual & mindfulness APIs. Free, no key or local compute."""
from __future__ import annotations
import json
import random
from urllib.request import urlopen, Request
from urllib.error import URLError


# 86. Meditation timer (local compute)
def meditation_session(duration_minutes: int = 10, style: str = "breath") -> dict:
    styles = {
        "breath": {
            "instruction": "Focus on your breath. Inhale 4 counts, exhale 6 counts.",
            "bell_intervals_min": [0, duration_minutes],
        },
        "body_scan": {
            "instruction": "Start from your toes. Slowly move attention up through your body.",
            "bell_intervals_min": [
                0,
                duration_minutes // 3,
                2 * duration_minutes // 3,
                duration_minutes,
            ],
        },
        "loving_kindness": {
            "instruction": "Send love to yourself, then someone close, then someone neutral, then someone difficult.",
            "bell_intervals_min": [
                0,
                duration_minutes // 4,
                duration_minutes // 2,
                3 * duration_minutes // 4,
                duration_minutes,
            ],
        },
        "mantra": {
            "instruction": "Repeat silently: 'I am at peace. I am enough. I am here.'",
            "bell_intervals_min": [0, duration_minutes],
        },
    }
    return {"duration_minutes": duration_minutes, **styles.get(style, styles["breath"])}


# 87. Mindfulness bell (local)
def mindfulness_reminder() -> str:
    reminders = [
        "Pause. Take three breaths. Notice where you are.",
        "What are you feeling right now? Just notice, don't judge.",
        "Drop your shoulders. Unclench your jaw. Breathe.",
        "Look around. Name one thing that's beautiful.",
        "Are you holding tension anywhere? Let it go.",
        "You are here. This moment is all there is.",
        "Place your hand on your heart. Feel it beating. You're alive.",
        "What would you tell a friend feeling what you feel right now?",
    ]
    return random.choice(reminders)


# 88. Moon phase (local astronomical calculation)
def moon_phase() -> dict:
    from datetime import datetime
    import math

    now = datetime.now()
    # Simplified calculation
    year = now.year
    month = now.month
    day = now.day
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = a // 4
    c = 2 - a + b
    e = int(365.25 * (year + 4716))
    f = int(30.6001 * (month + 1))
    jd = c + day + e + f - 1524.5
    days_since_new = (jd - 2451550.1) % 29.530588853
    phase_pct = days_since_new / 29.530588853
    if phase_pct < 0.0625:
        name = "New Moon"
    elif phase_pct < 0.1875:
        name = "Waxing Crescent"
    elif phase_pct < 0.3125:
        name = "First Quarter"
    elif phase_pct < 0.4375:
        name = "Waxing Gibbous"
    elif phase_pct < 0.5625:
        name = "Full Moon"
    elif phase_pct < 0.6875:
        name = "Waning Gibbous"
    elif phase_pct < 0.8125:
        name = "Last Quarter"
    elif phase_pct < 0.9375:
        name = "Waning Crescent"
    else:
        name = "New Moon"
    return {
        "phase": name,
        "illumination": round(abs(math.cos(phase_pct * 2 * math.pi)) * 100, 1),
        "days_since_new": round(days_since_new, 1),
    }


# 89. Daily wisdom from world traditions (local)
def daily_wisdom() -> dict:
    traditions = [
        {
            "tradition": "Buddhism",
            "text": "Pain is inevitable. Suffering is optional.",
            "source": "Haruki Murakami / Buddhist teaching",
        },
        {
            "tradition": "Stoicism",
            "text": "You have power over your mind -- not outside events. Realize this, and you will find strength.",
            "source": "Marcus Aurelius",
        },
        {
            "tradition": "Taoism",
            "text": "Nature does not hurry, yet everything is accomplished.",
            "source": "Lao Tzu",
        },
        {
            "tradition": "Islam",
            "text": "Verily, with hardship comes ease.",
            "source": "Quran 94:6",
        },
        {
            "tradition": "Christianity",
            "text": "Be still, and know that I am God.",
            "source": "Psalm 46:10",
        },
        {
            "tradition": "Hinduism",
            "text": "You have the right to work, but never to the fruit of the work.",
            "source": "Bhagavad Gita 2.47",
        },
        {
            "tradition": "Confucianism",
            "text": "It does not matter how slowly you go as long as you do not stop.",
            "source": "Confucius",
        },
        {
            "tradition": "Japanese",
            "text": "Fall seven times, stand up eight.",
            "source": "Japanese proverb",
        },
        {
            "tradition": "Arabic",
            "text": "Patience is the key to relief.",
            "source": "Arabic proverb",
        },
        {
            "tradition": "African",
            "text": "If you want to go fast, go alone. If you want to go far, go together.",
            "source": "African proverb",
        },
        {
            "tradition": "Native American",
            "text": "We do not inherit the Earth from our ancestors; we borrow it from our children.",
            "source": "Native American saying",
        },
        {
            "tradition": "Jewish",
            "text": "If I am not for myself, who will be for me? If I am only for myself, what am I?",
            "source": "Hillel",
        },
        {
            "tradition": "Chinese",
            "text": "Knowledge and action are one.",
            "source": "Wang Yangming",
        },
    ]
    return random.choice(traditions)


# 90. Compass direction from coordinates to destination (local)
def compass_direction(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> str:
    import math

    dlng = math.radians(to_lng - from_lng)
    y = math.sin(dlng) * math.cos(math.radians(to_lat))
    x = math.cos(math.radians(from_lat)) * math.sin(
        math.radians(to_lat)
    ) - math.sin(math.radians(from_lat)) * math.cos(math.radians(to_lat)) * math.cos(
        dlng
    )
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[int((bearing + 22.5) // 45) % 8]


def is_available() -> bool:
    return True
