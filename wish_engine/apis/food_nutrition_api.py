"""Food nutrition data from Open Food Facts.

API: https://world.openfoodfacts.org/cgi/search.pl
No auth required. Open database with 3M+ products.

Usage:
    from wish_engine.apis.food_nutrition_api import search_food, get_nutrition_summary

    items = search_food("apple", max_results=3)
    # [{"name": "Apple", "calories": 52, "protein": 0.3, ...}, ...]

    summary = get_nutrition_summary("banana")
    # {"name": "Banana", "calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3}
"""

from __future__ import annotations

import json
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote


def _http_get(url: str, timeout: int = 8) -> dict | list | None:
    try:
        req = Request(url, headers={"User-Agent": "WishEngine/1.0 (+https://soulmap.app)"})
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (URLError, json.JSONDecodeError, Exception):
        return None


def _parse_nutriments(nutriments: dict) -> dict:
    """Extract the key nutrition values per 100g."""
    def _val(key: str) -> float:
        # Try _100g suffix first, then plain key
        for k in (f"{key}_100g", key):
            v = nutriments.get(k)
            if v is not None:
                try:
                    return round(float(v), 1)
                except (TypeError, ValueError):
                    pass
        return 0.0

    return {
        "calories": _val("energy-kcal"),
        "protein":  _val("proteins"),
        "carbs":    _val("carbohydrates"),
        "fat":      _val("fat"),
        "fiber":    _val("fiber"),
        "sugar":    _val("sugars"),
        "sodium":   _val("sodium"),
    }


def search_food(query: str, max_results: int = 5) -> list[dict]:
    """Search Open Food Facts for foods matching the query.

    Args:
        query:       Search string (e.g. "apple", "whole wheat bread").
        max_results: Max items to return (1-20).

    Returns:
        List of dicts: {"name", "brand", "calories", "protein", "carbs", "fat",
                        "fiber", "sugar", "sodium", "per": "100g"}
        Empty list on network error.
    """
    max_results = max(1, min(20, max_results))
    encoded = quote(query)
    url = (
        f"https://world.openfoodfacts.org/cgi/search.pl"
        f"?search_terms={encoded}&json=1&page_size={max_results}"
        f"&fields=product_name,brands,nutriments"
    )
    data = _http_get(url)
    if not data or "products" not in data:
        return []

    results = []
    for p in data["products"][:max_results]:
        name = p.get("product_name", "").strip()
        if not name:
            continue
        n = _parse_nutriments(p.get("nutriments", {}))
        results.append({
            "name":    name,
            "brand":   p.get("brands", "").strip(),
            "per":     "100g",
            **n,
        })
    return results


def get_nutrition_summary(query: str) -> dict | None:
    """Return nutrition for the first (best-match) food found.

    Args:
        query: Food name to look up.

    Returns:
        {"name", "brand", "calories", "protein", "carbs", "fat", "fiber", "sugar", "sodium", "per"}
        or None if not found / network error.
    """
    items = search_food(query, max_results=1)
    return items[0] if items else None
