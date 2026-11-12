import os

import pytest

from app.core.exceptions import ProviderNotConfiguredError
from app.nutrition.matching import (
    MINIMUM_SCORE,
    best_match,
    normalize_query,
    score_candidate
)
from app.nutrition.providers.gemini import NutritionResult
from app.nutrition.providers.open_food_facts import (
    search_food as search_off_food
)
from app.nutrition.providers.usda import search_food as search_usda_food
from app.nutrition.service import search_food


MIXED_DISH_RESPONSE = {
    "name": "Chicken Biryani",
    "quantity_grams": 300.0,
    "meat_weight_grams": 150.0,
    "calories": 596.0,
    "protein": 44.3,
    "carbohydrates": 41.6,
    "fats": 27.1,
    "estimate": True,
    "components": [
        {"name": "Chicken (cooked)", "grams": 150.0, "calories": 285.0,
         "protein": 40.0, "carbohydrates": 0.0, "fats": 13.5},
        {"name": "Cooked basmati rice", "grams": 130.0, "calories": 169.0,
         "protein": 3.5, "carbohydrates": 41.0, "fats": 0.4},
        {"name": "Oil, fried onion & spices", "grams": 20.0, "calories": 142.0,
         "protein": 0.8, "carbohydrates": 0.6, "fats": 13.2},
    ],
}


# ---------------------------------------------------------------------------
# Matching / ranking
# ---------------------------------------------------------------------------

def test_normalize_query_collapses_whitespace():
    assert normalize_query("  chicken   biryani ") == "chicken biryani"
    assert normalize_query(None) == ""
    assert normalize_query("   ") == ""


def test_plain_food_outscores_prepared_dish():
    plain = score_candidate("eggs", "Egg, whole, raw, fresh")
    prepared = score_candidate("eggs", "Egg custard, baked")

    assert plain > prepared
    assert plain > MINIMUM_SCORE


def test_scoring_handles_case_and_plurals():
    assert score_candidate("EGGS", "egg") > MINIMUM_SCORE
    assert score_candidate("apples", "Apples, raw, with skin") > MINIMUM_SCORE


def test_scoring_handles_close_spelling_variants():
    assert score_candidate("yoghurt", "Yogurt, plain") > MINIMUM_SCORE


def test_unrelated_food_scores_below_minimum():
    assert score_candidate("eggs", "Chicken biryani") < MINIMUM_SCORE


def test_single_ingredient_does_not_stand_in_for_prepared_dish():
    # Plain chicken must not be silently returned for a biryani search.
    assert score_candidate("chicken biryani", "Chicken, raw") < MINIMUM_SCORE


def test_best_match_picks_exact_dish():
    names = [
        "Egg, whole, raw, fresh",
        "Egg custard, baked",
        "Egg salad",
    ]

    assert best_match("egg custard", names, get_name=str) == "Egg custard, baked"


def test_best_match_prefers_preparation_method():
    names = [
        "Egg custard, baked",
        "Eggs, scrambled, frozen mixture",
        "Egg, whole, cooked, hard-boiled",
    ]

    assert best_match("boiled eggs", names, get_name=str) == (
        "Egg, whole, cooked, hard-boiled"
    )


def test_best_match_returns_none_when_nothing_relevant():
    assert best_match("rice", ["Egg custard, baked"], get_name=str) is None


def test_best_match_prefers_plain_grain_over_dish():
    names = [
        "Rice bowl with chicken",
        "Fried rice",
        "Rice, white, long-grain, regular, cooked",
        "Rice cake",
    ]

    assert best_match("rice", names, get_name=str) == (
        "Rice, white, long-grain, regular, cooked"
    )
    assert best_match("fried rice", names, get_name=str) == "Fried rice"


def test_best_match_ignores_numbers_and_compound_words():
    names = [
        "Milk chocolate",
        "Milkshake",
        "Milk, whole, 3.25% milkfat",
    ]

    assert best_match("milk", names, get_name=str) == (
        "Milk, whole, 3.25% milkfat"
    )


