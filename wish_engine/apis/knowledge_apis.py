"""Knowledge & learning APIs. All free, no key."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError


# 56. Project Gutenberg — free ebooks
def search_books_gutenberg(query: str, max_results: int = 5) -> list[dict]:
    url = f"https://gutendex.com/books/?search={query}"
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=10) as r:
            data = json.loads(r.read().decode())
            return [
                {
                    "title": b.get("title", ""),
                    "authors": [a.get("name", "") for a in b.get("authors", [])],
                    "subjects": b.get("subjects", [])[:3],
                    "download_count": b.get("download_count", 0),
                    "formats": {
                        k: v
                        for k, v in b.get("formats", {}).items()
                        if "text/html" in k or "epub" in k
                    },
                }
                for b in data.get("results", [])[:max_results]
            ]
    except Exception:
        return []


# 57. Random Wikipedia article
def random_wikipedia() -> dict | None:
    try:
        with urlopen(
            Request(
                "https://en.wikipedia.org/api/rest_v1/page/random/summary",
                headers={"User-Agent": "SoulMap/1.0"},
            ),
            timeout=5,
        ) as r:
            data = json.loads(r.read().decode())
            return {
                "title": data.get("title", ""),
                "extract": data.get("extract", "")[:300],
                "url": data.get("content_urls", {})
                .get("desktop", {})
                .get("page", ""),
            }
    except Exception:
        return None


# 58. This Day in History
def today_in_history() -> list[dict]:
    from datetime import datetime

    month = datetime.now().month
    day = datetime.now().day
    url = f"https://history.muffinlabs.com/date/{month}/{day}"
    try:
        with urlopen(
            Request(url, headers={"Accept": "application/json"}), timeout=10
        ) as r:
            data = json.loads(r.read().decode())
            events = data.get("data", {}).get("Events", [])[:5]
            return [{"year": e.get("year", ""), "text": e.get("text", "")} for e in events]
    except Exception:
        return []


# 59. Country data by name (alternative to REST Countries)
def country_by_name(name: str) -> dict | None:
    try:
        url = f"https://restcountries.com/v3.1/name/{name}?fullText=false"
        with urlopen(
            Request(url, headers={"Accept": "application/json"}), timeout=5
        ) as r:
            data = json.loads(r.read().decode())
            if data and isinstance(data, list):
                c = data[0]
                return {
                    "name": c.get("name", {}).get("common", ""),
                    "capital": (c.get("capital") or [""])[0],
                    "population": c.get("population", 0),
                    "languages": list(c.get("languages", {}).values()),
                    "flag": c.get("flag", ""),
                }
    except Exception:
        pass
    return None


# 60. Random fun fact
def random_fun_fact() -> str:
    try:
        with urlopen(
            Request(
                "https://uselessfacts.jsph.pl/api/v2/facts/random",
                headers={"Accept": "application/json"},
            ),
            timeout=5,
        ) as r:
            return json.loads(r.read().decode()).get("text", "")
    except Exception:
        return ""


def is_available() -> bool:
    return True
