"""Random life advice. Free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_advice() -> str:
    try:
        req = Request("https://api.adviceslip.com/advice", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("slip", {}).get("advice", "")
    except: return ""

def search_advice(query: str) -> list[str]:
    try:
        req = Request(f"https://api.adviceslip.com/advice/search/{query}", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return [s.get("advice", "") for s in data.get("slips", [])[:5]]
    except: return []

def is_available() -> bool: return True
