"""Nager.Date API — public holidays by country. Free, no key."""
from __future__ import annotations
import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_holidays(country_code: str, year: int = 2026) -> list[dict[str, Any]]:
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code.upper()}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return [{"date": h.get("date", ""), "name": h.get("localName", ""), "name_en": h.get("name", ""), "types": h.get("types", [])} for h in data] if isinstance(data, list) else []
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []

def get_next_holiday(country_code: str) -> dict[str, Any] | None:
    from datetime import date
    holidays = get_holidays(country_code)
    today = date.today().isoformat()
    future = [h for h in holidays if h["date"] >= today]
    return future[0] if future else None

def is_available() -> bool:
    return True
