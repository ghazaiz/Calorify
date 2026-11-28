import os

import pytest

from app.core.exceptions import ProviderNotConfiguredError
from app.nutrition.matching import (
    MINIMUM_SCORE,
    best_match,
    normalize_query,
    score_candidate
)
from app.nutrition.providers.open_food_facts import (
    search_food as search_off_food
)
from app.nutrition.providers.usda import search_food as search_usda_food
from app.nutrition.service import search_food


RICE_RECORD = {
    "name": "Rice, cooked", "serving_size": 100, "serving_unit": "g",
    "calories": 130, "protein": 2.7, "carbohydrates": 28.2, "fats": 0.3,
    "fiber": 0.4, "sugars": 0, "sodium_mg": 1,
    "portions": {"serving": 150},
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
    assert food.get("fats") is None


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


def test_search_prefers_usda_and_scales_each_nutrient(monkeypatch):
    monkeypatch.setattr("app.nutrition.service.search_usda_food", lambda query: RICE_RECORD)
    monkeypatch.setattr("app.nutrition.service.search_off_food", lambda query: pytest.fail("Unexpected fallback"))

    result = search_food("cooked rice", 2, unit="serving")
    assert result["source"] == "usda"
    assert result["food"]["calories"] == 390
    assert result["food"]["protein"] == 8.1
    assert result["food"]["carbohydrates"] == 84.6
    assert result["food"]["fats"] == 0.9
    assert result["food"]["fiber"] == 1.2
    assert result["food"]["sodium_mg"] == 3
    assert result["food"]["quantity_grams"] == 300
    assert RICE_RECORD["calories"] == 130


@pytest.mark.parametrize("failure", [None, TimeoutError("provider timed out")])
def test_search_falls_through_to_label_data(monkeypatch, failure):
    def lookup(query):
        if failure:
            raise failure
        return None

    monkeypatch.setattr("app.nutrition.service.search_usda_food", lookup)
    monkeypatch.setattr("app.nutrition.service.search_off_food", lambda query: RICE_RECORD)
    result = search_food("rice", 250)
    assert result["source"] == "open_food_facts"
    assert result["food"]["calories"] == 325


def test_search_prefers_complete_fallback_and_never_fills_missing_macros(monkeypatch):
    incomplete = {**RICE_RECORD, "protein": None, "fats": None}
    monkeypatch.setattr("app.nutrition.service.search_usda_food", lambda query: incomplete)
    monkeypatch.setattr("app.nutrition.service.search_off_food", lambda query: RICE_RECORD)
    assert search_food("rice")["source"] == "open_food_facts"
    monkeypatch.setattr("app.nutrition.service.search_off_food", lambda query: None)
    result = search_food("rice")
    assert result["food"]["protein"] is None
    assert result["food"]["fats"] is None
    assert not result["food"]["complete"]


def test_search_returns_none_when_no_sources_are_configured(monkeypatch):
    monkeypatch.setattr("app.nutrition.service.search_usda_food", _raise_not_configured)
    monkeypatch.setattr("app.nutrition.service.search_off_food", _raise_not_configured)
    assert search_food("eggs") is None


def test_search_normalizes_the_query(monkeypatch):
    def lookup(query):
        assert query == "Boiled Eggs"
        return RICE_RECORD

    monkeypatch.setattr("app.nutrition.service.search_usda_food", lookup)
    assert search_food("  Boiled   Eggs ")["source"] == "usda"


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


def test_app_exposes_semantic_version():
    from app import create_app
    from app.version import APP_MAJOR, APP_MINOR, APP_PATCH, APP_VERSION

    app = create_app()
    assert app.config["APP_VERSION"] == APP_VERSION
    assert APP_VERSION == f"{APP_MAJOR}.{APP_MINOR}.{APP_PATCH}"


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1" or not os.getenv("USDA_API_KEY"),
    reason="Live USDA test requires RUN_INTEGRATION_TESTS=1 and a USDA API key",
)
def test_live_usda():
    food = search_usda_food("banana")
    assert food and "banana" in food["name"].lower()
    assert 60 < food["calories"] < 140


@pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Live Open Food Facts test requires RUN_INTEGRATION_TESTS=1",
)
def test_live_open_food_facts():
    food = search_off_food("nutella")
    assert food and food["calories"] > 0


