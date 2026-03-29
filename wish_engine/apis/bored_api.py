"""Random activity suggestions. Free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_activity(activity_type: str = "") -> dict | None:
    url = "https://bored-api.appbrewery.com/random"
    if activity_type: url = f"https://bored-api.appbrewery.com/filter?type={activity_type}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, list): data = data[0] if data else {}
            return {"activity": data.get("activity", ""), "type": data.get("type", ""), "participants": data.get("participants", 1)}
    except: return None

def is_available() -> bool: return True
