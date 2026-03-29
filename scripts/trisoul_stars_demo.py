#!/usr/bin/env python3
"""TriSoul Stars Demo: Scarlett opens SoulMap at each phase of her life.

☄️ Meteor = what she just said
⭐ Star = what she keeps talking about
🌍 Earth = what she doesn't know she wants
"""

import sys, json, re
from pathlib import Path
from collections import Counter, defaultdict
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.models import DetectorResults
from wish_engine.compass.compass import WishCompass
from wish_engine.trisoul_stars import generate_trisoul_stars, TriSoulStarMap

# Load Scarlett
with open("/Users/michael/soulgraph/fixtures/scarlett_full.jsonl") as f:
    all_d = [json.loads(l) for l in f]

phases = defaultdict(list)
for d in all_d:
    phases[d.get("chapter_phase", 0)].append(d)

# Mock OSM data (since real API is rate-limited)
MOCK_PLACES = {
    "restaurant": [
        {"title": "Noodle House", "description": "Hot noodles & comfort food", "category": "restaurant",
         "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["dining", "comfort"],
         "_lat": 25.201, "_lng": 55.271, "_opening_hours": "10am-11pm"},
    ],
    "cafe": [
        {"title": "The Reading Corner", "description": "Quiet cafe with books", "category": "cafe",
         "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "coffee", "calming", "books"],
         "_lat": 25.203, "_lng": 55.272, "_opening_hours": "7am-10pm"},
    ],
    "park": [
        {"title": "Riverside Garden", "description": "Peaceful garden by the water", "category": "park",
         "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "walking"],
         "_lat": 25.206, "_lng": 55.268},
    ],
    "library": [
        {"title": "City Library", "description": "Quiet reading rooms, free", "category": "library",
         "noise": "quiet", "social": "low", "mood": "calming", "tags": ["quiet", "reading", "calming", "free"],
         "_lat": 25.198, "_lng": 55.275, "_opening_hours": "8am-9pm"},
    ],
    "place_of_worship": [
        {"title": "Old Chapel", "description": "Historic chapel, open to all", "category": "place_of_worship",
         "noise": "quiet", "social": "low", "mood": "calming", "tags": ["spiritual", "quiet", "calming"],
         "_lat": 25.200, "_lng": 55.269},
    ],
    "gym": [
        {"title": "Iron Works Gym", "description": "Boxing, weights, CrossFit", "category": "gym",
         "noise": "loud", "social": "high", "mood": "intense", "tags": ["exercise", "intense", "fitness"],
         "_lat": 25.207, "_lng": 55.274},
    ],
    "community_centre": [
        {"title": "Community Hub", "description": "Events, classes, meetups", "category": "community_centre",
         "noise": "moderate", "social": "high", "mood": "calming", "tags": ["social", "community", "events"],
         "_lat": 25.204, "_lng": 55.270},
    ],
    "supermarket": [
        {"title": "Fresh Market", "description": "24h grocery store", "category": "supermarket",
         "noise": "moderate", "social": "medium", "mood": "calming", "tags": ["shopping", "food", "24h"],
         "_lat": 25.202, "_lng": 55.273, "_opening_hours": "24h"},
    ],
    "arts_centre": [
        {"title": "Gallery 21", "description": "Contemporary art exhibitions", "category": "arts_centre",
         "noise": "quiet", "social": "low", "mood": "calming", "tags": ["art", "quiet", "calming", "culture"],
         "_lat": 25.205, "_lng": 55.267},
    ],
    "garden": [
        {"title": "Zen Garden", "description": "Traditional meditation garden", "category": "garden",
         "noise": "quiet", "social": "low", "mood": "calming", "tags": ["nature", "quiet", "calming", "meditation"],
         "_lat": 25.199, "_lng": 55.266},
    ],
}

def mock_osm(lat, lng, radius_m=2000, place_types=None, max_results=15):
    results = []
    for pt in (place_types or MOCK_PLACES.keys()):
        if pt in MOCK_PLACES:
            results.extend(MOCK_PLACES[pt])
    return results[:max_results]


# Track history across phases
compass = WishCompass()
topic_history = Counter()

print("=" * 80)
print("☄️⭐🌍 TRISOUL STAR MAP — SCARLETT'S JOURNEY")
print("=" * 80)

with patch("wish_engine.trisoul_stars.search_and_enrich", side_effect=mock_osm):
    for phase_num in sorted(phases.keys()):
        chapter = phases[phase_num]
        recent_texts = [d["text"] for d in chapter[-5:]]  # Last 5 lines of chapter
        first_line = chapter[0]["text"][:65]

        # Update topic history from this chapter
        for d in chapter:
            text = d["text"].lower()
            if "ashley" in text or "love" in text: topic_history["love"] += 1
            if "money" in text or "dollar" in text or "hungry" in text: topic_history["money"] += 1
            if "tara" in text or "land" in text: topic_history["home"] += 1
            if "business" in text or "mill" in text or "lumber" in text: topic_history["business"] += 1
            if "child" in text or "bonnie" in text or "baby" in text: topic_history["children"] += 1
            if "war" in text or "yankee" in text: topic_history["war"] += 1
            if "mother" in text or "ellen" in text: topic_history["family"] += 1

        # Feed to Compass
        for d in chapter:
            names = set(re.findall(r'\b[A-Z][a-z]{2,}\b', d["text"])) - {'The','And','But','What','How','Why','God','Not'}
            emotion_words = ['hate','love','furious','scared','cry','want','need','angry','miss','dead','died']
            has_emo = any(w in d["text"].lower() for w in emotion_words)
            for name in names:
                if has_emo:
                    arousal = 0.5 if any(w in d["text"].lower() for w in ['hate','furious','love','cry','dead']) else 0.35
                    sentiment = 'negative' if any(w in d["text"].lower() for w in ['hate','furious','angry']) else 'mixed'
                    compass.scan(
                        topics=[{"entity": name, "sentiment": sentiment, "arousal": arousal, "mentions": 1}],
                        detector_results=DetectorResults(),
                        session_id=f"p{phase_num}_{chapter.index(d)}",
                    )

        # Generate star map
        star_map = generate_trisoul_stars(
            recent_texts=recent_texts,
            lat=25.2048, lng=55.2708,  # Dubai
            topic_history=dict(topic_history),
            compass=compass,
        )

        print(f"\n{'━' * 80}")
        print(f"Phase {phase_num}: \"{first_line}...\"")
        print(f"她最后说: \"{recent_texts[-1][:60]}...\"")
        print(f"{star_map.summary()}")

        # Meteors
        for m in star_map.meteors:
            print(f"\n  ☄️ 流星: {m.place_name}")
            print(f"     {m.why}")
            if m.distance_m:
                print(f"     📍 {m.distance_m:.0f}m | {m.opening_hours}")

        # Stars
        for s in star_map.stars:
            print(f"\n  ⭐ 星星: {s.place_name}")
            print(f"     {s.why}")
            if s.distance_m:
                print(f"     📍 {s.distance_m:.0f}m")

        # Earths
        for e in star_map.earths[:3]:  # Top 3
            print(f"\n  🌍 地球: {e.compass_topic} ({e.stage}, conf={e.confidence:.2f})")
            print(f"     {e.why}")

print(f"\n{'=' * 80}")
print("SCARLETT'S SOUL ACROSS THE WHOLE BOOK")
print(f"{'=' * 80}")
print(f"Topic history: {dict(topic_history.most_common(5))}")
compass_shells = [(s.topic, s.stage.value, round(s.confidence, 2)) for s in compass.vault.all_shells if s.confidence > 0.25]
print(f"Compass shells: {compass_shells}")
