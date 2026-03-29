"""Radio stations worldwide. Free, no key. radio-browser.info"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError


def search_stations(query: str = "", country: str = "", limit: int = 10) -> list[dict]:
    base = "https://de1.api.radio-browser.info/json/stations/search"
    params = []
    if query:
        params.append(f"name={query}")
    if country:
        params.append(f"country={country}")
    params.append(f"limit={limit}")
    params.append("order=clickcount")
    params.append("reverse=true")
    url = f"{base}?{'&'.join(params)}"
    try:
        with urlopen(
            Request(
                url,
                headers={"User-Agent": "SoulMap/1.0", "Accept": "application/json"},
            ),
            timeout=10,
        ) as r:
            data = json.loads(r.read().decode())
            return [
                {
                    "name": s.get("name", ""),
                    "country": s.get("country", ""),
                    "url": s.get("url_resolved", ""),
                    "tags": s.get("tags", ""),
                    "language": s.get("language", ""),
                    "codec": s.get("codec", ""),
                }
                for s in data[:limit]
            ]
    except Exception:
        return []


def stations_by_country(country: str, limit: int = 10) -> list[dict]:
    return search_stations(country=country, limit=limit)


def is_available() -> bool:
    return True