# ---------------------------------------------------------------------------
# USDA provider
# ---------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


EGGS_USDA_PAYLOAD = {
    "foods": [
        {
            # USDA's first hit for "eggs" can be a prepared dish - the
            # provider must rank past it.
            "description": "Egg custard, baked",
            "dataType": "Survey (FNDDS)",
            "foodNutrients": [
                {"nutrientName": "Energy", "unitName": "KCAL", "value": 112},
                {"nutrientName": "Protein", "unitName": "G", "value": 5.0},
            ],
        },
        {
            "description": "Eggs, Grade A, Large, egg whole",
            "dataType": "Foundation",
            "foodNutrients": [
                # kJ listed before kcal: the kJ value must never be
                # reported as calories.
                {"nutrientName": "Energy", "unitName": "kJ", "value": 620},
                {"nutrientName": "Energy", "unitName": "KCAL", "value": 148},
                {"nutrientName": "Protein", "unitName": "G", "value": 12.4},
                {"nutrientName": "Carbohydrate, by difference",
                 "unitName": "G", "value": 0.96},
                {"nutrientName": "Total lipid (fat)",
                 "unitName": "G", "value": 9.96},
            ],
        },
    ]
}


def _mock_usda(monkeypatch, payload):
    monkeypatch.setenv("USDA_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.nutrition.providers.usda.requests.get",
        lambda *args, **kwargs: FakeResponse(payload)
    )


def test_usda_prefers_plain_eggs_over_egg_custard(monkeypatch):
    _mock_usda(monkeypatch, EGGS_USDA_PAYLOAD)

    food = search_usda_food("eggs")

    assert food is not None
    assert "custard" not in food["name"].lower()
    assert food["calories"] == 148
    assert food["protein"] == 12.4
    assert food["carbohydrates"] == 0.96
    assert food["fats"] == 9.96
    assert food["serving_size"] == 100


def test_usda_still_returns_prepared_dish_when_asked(monkeypatch):
    _mock_usda(monkeypatch, EGGS_USDA_PAYLOAD)

    food = search_usda_food("egg custard")

    assert food is not None
    assert food["name"] == "Egg custard, baked"
    assert food["calories"] == 112


def test_usda_prefers_boiled_eggs(monkeypatch):
    _mock_usda(monkeypatch, {
        "foods": [
            {
                "description": "Egg custard, baked",
                "dataType": "Survey (FNDDS)",
                "foodNutrients": [
                    {"nutrientName": "Energy", "unitName": "KCAL",
                     "value": 112},
                ],
            },
            {
                "description": "Egg, whole, cooked, hard-boiled",
                "dataType": "SR Legacy",
                "foodNutrients": [
                    {"nutrientName": "Energy", "unitName": "KCAL",
                     "value": 155},
                ],
            },
        ]
    })

    food = search_usda_food("boiled eggs")

    assert food is not None
    assert food["name"] == "Egg, whole, cooked, hard-boiled"
    assert food["calories"] == 155


def test_usda_returns_none_for_irrelevant_results(monkeypatch):
    _mock_usda(monkeypatch, EGGS_USDA_PAYLOAD)

    assert search_usda_food("rice") is None


def test_usda_returns_none_for_empty_results(monkeypatch):
    _mock_usda(monkeypatch, {"foods": []})

    assert search_usda_food("eggs") is None


def test_usda_requires_api_key(monkeypatch):
    monkeypatch.delenv("USDA_API_KEY", raising=False)

    with pytest.raises(ProviderNotConfiguredError):
        search_usda_food("eggs")


# ---------------------------------------------------------------------------
# Open Food Facts provider
# ---------------------------------------------------------------------------

def _mock_off(monkeypatch, payload):
    monkeypatch.setattr(
        "app.nutrition.providers.open_food_facts.requests.get",
        lambda *args, **kwargs: FakeResponse(payload)
    )


