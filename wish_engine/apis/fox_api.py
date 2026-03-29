"""Random fox images. Free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def random_fox_image() -> str:
    try:
        req = Request("https://randomfox.ca/floof/", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode()).get("image", "")
    except: return ""

def is_available() -> bool: return True
