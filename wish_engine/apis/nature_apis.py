"""Nature & animal APIs. All free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError


# 51. Random bird image
def random_bird_image() -> str:
    try:
        with urlopen(Request("https://shibe.online/api/birds?count=1"), timeout=5) as r:
            data = json.loads(r.read().decode())
            return data[0] if data else ""
    except Exception:
        return ""


# 52. Random shiba image
def random_shiba_image() -> str:
    try:
        with urlopen(Request("https://shibe.online/api/shibes?count=1"), timeout=5) as r:
            data = json.loads(r.read().decode())
            return data[0] if data else ""
    except Exception:
        return ""


# 53. Dog breed info
def dog_breeds() -> list[str]:
    try:
        with urlopen(Request("https://dog.ceo/api/breeds/list/all"), timeout=5) as r:
            data = json.loads(r.read().decode())
            return list(data.get("message", {}).keys())
    except Exception:
        return []


# 54. Random duck image
def random_duck_image() -> str:
    try:
        with urlopen(Request("https://random-d.uk/api/v2/random"), timeout=5) as r:
            return json.loads(r.read().decode()).get("url", "")
    except Exception:
        return ""


# 55. Random inspirational image (picsum)
def random_nature_image(width: int = 800, height: int = 600) -> str:
    return f"https://picsum.photos/{width}/{height}"


def is_available() -> bool:
    return True
