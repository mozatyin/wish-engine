"""Free transit API — zero API key required.

Sources:
  - OSM Overpass API: find nearby transit stops (bus, subway, tram, rail)
  - OSRM public demo: routing directions (foot / bike / car)
  - Haversine: fallback distance calculation when OSRM unavailable

Usage:
    from wish_engine.apis.free_transit_api import find_nearest_stops, route_summary

    stops = find_nearest_stops(51.5074, -0.1278, radius_m=400)
    # [{"name": "Baker Street", "type": "subway_entrance", "distance_m": 230}, ...]

    route = route_summary(51.5074, -0.1278, 51.515, -0.085)
    # {"distance_km": 8.3, "duration_min": 100, "mode": "foot-walking", "source": "osrm"}
"""

from __future__ import annotations

import json
import math
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote


# ── Haversine ─────────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _http_get(url: str, timeout: int = 10) -> dict | list | None:
    try:
        req = Request(url, headers={"User-Agent": "WishEngine/1.0 (+https://soulmap.app)"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (URLError, json.JSONDecodeError, Exception):
        return None


# ── OSM Overpass — transit stops ──────────────────────────────────────────────

# Node types that represent public-transit boarding points
_TRANSIT_TYPES = [
    "bus_stop",
    "subway_entrance",
    "train_station",
    "tram_stop",
    "ferry_terminal",
    "aerodrome",          # not really transit but requested sometimes
    "halt",
    "stop_position",
]


def find_nearest_stops(
    lat: float,
    lng: float,
    radius_m: int = 500,
    max_results: int = 5,
) -> list[dict]:
    """Find nearby public-transit stops via OSM Overpass API.

    Args:
        lat:        Latitude of current location.
        lng:        Longitude of current location.
        radius_m:   Search radius in metres (default 500).
        max_results: Maximum stops to return.

    Returns:
        List of dicts sorted by distance:
          {"name": str, "type": str, "lat": float, "lng": float, "distance_m": float}
        Empty list on network error or no stops found.
    """
    radius_m = max(50, min(5000, radius_m))
    # Build union query for all transit node types
    node_queries = "\n".join(
        f'  node["{("railway" if t in ("train_station","halt","stop_position","tram_stop") else "public_transport" if t in ("stop_position","station") else "highway" if t == "bus_stop" else "railway" if t == "subway_entrance" else "amenity")}"="{t}"](around:{radius_m},{lat},{lng});'
        for t in _TRANSIT_TYPES[:4]  # keep query short
    )
    # Simplified but robust Overpass query
    overpass_query = f"""[out:json][timeout:10];
(
  node["highway"="bus_stop"](around:{radius_m},{lat},{lng});
  node["public_transport"="stop_position"](around:{radius_m},{lat},{lng});
  node["railway"="station"](around:{radius_m},{lat},{lng});
  node["railway"="subway_entrance"](around:{radius_m},{lat},{lng});
  node["railway"="tram_stop"](around:{radius_m},{lat},{lng});
  node["railway"="halt"](around:{radius_m},{lat},{lng});
);
out body;"""

    encoded = quote(overpass_query)
    url = f"https://overpass-api.de/api/interpreter?data={encoded}"
    data = _http_get(url, timeout=12)
    if not data or "elements" not in data:
        return []

    stops = []
    for el in data["elements"]:
        if el.get("type") != "node":
            continue
        tags = el.get("tags", {})
        name = (
            tags.get("name")
            or tags.get("ref")
            or tags.get("local_ref")
            or tags.get("public_transport")
            or tags.get("highway")
            or tags.get("railway")
            or "Stop"
        )
        stop_type = (
            tags.get("public_transport")
            or tags.get("highway")
            or tags.get("railway")
            or "stop"
        )
        stop_lat, stop_lng = el.get("lat", lat), el.get("lon", lng)
        dist_m = _haversine_km(lat, lng, stop_lat, stop_lng) * 1000
        stops.append({
            "name":       name,
            "type":       stop_type,
            "lat":        stop_lat,
            "lng":        stop_lng,
            "distance_m": round(dist_m, 0),
        })

    stops.sort(key=lambda s: s["distance_m"])
    return stops[:max_results]


# ── OSRM public demo — routing ─────────────────────────────────────────────────

_OSRM_PROFILES = {
    "foot-walking": "foot",
    "walking":      "foot",
    "foot":         "foot",
    "cycling":      "bike",
    "bike":         "bike",
    "driving":      "car",
    "car":          "car",
}


def route_summary(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    mode: str = "foot-walking",
) -> dict:
    """Get a walking/cycling/driving route summary.

    Uses OSRM public demo server (router.project-osrm.org).
    Falls back to haversine straight-line distance if OSRM is unavailable.

    Args:
        origin_lat, origin_lng: Start coordinates.
        dest_lat,   dest_lng:   End coordinates.
        mode: One of "foot-walking", "cycling", "driving" (default "foot-walking").

    Returns:
        {
          "distance_km":  float,
          "duration_min": float,
          "mode":         str,
          "source":       "osrm" | "haversine",
        }
    """
    profile = _OSRM_PROFILES.get(mode.lower(), "foot")
    url = (
        f"http://router.project-osrm.org/route/v1/{profile}/"
        f"{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
        f"?overview=false"
    )
    data = _http_get(url)
    if data and data.get("code") == "Ok" and data.get("routes"):
        route = data["routes"][0]
        distance_km = round(route["distance"] / 1000, 2)
        duration_min = round(route["duration"] / 60, 1)
        return {
            "distance_km":  distance_km,
            "duration_min": duration_min,
            "mode":         mode,
            "source":       "osrm",
        }

    # Haversine fallback — straight-line with speed estimate
    _SPEED_KMH = {"foot": 5, "bike": 15, "car": 50}
    km = _haversine_km(origin_lat, origin_lng, dest_lat, dest_lng)
    spd = _SPEED_KMH.get(profile, 5)
    return {
        "distance_km":  round(km, 2),
        "duration_min": round(km / spd * 60, 1),
        "mode":         mode,
        "source":       "haversine",
    }
