"""Random dog images for mood boost. Free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def random_dog_image() -> str:
    try:
        req = Request("https://dog.ceo/api/breeds/image/random", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode()).get("message", "")
    except: return ""

def random_dog_by_breed(breed: str) -> str:
    try:
        req = Request(f"https://dog.ceo/api/breed/{breed}/images/random", headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode()).get("message", "")
    except: return ""

def is_available() -> bool: return True