def test_off_ranks_products_and_normalizes_result(monkeypatch):
    _mock_off(monkeypatch, {
        "products": [
            # No name: must be skipped, not returned as "".
            {"nutriments": {"energy-kcal_100g": 500}},
            {
                "product_name": "Egg custard dessert",
                "nutriments": {"energy-kcal_100g": 120},
            },
            {
                "product_name": "Fresh eggs",
                "nutriments": {
                    "energy-kcal_100g": 140,
                    "proteins_100g": 12.5,
                    "carbohydrates_100g": 0.7,
                    "fat_100g": 9.5,
                },
            },
            # No calorie data: useless for a calorie tracker.
            {"product_name": "Eggs premium pack", "nutriments": {}},
        ]
    })

    food = search_off_food("eggs")

    assert food is not None
    assert food["name"] == "Fresh eggs"
    assert food["calories"] == 140
    assert food["protein"] == 12.5
    assert food["carbohydrates"] == 0.7
    assert food["fats"] == 9.5
    assert food["serving_unit"] == "g"


def test_off_returns_none_for_irrelevant_products(monkeypatch):
    _mock_off(monkeypatch, {
        "products": [
            {
                "product_name": "Chocolate hazelnut spread",
                "nutriments": {"energy-kcal_100g": 539},
            },
        ]
    })

    assert search_off_food("eggs") is None


# ---------------------------------------------------------------------------
# Search service (provider order, fallback, error handling)
# ---------------------------------------------------------------------------

def _raise_not_configured(*args, **kwargs):
    raise ProviderNotConfiguredError("provider is not configured")


def test_search_prefers_gemini_and_passes_quantities(monkeypatch):
    captured = {}

    def fake_gemini(food_name, quantity_grams=None, meat_weight_grams=None):
        captured["food_name"] = food_name
        captured["quantity_grams"] = quantity_grams
        captured["meat_weight_grams"] = meat_weight_grams
        return MIXED_DISH_RESPONSE

    monkeypatch.setattr(
        "app.nutrition.service.get_nutrition_from_gemini", fake_gemini
    )
    monkeypatch.setattr(
        "app.nutrition.service.search_usda_food", _raise_not_configured
    )

    result = search_food("chicken biryani", 300, 150)

    assert result["source"] == "gemini"
    assert result["food"]["name"] == "Chicken Biryani"
    assert result["food"]["meat_weight_grams"] == 150
    assert captured == {
        "food_name": "chicken biryani",
        "quantity_grams": 300,
        "meat_weight_grams": 150,
    }


def test_search_falls_back_to_usda_when_gemini_fails(monkeypatch):
    monkeypatch.setattr(
        "app.nutrition.service.get_nutrition_from_gemini",
        _raise_not_configured
    )
    monkeypatch.setattr(
        "app.nutrition.service.search_usda_food",
        lambda food_name: {"name": "Egg, whole, raw", "calories": 143}
    )

    result = search_food("eggs")

    assert result["source"] == "usda"
    assert result["food"]["name"] == "Egg, whole, raw"


def test_search_falls_through_irrelevant_usda_to_off(monkeypatch):
    # USDA finding nothing relevant must not block a better match from
    # Open Food Facts.
    monkeypatch.setattr(
        "app.nutrition.service.get_nutrition_from_gemini",
        _raise_not_configured
    )
    monkeypatch.setattr(
        "app.nutrition.service.search_usda_food",
        lambda food_name: None
    )
    monkeypatch.setattr(
        "app.nutrition.service.search_off_food",
        lambda food_name: {"name": "Fresh eggs", "calories": 140}
    )

    result = search_food("eggs")

    assert result["source"] == "open_food_facts"
    assert result["food"]["name"] == "Fresh eggs"


