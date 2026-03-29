"""Location-related APIs. All free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError


# 76. What3words alternative -- coordinate to readable location
def coords_to_description(lat: float, lng: float) -> str:
    """Rough human-readable location description."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&zoom=14"
        with urlopen(
            Request(url, headers={"User-Agent": "SoulMap/1.0"}), timeout=5
        ) as r:
            data = json.loads(r.read().decode())
            return data.get("display_name", f"{lat:.3f}, {lng:.3f}")
    except Exception:
        return f"{lat:.3f}, {lng:.3f}"


# 77. Distance between two points (local compute)
def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance in km between two GPS points."""
    import math

    R = 6371  # Earth radius km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


# 78. Timezone offset from coordinates (using open meteo)
def timezone_from_coords(lat: float, lng: float) -> str:
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&timezone=auto&forecast_days=1"
        with urlopen(Request(url), timeout=5) as r:
            return json.loads(r.read().decode()).get("timezone", "")
    except Exception:
        return ""


# 79. Elevation from coordinates
def get_elevation(lat: float, lng: float) -> float | None:
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lng}"
        with urlopen(Request(url), timeout=5) as r:
            data = json.loads(r.read().decode())
            elevations = data.get("elevation", [])
            return elevations[0] if elevations else None
    except Exception:
        return None


# 80. Nearby public wifi (from OSM)
def nearby_wifi(lat: float, lng: float, radius_m: int = 1000) -> list[dict]:
    from wish_engine.apis.osm_api import nearby_places

    places = nearby_places(lat, lng, radius_m, ["cafe", "library", "community_centre"])
    # Libraries and cafes typically have wifi
    return [
        {
            "name": p.get("name", ""),
            "type": p.get("category", ""),
            "lat": p.get("lat"),
            "lng": p.get("lng"),
        }
        for p in places
        if p.get("name")
    ]


def is_available() -> bool:
    return True
