"""USGS Earthquake data. Free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def recent_earthquakes(min_magnitude: float = 4.5, limit: int = 5) -> list[dict]:
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude={min_magnitude}&limit={limit}&orderby=time"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return [{"place": f.get("properties", {}).get("place", ""), "magnitude": f.get("properties", {}).get("mag", 0), "time": f.get("properties", {}).get("time", 0), "url": f.get("properties", {}).get("url", "")} for f in data.get("features", [])[:limit]]
    except: return []

def nearby_earthquakes(lat: float, lng: float, radius_km: int = 500, days: int = 30) -> list[dict]:
    from datetime import datetime, timedelta
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lng}&maxradiuskm={radius_km}&starttime={start}&minmagnitude=2.5&limit=10"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return [{"place": f.get("properties", {}).get("place", ""), "magnitude": f.get("properties", {}).get("mag", 0)} for f in data.get("features", [])]
    except: return []

def is_available() -> bool: return True