def test_search_survives_all_providers_failing(monkeypatch):
    monkeypatch.setattr(
        "app.nutrition.service.get_nutrition_from_gemini",
        _raise_not_configured
    )
    monkeypatch.setattr(
        "app.nutrition.service.search_usda_food", _raise_not_configured
    )
    monkeypatch.setattr(
        "app.nutrition.service.search_off_food", _raise_not_configured
    )

    assert search_food("eggs") is None


def test_search_normalizes_the_query(monkeypatch):
    received = {}

    monkeypatch.setattr(
        "app.nutrition.service.get_nutrition_from_gemini",
        _raise_not_configured
    )

    def fake_usda(food_name):
        received["query"] = food_name
        return {"name": "Egg, whole, cooked, hard-boiled", "calories": 155}

    monkeypatch.setattr(
        "app.nutrition.service.search_usda_food", fake_usda
    )

    result = search_food("  Boiled   Eggs ")

    assert received["query"] == "Boiled Eggs"
    assert result["source"] == "usda"


def test_search_rejects_empty_queries():
    assert search_food("") is None
    assert search_food("   ") is None
    assert search_food(None) is None


# ---------------------------------------------------------------------------
# Search route
# ---------------------------------------------------------------------------

def test_search_route_returns_result(monkeypatch):
    from app import create_app

    monkeypatch.setattr(
        "app.nutrition.routes.search_food",
        lambda *args, **kwargs: {
            "source": "usda",
            "food": {
                "name": "Egg, whole, raw, fresh",
                "serving_size": 100,
                "serving_unit": "g",
                "calories": 143,
                "protein": 12.4,
                "carbohydrates": 0.96,
                "fats": 9.96,
            },
        }
    )

    client = create_app().test_client()

    response = client.get(
        "/nutrition/search?food=eggs",
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 200
    assert response.get_json()["food"]["name"] == "Egg, whole, raw, fresh"


def test_search_route_handles_not_found_without_crashing(monkeypatch):
    from app import create_app

    monkeypatch.setattr(
        "app.nutrition.routes.search_food",
        lambda *args, **kwargs: None
    )

    client = create_app().test_client()

    response = client.get(
        "/nutrition/search?food=zzzz",
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 404
    assert response.get_json()["message"] == "Food not found"


def test_search_route_rejects_invalid_quantities():
    from app import create_app

    client = create_app().test_client()

    response = client.get(
        "/nutrition/search?food=eggs&quantity=-5",
        headers={"Accept": "application/json"}
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Mixed dishes (Gemini schema)
# ---------------------------------------------------------------------------

def test_mixed_dish_schema_accepts_components():
    result = NutritionResult.model_validate(MIXED_DISH_RESPONSE)

    assert result.estimate is True
    assert result.meat_weight_grams == 150
    assert len(result.components) == 3


def test_mixed_dish_components_do_not_double_count():
    result = NutritionResult.model_validate(MIXED_DISH_RESPONSE)

    component_grams = sum(c.grams for c in result.components)
    component_calories = sum(c.calories for c in result.components)

    # The meat is part of the total, so component grams and calories
    # must add up to the whole dish - not total + meat.
    assert component_grams == result.quantity_grams
    assert abs(component_calories - result.calories) < 1
    assert result.meat_weight_grams < result.quantity_grams


def test_simple_food_without_components_is_valid():
    result = NutritionResult.model_validate({
        "name": "Banana, raw",
        "quantity_grams": 118,
        "meat_weight_grams": None,
        "calories": 105,
        "protein": 1.3,
        "carbohydrates": 27,
        "fats": 0.4,
        "estimate": False,
    })

    assert result.components is None


# ---------------------------------------------------------------------------
# Live integration tests (opt-in)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Live nutrition providers require RUN_INTEGRATION_TESTS=1"
)
def test_search_food():
    result = search_food("apple")

    assert result is not None
    assert "source" in result
    assert "food" in result


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Live nutrition providers require RUN_INTEGRATION_TESTS=1"
)
def test_search_mixed_dish():
    result = search_food("chicken biryani", 300, 150)

    assert result is not None
    assert result["food"]["calories"] > 0
