import os

import requests

from app.core.exceptions import ProviderNotConfiguredError
from app.nutrition.matching import best_match, compatible_food
from app.nutrition.portions import CORE_NUTRIENTS, KJ_PER_KCAL, label_portions, number


USDA_API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
DATA_TYPE_BONUS = {"Foundation": 0.10, "SR Legacy": 0.08, "Survey (FNDDS)": 0.04}

# Each entry maps a USDA nutrient ID to its result key and expected unit.
NUTRIENT_IDS = {
    1003: ("protein", "g"),
    1004: ("fats", "g"),
    1005: ("carbohydrates", "g"),
    1079: ("fiber", "g"),
    2000: ("sugars", "g"),
    1093: ("sodium_mg", "mg"),
}
ENERGY_IDS = (1008, 2048, 2047, 1062)
LEGACY_NAMES = {
    "protein": 1003, "total lipid (fat)": 1004, "carbohydrate, by difference": 1005,
    "fiber, total dietary": 1079, "total sugars": 2000, "sodium, na": 1093,
}


def _nutrients(rows):
    values = {}
    energy = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = number(row.get("value"))
        if value is None:
            continue
        unit = str(row.get("unitName", "")).lower()
        nutrient_id = row.get("nutrientId")
        if nutrient_id is None:
            name = str(row.get("nutrientName", "")).lower()
            nutrient_id = LEGACY_NAMES.get(name)
            if name == "energy":
                nutrient_id = 1008 if unit == "kcal" else 1062

        if nutrient_id in ENERGY_IDS:
            expected_unit = "kj" if nutrient_id == 1062 else "kcal"
            if unit == expected_unit:
                energy.setdefault(nutrient_id, value / KJ_PER_KCAL if unit == "kj" else value)
        elif isinstance(nutrient_id, int) and nutrient_id in NUTRIENT_IDS:
            key, expected_unit = NUTRIENT_IDS[nutrient_id]
            if unit == expected_unit:
                values.setdefault(key, value)

    values["calories"] = next((energy[key] for key in ENERGY_IDS if key in energy), None)
    return values


def _record(food):
    name = food.get("description")
    if not isinstance(name, str) or not name.strip():
        return None
    nutrients = _nutrients(food.get("foodNutrients") or [])
    if nutrients["calories"] is None or nutrients["calories"] > 1000:
        return None
    serving_unit = str(food.get("servingSizeUnit", "")).lower()
    data_type = food.get("dataType")
    basis = "ml" if data_type == "Branded" and serving_unit in {"ml", "mlt"} else "g"
    portions = label_portions(
        food.get("servingSize"), food.get("householdServingFullText")
    ) if serving_unit in {"g", "grm", "ml", "mlt"} else {}
    if serving_unit in {"ml", "mlt"} and basis == "g":
        portions = {}
    for measure in food.get("foodMeasures") or []:
        if not isinstance(measure, dict):
            continue
        weight = number(measure.get("gramWeight"))
        label = str(measure.get("disseminationText") or "").lower()
        if basis == "g" and weight and label.startswith("1 "):
            measured = label_portions(weight, label)
            if "piece" in measured:
                portions.setdefault("piece", measured["piece"])
            if label == "1 serving":
                portions.setdefault("serving", weight)
    for key in ("protein", "carbohydrates", "fats", "fiber", "sugars"):
        if nutrients.get(key, 0) > 100:
            nutrients.pop(key)
    if nutrients.get("sodium_mg", 0) > 100_000:
        nutrients.pop("sodium_mg")
    fdc_id = str(food.get("fdcId", ""))
    return {
        **nutrients, "name": name, "serving_size": 100, "serving_unit": basis,
        "portions": portions, "data_type": data_type,
        "source_url": f"https://fdc.nal.usda.gov/food-details/{fdc_id}/nutrients" if fdc_id.isdigit() else None,
    }


def search_food(food_name):
    api_key = os.getenv("USDA_API_KEY")
    if not api_key:
        raise ProviderNotConfiguredError("USDA_API_KEY is not configured")

    response = requests.get(
        USDA_API_URL,
        params={"api_key": api_key, "query": food_name, "pageSize": 35},
        timeout=5,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        return None
    candidates = []
    for food in data.get("foods") or []:
        if isinstance(food, dict) and (record := _record(food)):
            if compatible_food(food_name, record["name"]):
                candidates.append(record)

    complete = [food for food in candidates if all(food.get(key) is not None for key in CORE_NUTRIENTS)]
    return best_match(
        food_name, complete or candidates,
        get_name=lambda food: food["name"],
        get_bonus=lambda food: DATA_TYPE_BONUS.get(food["data_type"], 0),
    )
