"""Open Library API — free, open source. Book metadata + covers."""

from __future__ import annotations
import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib.error import URLError

SEARCH_URL = "https://openlibrary.org/search.json"

def search_books(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search Open Library. FREE, no key needed."""
    params = {"q": query, "limit": max_results, "fields": "title,author_name,first_sentence,subject,cover_i,first_publish_year,number_of_pages_median,ratings_average"}
    url = f"{SEARCH_URL}?{urlencode(params)}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        results = []
        for doc in data.get("docs", [])[:max_results]:
            cover_id = doc.get("cover_i")
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""
            first_sentence = doc.get("first_sentence", [""])[0] if doc.get("first_sentence") else ""
            results.append({
                "title": doc.get("title", ""),
                "authors": doc.get("author_name", []),
                "description": first_sentence[:200],
                "subjects": doc.get("subject", [])[:5],
                "rating": doc.get("ratings_average", 0),
                "page_count": doc.get("number_of_pages_median", 0),
                "cover_url": cover_url,
                "year": doc.get("first_publish_year", 0),
            })
        return results
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []

def is_available() -> bool:
    return True
