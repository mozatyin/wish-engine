"""Real recipes with steps. Free, no key. themealdb.com"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import URLError

def search_meal(name: str) -> list[dict]:
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={quote(name)}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            meals = data.get("meals") or []
            return [{"name": m.get("strMeal", ""), "category": m.get("strCategory", ""), "area": m.get("strArea", ""), "instructions": (m.get("strInstructions") or "")[:300], "thumbnail": m.get("strMealThumb", ""), "youtube": m.get("strYoutube", "")} for m in meals[:5]]
    except: return []

def random_meal() -> dict | None:
    url = "https://www.themealdb.com/api/json/v1/1/random.php"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            meals = data.get("meals") or []
            if meals:
                m = meals[0]
                return {"name": m.get("strMeal", ""), "category": m.get("strCategory", ""), "area": m.get("strArea", ""), "instructions": (m.get("strInstructions") or "")[:300], "thumbnail": m.get("strMealThumb", "")}
    except: pass
    return None

def is_available() -> bool: return True
