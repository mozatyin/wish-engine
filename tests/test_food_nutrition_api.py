"""Tests for food_nutrition_api (Open Food Facts)."""
import json
from unittest.mock import MagicMock, patch

import pytest

from wish_engine.apis.food_nutrition_api import search_food, get_nutrition_summary


def _mock_response(mock_urlopen: MagicMock, payload: dict) -> None:
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = mock_resp


class TestSearchFood:
    def test_returns_empty_on_network_error(self):
        with patch("wish_engine.apis.food_nutrition_api.urlopen", side_effect=Exception("fail")):
            result = search_food("apple")
        assert result == []

    def test_returns_empty_on_missing_products_key(self):
        with patch("wish_engine.apis.food_nutrition_api.urlopen") as mock_u:
            _mock_response(mock_u, {})
            result = search_food("apple")
        assert result == []

    @patch("wish_engine.apis.food_nutrition_api.urlopen")
    def test_parses_basic_product(self, mock_urlopen):
        payload = {"products": [{
            "product_name": "Apple",
            "brands": "Generic",
            "nutriments": {
                "energy-kcal_100g": 52,
                "proteins_100g": 0.3,
                "carbohydrates_100g": 14.0,
                "fat_100g": 0.2,
                "fiber_100g": 2.4,
                "sugars_100g": 10.0,
                "sodium_100g": 0.001,
            },
        }]}
        _mock_response(mock_urlopen, payload)
        results = search_food("apple")
        assert len(results) == 1
        item = results[0]
        assert item["name"] == "Apple"
        assert item["brand"] == "Generic"
        assert item["calories"] == pytest.approx(52)
        assert item["protein"] == pytest.approx(0.3, abs=0.01)
        assert item["per"] == "100g"

    @patch("wish_engine.apis.food_nutrition_api.urlopen")
    def test_max_results_respected(self, mock_urlopen):
        products = [{"product_name": f"Food {i}", "nutriments": {}} for i in range(10)]
        _mock_response(mock_urlopen, {"products": products})
        results = search_food("food", max_results=3)
        assert len(results) <= 3

    @patch("wish_engine.apis.food_nutrition_api.urlopen")
    def test_skips_products_without_name(self, mock_urlopen):
        payload = {"products": [
            {"product_name": "", "nutriments": {}},
            {"product_name": "Banana", "nutriments": {"energy-kcal_100g": 89}},
        ]}
        _mock_response(mock_urlopen, payload)
        results = search_food("banana")
        assert len(results) == 1
        assert results[0]["name"] == "Banana"

    @patch("wish_engine.apis.food_nutrition_api.urlopen")
    def test_missing_nutriments_returns_zeros(self, mock_urlopen):
        payload = {"products": [{"product_name": "Mystery", "nutriments": {}}]}
        _mock_response(mock_urlopen, payload)
        results = search_food("mystery")
        assert results[0]["calories"] == 0.0
        assert results[0]["protein"] == 0.0

    @patch("wish_engine.apis.food_nutrition_api.urlopen")
    def test_required_fields_always_present(self, mock_urlopen):
        payload = {"products": [{"product_name": "Test", "nutriments": {}}]}
        _mock_response(mock_urlopen, payload)
        results = search_food("test")
        required = {"name", "brand", "per", "calories", "protein", "carbs", "fat", "fiber", "sugar", "sodium"}
        assert required.issubset(results[0].keys())


class TestGetNutritionSummary:
    @patch("wish_engine.apis.food_nutrition_api.urlopen")
    def test_returns_first_item(self, mock_urlopen):
        payload = {"products": [
            {"product_name": "Banana", "nutriments": {"energy-kcal_100g": 89}},
            {"product_name": "Banana Chips", "nutriments": {"energy-kcal_100g": 519}},
        ]}
        _mock_response(mock_urlopen, payload)
        result = get_nutrition_summary("banana")
        assert result is not None
        assert result["name"] == "Banana"

    def test_returns_none_on_no_results(self):
        with patch("wish_engine.apis.food_nutrition_api.urlopen", side_effect=Exception("fail")):
            result = get_nutrition_summary("nonexistent_xyz_food")
        assert result is None
