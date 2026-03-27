"""CatalogStore — unified access to all catalog data.

Loads catalogs.json once, provides search by catalog_id + keyword.
Replaces 140 individual Python catalog variables.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_CATALOG_PATH = Path(__file__).parent / "catalogs.json"
_catalogs: dict[str, Any] | None = None


def _load():
    global _catalogs
    if _catalogs is None:
        with open(_CATALOG_PATH) as f:
            _catalogs = json.load(f)
    return _catalogs


def get_catalog(catalog_id: str) -> list[dict]:
    """Get items for a specific catalog."""
    cats = _load()
    entry = cats.get(catalog_id)
    return entry["items"] if entry else []


def get_all_catalog_ids() -> list[str]:
    """Get all available catalog IDs."""
    return list(_load().keys())


def search(catalog_id: str, keywords: list[str] | None = None) -> list[dict]:
    """Search within a catalog by keywords.

    If keywords provided, filter items where any keyword appears in
    title, description, category, or tags.
    If no keywords, return all items in the catalog.
    """
    items = get_catalog(catalog_id)
    if not keywords:
        return items

    results = []
    for item in items:
        searchable = (
            item.get("title", "").lower() + " " +
            item.get("description", "").lower() + " " +
            item.get("category", "").lower() + " " +
            " ".join(item.get("tags", []))
        ).lower()
        if any(kw.lower() in searchable for kw in keywords):
            results.append(item)

    return results if results else items  # fallback to all if no keyword match


def catalog_stats() -> dict:
    """Return stats about the catalog store."""
    cats = _load()
    return {
        "total_catalogs": len(cats),
        "total_items": sum(len(c["items"]) for c in cats.values()),
        "catalogs": {k: len(v["items"]) for k, v in cats.items()},
    }
