"""Currency exchange rates. Free, no key. frankfurter.app"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_rate(base: str = "USD", target: str = "EUR") -> float | None:
    url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("rates", {}).get(target)
    except: return None

def get_rates(base: str = "USD") -> dict:
    url = f"https://api.frankfurter.app/latest?from={base}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode()).get("rates", {})
    except: return {}

def is_available() -> bool: return True
