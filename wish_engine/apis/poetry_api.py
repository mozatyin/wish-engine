"""PoetryDB API — real English poetry. Free, no key."""
from __future__ import annotations
import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

POETRYDB_URL = "https://poetrydb.org"

def random_poem() -> dict[str, Any] | None:
    try:
        req = Request(f"{POETRYDB_URL}/random/1", headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data and isinstance(data, list):
            p = data[0]
            return {"title": p.get("title", ""), "author": p.get("author", ""), "lines": p.get("lines", []), "linecount": p.get("linecount", 0)}
        return None
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return None

def search_by_author(author: str) -> list[dict[str, Any]]:
    try:
        req = Request(f"{POETRYDB_URL}/author/{author}", headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if isinstance(data, list):
            return [{"title": p.get("title", ""), "author": p.get("author", ""), "lines": p.get("lines", [])[:10]} for p in data[:5]]
        return []
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []

def search_by_title(title: str) -> list[dict[str, Any]]:
    try:
        req = Request(f"{POETRYDB_URL}/title/{title}", headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if isinstance(data, list):
            return [{"title": p.get("title", ""), "author": p.get("author", ""), "lines": p.get("lines", [])[:10]} for p in data[:5]]
        return []
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []

def is_available() -> bool:
    return True
