"""International Space Station location. Free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def iss_location() -> dict | None:
    try:
        req = Request("http://api.open-notify.org/iss-now.json")
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            pos = data.get("iss_position", {})
            return {"lat": float(pos.get("latitude", 0)), "lng": float(pos.get("longitude", 0)), "timestamp": data.get("timestamp", 0)}
    except: return None

def people_in_space() -> list[dict]:
    try:
        req = Request("http://api.open-notify.org/astros.json")
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return [{"name": p.get("name", ""), "craft": p.get("craft", "")} for p in data.get("people", [])]
    except: return []

def is_available() -> bool: return True
