#!/usr/bin/env python3
"""Demo: Proactive Engine — real places based on what's on the user's mind.

Simulates 5 users in different cities at different times with different Soul states.
Shows what REAL places the system would proactively recommend.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import DetectorResults
from wish_engine.proactive_engine import generate_daily_stars

USERS = [
    {
        "name": "Scarlett in Dubai (anxious, evening)",
        "det": DetectorResults(
            emotion={"emotions": {"anxiety": 0.65, "loneliness": 0.4}, "distress": 0.5},
            mbti={"type": "ESTJ", "dimensions": {"E_I": 0.7}},
            values={"top_values": ["power", "achievement"]},
            attachment={"style": "fearful"},
        ),
        "lat": 25.2048, "lng": 55.2708,  # Dubai Downtown
        "hour": 18, "day": 4,  # Friday evening
        "compass": [{"topic": "Rhett", "stage": "bud", "confidence": 0.6}],
    },
    {
        "name": "Darcy in London (sad, morning)",
        "det": DetectorResults(
            emotion={"emotions": {"sadness": 0.6, "anxiety": 0.3}, "distress": 0.4},
            mbti={"type": "INTJ", "dimensions": {"E_I": 0.2}},
            values={"top_values": ["tradition", "achievement"]},
            attachment={"style": "avoidant"},
        ),
        "lat": 51.5074, "lng": -0.1278,  # London Central
        "hour": 8, "day": 1,  # Tuesday morning
        "compass": [{"topic": "Elizabeth", "stage": "sprout", "confidence": 0.4}],
    },
    {
        "name": "Xu Sanguan in Shenzhen (desperate, night)",
        "det": DetectorResults(
            emotion={"emotions": {"sadness": 0.7, "anxiety": 0.8}, "distress": 0.8},
            mbti={"type": "ESFJ", "dimensions": {"E_I": 0.6}},
            values={"top_values": ["security", "benevolence"]},
        ),
        "lat": 22.5431, "lng": 114.0579,  # Shenzhen
        "hour": 22, "day": 2,  # Wednesday night
        "compass": [],
    },
    {
        "name": "Anna Karenina in Milan (crisis, afternoon)",
        "det": DetectorResults(
            emotion={"emotions": {"sadness": 0.9, "anxiety": 0.8, "loneliness": 0.7}, "distress": 0.85},
            mbti={"type": "INFJ", "dimensions": {"E_I": 0.3}},
            values={"top_values": ["stimulation", "benevolence"]},
            attachment={"style": "anxious"},
        ),
        "lat": 45.4642, "lng": 9.1900,  # Milan
        "hour": 15, "day": 3,  # Thursday afternoon
        "compass": [{"topic": "Vronsky", "stage": "bloom", "confidence": 0.8}],
    },
    {
        "name": "Atticus in Nairobi (calm, weekend)",
        "det": DetectorResults(
            emotion={"emotions": {"sadness": 0.2}, "distress": 0.1},
            mbti={"type": "INFJ", "dimensions": {"E_I": 0.35}},
            values={"top_values": ["universalism", "benevolence"]},
            eq={"overall": 0.9},
        ),
        "lat": -1.2921, "lng": 36.8219,  # Nairobi
        "hour": 10, "day": 5,  # Saturday morning
        "compass": [],
    },
]


def main():
    print("=" * 80)
    print("PROACTIVE ENGINE — REAL PLACES BASED ON YOUR SOUL")
    print("What stars light up when you open the app?")
    print("=" * 80)

    for user in USERS:
        print(f"\n{'━' * 80}")
        print(f"👤 {user['name']}")

        result = generate_daily_stars(
            det=user["det"],
            lat=user["lat"],
            lng=user["lng"],
            hour=user["hour"],
            day_of_week=user["day"],
            compass_shells=user.get("compass", []),
        )

        print(f"   {result.summary}")
        if result.compass_whisper:
            print(f"   🔮 {result.compass_whisper}")

        if not result.stars:
            print("   (no OSM data returned — API may be rate-limited or location has sparse data)")
            print("   Fallback: would use catalog recommendations")
            continue

        for i, star in enumerate(result.stars, 1):
            rec = star.recommendation
            print(f"\n   ⭐ Star {i}: {rec.title}")
            print(f"      {rec.description}")
            print(f"      Why now: {star.trigger_reason}")
            print(f"      For you: {rec.relevance_reason}")
            if star.distance_note:
                print(f"      📍 {star.distance_note}")
            if star.time_note:
                print(f"      🕐 {star.time_note}")
            print(f"      [{star.urgency}]")


if __name__ == "__main__":
    main()
