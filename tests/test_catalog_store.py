"""Tests for CatalogStore — unified catalog access."""

import pytest
from wish_engine.catalog_store import get_catalog, get_all_catalog_ids, search, catalog_stats


class TestGetCatalog:
    def test_food_catalog_exists(self):
        items = get_catalog("food")
        assert len(items) >= 10

    def test_suicide_prevention_exists(self):
        items = get_catalog("suicide_prevention")
        assert len(items) >= 5

    def test_places_catalog_exists(self):
        items = get_catalog("places")
        assert len(items) >= 10

    def test_unknown_returns_empty(self):
        assert get_catalog("nonexistent") == []

    def test_each_item_has_title(self):
        items = get_catalog("food")
        for item in items:
            assert "title" in item

    def test_each_item_has_category(self):
        items = get_catalog("places")
        for item in items:
            assert "category" in item


class TestGetAllIds:
    def test_has_many_catalogs(self):
        ids = get_all_catalog_ids()
        assert len(ids) >= 50

    def test_food_in_ids(self):
        assert "food" in get_all_catalog_ids()

    def test_places_in_ids(self):
        assert "places" in get_all_catalog_ids()

    def test_suicide_prevention_in_ids(self):
        assert "suicide_prevention" in get_all_catalog_ids()


class TestSearch:
    def test_keyword_search(self):
        results = search("food", ["comfort", "soup"])
        assert len(results) >= 1

    def test_no_keywords_returns_all(self):
        all_items = get_catalog("food")
        results = search("food")
        assert len(results) == len(all_items)

    def test_no_match_returns_all(self):
        results = search("food", ["xyznonexistent"])
        assert len(results) >= 1  # fallback to all

    def test_search_by_tag(self):
        results = search("food", ["halal"])
        assert len(results) >= 1

    def test_search_nonexistent_catalog(self):
        results = search("nonexistent", ["anything"])
        assert results == []


class TestStats:
    def test_stats_structure(self):
        stats = catalog_stats()
        assert "total_catalogs" in stats
        assert "total_items" in stats
        assert stats["total_catalogs"] >= 50
        assert stats["total_items"] >= 500

    def test_stats_catalogs_dict(self):
        stats = catalog_stats()
        assert "food" in stats["catalogs"]
        assert stats["catalogs"]["food"] >= 10
