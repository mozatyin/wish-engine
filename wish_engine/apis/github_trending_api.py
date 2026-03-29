"""GitHub trending. Free, no key (scrapes the page via an unofficial API)."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def trending_repos(language: str = "", since: str = "daily") -> list[dict]:
    """since: daily, weekly, monthly"""
    url = f"https://api.gitterapp.com/repositories?language={language}&since={since}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return [{"name": r.get("name", ""), "author": r.get("author", ""), "description": (r.get("description") or "")[:100], "stars": r.get("stars", 0), "language": r.get("language", ""), "url": r.get("url", "")} for r in (data if isinstance(data, list) else [])[:10]]
    except: return []

def is_available() -> bool: return True
