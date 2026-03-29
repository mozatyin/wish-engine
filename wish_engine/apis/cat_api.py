"""Random cat images. Free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def random_cat_image() -> str:
    try:
        req = Request("https://api.thecatapi.com/v1/images/search", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data[0].get("url", "") if data else ""
    except: return ""

def cat_fact() -> str:
    try:
        req = Request("https://catfact.ninja/fact", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode()).get("fact", "")
    except: return ""

def is_available() -> bool: return True
