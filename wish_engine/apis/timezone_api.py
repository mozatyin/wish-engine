"""World timezone. Free, no key. worldtimeapi.org"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_timezone(timezone: str = "Asia/Dubai") -> dict | None:
    url = f"http://worldtimeapi.org/api/timezone/{timezone}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {"datetime": data.get("datetime", ""), "timezone": data.get("timezone", ""), "utc_offset": data.get("utc_offset", ""), "day_of_week": data.get("day_of_week", 0)}
    except: return None

def get_ip_timezone() -> dict | None:
    """Get timezone based on caller's IP."""
    return get_timezone("ip")

def is_available() -> bool: return True
