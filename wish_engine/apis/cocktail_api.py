"""Cocktail/drink recipes. Free, no key. thecocktaildb.com"""
from __future__ import annotations
import json
from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import URLError

def search_cocktail(name: str) -> list[dict]:
    url = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?s={quote(name)}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            drinks = data.get("drinks") or []
            return [{"name": d.get("strDrink", ""), "category": d.get("strCategory", ""), "instructions": (d.get("strInstructions") or "")[:200], "thumbnail": d.get("strDrinkThumb", ""), "alcoholic": d.get("strAlcoholic", "")} for d in drinks[:5]]
    except: return []

def random_cocktail() -> dict | None:
    try:
        req = Request("https://www.thecocktaildb.com/api/json/v1/1/random.php", headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            drinks = data.get("drinks") or []
            if drinks:
                d = drinks[0]
                return {"name": d.get("strDrink", ""), "instructions": (d.get("strInstructions") or "")[:200], "thumbnail": d.get("strDrinkThumb", "")}
    except: pass
    return None

def is_available() -> bool: return True
