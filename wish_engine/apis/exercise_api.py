"""Exercise database. Free, no key for basic. exercisedb on GitHub."""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

# Using the free wger API (no key, open source)
WGER_URL = "https://wger.de/api/v2"

def search_exercises(term: str = "", language: int = 2, limit: int = 10) -> list[dict]:
    """Search exercises. language: 2=English."""
    url = f"{WGER_URL}/exercise/search/?term={term}&language={language}&format=json"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return [{"name": e.get("name", ""), "category": e.get("category", ""), "id": e.get("id")} for e in data.get("suggestions", [])[:limit]]
    except: return []

def get_exercise(exercise_id: int) -> dict | None:
    url = f"{WGER_URL}/exerciseinfo/{exercise_id}/?format=json"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {"name": data.get("name", ""), "description": (data.get("description") or "")[:200], "muscles": [m.get("name_en", "") for m in data.get("muscles", [])], "equipment": [e.get("name", "") for e in data.get("equipment", [])]}
    except: return None

def is_available() -> bool: return True
