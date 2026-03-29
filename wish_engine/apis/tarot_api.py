"""Tarot card readings. Free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def draw_cards(count: int = 3) -> list[dict]:
    url = f"https://tarotapi.dev/api/v1/cards/random?n={count}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return [{"name": c.get("name", ""), "meaning_up": c.get("meaning_up", ""), "meaning_rev": c.get("meaning_rev", ""), "desc": c.get("desc", "")[:100]} for c in data.get("cards", [])]
    except: return []

def is_available() -> bool: return True