def test_usda_uses_nutrient_ids_without_counting_duplicate_energy(monkeypatch):
    _mock_usda(monkeypatch, {"foods": [{
        "description": "Rice, cooked", "fdcId": 12345,
        "foodNutrients": [
            {"nutrientId": 1062, "unitName": "kJ", "value": 600},
            {"nutrientId": 2047, "unitName": "KCAL", "value": 125},
            {"nutrientId": 2048, "unitName": "KCAL", "value": 130},
            {"nutrientId": 1003, "unitName": "G", "value": 2.7},
            {"nutrientId": 1005, "unitName": "G", "value": 28.2},
            {"nutrientId": 1004, "unitName": "G", "value": 0.3},
            {"nutrientName": "Sugars, Total", "unitName": "G", "value": 9},
            {"nutrientId": 1093, "unitName": "MG", "value": 1},
        ],
    }]})
    food = search_usda_food("cooked rice")
    assert food["calories"] == 130
    assert food["carbohydrates"] == 28.2
    assert food["sodium_mg"] == 1


def test_usda_rejects_raw_or_unrelated_entries_for_boiled_eggs(monkeypatch):
    _mock_usda(monkeypatch, EGGS_USDA_PAYLOAD)
    assert search_usda_food("boiled eggs") is None


def test_off_keeps_liquid_basis_and_converts_label_servings(monkeypatch):
    _mock_off(monkeypatch, {"products": [{
        "product_name": "Orange juice", "product_quantity_unit": "ml",
        "serving_quantity": 200, "serving_quantity_unit": "ml",
        "nutriments": {
            "energy_100g": 209.2, "proteins_100g": 0,
            "carbohydrates_100g": 12, "fat_100g": 0, "sodium_100g": 0.02,
        },
    }]})
    food = search_off_food("orange juice")
    assert food["serving_unit"] == "ml"
    assert food["calories"] == pytest.approx(50)
    assert food["sodium_mg"] == 20
    assert food["portions"] == {"serving": 200}


def test_search_handles_piece_conversion_and_unsupported_units(monkeypatch):
    record = {**RICE_RECORD, "portions": {"piece": 25}}
    monkeypatch.setattr("app.nutrition.service.search_usda_food", lambda query: record)
    monkeypatch.setattr("app.nutrition.service.search_off_food", lambda query: None)
    assert search_food("rice", 2, unit="piece")["food"]["calories"] == 65
    assert search_food("rice", 2, unit="ml")["portion_unavailable"]


def test_all_provider_failures_render_a_friendly_error(monkeypatch):
    from app import create_app

    def fail(query):
        raise TimeoutError("private request metadata")

    monkeypatch.setattr("app.nutrition.service.search_usda_food", fail)
    monkeypatch.setattr("app.nutrition.service.search_off_food", fail)
    response = create_app().test_client().get("/nutrition/search?food=rice")
    assert response.status_code == 503
    assert b"Nutrition databases are unavailable" in response.data
    assert b"private request metadata" not in response.data


def test_lookup_serving_and_partial_result_render_without_a_profile(monkeypatch):
    from app import create_app

    monkeypatch.setattr("app.nutrition.service.search_usda_food", lambda query: RICE_RECORD)
    monkeypatch.setattr("app.nutrition.service.search_off_food", lambda query: None)
    client = create_app().test_client()
    response = client.get("/nutrition/search?food=cooked+rice&quantity=2&unit=serving")
    assert response.status_code == 200
    assert b"390.0" in response.data
    assert b"USDA FoodData Central" in response.data
    assert b"300.0 g total" in response.data
    assert client.get("/nutrition/search?food=rice&quantity=1&unit=ml").status_code == 422

    monkeypatch.setattr(
        "app.nutrition.service.search_usda_food",
        lambda query: {**RICE_RECORD, "protein": None},
    )
    response = client.get("/nutrition/search?food=rice")
    assert response.status_code == 200
    assert b"missing one or more macros" in response.data


@pytest.mark.parametrize("query", [
    "quantity=invalid", "quantity=100&meat_weight=150", "servings=nan", "unit=ounce",
])
def test_search_route_rejects_invalid_options_before_provider_call(monkeypatch, query):
    from app import create_app

    def unexpected_search(*args):
        pytest.fail("Invalid options reached the nutrition search")

    monkeypatch.setattr("app.nutrition.routes.search_food", unexpected_search)
    client = create_app().test_client()
    response = client.get(f"/nutrition/search?food=rice&{query}", headers={"Accept": "application/json"})
    assert response.status_code == 400


