"""Open Food Facts API — nutrition, allergens, ingredients. Free, no key."""
from __future__ import annotations
import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

def get_product(barcode: str) -> dict[str, Any] | None:
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        req = Request(url, headers={"User-Agent": "SoulMap/1.0", "Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        p = data.get("product", {})
        if not p: return None
        return {
            "name": p.get("product_name", ""),
            "brands": p.get("brands", ""),
            "categories": p.get("categories", ""),
            "allergens": p.get("allergens_tags", []),
            "nutriscore": p.get("nutriscore_grade", ""),
            "ingredients": (p.get("ingredients_text") or "")[:200],
            "image_url": p.get("image_url", ""),
        }
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return None

def search_products(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={query}&json=1&page_size={max_results}"
    try:
        req = Request(url, headers={"User-Agent": "SoulMap/1.0", "Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return [{"name": p.get("product_name", ""), "brands": p.get("brands", ""), "nutriscore": p.get("nutriscore_grade", ""), "allergens": p.get("allergens_tags", [])} for p in data.get("products", [])[:max_results]]
    except (URLError, json.JSONDecodeError, OSError, TimeoutError):
        return []

def is_available() -> bool:
    return True
