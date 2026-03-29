"""Daily affirmations. Free, no key. affirmations.dev"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_affirmation() -> str:
    try:
        req = Request("https://www.affirmations.dev/", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode()).get("affirmation", "You are enough.")
    except: return "You are enough."

def is_available() -> bool: return True