@pytest.mark.parametrize("search", [
    {"food": "chicken biryani", "quantity": "200", "unit": "g", "meat_weight": "100"},
    {"sentence": "I ate 200 g biryani rice and 100 g chicken breast"},
    {"sentence": "How many calories are there in 300 g chicken biryani including 100 g chicken breast?"},
])
def test_check_calculates_biryani_from_separate_weights(search):
    from app import create_app

    client = create_app().test_client()
    response = client.get("/nutrition/search", query_string=search, headers={"Accept": "application/json"})

    assert response.status_code == 200
    result = response.get_json()
    assert result["estimate"] is True
    assert result["food"]["quantity_grams"] == 300
    assert result["food"]["calories"] == 422.6
    assert [part["quantity_grams"] for part in result["components"]] == [200, 100]

    page = client.get("/nutrition/search", query_string=search)
    assert page.status_code == 200
    assert b"422.6" in page.data
    assert b"Estimate based on the references shown" in page.data


@pytest.mark.parametrize(("search", "calories", "ingredients"), [
    ({"food": "biryani", "quantity": "200", "meat_weight": "100", "chicken_cut": "thigh"},
     436.6, ["Biryani rice", "Cooked chicken thigh"]),
    ({"sentence": "I ate 200 g plain cooked rice, 100 g cooked chicken thigh and 10 g ghee"},
     526.6, ["Plain cooked rice", "Cooked chicken thigh", "Ghee"]),
])
def test_check_uses_selected_chicken_cut_and_measured_ghee(search, calories, ingredients):
    from app import create_app

    response = create_app().test_client().get(
        "/nutrition/search", query_string=search, headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    result = response.get_json()
    assert result["food"]["calories"] == calories
    assert [part["name"] for part in result["components"]] == ingredients


def test_check_scales_user_label_without_database_lookup(monkeypatch):
    from app import create_app

    def unexpected_search(*args, **kwargs):
        pytest.fail("A user-entered label should not need a database lookup")

    monkeypatch.setattr("app.nutrition.routes.search_food", unexpected_search)
    client = create_app().test_client()
    query = {
        "mode": "label", "food": "Packaged lasagna", "label_grams": 100,
        "serving_grams": 250, "label_calories": 180, "label_protein": 10,
    }
    response = client.get("/nutrition/search", query_string=query, headers={"Accept": "application/json"})
    assert response.status_code == 200
    result = response.get_json()
    assert result["food"]["calories"] == 450
    assert result["food"]["protein"] == 25
    assert result["food"]["fats"] is None
    assert b"Nutrition label you entered" in client.get("/nutrition/search", query_string=query).data


def test_recipe_scales_ingredients_by_finished_batch_weight(monkeypatch):
    from app import create_app

    def lookup(name):
        return {
            "name": name, "serving_size": 100, "serving_unit": "g",
            "calories": {"dry pasta": 350, "tomatoes": 25, "olive oil": 900}[name],
            "protein": 1, "carbohydrates": 1, "fats": 1,
        }

    monkeypatch.setattr("app.nutrition.service.search_usda_food", lookup)
    client = create_app().test_client()
    query = {
        "mode": "recipe", "food": "Pasta with tomato sauce",
        "ingredients": "300 g dry pasta\n400 g tomatoes\n20 g olive oil",
        "batch_grams": 950, "serving_grams": 190,
    }
    response = client.get("/nutrition/search", query_string=query, headers={"Accept": "application/json"})
    assert response.status_code == 200
    result = response.get_json()
    assert result["recipe_yield"] == 950
    assert [part["calories"] for part in result["components"]] == [1050, 100, 180]
    assert result["food"]["calories"] == 266
    assert result["food"]["quantity_grams"] == 190
    assert b"for the whole batch" in client.get("/nutrition/search", query_string=query).data
    assert client.get("/nutrition/search", query_string={**query, "serving_grams": 951}).status_code == 400


def test_check_extracts_food_and_amount_from_sentence(monkeypatch):
    from app import create_app

    def lookup(food, amount, *, unit):
        assert (food, amount, unit) == ("lasagna", 250, "g")
        return {"food": {"name": "Lasagna"}}

    monkeypatch.setattr("app.nutrition.routes.search_food", lookup)
    response = create_app().test_client().get(
        "/nutrition/search", query_string={"sentence": "I had about 250 grams of lasagna for lunch."},
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.get_json()["food"]["name"] == "Lasagna"


def test_usda_keeps_branded_liquid_basis(monkeypatch):
    _mock_usda(monkeypatch, {"foods": [{
        "description": "Orange juice", "dataType": "Branded",
        "servingSize": 200, "servingSizeUnit": "mL",
        "foodNutrients": [{"nutrientId": 1008, "unitName": "KCAL", "value": 48}],
    }]})
    record = search_usda_food("orange juice")
    assert record["serving_unit"] == "ml"
    assert record["portions"] == {"serving": 200}
