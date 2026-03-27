"""Prayer Times Calculator — pure local computation using astronomical formulas.

Calculates 5 daily Islamic prayer times from latitude, longitude, and date.
Supports 5 calculation methods: MWL, ISNA, Egypt, Makkah, Karachi.
Zero API calls required. Zero LLM.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any


# ── Calculation method parameters ─────────────────────────────────────────────
# Each method defines Fajr angle and Isha angle (or minutes after Maghrib).

METHODS: dict[str, dict[str, Any]] = {
    "MWL": {"fajr_angle": 18.0, "isha_angle": 17.0},
    "ISNA": {"fajr_angle": 15.0, "isha_angle": 15.0},
    "Egypt": {"fajr_angle": 19.5, "isha_angle": 17.5},
    "Makkah": {"fajr_angle": 18.5, "isha_minutes": 90},
    "Karachi": {"fajr_angle": 18.0, "isha_angle": 18.0},
}


def is_available() -> bool:
    """Always True — pure local computation, no API needed."""
    return True


# ── Solar calculation helpers ─────────────────────────────────────────────────


def _day_of_year(dt: datetime) -> int:
    return dt.timetuple().tm_yday


def _solar_declination(day_of_year: int) -> float:
    """Solar declination in degrees."""
    return 23.45 * math.sin(math.radians(360 / 365 * (day_of_year - 81)))


def _equation_of_time(day_of_year: int) -> float:
    """Equation of time correction in minutes."""
    b = math.radians(360 / 365 * (day_of_year - 81))
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def _hour_angle(lat: float, declination: float, angle: float) -> float:
    """Hour angle in degrees for a given sun angle below horizon."""
    lat_r = math.radians(lat)
    dec_r = math.radians(declination)
    cos_ha = (
        math.sin(math.radians(angle))
        - math.sin(lat_r) * math.sin(dec_r)
    ) / (math.cos(lat_r) * math.cos(dec_r))
    cos_ha = max(-1.0, min(1.0, cos_ha))
    return math.degrees(math.acos(cos_ha))


def _asr_hour_angle(lat: float, declination: float, shadow_factor: int = 1) -> float:
    """Hour angle for Asr prayer (Shafi'i: shadow_factor=1, Hanafi: shadow_factor=2)."""
    lat_r = math.radians(lat)
    dec_r = math.radians(declination)
    angle = math.atan(1.0 / (shadow_factor + math.tan(abs(lat_r - dec_r))))
    cos_ha = (
        math.sin(angle) - math.sin(lat_r) * math.sin(dec_r)
    ) / (math.cos(lat_r) * math.cos(dec_r))
    cos_ha = max(-1.0, min(1.0, cos_ha))
    return math.degrees(math.acos(cos_ha))


def _to_time_str(hours: float) -> str:
    """Convert decimal hours to HH:MM string."""
    hours = hours % 24
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h:02d}:{m:02d}"


# ── Main API ──────────────────────────────────────────────────────────────────


def get_prayer_times(
    lat: float,
    lng: float,
    date: datetime | None = None,
    method: str = "MWL",
) -> dict[str, str]:
    """Calculate Islamic prayer times for a location and date.

    Args:
        lat: Latitude in degrees.
        lng: Longitude in degrees.
        date: Date for calculation. Defaults to today (UTC).
        method: Calculation method — one of MWL, ISNA, Egypt, Makkah, Karachi.

    Returns:
        Dict with keys: Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha — each HH:MM.
    """
    if method not in METHODS:
        raise ValueError(f"Unknown method '{method}'. Choose from: {list(METHODS.keys())}")

    if date is None:
        date = datetime.now(timezone.utc)

    params = METHODS[method]
    doy = _day_of_year(date)
    declination = _solar_declination(doy)
    eot = _equation_of_time(doy)

    # Timezone offset: approximate from longitude (each 15° = 1 hour)
    tz_offset = lng / 15.0

    # Solar noon (Dhuhr) in approximate local time
    # UTC solar noon = 12.0 - eot/60 - lng/15
    # Local time = UTC + tz_offset = UTC + lng/15
    # So local dhuhr = 12.0 - eot/60.0 (lng terms cancel)
    dhuhr = 12.0 - eot / 60.0

    # Sunrise & Sunset (sun at -0.833° for atmospheric refraction)
    sunrise_ha = _hour_angle(lat, declination, -0.833)
    sunrise = dhuhr - sunrise_ha / 15.0
    sunset = dhuhr + sunrise_ha / 15.0  # Maghrib

    # Fajr
    fajr_ha = _hour_angle(lat, declination, -params["fajr_angle"])
    fajr = dhuhr - fajr_ha / 15.0

    # Asr (Shafi'i method: shadow = object length + noon shadow)
    asr_ha = _asr_hour_angle(lat, declination, shadow_factor=1)
    asr = dhuhr + asr_ha / 15.0

    # Isha
    if "isha_angle" in params:
        isha_ha = _hour_angle(lat, declination, -params["isha_angle"])
        isha = dhuhr + isha_ha / 15.0
    else:
        # Makkah method: fixed minutes after Maghrib
        isha = sunset + params["isha_minutes"] / 60.0

    return {
        "Fajr": _to_time_str(fajr),
        "Sunrise": _to_time_str(sunrise),
        "Dhuhr": _to_time_str(dhuhr),
        "Asr": _to_time_str(asr),
        "Maghrib": _to_time_str(sunset),
        "Isha": _to_time_str(isha),
    }


def get_next_prayer(
    lat: float,
    lng: float,
    method: str = "MWL",
) -> tuple[str, str, int]:
    """Get the next upcoming prayer.

    Returns:
        (prayer_name, time_str, minutes_until) tuple.
    """
    now = datetime.now(timezone.utc)
    tz_offset = lng / 15.0
    local_now = now + timedelta(hours=tz_offset)

    times = get_prayer_times(lat, lng, date=now, method=method)

    current_minutes = local_now.hour * 60 + local_now.minute

    prayer_order = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"]
    for name in prayer_order:
        time_str = times[name]
        h, m = map(int, time_str.split(":"))
        prayer_minutes = h * 60 + m
        if prayer_minutes > current_minutes:
            return (name, time_str, prayer_minutes - current_minutes)

    # All prayers passed today — next is tomorrow's Fajr
    fajr_str = times["Fajr"]
    h, m = map(int, fajr_str.split(":"))
    fajr_minutes = h * 60 + m
    minutes_until = (24 * 60 - current_minutes) + fajr_minutes
    return ("Fajr", fajr_str, minutes_until)


def find_nearest_mosque(lat: float, lng: float) -> dict[str, Any] | None:
    """Find nearest mosque using Google Places API if available.

    Returns None if API key is not configured.
    """
    try:
        from wish_engine.apis.places_api import search_nearby
        results = search_nearby(lat, lng, place_type="mosque", radius_km=5)
        if results:
            return results[0]
    except Exception:
        pass
    return None
