import logging

from app.core.exceptions import NutritionProviderError, ProviderNotConfiguredError
from app.nutrition.meal_query import FOOD_ALIASES
from app.nutrition.matching import normalize_query
from app.nutrition.portions import MAX_QUANTITY, NUTRIENTS, scale_food
from app.nutrition.providers.open_food_facts import search_food as search_off_food
from app.nutrition.providers.usda import search_food as search_usda_food


logger = logging.getLogger(__name__)

# Reference portions for the biryani and ingredient lookups.
BIRYANI_REFERENCES = {
    "biryani rice": {
        "name": "Biryani rice", "serving_size": 125, "calories": 161,
        "protein": 3.5, "carbohydrates": 31, "fats": 2.3, "fiber": 1.1,
        "sugars": 0.4, "sodium_mg": 204,
        "source_name": "Tilda seasoned basmati rice reference",
        "source_url": "https://www.tilda.com/en-ie/products/steamed-pilau-basmati-rice/",
    },
    "vegetable biryani": {
        "name": "Vegetable biryani", "serving_size": 250, "calories": 298,
        "protein": 6, "carbohydrates": 50.6, "fats": 6.9, "fiber": 4.8,
        "sugars": 3.8, "sodium_mg": 636,
        "source_name": "Tilda vegetable biryani label",
        "source_url": "https://www.tilda.com/products/easy-meals-vegetable-biryani/",
    },
    "cooked chicken thigh": {
        "name": "Cooked chicken thigh", "serving_size": 100, "calories": 179,
        "protein": 24.76, "carbohydrates": 0, "fats": 8.15, "fiber": 0, "sugars": 0,
        "source_name": "USDA roasted chicken thigh, meat only",
        "source_url": "https://www.ars.usda.gov/ARSUserFiles/80400535/Data/SR/SR28/reports/sr28fg05.pdf",
    },
    "plain cooked rice": {
        "name": "Plain cooked rice", "serving_size": 100, "calories": 130,
        "protein": 2.69, "carbohydrates": 28.17, "fats": 0.28, "fiber": 0.4,
        "source_name": "USDA cooked white long-grain rice",
        "source_url": "https://www.ars.usda.gov/ARSUserFiles/80400535/Data/SR/SR28/reports/sr28fg20.pdf",
    },
    "ghee": {
        "name": "Ghee", "serving_size": 100, "calories": 876,
        "protein": 0.28, "carbohydrates": 0, "fats": 99.48, "fiber": 0, "sugars": 0,
        "source_name": "USDA butter oil reference",
        "source_url": "https://www.ars.usda.gov/ARSUserFiles/80400525/Data/SR/sr28/reports/sr28fg01.pdf",
    },
    "cooked chicken breast": {
        "name": "Cooked chicken breast", "serving_size": 100, "calories": 165,
        "protein": 31.02, "carbohydrates": 0, "fats": 3.57, "fiber": 0,
        "sugars": 0, "sodium_mg": 74,
        "source_name": "USDA roasted chicken breast",
        "source_url": "https://fdc.nal.usda.gov/food-details/171477/nutrients",
    },
    "chicken biryani": {
        "name": "Chicken biryani", "serving_size": 100, "calories": 141,
        "protein": 8.8, "carbohydrates": 18.5, "fats": 3.2, "fiber": 1.4,
        "sugars": 3.4, "sodium_mg": 180,
        "source_name": "Tesco chicken tikka biryani label",
        "source_url": "https://www.tesco.com/shop/en-GB/products/321964065",
    },
}


def _reference_result(record, quantity, unit):
    reference = {"serving_unit": "g", **record}
    selected = scale_food(reference, quantity if quantity is not None else record["serving_size"], unit or "g")
    return {
        "source": "reference", "reference": reference,
        "food": selected or scale_food(reference, record["serving_size"], "g"),
        "portion_unavailable": selected is None, "estimate": True,
    }


