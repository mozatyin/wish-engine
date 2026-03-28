"""Proactive Engine — recommends REAL things based on what's on the user's mind.

Not waiting for "I want X". Instead:
  Soul state + Location + Time → what real thing could help them right now?

Uses OSM for real places, PersonalityFilter for ranking, Compass for hidden needs.
"""

from __future__ import annotations

import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any

from wish_engine.models import DetectorResults, Recommendation, MapData
from wish_engine.apis.osm_api import search_and_enrich, nearby_events_venues
from wish_engine.l2_fulfiller import PersonalityFilter
from wish_engine.personalization import personalize_reason


@dataclass
class ProactiveRecommendation:
    """A proactive recommendation — the system initiates, not the user."""
    trigger_reason: str          # WHY this is being suggested now
    recommendation: Recommendation
    map_data: MapData | None = None
    distance_note: str = ""      # "500m from you"
    time_note: str = ""          # "Open now until 10pm"
    urgency: str = "gentle"      # "gentle" / "timely" / "urgent"


@dataclass
class DailyStar:
    """What the star map shows today — proactive, not reactive."""
    stars: list[ProactiveRecommendation] = field(default_factory=list)
    compass_whisper: str = ""    # Compass hint if any
    summary: str = ""


# ── Trigger Rules ────────────────────────────────────────────────────────────

def _check_emotional_need(det: DetectorResults) -> list[dict]:
    """What does their emotional state suggest they need?"""
    needs = []
    emotions = det.emotion.get("emotions", {})
    distress = det.emotion.get("distress", 0)

    anxiety = emotions.get("anxiety", 0)
    sadness = emotions.get("sadness", 0)
    loneliness = emotions.get("loneliness", 0)
    anger = emotions.get("anger", 0)

    if anxiety > 0.5:
        needs.append({
            "trigger": f"Your anxiety has been at {anxiety:.0%} — your mind needs a break",
            "osm_types": ["park", "garden", "library", "cafe"],
            "personality_tags": ["quiet", "calming", "nature"],
            "urgency": "timely",
        })
    if sadness > 0.5:
        needs.append({
            "trigger": "You've been carrying sadness — sometimes a change of scenery helps",
            "osm_types": ["park", "garden", "arts_centre", "museum"],
            "personality_tags": ["calming", "quiet", "nature", "art"],
            "urgency": "gentle",
        })
    if loneliness > 0.4:
        needs.append({
            "trigger": "You've been feeling alone — being around others (even strangers) can help",
            "osm_types": ["cafe", "community_centre", "library"],
            "personality_tags": ["social", "community", "calming"],
            "urgency": "gentle",
        })
    if anger > 0.5:
        needs.append({
            "trigger": "That anger needs somewhere to go — physical movement helps",
            "osm_types": ["gym", "fitness_centre", "swimming_pool", "park"],
            "personality_tags": ["exercise", "intense", "physical"],
            "urgency": "timely",
        })
    if distress > 0.7:
        needs.append({
            "trigger": "Your distress level is high — please take care of yourself right now",
            "osm_types": ["park", "place_of_worship", "library"],
            "personality_tags": ["quiet", "calming", "safe"],
            "urgency": "urgent",
        })

    return needs


def _check_time_based(hour: int, day_of_week: int) -> list[dict]:
    """What does the time suggest?"""
    needs = []

    if hour >= 6 and hour < 9:
        needs.append({
            "trigger": "Good morning — start the day with something calming",
            "osm_types": ["cafe", "park", "garden"],
            "personality_tags": ["calming", "quiet", "morning"],
            "urgency": "gentle",
        })
    elif hour >= 11 and hour < 14:
        needs.append({
            "trigger": "Lunchtime — a good meal resets the afternoon",
            "osm_types": ["restaurant", "cafe"],
            "personality_tags": ["dining", "calming"],
            "urgency": "gentle",
        })
    elif hour >= 17 and hour < 20:
        needs.append({
            "trigger": "Evening — time to decompress",
            "osm_types": ["park", "garden", "cafe", "arts_centre"],
            "personality_tags": ["calming", "nature", "quiet"],
            "urgency": "gentle",
        })

    # Weekend
    if day_of_week >= 4:  # Friday-Saturday (MENA weekend) or Saturday-Sunday
        needs.append({
            "trigger": "It's the weekend — explore something new?",
            "osm_types": ["museum", "gallery", "park", "arts_centre", "theatre"],
            "personality_tags": ["culture", "exploration", "calming"],
            "urgency": "gentle",
        })

    return needs


def _check_compass(compass_shells: list[dict]) -> list[dict]:
    """What do the hidden desires suggest?"""
    needs = []
    for shell in compass_shells:
        if shell.get("stage") in ("bud", "bloom") and shell.get("confidence", 0) > 0.5:
            topic = shell.get("topic", "")
            needs.append({
                "trigger": f"Something about '{topic}' keeps coming up in your conversations — maybe it's worth exploring",
                "osm_types": ["cafe", "park", "library"],  # generic — place to think
                "personality_tags": ["quiet", "calming", "introspective"],
                "urgency": "gentle",
            })
    return needs


