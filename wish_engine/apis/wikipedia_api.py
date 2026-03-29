"""Wikipedia API — free summaries for any topic. No key."""
from __future__ import annotations
import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import URLError

def get_summary(topic: str, lang: str = "en") -> dict[str, Any] | None:
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(topic)}"
    try:
        req = Request(url, headers={"User-Agent": "SoulMap/1.0", "Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return {
            "title": data.get("title", ""),
            "extract": data.get("extract", "")[:500],
            "description": data.get("description", ""),
            "thumbnail": data.get("thumbnail", {}).get("source", ""),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return None

def is_available() -> bool:
    return True