def search_food(food_name, quantity=None, meat_weight_grams=None, *, unit=None):
    food_name = normalize_query(food_name)
    if not food_name or meat_weight_grams is not None:
        return None
    key = food_name.lower()
    if key in BIRYANI_REFERENCES and key not in {"chicken biryani", "vegetable biryani"}:
        return _reference_result(BIRYANI_REFERENCES[key], quantity, unit)
    if key in {"biriyani", "briyani", "chicken biriyani", "chicken briyani"}:
        food_name = key.replace("biriyani", "biryani").replace("briyani", "biryani")
    food_name = FOOD_ALIASES.get(food_name.lower(), food_name)

    best = None
    provider_responded = False
    provider_failed = False
    for source, lookup in (("usda", search_usda_food), ("open_food_facts", search_off_food)):
        try:
            food = lookup(food_name)
        except ProviderNotConfiguredError:
            continue
        except Exception as error:
            provider_failed = True
            logger.warning("%s lookup failed (%s)", source, type(error).__name__)
            continue

        provider_responded = True
        if food is None:
            continue

        basis_unit = food["serving_unit"]
        amount = quantity if quantity is not None else food["serving_size"]
        requested_unit = unit or (basis_unit if quantity is None else "g")
        selected = scale_food(food, amount, requested_unit)
        fallback = scale_food(food, food["serving_size"], basis_unit)
        result = {
            "source": source,
            "food": selected or fallback,
            "reference": food,
            "portion_unavailable": selected is None,
            "estimate": True,
        }
        if selected and selected["complete"]:
            return result
        if best is None or (best["portion_unavailable"] and selected is not None):
            best = result
    if best is None and food_name.lower() in {"biryani", "chicken biryani", "vegetable biryani"}:
        record = BIRYANI_REFERENCES["chicken biryani" if food_name.lower() == "chicken biryani" else "vegetable biryani"]
        return _reference_result(record, quantity, unit)
    if provider_failed and not provider_responded:
        raise NutritionProviderError("Nutrition databases are unavailable")
    return best


def label_result(name, label_grams, serving_grams, nutrients):
    reference = {
        "name": name, "serving_size": label_grams, "serving_unit": "g",
        "source_name": "Nutrition label you entered", **nutrients,
    }
    return {
        "source": "user_label", "reference": reference,
        "food": scale_food(reference, serving_grams, "g"),
        "portion_unavailable": False,
    }


def search_meal(items, *, name=None, yield_grams=None, serving_grams=None):
    components = []
    for food_name, amount, unit in items:
        result = search_food(food_name, amount, unit=unit)
        if result is None:
            raise LookupError(f"No nutrition match for {food_name}. Try a more specific name.")
        if result["portion_unavailable"]:
            raise ValueError(f"Enter a measured amount in a supported unit for {food_name}.")
        food = result["food"]
        components.append({
            **food, "source": result["source"], "estimate": result.get("estimate", False),
        })

    grams = [food["quantity_grams"] for food in components]
    weighed = all(weight is not None for weight in grams)
    size, unit = (sum(grams), "g") if weighed else (1, "serving")
    if size > MAX_QUANTITY:
        raise ValueError(f"Enter a combined weight of {MAX_QUANTITY:,} g or less.")
    reference = {
        "name": name or " + ".join(food["name"] for food in components)[:200],
        "serving_size": yield_grams if yield_grams is not None else size,
        "serving_unit": "g" if yield_grams is not None else unit,
        **{
            key: sum(food[key] for food in components)
            if all(food[key] is not None for food in components) else None
            for key in NUTRIENTS
        },
    }
    return {
        "source": "recipe" if yield_grams is not None else "meal", "reference": reference,
        "food": scale_food(
            reference, serving_grams if yield_grams is not None else size, reference["serving_unit"],
        ),
        "recipe_yield": yield_grams,
        "components": components, "portion_unavailable": False,
        "estimate": any(food["estimate"] for food in components),
    }