def _check_values_interests(det: DetectorResults) -> list[dict]:
    """What do their values and interests suggest?"""
    needs = []
    values = det.values.get("top_values", [])

    if "tradition" in values:
        needs.append({
            "trigger": "Your values center around tradition — have you visited a spiritual place recently?",
            "osm_types": ["place_of_worship"],
            "personality_tags": ["spiritual", "traditional", "quiet"],
            "urgency": "gentle",
        })
    if "universalism" in values:
        needs.append({
            "trigger": "You care about the greater good — there might be community activities nearby",
            "osm_types": ["community_centre"],
            "personality_tags": ["community", "social", "helping"],
            "urgency": "gentle",
        })
    if "aesthetics" in values or "stimulation" in values:
        needs.append({
            "trigger": "You're a creative soul — have you checked out any art nearby?",
            "osm_types": ["arts_centre", "gallery", "museum", "theatre"],
            "personality_tags": ["art", "culture", "creative"],
            "urgency": "gentle",
        })
    if "self-direction" in values:
        needs.append({
            "trigger": "You value independence — a quiet workspace might fuel your next idea",
            "osm_types": ["cafe", "library"],
            "personality_tags": ["quiet", "productive", "autonomous"],
            "urgency": "gentle",
        })

    return needs


# ── Main Engine ──────────────────────────────────────────────────────────────

def generate_daily_stars(
    det: DetectorResults,
    lat: float,
    lng: float,
    hour: int | None = None,
    day_of_week: int | None = None,
    compass_shells: list[dict] | None = None,
    history: set[str] | None = None,
    max_stars: int = 3,
) -> DailyStar:
    """Generate proactive recommendations based on Soul + Location + Time.

    This is the core function the product calls daily (or when user opens the app).

    Args:
        det: User's 16-dimension Soul profile
        lat, lng: Current GPS coordinates
        hour: Current hour (0-23). Auto-detected if None.
        day_of_week: 0=Monday. Auto-detected if None.
        compass_shells: Compass shell summaries [{topic, stage, confidence}]
        history: Set of previously recommended titles (for dedup)
        max_stars: Max stars to generate

    Returns:
        DailyStar with proactive recommendations
    """
    now = datetime.now()
    if hour is None:
        hour = now.hour
    if day_of_week is None:
        day_of_week = now.weekday()
    if history is None:
        history = set()

    # Collect all trigger needs
    all_needs = []
    all_needs.extend(_check_emotional_need(det))
    all_needs.extend(_check_time_based(hour, day_of_week))
    all_needs.extend(_check_compass(compass_shells or []))
    all_needs.extend(_check_values_interests(det))

    # Sort by urgency: urgent > timely > gentle
    urgency_order = {"urgent": 0, "timely": 1, "gentle": 2}
    all_needs.sort(key=lambda n: urgency_order.get(n["urgency"], 2))

    # For each need, search OSM for real places
    pf = PersonalityFilter(det)
    stars = []
    used_titles = set(history)

    for need in all_needs:
        if len(stars) >= max_stars:
            break

        osm_places = search_and_enrich(lat, lng, radius_m=2000, place_types=need["osm_types"])

        if not osm_places:
            # Try wider radius
            osm_places = search_and_enrich(lat, lng, radius_m=5000, place_types=need["osm_types"])

        if not osm_places:
            continue

        # Personality filter
        ranked = pf.filter_and_rank(osm_places, max_results=3)

        for place in ranked:
            title = place.get("title", "")
            if title in used_titles:
                continue
            used_titles.add(title)

            reason = personalize_reason(
                title, place.get("tags", []), det, need["trigger"],
            )

            rec = Recommendation(
                title=title,
                description=place.get("description", ""),
                category=place.get("category", "place"),
                relevance_reason=reason,
                score=place.get("_personality_score", 0.5),
                action_url=place.get("action_url"),
                tags=place.get("tags", []),
            )

            place_lat = place.get("_lat")
            place_lng = place.get("_lng")
            dist_note = ""
            if place_lat and place_lng:
                # Rough distance in meters
                import math
                dlat = (place_lat - lat) * 111000
                dlng = (place_lng - lng) * 111000 * math.cos(math.radians(lat))
                dist_m = math.sqrt(dlat**2 + dlng**2)
                if dist_m < 1000:
                    dist_note = f"{int(dist_m)}m from you"
                else:
                    dist_note = f"{dist_m/1000:.1f}km from you"

            time_note = place.get("_opening_hours", "")

            stars.append(ProactiveRecommendation(
                trigger_reason=need["trigger"],
                recommendation=rec,
                map_data=MapData(place_type=rec.category, radius_km=2.0),
                distance_note=dist_note,
                time_note=time_note,
                urgency=need["urgency"],
            ))
            break  # One place per need

    # Compass whisper
    whisper = ""
    if compass_shells:
        bud_shells = [s for s in compass_shells if s.get("stage") in ("bud", "bloom")]
        if bud_shells:
            topic = bud_shells[0]["topic"]
            whisper = f"A distant star is flickering... something about '{topic}' keeps echoing in your conversations."

    # Summary
    if stars:
        summary = f"{len(stars)} stars lit up for you today"
    else:
        summary = "The stars are quiet today. Check back later."

    return DailyStar(stars=stars, compass_whisper=whisper, summary=summary)
