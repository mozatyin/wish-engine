"""REST Countries API — country info. Free, no key."""
from __future__ import annotations
import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_country(code: str) -> dict[str, Any] | None:
    url = f"https://restcountries.com/v3.1/alpha/{code.lower()}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        if data and isinstance(data, list):
            c = data[0]
            return {
                "name": c.get("name", {}).get("common", ""),
                "official_name": c.get("name", {}).get("official", ""),
                "capital": c.get("capital", [""])[0] if c.get("capital") else "",
                "languages": list(c.get("languages", {}).values()),
                "currencies": [v.get("name", "") for v in c.get("currencies", {}).values()],
                "timezone": c.get("timezones", [""])[0] if c.get("timezones") else "",
                "population": c.get("population", 0),
                "flag_emoji": c.get("flag", ""),
                "region": c.get("region", ""),
            }
        return None
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return None

def is_available() -> bool:
    return True
