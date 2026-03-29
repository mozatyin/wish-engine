"""Google Books API — free, no key needed. Search books worldwide."""

from __future__ import annotations
import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib.error import URLError

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"

def search_books(query: str, max_results: int = 10, lang: str = "") -> list[dict[str, Any]]:
    """Search Google Books. FREE, no API key needed."""
    params = {"q": query, "maxResults": max_results, "printType": "books"}
    if lang:
        params["langRestrict"] = lang
    url = f"{GOOGLE_BOOKS_URL}?{urlencode(params)}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        results = []
        for item in data.get("items", []):
            info = item.get("volumeInfo", {})
            results.append({
                "title": info.get("title", ""),
                "authors": info.get("authors", []),
                "description": (info.get("description") or "")[:200],
                "categories": info.get("categories", []),
                "rating": info.get("averageRating", 0),
                "page_count": info.get("pageCount", 0),
                "thumbnail": info.get("imageLinks", {}).get("thumbnail", ""),
                "preview_link": info.get("previewLink", ""),
                "language": info.get("language", ""),
                "published": info.get("publishedDate", ""),
            })
        return results
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []

def is_available() -> bool:
    return True  # Always free, no key needed
