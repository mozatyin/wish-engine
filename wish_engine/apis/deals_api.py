"""Deals/Discount Aggregator API — multi-source deal discovery.

Falls back gracefully when API keys are unavailable.
Zero LLM.
"""

from __future__ import annotations

import os
from typing import Any


# ── API key env vars ──────────────────────────────────────────────────────────

DEALS_KEY_ENV = "DEALS_API_KEY"


def is_available() -> bool:
    """Check if any deals API is configured."""
    return bool(os.environ.get(DEALS_KEY_ENV))


def search_deals(
    lat: float,
    lng: float,
    category: str | None = None,
    keyword: str | None = None,
    max_results: int = 20,
) -> list[dict[str, Any]]:
    """Search for deals from configured API sources.

    Args:
        lat: Latitude.
        lng: Longitude.
        category: Deal category filter (e.g. "dining", "learning").
        keyword: Keyword search term.
        max_results: Maximum number of results.

    Returns:
        List of normalized deal dicts. Empty list if no API configured.
    """
    if not is_available():
        return []

    # Placeholder for real API integration
    # In production, this would call actual deal aggregation APIs
    return []


def normalize_deal(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw deal from any source into standard format.

    Standard format:
        {name, description, discount_pct, original_price, deal_price,
         store, url, category, expiry}
    """
    return {
        "name": raw.get("name", raw.get("title", "")),
        "description": raw.get("description", ""),
        "discount_pct": raw.get("discount_pct", raw.get("discount", 0)),
        "original_price": raw.get("original_price", 0),
        "deal_price": raw.get("deal_price", raw.get("price", 0)),
        "store": raw.get("store", raw.get("merchant", "")),
        "url": raw.get("url", raw.get("link", "")),
        "category": raw.get("category", "general"),
        "expiry": raw.get("expiry", raw.get("expires_at", "")),
    }
