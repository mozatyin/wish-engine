"""Listen Notes API — podcast search. Free tier: 300 req/month."""

from __future__ import annotations
import json, os
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib.error import URLError

LN_KEY_ENV = "LISTEN_NOTES_API_KEY"
LN_URL = "https://listen-api.listennotes.com/api/v2/search"

def is_available() -> bool:
    return os.environ.get(LN_KEY_ENV) is not None

def search_podcasts(query: str, language: str = "", max_results: int = 5) -> list[dict[str, Any]]:
    """Search podcasts. Free tier: 300 req/month."""
    key = os.environ.get(LN_KEY_ENV)
    if not key:
        return []
    params = {"q": query, "type": "podcast", "page_size": max_results}
    if language: params["language"] = language
    url = f"{LN_URL}?{urlencode(params)}"
    try:
        req = Request(url, headers={"X-ListenAPI-Key": key, "Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        results = []
        for pod in data.get("results", []):
            results.append({
                "title": pod.get("title_original", ""),
                "description": (pod.get("description_original") or "")[:200],
                "publisher": pod.get("publisher_original", ""),
                "image": pod.get("image", ""),
                "listen_url": pod.get("listennotes_url", ""),
                "total_episodes": pod.get("total_episodes", 0),
                "language": pod.get("language", ""),
            })
        return results
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []
