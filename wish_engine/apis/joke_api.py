"""Random jokes. Free, no key. v2.jokeapi.dev"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_joke(category: str = "Any", lang: str = "en") -> dict | None:
    url = f"https://v2.jokeapi.dev/joke/{category}?lang={lang}&safe-mode"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("type") == "single":
                return {"joke": data.get("joke", ""), "category": data.get("category", "")}
            else:
                return {"joke": f"{data.get('setup', '')} — {data.get('delivery', '')}", "category": data.get("category", "")}
    except: return None

def is_available() -> bool: return True
